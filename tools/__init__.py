"""Tools module for agent interactions with external data sources."""
from tools.financial_data import (
    get_financial_statements,
    get_income_statement,
    get_balance_sheet,
    get_cash_flow,
)
from tools.stock_price import (
    get_stock_info,
    get_stock_price,
    get_price_history,
)
from tools.macro_data import (
    get_interest_rates,
    get_economic_indicators,
)
from tools.valuation_calc import (
    calculate_dcf,
    calculate_multiples,
)

__all__ = [
    # Financial data
    "get_financial_statements",
    "get_income_statement",
    "get_balance_sheet",
    "get_cash_flow",
    # Stock price
    "get_stock_info",
    "get_stock_price",
    "get_price_history",
    # Macro data
    "get_interest_rates",
    "get_economic_indicators",
    # Valuation
    "calculate_dcf",
    "calculate_multiples",
]
