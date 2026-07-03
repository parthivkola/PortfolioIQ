/**
 * Main app: hash-based router, views, interactions.
 */

const $ = (sel) => document.querySelector(sel);
const $root = () => $('#app');

function navigate(hash) { window.location.hash = hash; }

function fmt(val) {
  if (val == null) return '--';
  const n = parseFloat(val);
  return isNaN(n) ? val : n.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function pnlClass(val) {
  const n = parseFloat(val);
  if (n > 0) return 'positive';
  if (n < 0) return 'negative';
  return '';
}

function timeAgo(ts) {
  const d = new Date(ts);
  return d.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' });
}

// Toast notifications
function showToast(message, type = 'success') {
  let container = document.querySelector('.toast-container');
  if (!container) {
    container = document.createElement('div');
    container.className = 'toast-container';
    document.body.appendChild(container);
  }
  const icon = type === 'success' ? '&#10003;' : '&#10007;';
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `<span>${icon}</span> ${message}`;
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(8px)';
    toast.style.transition = '0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 2800);
}

// Router
window.addEventListener('hashchange', route);
window.addEventListener('DOMContentLoaded', () => {
  if (!window.location.hash) window.location.hash = '#/';
  route();
});

function route() {
  const hash = window.location.hash || '#/';
  if (!api.isLoggedIn() && hash !== '#/auth') { navigate('#/auth'); return; }
  if (api.isLoggedIn() && hash === '#/auth') { navigate('#/'); return; }

  if (hash === '#/auth') renderAuth();
  else if (hash === '#/') renderDashboard();
  else if (hash.startsWith('#/portfolio/')) renderPortfolio(hash.replace('#/portfolio/', ''));
  else renderDashboard();
}

function renderHeader() {
  if (!api.isLoggedIn()) return '';
  return `<header>
    <div class="logo">Portfolio<span>IQ</span></div>
    <nav>
      <button onclick="navigate('#/')">Dashboard</button>
      <button onclick="handleLogout()">Logout</button>
    </nav>
  </header>`;
}

// -------- Auth --------

function renderAuth() {
  $root().innerHTML = `
    ${renderHeader()}
    <div class="auth-wrapper">
      <div class="card auth-card">
        <h2 id="auth-title">Sign in</h2>
        <p class="subtitle" id="auth-sub">Access your portfolio dashboard</p>
        <div class="error-msg" id="auth-error"></div>
        <div id="auth-name-field" class="form-group" style="display:none">
          <label>Full name</label>
          <input type="text" id="auth-name" placeholder="Your name">
        </div>
        <div class="form-group">
          <label>Email</label>
          <input type="email" id="auth-email" placeholder="you@example.com">
        </div>
        <div class="form-group">
          <label>Password</label>
          <input type="password" id="auth-pass" placeholder="Minimum 8 characters">
        </div>
        <button class="btn btn-primary" id="auth-submit">Sign in</button>
        <p class="auth-toggle">
          <span id="auth-toggle-text">No account?</span>
          <a id="auth-toggle-link" onclick="toggleAuthMode()">Create one</a>
        </p>
      </div>
    </div>`;
  window._authMode = 'login';
  $('#auth-submit').addEventListener('click', handleAuth);
  $('#auth-pass').addEventListener('keydown', e => { if (e.key === 'Enter') handleAuth(); });
  $('#auth-email').addEventListener('keydown', e => { if (e.key === 'Enter') handleAuth(); });
}

function toggleAuthMode() {
  const isLogin = window._authMode === 'login';
  window._authMode = isLogin ? 'register' : 'login';
  $('#auth-title').textContent = isLogin ? 'Create account' : 'Sign in';
  $('#auth-sub').textContent = isLogin ? 'Start tracking your investments' : 'Access your portfolio dashboard';
  $('#auth-name-field').style.display = isLogin ? 'block' : 'none';
  $('#auth-submit').textContent = isLogin ? 'Create account' : 'Sign in';
  $('#auth-toggle-text').textContent = isLogin ? 'Have an account?' : 'No account?';
  $('#auth-toggle-link').textContent = isLogin ? 'Sign in' : 'Create one';
}

async function handleAuth() {
  const email = $('#auth-email').value;
  const pass = $('#auth-pass').value;
  const errEl = $('#auth-error');
  errEl.classList.remove('visible');

  try {
    let data;
    if (window._authMode === 'register') {
      data = await api.register(email, pass, $('#auth-name').value);
    } else {
      data = await api.login(email, pass);
    }
    api.setTokens(data.access_token, data.refresh_token);
    navigate('#/');
  } catch (e) {
    errEl.textContent = e.error || 'Something went wrong';
    errEl.classList.add('visible');
  }
}

async function handleLogout() {
  try { await api.request('POST', '/auth/logout'); } catch (_) {}
  api.clearTokens();
  navigate('#/auth');
}

// -------- Dashboard --------

async function renderDashboard() {
  $root().innerHTML = `${renderHeader()}<div class="app-container"><div class="loading"><div class="spinner"></div> Loading dashboard...</div></div>`;

  try {
    const [portfolios, dashboard] = await Promise.all([api.listPortfolios(), api.getDashboard()]);
    renderDashboardContent(portfolios, dashboard);
  } catch (e) {
    $root().innerHTML = `${renderHeader()}<div class="app-container"><div class="empty-state"><p>Could not load dashboard.</p><button class="btn btn-secondary" onclick="renderDashboard()">Retry</button></div></div>`;
  }
}

function renderDashboardContent(portfolios, dash) {
  const gain = dash.overall_gain || {};
  const gainAmt = gain.amount || '0';
  const gainPct = gain.percent || '0';
  const cls = pnlClass(gainAmt);

  let allocHtml = '';
  if (dash.asset_allocation && dash.asset_allocation.length) {
    allocHtml = dash.asset_allocation.map(a => `
      <div class="alloc-item">
        <span class="alloc-label">${a.asset_type}</span>
        <div class="alloc-track"><div class="alloc-fill" style="width:0%" data-width="${a.percent}"></div></div>
        <span class="alloc-pct">${a.percent}%</span>
      </div>`).join('');
  } else {
    allocHtml = '<p style="color:var(--text-dim);font-size:0.85rem">No allocations yet</p>';
  }

  let moversHtml = '';
  const gainers = dash.top_gainers || [];
  const losers = dash.top_losers || [];
  if (gainers.length || losers.length) {
    moversHtml = [
      ...gainers.map(g => `<div class="mover-item" onclick="showQuote('${g.symbol}')"><span class="mover-symbol">${g.symbol}</span><span class="mover-pct positive">+${g.percent}%</span></div>`),
      ...losers.map(l => `<div class="mover-item" onclick="showQuote('${l.symbol}')"><span class="mover-symbol">${l.symbol}</span><span class="mover-pct negative">${l.percent}%</span></div>`),
    ].join('');
  } else {
    moversHtml = '<p style="color:var(--text-dim);font-size:0.85rem">No movement data yet</p>';
  }

  let txnsHtml = '';
  const txns = dash.recent_transactions || [];
  if (txns.length) {
    txnsHtml = txns.map(t => `
      <div class="txn-item">
        <div><span class="txn-badge ${t.transaction_type}">${t.transaction_type}</span><span class="txn-symbol">${t.symbol}</span></div>
        <span class="txn-time">${timeAgo(t.timestamp)}</span>
      </div>`).join('');
  } else {
    txnsHtml = '<p style="color:var(--text-dim);font-size:0.85rem">No transactions yet</p>';
  }

  let portfolioListHtml = '';
  if (portfolios.length) {
    portfolioListHtml = portfolios.map(p => `
      <div class="portfolio-item" onclick="navigate('#/portfolio/${p.id}')">
        <span class="name">${p.name}</span>
        <span class="arrow">&#8594;</span>
      </div>`).join('');
  }

  $root().innerHTML = `
    ${renderHeader()}
    <div class="app-container">
      <div class="page-header">
        <div class="page-title">Dashboard</div>
        <button class="btn btn-secondary btn-sm" onclick="renderDashboard()">&#8635; Refresh</button>
      </div>
      <div class="stats-row">
        <div class="card">
          <div class="card-title">Current Value</div>
          <div class="stat-value">${fmt(dash.current_value)}</div>
        </div>
        <div class="card">
          <div class="card-title">Total Invested</div>
          <div class="stat-value">${fmt(dash.total_invested)}</div>
        </div>
        <div class="card">
          <div class="card-title">Overall Gain</div>
          <div class="stat-value ${cls}">${fmt(gainAmt)}</div>
          <div class="stat-sub ${cls}">${parseFloat(gainPct) >= 0 ? '+' : ''}${gainPct}%</div>
        </div>
      </div>
      <div class="dashboard-grid">
        <div class="card">
          <div class="card-title">Asset Allocation</div>
          <div class="alloc-bar-group" style="margin-top:14px">${allocHtml}</div>
        </div>
        <div class="card">
          <div class="card-title">Top Movers</div>
          <div class="mover-list" style="margin-top:14px">${moversHtml}</div>
        </div>
      </div>
      <div class="dashboard-grid">
        <div class="card">
          <div class="card-title">Recent Transactions</div>
          <div class="txn-list" style="margin-top:14px">${txnsHtml}</div>
        </div>
        <div class="card">
          <div class="card-header">
            <div class="card-title">Portfolios</div>
            <button class="btn btn-secondary btn-sm" onclick="showCreatePortfolio()">+ New</button>
          </div>
          <div class="portfolio-list">${portfolioListHtml || '<div class="empty-state" style="padding:24px"><p>Create your first portfolio</p><button class="btn btn-primary btn-sm" onclick="showCreatePortfolio()" style="width:auto;margin:0 auto">Get Started</button></div>'}</div>
        </div>
      </div>
    </div>
    <div class="modal-overlay" id="modal-overlay" onclick="closeModal(event)">
      <div class="modal" id="modal-content"></div>
    </div>`;

  // Animate allocation bars after render
  requestAnimationFrame(() => {
    document.querySelectorAll('.alloc-fill[data-width]').forEach(el => {
      setTimeout(() => { el.style.width = el.dataset.width + '%'; }, 100);
    });
  });
}

// -------- Portfolio Detail --------

async function renderPortfolio(id) {
  $root().innerHTML = `${renderHeader()}<div class="app-container"><div class="loading"><div class="spinner"></div> Loading portfolio...</div></div>`;

  try {
    const [holdings, perf, alloc, txnData] = await Promise.all([
      api.listHoldings(id),
      api.getPerformance(id).catch(() => null),
      api.getAllocation(id).catch(() => null),
      api.listTransactions(id).catch(() => ({ data: [] })),
    ]);

    const priceMap = {};
    await Promise.all(holdings.map(async h => {
      try {
        const q = await api.getQuote(h.symbol);
        priceMap[h.symbol] = parseFloat(q.price);
      } catch (_) {
        priceMap[h.symbol] = parseFloat(h.average_buy_price);
      }
    }));

    renderPortfolioContent(id, holdings, perf, alloc, txnData.data || [], priceMap);
  } catch (e) {
    $root().innerHTML = `${renderHeader()}<div class="app-container"><div class="empty-state"><p>Could not load portfolio.</p><button class="btn btn-secondary" onclick="renderPortfolio('${id}')">Retry</button></div></div>`;
  }
}

function renderPortfolioContent(pid, holdings, perf, alloc, txns, priceMap) {
  let metricsHtml = '';
  if (perf) {
    const items = [
      { label: 'XIRR', value: perf.xirr ? perf.xirr + '%' : '--' },
      { label: 'CAGR', value: perf.cagr ? perf.cagr + '%' : '--' },
      { label: 'Absolute Return', value: perf.absolute_return_percent + '%', cls: pnlClass(perf.absolute_return_percent) },
      { label: 'Unrealized P&L', value: fmt(perf.unrealized_pnl), cls: pnlClass(perf.unrealized_pnl) },
      { label: 'Realized P&L', value: fmt(perf.realized_pnl), cls: pnlClass(perf.realized_pnl) },
    ];
    metricsHtml = items.map(m => `<div class="metric-card"><div class="metric-label">${m.label}</div><div class="metric-value ${m.cls || ''}">${m.value}</div></div>`).join('');
  }

  let holdingsHtml = '';
  if (holdings.length) {
    const rows = holdings.map(h => {
      const qty = parseFloat(h.quantity);
      const avg = parseFloat(h.average_buy_price);
      const cur = priceMap[h.symbol] || avg;
      const pnl = qty * (cur - avg);
      const pnlPct = avg > 0 ? ((cur - avg) / avg * 100) : 0;
      return `<tr>
        <td><span class="symbol-link" onclick="showQuote('${h.symbol}')">${h.symbol}</span></td>
        <td>${h.asset_type}</td>
        <td class="num">${fmt(qty)}</td>
        <td class="num">${fmt(avg)}</td>
        <td class="num">${fmt(cur)}</td>
        <td class="num ${pnlClass(pnl)}">${fmt(pnl)}</td>
        <td class="num ${pnlClass(pnlPct)}">${pnlPct >= 0 ? '+' : ''}${pnlPct.toFixed(1)}%</td>
      </tr>`;
    }).join('');
    holdingsHtml = `<table class="data-table">
      <thead><tr><th>Symbol</th><th>Type</th><th class="num">Qty</th><th class="num">Avg Price</th><th class="num">LTP</th><th class="num">P&L</th><th class="num">%</th></tr></thead>
      <tbody>${rows}</tbody>
    </table>`;
  } else {
    holdingsHtml = '<div class="empty-state"><p>No holdings yet.</p><button class="btn btn-primary btn-sm" style="width:auto;margin:0 auto" onclick="showAddHolding(\'' + pid + '\')">Add First Holding</button></div>';
  }

  let txnHtml = '';
  if (txns.length) {
    txnHtml = txns.slice(0, 10).map(t => `
      <tr>
        <td><span class="txn-badge ${t.transaction_type}">${t.transaction_type}</span></td>
        <td>${fmt(t.quantity)}</td>
        <td class="num">${fmt(t.price)}</td>
        <td class="num">${timeAgo(t.timestamp)}</td>
      </tr>`).join('');
    txnHtml = `<table class="data-table"><thead><tr><th>Type</th><th>Qty</th><th class="num">Price</th><th class="num">Date</th></tr></thead><tbody>${txnHtml}</tbody></table>`;
  }

  $root().innerHTML = `
    ${renderHeader()}
    <div class="app-container">
      <div class="breadcrumb">
        <a onclick="navigate('#/')">Dashboard</a>
        <span class="sep">/</span>
        <span>Portfolio</span>
      </div>
      ${metricsHtml ? `<div class="metrics-row">${metricsHtml}</div>` : ''}
      <div class="card" style="margin-bottom:16px">
        <div class="card-header">
          <div class="card-title">Holdings</div>
          <div style="display:flex;gap:8px">
            <button class="btn btn-secondary btn-sm" onclick="showAddHolding('${pid}')">+ Holding</button>
            <button class="btn btn-secondary btn-sm" onclick="showAddTransaction('${pid}')">+ Transaction</button>
            <button class="btn btn-secondary btn-sm" onclick="renderPortfolio('${pid}')">&#8635;</button>
          </div>
        </div>
        ${holdingsHtml}
      </div>
      ${txnHtml ? `<div class="card"><div class="card-title" style="margin-bottom:12px">Recent Transactions</div>${txnHtml}</div>` : ''}
    </div>
    <div class="modal-overlay" id="modal-overlay" onclick="closeModal(event)">
      <div class="modal" id="modal-content"></div>
    </div>`;
}

// -------- Quote popup --------

async function showQuote(symbol) {
  openModal(`<div class="loading" style="padding:20px"><div class="spinner"></div> Fetching quote...</div>`);
  try {
    const q = await api.getQuote(symbol);
    openModal(`
      <div class="quote-popup" style="box-shadow:none;border:none;padding:0">
        <div class="quote-symbol">${symbol}</div>
        <div class="quote-price">${fmt(q.price)}</div>
        <div class="quote-meta">Source: ${q.source || 'provider'} &middot; ${q.as_of ? new Date(q.as_of).toLocaleString('en-IN') : '--'}</div>
      </div>
      <div class="modal-actions" style="margin-top:20px">
        <button class="btn btn-secondary" onclick="closeModal({target:$('#modal-overlay'),currentTarget:$('#modal-overlay')})">Close</button>
      </div>`);
  } catch (_) {
    openModal(`<p style="color:var(--red);margin-bottom:16px">Could not fetch quote for ${symbol}</p>
      <button class="btn btn-secondary" onclick="closeModal({target:$('#modal-overlay'),currentTarget:$('#modal-overlay')})" style="width:100%">Close</button>`);
  }
}

// -------- Modals --------

function openModal(html) {
  $('#modal-content').innerHTML = html;
  $('#modal-overlay').classList.add('active');
}

function closeModal(e) {
  if (e && e.target !== e.currentTarget) return;
  $('#modal-overlay').classList.remove('active');
}

function showCreatePortfolio() {
  openModal(`
    <h3>Create Portfolio</h3>
    <div class="form-group"><label>Name</label><input type="text" id="m-pname" placeholder="e.g. Long Term Equity" autofocus></div>
    <div class="error-msg" id="m-error"></div>
    <div class="modal-actions">
      <button class="btn btn-secondary" onclick="closeModal(arguments[0])">Cancel</button>
      <button class="btn btn-primary" onclick="submitCreatePortfolio()">Create</button>
    </div>`);
  setTimeout(() => { const el = $('#m-pname'); if (el) el.focus(); }, 100);
}

async function submitCreatePortfolio() {
  const name = $('#m-pname').value.trim();
  if (!name) return;
  try {
    await api.createPortfolio(name);
    closeModal({ target: $('#modal-overlay'), currentTarget: $('#modal-overlay') });
    showToast('Portfolio created');
    renderDashboard();
  } catch (e) {
    const el = $('#m-error');
    el.textContent = e.error || 'Failed';
    el.classList.add('visible');
  }
}

function showAddHolding(pid) {
  openModal(`
    <h3>Add Holding</h3>
    <div class="form-group"><label>Symbol</label><input type="text" id="m-symbol" placeholder="e.g. RELIANCE.NS" autofocus></div>
    <div class="form-group"><label>Asset type</label>
      <select id="m-atype"><option value="STOCK">Stock</option><option value="ETF">ETF</option><option value="MUTUAL_FUND">Mutual Fund</option><option value="BOND">Bond</option><option value="GOLD">Gold</option></select>
    </div>
    <div class="error-msg" id="m-error"></div>
    <div class="modal-actions">
      <button class="btn btn-secondary" onclick="closeModal(arguments[0])">Cancel</button>
      <button class="btn btn-primary" onclick="submitAddHolding('${pid}')">Add</button>
    </div>`);
  setTimeout(() => { const el = $('#m-symbol'); if (el) el.focus(); }, 100);
}

async function submitAddHolding(pid) {
  const sym = $('#m-symbol').value.trim().toUpperCase();
  const atype = $('#m-atype').value;
  if (!sym) return;
  try {
    await api.createHolding(pid, atype, sym);
    closeModal({ target: $('#modal-overlay'), currentTarget: $('#modal-overlay') });
    showToast(`${sym} added`);
    renderPortfolio(pid);
  } catch (e) {
    const el = $('#m-error');
    el.textContent = e.error || 'Failed';
    el.classList.add('visible');
  }
}

async function showAddTransaction(pid) {
  let holdings;
  try { holdings = await api.listHoldings(pid); } catch (_) { holdings = []; }

  if (!holdings.length) {
    openModal(`<h3>No holdings</h3><p style="color:var(--text-secondary);margin-bottom:16px">Add a holding first before recording transactions.</p>
      <button class="btn btn-secondary" onclick="closeModal(arguments[0])" style="width:100%">OK</button>`);
    return;
  }

  const opts = holdings.map(h => `<option value="${h.id}">${h.symbol}</option>`).join('');
  const now = new Date().toISOString().slice(0, 16);

  openModal(`
    <h3>Record Transaction</h3>
    <div class="form-group"><label>Holding</label><select id="m-thid">${opts}</select></div>
    <div class="form-group"><label>Type</label>
      <select id="m-ttype"><option value="BUY">Buy</option><option value="SELL">Sell</option><option value="DIVIDEND">Dividend</option></select>
    </div>
    <div class="form-group"><label>Quantity</label><input type="number" id="m-tqty" placeholder="10" step="any"></div>
    <div class="form-group"><label>Price</label><input type="number" id="m-tprice" placeholder="2450.50" step="any"></div>
    <div class="form-group"><label>Date & time</label><input type="datetime-local" id="m-tdate" value="${now}"></div>
    <div class="error-msg" id="m-error"></div>
    <div class="modal-actions">
      <button class="btn btn-secondary" onclick="closeModal(arguments[0])">Cancel</button>
      <button class="btn btn-primary" onclick="submitAddTransaction('${pid}')">Submit</button>
    </div>`);
}

async function submitAddTransaction(pid) {
  const hid = $('#m-thid').value;
  const type = $('#m-ttype').value;
  const qty = $('#m-tqty').value;
  const price = $('#m-tprice').value;
  const dt = $('#m-tdate').value;
  if (!qty || !price) return;

  const ts = new Date(dt).toISOString();
  try {
    await api.createTransaction(hid, type, qty, price, ts);
    closeModal({ target: $('#modal-overlay'), currentTarget: $('#modal-overlay') });
    showToast(`${type} recorded`);
    renderPortfolio(pid);
  } catch (e) {
    const el = $('#m-error');
    el.textContent = e.error || 'Failed';
    el.classList.add('visible');
  }
}
