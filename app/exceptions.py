"""Domain exceptions mapped to API error codes from the specification."""


class DomainError(Exception):
    """Base for all domain-level errors."""

    def __init__(self, message: str, code: str, status_code: int = 400):
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(message)


# -- Auth --


class AuthError(DomainError):
    def __init__(self, message: str = "Authentication failed", code: str = "AUTH_001"):
        super().__init__(message, code, status_code=401)


class RateLimitError(DomainError):
    def __init__(self, message: str = "Too many requests"):
        super().__init__(message, "AUTH_004", status_code=429)


# -- Portfolio --


class PortfolioNotFoundError(DomainError):
    def __init__(self):
        super().__init__("Portfolio not found", "PORTFOLIO_001", 404)


class PortfolioAccessDeniedError(DomainError):
    def __init__(self):
        super().__init__(
            "Portfolio does not belong to the authenticated user",
            "PORTFOLIO_002",
            403,
        )


class PortfolioNameConflictError(DomainError):
    def __init__(self):
        super().__init__("Portfolio name already exists for this user", "PORTFOLIO_003", 409)


class PortfolioHasHoldingsError(DomainError):
    def __init__(self):
        super().__init__(
            "Portfolio cannot be deleted while it has open holdings", "PORTFOLIO_004", 400
        )


# -- Holding --


class HoldingNotFoundError(DomainError):
    def __init__(self):
        super().__init__("Holding not found", "HOLDING_001", 404)


class HoldingAlreadyExistsError(DomainError):
    def __init__(self):
        super().__init__(
            "Holding already exists for this symbol in this portfolio", "HOLDING_002", 409
        )


# -- Transaction --


class OverSellError(DomainError):
    def __init__(self):
        super().__init__("Sell would reduce quantity below zero", "TXN_001", 400)


class SellExceedsQuantityError(DomainError):
    def __init__(self):
        super().__init__("Sell quantity exceeds current holding quantity", "TXN_002", 400)


class DuplicateTransactionError(DomainError):
    def __init__(self):
        super().__init__("Duplicate transaction", "TXN_003", 409)


# -- Analytics --


class XIRRConvergenceError(DomainError):
    def __init__(self, detail: str = "XIRR undefined for the given cash-flow series"):
        super().__init__(detail, "ANALYTICS_001", 422)


# -- Market --


class MarketProviderError(DomainError):
    def __init__(self):
        super().__init__("Market data provider unavailable", "MARKET_001", 503)
