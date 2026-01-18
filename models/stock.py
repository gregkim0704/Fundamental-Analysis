"""Stock data models."""
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class MarketType(str, Enum):
    """Market type enumeration."""
    KOREA_KOSPI = "KOSPI"
    KOREA_KOSDAQ = "KOSDAQ"
    US_NYSE = "NYSE"
    US_NASDAQ = "NASDAQ"
    US_AMEX = "AMEX"
    JAPAN_TSE = "TSE"
    CHINA_SSE = "SSE"
    CHINA_SZSE = "SZSE"
    HONG_KONG_HKEX = "HKEX"
    OTHER = "OTHER"


class StockInfo(BaseModel):
    """Basic stock information."""
    ticker: str = Field(..., description="Stock ticker symbol")
    name: str = Field(..., description="Company name")
    market: MarketType = Field(..., description="Market type")
    sector: Optional[str] = Field(None, description="Industry sector")
    industry: Optional[str] = Field(None, description="Specific industry")
    currency: str = Field(default="USD", description="Trading currency")
    country: str = Field(default="US", description="Country code")

    @property
    def is_korean(self) -> bool:
        """Check if stock is traded in Korean market."""
        return self.market in [MarketType.KOREA_KOSPI, MarketType.KOREA_KOSDAQ]

    @property
    def is_us(self) -> bool:
        """Check if stock is traded in US market."""
        return self.market in [MarketType.US_NYSE, MarketType.US_NASDAQ, MarketType.US_AMEX]


class Stock(BaseModel):
    """Stock model with price and fundamental data."""
    info: StockInfo = Field(..., description="Basic stock information")

    # Price data
    current_price: Optional[float] = Field(None, description="Current stock price")
    prev_close: Optional[float] = Field(None, description="Previous close price")
    market_cap: Optional[float] = Field(None, description="Market capitalization")
    volume: Optional[int] = Field(None, description="Trading volume")
    avg_volume: Optional[int] = Field(None, description="Average trading volume")

    # Price metrics
    price_52w_high: Optional[float] = Field(None, description="52-week high price")
    price_52w_low: Optional[float] = Field(None, description="52-week low price")
    beta: Optional[float] = Field(None, description="Beta coefficient")

    # Valuation metrics
    pe_ratio: Optional[float] = Field(None, description="P/E ratio (TTM)")
    forward_pe: Optional[float] = Field(None, description="Forward P/E ratio")
    pb_ratio: Optional[float] = Field(None, description="P/B ratio")
    ps_ratio: Optional[float] = Field(None, description="P/S ratio")
    ev_ebitda: Optional[float] = Field(None, description="EV/EBITDA ratio")
    peg_ratio: Optional[float] = Field(None, description="PEG ratio")

    # Dividend
    dividend_yield: Optional[float] = Field(None, description="Dividend yield (%)")
    dividend_payout_ratio: Optional[float] = Field(None, description="Dividend payout ratio")

    # Profitability
    roe: Optional[float] = Field(None, description="Return on Equity (%)")
    roa: Optional[float] = Field(None, description="Return on Assets (%)")
    roic: Optional[float] = Field(None, description="Return on Invested Capital (%)")
    profit_margin: Optional[float] = Field(None, description="Profit margin (%)")
    operating_margin: Optional[float] = Field(None, description="Operating margin (%)")
    gross_margin: Optional[float] = Field(None, description="Gross margin (%)")

    # Financial health
    current_ratio: Optional[float] = Field(None, description="Current ratio")
    quick_ratio: Optional[float] = Field(None, description="Quick ratio")
    debt_to_equity: Optional[float] = Field(None, description="Debt to equity ratio")
    interest_coverage: Optional[float] = Field(None, description="Interest coverage ratio")

    # Growth
    revenue_growth: Optional[float] = Field(None, description="Revenue growth rate (%)")
    earnings_growth: Optional[float] = Field(None, description="Earnings growth rate (%)")
    fcf_growth: Optional[float] = Field(None, description="FCF growth rate (%)")

    # Cash flow
    operating_cash_flow: Optional[float] = Field(None, description="Operating cash flow")
    free_cash_flow: Optional[float] = Field(None, description="Free cash flow")
    fcf_yield: Optional[float] = Field(None, description="FCF yield (%)")

    # Metadata
    last_updated: datetime = Field(default_factory=datetime.now, description="Last update time")

    @property
    def ticker(self) -> str:
        """Get ticker symbol."""
        return self.info.ticker

    @property
    def name(self) -> str:
        """Get company name."""
        return self.info.name

    @property
    def price_change_pct(self) -> Optional[float]:
        """Calculate price change percentage from previous close."""
        if self.current_price and self.prev_close and self.prev_close != 0:
            return ((self.current_price - self.prev_close) / self.prev_close) * 100
        return None

    @property
    def distance_from_52w_high(self) -> Optional[float]:
        """Calculate distance from 52-week high (%)."""
        if self.current_price and self.price_52w_high and self.price_52w_high != 0:
            return ((self.current_price - self.price_52w_high) / self.price_52w_high) * 100
        return None

    @property
    def distance_from_52w_low(self) -> Optional[float]:
        """Calculate distance from 52-week low (%)."""
        if self.current_price and self.price_52w_low and self.price_52w_low != 0:
            return ((self.current_price - self.price_52w_low) / self.price_52w_low) * 100
        return None


class FinancialStatements(BaseModel):
    """Financial statements data."""
    ticker: str = Field(..., description="Stock ticker")
    fiscal_year: int = Field(..., description="Fiscal year")
    fiscal_quarter: Optional[int] = Field(None, description="Fiscal quarter (1-4)")

    # Income Statement
    revenue: Optional[float] = Field(None, description="Total revenue")
    cost_of_revenue: Optional[float] = Field(None, description="Cost of revenue")
    gross_profit: Optional[float] = Field(None, description="Gross profit")
    operating_income: Optional[float] = Field(None, description="Operating income")
    net_income: Optional[float] = Field(None, description="Net income")
    ebitda: Optional[float] = Field(None, description="EBITDA")
    eps: Optional[float] = Field(None, description="Earnings per share")

    # Balance Sheet
    total_assets: Optional[float] = Field(None, description="Total assets")
    total_liabilities: Optional[float] = Field(None, description="Total liabilities")
    total_equity: Optional[float] = Field(None, description="Total equity")
    cash_and_equivalents: Optional[float] = Field(None, description="Cash and equivalents")
    total_debt: Optional[float] = Field(None, description="Total debt")
    net_debt: Optional[float] = Field(None, description="Net debt")
    working_capital: Optional[float] = Field(None, description="Working capital")
    book_value_per_share: Optional[float] = Field(None, description="Book value per share")

    # Cash Flow Statement
    operating_cash_flow: Optional[float] = Field(None, description="Operating cash flow")
    capital_expenditure: Optional[float] = Field(None, description="Capital expenditure")
    free_cash_flow: Optional[float] = Field(None, description="Free cash flow")
    dividends_paid: Optional[float] = Field(None, description="Dividends paid")
    share_buyback: Optional[float] = Field(None, description="Share buyback amount")

    # Calculated metrics
    invested_capital: Optional[float] = Field(None, description="Invested capital")
    nopat: Optional[float] = Field(None, description="NOPAT")

    @property
    def gross_margin(self) -> Optional[float]:
        """Calculate gross margin."""
        if self.gross_profit and self.revenue and self.revenue != 0:
            return (self.gross_profit / self.revenue) * 100
        return None

    @property
    def operating_margin(self) -> Optional[float]:
        """Calculate operating margin."""
        if self.operating_income and self.revenue and self.revenue != 0:
            return (self.operating_income / self.revenue) * 100
        return None

    @property
    def net_margin(self) -> Optional[float]:
        """Calculate net margin."""
        if self.net_income and self.revenue and self.revenue != 0:
            return (self.net_income / self.revenue) * 100
        return None

    @property
    def fcf_margin(self) -> Optional[float]:
        """Calculate FCF margin."""
        if self.free_cash_flow and self.revenue and self.revenue != 0:
            return (self.free_cash_flow / self.revenue) * 100
        return None
