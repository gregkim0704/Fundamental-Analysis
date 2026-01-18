"""ROIC and WACC calculation logic."""
import logging
from typing import Any, Optional

import yfinance as yf
import numpy as np

logger = logging.getLogger(__name__)


class ROICCalculator:
    """Calculate Return on Invested Capital (ROIC)."""

    def __init__(self, ticker: str):
        """Initialize ROIC calculator.

        Args:
            ticker: Stock ticker symbol
        """
        self.ticker = ticker
        self._stock = yf.Ticker(ticker)
        self._info = self._stock.info
        self._income = self._stock.income_stmt
        self._balance = self._stock.balance_sheet

    def calculate_invested_capital(self) -> Optional[float]:
        """Calculate invested capital.

        Invested Capital = Total Equity + Total Debt - Cash

        Returns:
            Invested capital or None if data unavailable
        """
        try:
            if self._balance.empty:
                return None

            latest = self._balance.iloc[:, 0]

            # Get components
            total_equity = None
            for equity_key in ["Total Equity Gross Minority Interest", "Stockholders Equity", "Total Stockholder Equity"]:
                if equity_key in latest.index:
                    total_equity = latest[equity_key]
                    break

            total_debt = latest.get("Total Debt", 0) or 0
            cash = latest.get("Cash And Cash Equivalents", 0) or 0

            if total_equity is None:
                return None

            invested_capital = total_equity + total_debt - cash
            return float(invested_capital)

        except Exception as e:
            logger.error(f"Error calculating invested capital: {e}")
            return None

    def calculate_nopat(self, tax_rate: Optional[float] = None) -> Optional[float]:
        """Calculate Net Operating Profit After Tax (NOPAT).

        NOPAT = Operating Income × (1 - Tax Rate)

        Args:
            tax_rate: Effective tax rate (if None, estimate from financials)

        Returns:
            NOPAT or None if data unavailable
        """
        try:
            if self._income.empty:
                return None

            latest = self._income.iloc[:, 0]

            # Get operating income
            operating_income = None
            for op_key in ["Operating Income", "EBIT"]:
                if op_key in latest.index:
                    operating_income = latest[op_key]
                    break

            if operating_income is None:
                return None

            # Estimate tax rate if not provided
            if tax_rate is None:
                income_before_tax = latest.get("Pretax Income")
                income_tax = latest.get("Tax Provision") or latest.get("Income Tax Expense")

                if income_before_tax and income_tax and income_before_tax != 0:
                    tax_rate = abs(income_tax / income_before_tax)
                else:
                    tax_rate = 0.25  # Default assumption

            nopat = operating_income * (1 - tax_rate)
            return float(nopat)

        except Exception as e:
            logger.error(f"Error calculating NOPAT: {e}")
            return None

    def calculate_roic(self, tax_rate: Optional[float] = None) -> dict[str, Any]:
        """Calculate ROIC.

        ROIC = NOPAT / Invested Capital

        Args:
            tax_rate: Effective tax rate

        Returns:
            Dictionary with ROIC calculation details
        """
        invested_capital = self.calculate_invested_capital()
        nopat = self.calculate_nopat(tax_rate)

        if invested_capital is None or nopat is None:
            return {
                "ticker": self.ticker,
                "error": "Insufficient data to calculate ROIC",
            }

        if invested_capital <= 0:
            return {
                "ticker": self.ticker,
                "error": "Invested capital is zero or negative",
            }

        roic = nopat / invested_capital

        # Assess quality
        if roic > 0.20:
            assessment = "excellent"
        elif roic > 0.15:
            assessment = "very_good"
        elif roic > 0.10:
            assessment = "good"
        elif roic > 0.05:
            assessment = "fair"
        else:
            assessment = "poor"

        return {
            "ticker": self.ticker,
            "roic": round(roic * 100, 2),
            "roic_decimal": round(roic, 4),
            "nopat": round(nopat, 2),
            "invested_capital": round(invested_capital, 2),
            "assessment": assessment,
        }

    def calculate_multi_year_roic(self, years: int = 5) -> dict[str, Any]:
        """Calculate ROIC for multiple years.

        Args:
            years: Number of years

        Returns:
            Dictionary with multi-year ROIC data
        """
        try:
            if self._income.empty or self._balance.empty:
                return {"error": "Insufficient data"}

            roic_series = []
            num_periods = min(years, len(self._income.columns), len(self._balance.columns))

            for i in range(num_periods):
                try:
                    income_col = self._income.iloc[:, i]
                    balance_col = self._balance.iloc[:, i]

                    # Operating income
                    operating_income = None
                    for key in ["Operating Income", "EBIT"]:
                        if key in income_col.index:
                            operating_income = income_col[key]
                            break

                    # Tax rate estimation
                    pretax = income_col.get("Pretax Income")
                    tax = income_col.get("Tax Provision") or income_col.get("Income Tax Expense")
                    tax_rate = abs(tax / pretax) if pretax and tax and pretax != 0 else 0.25

                    nopat = operating_income * (1 - tax_rate) if operating_income else None

                    # Invested capital
                    equity = None
                    for key in ["Total Equity Gross Minority Interest", "Stockholders Equity"]:
                        if key in balance_col.index:
                            equity = balance_col[key]
                            break

                    debt = balance_col.get("Total Debt", 0) or 0
                    cash = balance_col.get("Cash And Cash Equivalents", 0) or 0
                    invested_capital = equity + debt - cash if equity else None

                    if nopat and invested_capital and invested_capital > 0:
                        roic = nopat / invested_capital
                        period = self._income.columns[i]
                        year = period.year if hasattr(period, "year") else str(period)
                        roic_series.append({
                            "year": year,
                            "roic": round(roic * 100, 2),
                        })
                except Exception:
                    continue

            # Calculate trend
            if len(roic_series) >= 2:
                recent = roic_series[0]["roic"]
                oldest = roic_series[-1]["roic"]
                if recent > oldest * 1.1:
                    trend = "improving"
                elif recent < oldest * 0.9:
                    trend = "declining"
                else:
                    trend = "stable"
            else:
                trend = "unknown"

            return {
                "ticker": self.ticker,
                "roic_history": roic_series,
                "average_roic": round(
                    sum(r["roic"] for r in roic_series) / len(roic_series), 2
                ) if roic_series else None,
                "trend": trend,
            }

        except Exception as e:
            logger.error(f"Error calculating multi-year ROIC: {e}")
            return {"error": str(e)}


class WACCCalculator:
    """Calculate Weighted Average Cost of Capital (WACC)."""

    def __init__(self, ticker: str):
        """Initialize WACC calculator.

        Args:
            ticker: Stock ticker symbol
        """
        self.ticker = ticker
        self._stock = yf.Ticker(ticker)
        self._info = self._stock.info

    def estimate_cost_of_equity(
        self,
        risk_free_rate: float = 0.04,
        market_premium: float = 0.055,
    ) -> dict[str, Any]:
        """Estimate cost of equity using CAPM.

        Cost of Equity = Risk-Free Rate + Beta × Market Risk Premium

        Args:
            risk_free_rate: Risk-free rate (10-year treasury)
            market_premium: Equity market risk premium

        Returns:
            Dictionary with cost of equity calculation
        """
        beta = self._info.get("beta", 1.0)
        if beta is None:
            beta = 1.0

        cost_of_equity = risk_free_rate + beta * market_premium

        return {
            "cost_of_equity": round(cost_of_equity * 100, 2),
            "cost_of_equity_decimal": round(cost_of_equity, 4),
            "beta": round(beta, 2),
            "risk_free_rate": round(risk_free_rate * 100, 2),
            "market_premium": round(market_premium * 100, 2),
            "method": "CAPM",
        }

    def estimate_cost_of_debt(self) -> dict[str, Any]:
        """Estimate cost of debt.

        Returns:
            Dictionary with cost of debt estimation
        """
        # Try to get interest expense and total debt
        try:
            income = self._stock.income_stmt
            balance = self._stock.balance_sheet

            if not income.empty and not balance.empty:
                interest_expense = None
                for key in ["Interest Expense", "Interest Expense Non Operating"]:
                    if key in income.index:
                        interest_expense = abs(income.iloc[:, 0][key])
                        break

                total_debt = balance.iloc[:, 0].get("Total Debt", 0)

                if interest_expense and total_debt and total_debt > 0:
                    cost_of_debt = interest_expense / total_debt
                    return {
                        "cost_of_debt": round(cost_of_debt * 100, 2),
                        "cost_of_debt_decimal": round(cost_of_debt, 4),
                        "interest_expense": interest_expense,
                        "total_debt": total_debt,
                        "method": "calculated",
                    }
        except Exception:
            pass

        # Default estimate based on credit quality
        debt_to_equity = self._info.get("debtToEquity", 50) or 50

        if debt_to_equity < 30:
            estimated_rate = 0.045  # Investment grade
        elif debt_to_equity < 100:
            estimated_rate = 0.06  # BBB range
        elif debt_to_equity < 200:
            estimated_rate = 0.08  # Below investment grade
        else:
            estimated_rate = 0.10  # High yield

        return {
            "cost_of_debt": round(estimated_rate * 100, 2),
            "cost_of_debt_decimal": round(estimated_rate, 4),
            "method": "estimated",
            "note": "Estimated based on debt-to-equity ratio",
        }

    def calculate_wacc(
        self,
        risk_free_rate: float = 0.04,
        market_premium: float = 0.055,
        tax_rate: float = 0.25,
    ) -> dict[str, Any]:
        """Calculate WACC.

        WACC = E/(E+D) × Re + D/(E+D) × Rd × (1-T)

        Args:
            risk_free_rate: Risk-free rate
            market_premium: Market risk premium
            tax_rate: Corporate tax rate

        Returns:
            Dictionary with WACC calculation
        """
        # Get market cap (equity value)
        market_cap = self._info.get("marketCap")
        if not market_cap:
            return {
                "ticker": self.ticker,
                "error": "Market cap not available",
            }

        # Get total debt
        try:
            balance = self._stock.balance_sheet
            if not balance.empty:
                total_debt = balance.iloc[:, 0].get("Total Debt", 0) or 0
            else:
                total_debt = 0
        except Exception:
            total_debt = 0

        # Calculate weights
        total_capital = market_cap + total_debt
        equity_weight = market_cap / total_capital
        debt_weight = total_debt / total_capital

        # Get cost of equity
        coe_result = self.estimate_cost_of_equity(risk_free_rate, market_premium)
        cost_of_equity = coe_result["cost_of_equity_decimal"]

        # Get cost of debt
        cod_result = self.estimate_cost_of_debt()
        cost_of_debt = cod_result["cost_of_debt_decimal"]

        # After-tax cost of debt
        after_tax_cost_of_debt = cost_of_debt * (1 - tax_rate)

        # WACC
        wacc = (equity_weight * cost_of_equity) + (debt_weight * after_tax_cost_of_debt)

        return {
            "ticker": self.ticker,
            "wacc": round(wacc * 100, 2),
            "wacc_decimal": round(wacc, 4),
            "components": {
                "market_cap": market_cap,
                "total_debt": total_debt,
                "equity_weight": round(equity_weight * 100, 1),
                "debt_weight": round(debt_weight * 100, 1),
                "cost_of_equity": coe_result,
                "cost_of_debt": cod_result,
                "after_tax_cost_of_debt": round(after_tax_cost_of_debt * 100, 2),
                "tax_rate": round(tax_rate * 100, 1),
            },
        }


def calculate_value_creation(ticker: str) -> dict[str, Any]:
    """Calculate value creation metrics (ROIC vs WACC, EVA).

    Args:
        ticker: Stock ticker symbol

    Returns:
        Dictionary with value creation analysis
    """
    roic_calc = ROICCalculator(ticker)
    wacc_calc = WACCCalculator(ticker)

    roic_result = roic_calc.calculate_roic()
    wacc_result = wacc_calc.calculate_wacc()

    if "error" in roic_result or "error" in wacc_result:
        return {
            "ticker": ticker,
            "error": "Could not calculate value creation metrics",
            "roic": roic_result,
            "wacc": wacc_result,
        }

    roic = roic_result["roic_decimal"]
    wacc = wacc_result["wacc_decimal"]
    spread = roic - wacc

    # Calculate EVA
    invested_capital = roic_result["invested_capital"]
    eva = spread * invested_capital

    # Assessment
    if spread > 0.10:
        value_creation = "exceptional"
    elif spread > 0.05:
        value_creation = "strong"
    elif spread > 0:
        value_creation = "positive"
    elif spread > -0.05:
        value_creation = "marginal_destruction"
    else:
        value_creation = "value_destruction"

    return {
        "ticker": ticker,
        "roic": round(roic * 100, 2),
        "wacc": round(wacc * 100, 2),
        "spread": round(spread * 100, 2),
        "eva": round(eva, 2),
        "invested_capital": round(invested_capital, 2),
        "value_creation_assessment": value_creation,
        "creates_value": spread > 0,
        "details": {
            "roic_analysis": roic_result,
            "wacc_analysis": wacc_result,
        },
    }
