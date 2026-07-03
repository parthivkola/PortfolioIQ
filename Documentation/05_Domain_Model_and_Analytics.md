**PORTFOLIO INTELLIGENCE PLATFORM**

**Domain Model & Analytics Algorithms**

*Entities, invariants, and the math behind the Analytics Engine*

**Version:  **1.0

**Author:  **Kola

**Positioning:  **This is a Financial Analytics Engine with a portfolio CRUD surface, not the other way around.


# **1. Why Analytics Is the Core, Not CRUD**


***Portfolio, Holding, and Transaction CRUD exists to feed one thing: the Analytics Engine. The value a user gets from this platform isn't storing their holdings — it's the correct, defensible computation of returns, risk, and allocation on top of that data. Every other component exists to get clean, immutable data into the engine and get computed results back out.***

*Figure 1 — Data flows from an immutable ledger through the Portfolio Engine into the Analytics Engine, which is the true product surface.*


# **2. Domain Model**



## **2.1 Core Entities**


**Entity**

**Definition**

Transaction

An immutable, timestamped fact: a BUY, SELL, DIVIDEND, BONUS, or SPLIT event for a given holding, at a given quantity and price.

Holding

A derived, mutable projection: the current quantity and weighted-average cost basis of one asset within one portfolio, computed by folding its Transactions.

Portfolio

A named container of Holdings owned by one user; has no directly-stored value — value is always computed.

PortfolioSnapshot

A point-in-time computed rollup of a Portfolio's value and invested capital, used both for history charts and as the cash-flow series XIRR is computed over.

MarketSnapshot

A point-in-time observed price for a symbol, sourced from the Market Data Provider.


## **2.2 Business Invariants**


***These are the rules the system must never violate, regardless of which API path or background job touches the data. They are enforced in the Portfolio Engine's service layer (not just the database), because some of them are behavioral rather than structural.***

- Transactions are append-only. Corrections are made by inserting a compensating transaction, never by mutating or deleting a historical row. This preserves an audit trail and guarantees XIRR's cash-flow series is reproducible.

- Holdings are derived, never directly written by a client. quantity and average_buy_price on a Holding are recomputed from its Transaction history; the PUT /holdings/{id} endpoint exists only for administrative correction and is logged distinctly from normal flow.

- Portfolio value is always computed, never stored as an editable field. It is quantity x latest_market_price, summed across Holdings — there is no 'set portfolio value' operation anywhere in the system.

- A SELL transaction cannot reduce a Holding's quantity below zero. Attempting to oversell is rejected with a 400 (error code TXN_001), not silently clamped.

- average_buy_price only changes on BUY (and SPLIT-adjustment) events. SELL transactions reduce quantity but leave the average buy price of the remaining position unchanged (standard weighted-average-cost accounting).

- PortfolioSnapshot rows, once written, are immutable — the daily snapshot job never rewrites a past day's snapshot, even if historical MarketSnapshot data is later corrected. A correction produces a new, separately-flagged snapshot instead.


## **2.3 Holding State Transitions**


**Event**

**Effect on Holding**

BUY qty=q @ price=p

new_qty = qty + q;  new_avg = ((qty*avg) + (q*p)) / new_qty

SELL qty=q

new_qty = qty - q;  avg unchanged;  realized_pnl += q * (current_avg - avg... see 3.4)

DIVIDEND amount=a

qty and avg unchanged; contributes to dividend_income, not to cost basis

BONUS ratio=r

new_qty = qty * (1 + r);  new_avg = avg / (1 + r)  (cost basis redistributed over more units)

SPLIT ratio=r

new_qty = qty * r;  new_avg = avg / r  (same economic value, more units)


# **3. Analytics Algorithms**



## **3.1 XIRR (Extended Internal Rate of Return) — Newton-Raphson**


***XIRR solves for the annualized discount rate r that makes the net present value of an irregular series of cash flows equal to zero. Unlike CAGR, it correctly handles cash flows that occur at arbitrary, non-uniform dates — exactly the shape of a real portfolio's BUY/SELL/DIVIDEND history.***


### **Formula**


NPV(r) = sum_{i=0}^{n} CF_i / (1 + r)^((d_i - d_0) / 365)

Find r such that NPV(r) = 0

***Where CF_i is the signed cash flow at date d_i (outflows/BUYs negative, inflows/SELLs and the final portfolio value positive), and d_0 is the date of the first cash flow.***


### **Newton-Raphson Iteration**


r_{n+1} = r_n - NPV(r_n) / NPV'(r_n)

NPV'(r) = sum_{i=0}^{n} -t_i * CF_i / (1 + r)^(t_i + 1),   t_i = (d_i - d_0) / 365


### **Pseudocode**


def xirr(cash_flows, dates, guess=0.1, tol=1e-6, max_iter=100):
    r = guess
    d0 = dates[0]
    for _ in range(max_iter):
        t = [(d - d0).days / 365.0 for d in dates]
        npv  = sum(cf / (1 + r) ** ti for cf, ti in zip(cash_flows, t))
        dnpv = sum(-ti * cf / (1 + r) ** (ti + 1) for cf, ti in zip(cash_flows, t))
        if abs(dnpv) < 1e-12:
            raise XIRRConvergenceError("derivative too small")
        r_next = r - npv / dnpv
        if abs(r_next - r) < tol:
            return r_next
        r = r_next
    raise XIRRConvergenceError("did not converge in max_iter")


### **Edge Cases the Implementation Must Handle**


- All cash flows same sign (e.g., only BUYs, no current value) — no real root exists; the performance service returns a `null` value for XIRR to prevent dashboard UI breakage.

- Non-convergence within max_iter — fall back to a bisection method over a bounded range (e.g., -0.99 to 10.0) as a safety net. If that also fails, return `null`.

- Single cash flow (or days held < 1) — XIRR and CAGR are undefined; the performance service returns `null` for these metrics.


- The cash-flow series is built from PortfolioSnapshot + Transaction history: every BUY/transfer-in is a negative flow, every SELL/DIVIDEND/transfer-out is a positive flow, and the most recent portfolio value is appended as a final synthetic positive flow at today's date.


## **3.2 CAGR (Compound Annual Growth Rate)**


***CAGR assumes a single lump-sum investment held for a fixed period — simpler than XIRR but not accurate for portfolios with multiple cash flows at different times. It is retained as a complementary, easier-to-explain headline metric alongside XIRR.***

CAGR = (ending_value / beginning_value) ^ (365 / days_held) - 1


## **3.3 Weighted Average Buy Price**


***Maintained incrementally on every BUY so historical recomputation isn't required for every read (see state transition table in Section 2.3):***

new_avg_price = ((existing_qty * existing_avg_price) + (buy_qty * buy_price)) / (existing_qty + buy_qty)


## **3.4 Realized vs Unrealized P&L**


unrealized_pnl = sum over open holdings of: quantity * (latest_market_price - average_buy_price)

realized_pnl   = sum over SELL transactions of: sell_qty * (sell_price - average_buy_price_at_time_of_sale)

***Realized P&L is computed and persisted at the moment a SELL transaction is processed (using the average buy price at that instant), not recalculated retroactively — this keeps historical realized P&L stable even as later BUYs change the current average.***


## **3.5 Diversification Score**


***Computed as the complement of the Herfindahl-Hirschman Index (HHI) over holding weights, normalized to a 0-1 scale where higher means more diversified:***

HHI = sum_{i=1}^{n} (w_i)^2,   where w_i = holding_i_value / total_portfolio_value

diversification_score = 1 - HHI    (0 = fully concentrated in one asset, approaching 1 = maximally diversified)


## **3.6 Tax-Loss Harvesting Candidates**


***Surfaces holdings where unrealized loss exceeds a materiality threshold, as candidates a user may want to review — the platform does not execute trades or give tax advice, only surfaces the computed opportunity.***

for holding in open_holdings:
    unrealized = holding.quantity * (latest_price(holding.symbol) - holding.average_buy_price)
    if unrealized < 0 and abs(unrealized) >= MATERIALITY_THRESHOLD:
        candidates.append({ holding, unrealized_loss: unrealized })
return sorted(candidates, key=lambda c: c.unrealized_loss)  # largest loss first


# **4. Cache Invalidation Matrix**


***Every write that changes a value feeding a cached read must invalidate the corresponding key(s). This table is the authoritative reference the Analytics and Portfolio services implement against.***

**Write Event**

**Keys Invalidated**

New Transaction (BUY/SELL/DIVIDEND/BONUS/SPLIT)

dashboard:{user_id}, analytics:{portfolio_id}

Holding manual correction (PUT /holdings/{id})

dashboard:{user_id}, analytics:{portfolio_id}

Portfolio renamed/created/deleted

dashboard:{user_id}

Scheduled market price refresh

quote:{symbol}  (repopulated, not just deleted)

Daily snapshot job

analytics:{portfolio_id}  (new snapshot changes XIRR inputs)