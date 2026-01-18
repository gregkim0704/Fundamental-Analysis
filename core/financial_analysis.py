"""Comprehensive financial analysis module."""
import logging
from typing import Any, Optional

import yfinance as yf
import numpy as np
import pandas as pd

from core.roic_wacc import ROICCalculator, WACCCalculator, calculate_value_creation
from core.quality_metrics import EarningsQualityAnalyzer

logger = logging.getLogger(__name__)


class FinancialAnalyzer:
    """Comprehensive financial statement analyzer."""

    def __init__(self, ticker: str):
        """Initialize financial analyzer.

        Args:
            ticker: Stock ticker symbol
        """
        self.ticker = ticker
        self._stock = yf.Ticker(ticker)
        self._info = self._stock.info
        self._income = self._stock.income_stmt
        self._balance = self._stock.balance_sheet
        self._cashflow = self._stock.cashflow

        # Sub-analyzers
        self._roic_calc = ROICCalculator(ticker)
        self._wacc_calc = WACCCalculator(ticker)
        self._quality_analyzer = EarningsQualityAnalyzer(ticker)

    def get_profitability_analysis(self) -> dict[str, Any]:
        """Analyze profitability metrics.

        Returns:
            Dictionary with profitability analysis
        """
        try:
            metrics = {
                "gross_margin": self._info.get("grossMargins"),
                "operating_margin": self._info.get("operatingMargins"),
                "profit_margin": self._info.get("profitMargins"),
                "roe": self._info.get("returnOnEquity"),
                "roa": self._info.get("returnOnAssets"),
            }

            # Convert to percentages
            for key, value in metrics.items():
                if value is not None:
                    metrics[key] = round(value * 100, 2)

            # Get historical margins
            history = []
            if not self._income.empty:
                num_periods = min(5, len(self._income.columns))
                for i in range(num_periods):
                    col = self._income.iloc[:, i]
                    revenue = col.get("Total Revenue")
                    gross_profit = col.get("Gross Profit")
                    operating_income = col.get("Operating Income")
                    net_income = col.get("Net Income")

                    period = self._income.columns[i]
                    year = period.year if hasattr(period, "year") else str(period)

                    if revenue and revenue != 0:
                        history.append({
                            "year": year,
                            "revenue": revenue,
                            "gross_margin": round(gross_profit / revenue * 100, 2) if gross_profit else None,
                            "operating_margin": round(operating_income / revenue * 100, 2) if operating_income else None,
                            "net_margin": round(net_income / revenue * 100, 2) if net_income else None,
                        })

            # Trend analysis
            if len(history) >= 2:
                recent_margin = history[0].get("operating_margin")
                oldest_margin = history[-1].get("operating_margin")
                if recent_margin and oldest_margin:
                    if recent_margin > oldest_margin + 2:
                        margin_trend = "expanding"
                    elif recent_margin < oldest_margin - 2:
                        margin_trend = "contracting"
                    else:
                        margin_trend = "stable"
                else:
                    margin_trend = "unknown"
            else:
                margin_trend = "unknown"

            # Quality assessment
            op_margin = metrics.get("operating_margin", 0) or 0
            if op_margin > 25:
                profitability_quality = "excellent"
            elif op_margin > 15:
                profitability_quality = "good"
            elif op_margin > 10:
                profitability_quality = "fair"
            elif op_margin > 0:
                profitability_quality = "poor"
            else:
                profitability_quality = "unprofitable"

            return {
                "ticker": self.ticker,
                "current_metrics": metrics,
                "history": history,
                "margin_trend": margin_trend,
                "profitability_quality": profitability_quality,
            }

        except Exception as e:
            logger.error(f"Error analyzing profitability: {e}")
            return {"error": str(e)}

    def get_growth_analysis(self) -> dict[str, Any]:
        """Analyze growth metrics.

        Returns:
            Dictionary with growth analysis
        """
        try:
            # Current growth rates from info
            current_growth = {
                "revenue_growth": self._info.get("revenueGrowth"),
                "earnings_growth": self._info.get("earningsGrowth"),
            }

            # Convert to percentages
            for key, value in current_growth.items():
                if value is not None:
                    current_growth[key] = round(value * 100, 2)

            # Historical growth
            history = []
            if not self._income.empty and len(self._income.columns) >= 2:
                num_periods = min(5, len(self._income.columns))
                for i in range(num_periods - 1):
                    current_col = self._income.iloc[:, i]
                    prior_col = self._income.iloc[:, i + 1]

                    current_revenue = current_col.get("Total Revenue")
                    prior_revenue = prior_col.get("Total Revenue")
                    current_net_income = current_col.get("Net Income")
                    prior_net_income = prior_col.get("Net Income")

                    period = self._income.columns[i]
                    year = period.year if hasattr(period, "year") else str(period)

                    revenue_growth = None
                    if current_revenue and prior_revenue and prior_revenue != 0:
                        revenue_growth = round(
                            (current_revenue - prior_revenue) / abs(prior_revenue) * 100, 2
                        )

                    earnings_growth = None
                    if current_net_income and prior_net_income and prior_net_income != 0:
                        earnings_growth = round(
                            (current_net_income - prior_net_income) / abs(prior_net_income) * 100, 2
                        )

                    history.append({
                        "year": year,
                        "revenue": current_revenue,
                        "revenue_growth": revenue_growth,
                        "net_income": current_net_income,
                        "earnings_growth": earnings_growth,
                    })

            # Calculate CAGR
            if not self._income.empty and len(self._income.columns) >= 2:
                oldest_revenue = self._income.iloc[:, -1].get("Total Revenue")
                newest_revenue = self._income.iloc[:, 0].get("Total Revenue")
                years = len(self._income.columns) - 1

                if oldest_revenue and newest_revenue and oldest_revenue > 0:
                    revenue_cagr = round(
                        ((newest_revenue / oldest_revenue) ** (1 / years) - 1) * 100, 2
                    )
                else:
                    revenue_cagr = None
            else:
                revenue_cagr = None

            # Growth quality assessment
            rev_growth = current_growth.get("revenue_growth", 0) or 0
            if rev_growth > 20:
                growth_quality = "high_growth"
            elif rev_growth > 10:
                growth_quality = "moderate_growth"
            elif rev_growth > 0:
                growth_quality = "slow_growth"
            elif rev_growth > -5:
                growth_quality = "stagnant"
            else:
                growth_quality = "declining"

            return {
                "ticker": self.ticker,
                "current_growth": current_growth,
                "revenue_cagr": revenue_cagr,
                "history": history,
                "growth_quality": growth_quality,
            }

        except Exception as e:
            logger.error(f"Error analyzing growth: {e}")
            return {"error": str(e)}

    def get_leverage_analysis(self) -> dict[str, Any]:
        """Analyze leverage and financial health.

        Returns:
            Dictionary with leverage analysis
        """
        try:
            # Current metrics
            metrics = {
                "debt_to_equity": self._info.get("debtToEquity"),
                "current_ratio": self._info.get("currentRatio"),
                "quick_ratio": self._info.get("quickRatio"),
            }

            # Get more detail from balance sheet
            if not self._balance.empty:
                latest = self._balance.iloc[:, 0]
                total_debt = latest.get("Total Debt", 0) or 0
                total_equity = None
                for key in ["Total Equity Gross Minority Interest", "Stockholders Equity"]:
                    if key in latest.index:
                        total_equity = latest[key]
                        break

                total_assets = latest.get("Total Assets")
                cash = latest.get("Cash And Cash Equivalents", 0) or 0

                metrics["total_debt"] = total_debt
                metrics["total_equity"] = total_equity
                metrics["total_assets"] = total_assets
                metrics["cash"] = cash
                metrics["net_debt"] = total_debt - cash

                if total_assets and total_assets != 0:
                    metrics["debt_to_assets"] = round(total_debt / total_assets * 100, 2)

                if total_equity and total_equity != 0:
                    metrics["net_debt_to_equity"] = round((total_debt - cash) / total_equity * 100, 2)

            # Interest coverage from income statement
            if not self._income.empty:
                latest_income = self._income.iloc[:, 0]
                operating_income = latest_income.get("Operating Income")
                interest_expense = latest_income.get("Interest Expense")

                if operating_income and interest_expense and interest_expense != 0:
                    metrics["interest_coverage"] = round(
                        abs(operating_income / interest_expense), 2
                    )

            # Leverage assessment
            de_ratio = metrics.get("debt_to_equity", 0) or 0
            if de_ratio < 30:
                leverage_assessment = "conservative"
            elif de_ratio < 100:
                leverage_assessment = "moderate"
            elif de_ratio < 200:
                leverage_assessment = "elevated"
            else:
                leverage_assessment = "high"

            # Interest coverage assessment
            int_cov = metrics.get("interest_coverage", 999)
            if int_cov > 10:
                coverage_assessment = "excellent"
            elif int_cov > 5:
                coverage_assessment = "good"
            elif int_cov > 2:
                coverage_assessment = "adequate"
            elif int_cov > 1:
                coverage_assessment = "weak"
            else:
                coverage_assessment = "critical"

            return {
                "ticker": self.ticker,
                "metrics": metrics,
                "leverage_assessment": leverage_assessment,
                "coverage_assessment": coverage_assessment,
            }

        except Exception as e:
            logger.error(f"Error analyzing leverage: {e}")
            return {"error": str(e)}

    def get_cash_flow_analysis(self) -> dict[str, Any]:
        """Analyze cash flow.

        Returns:
            Dictionary with cash flow analysis
        """
        try:
            history = []
            if not self._cashflow.empty:
                num_periods = min(5, len(self._cashflow.columns))
                for i in range(num_periods):
                    col = self._cashflow.iloc[:, i]

                    operating_cf = None
                    for key in ["Operating Cash Flow", "Cash Flow From Operating Activities"]:
                        if key in col.index:
                            operating_cf = col[key]
                            break

                    investing_cf = col.get("Cash Flow From Investing Activities") or col.get("Investing Cash Flow")
                    financing_cf = col.get("Cash Flow From Financing Activities") or col.get("Financing Cash Flow")
                    capex = col.get("Capital Expenditure")
                    fcf = col.get("Free Cash Flow")

                    if fcf is None and operating_cf and capex:
                        fcf = operating_cf + capex  # capex is typically negative

                    period = self._cashflow.columns[i]
                    year = period.year if hasattr(period, "year") else str(period)

                    history.append({
                        "year": year,
                        "operating_cf": operating_cf,
                        "investing_cf": investing_cf,
                        "financing_cf": financing_cf,
                        "capex": capex,
                        "free_cash_flow": fcf,
                    })

            # FCF yield
            fcf_yield = None
            if history and history[0].get("free_cash_flow"):
                market_cap = self._info.get("marketCap")
                if market_cap and market_cap > 0:
                    fcf_yield = round(history[0]["free_cash_flow"] / market_cap * 100, 2)

            # FCF trend
            if len(history) >= 2:
                recent_fcf = history[0].get("free_cash_flow", 0) or 0
                oldest_fcf = history[-1].get("free_cash_flow", 0) or 0
                if recent_fcf > oldest_fcf * 1.1:
                    fcf_trend = "growing"
                elif recent_fcf < oldest_fcf * 0.9:
                    fcf_trend = "declining"
                else:
                    fcf_trend = "stable"
            else:
                fcf_trend = "unknown"

            # FCF quality
            if fcf_yield and fcf_yield > 8:
                fcf_quality = "excellent"
            elif fcf_yield and fcf_yield > 5:
                fcf_quality = "good"
            elif fcf_yield and fcf_yield > 2:
                fcf_quality = "fair"
            elif fcf_yield and fcf_yield > 0:
                fcf_quality = "low"
            else:
                fcf_quality = "negative"

            return {
                "ticker": self.ticker,
                "history": history,
                "fcf_yield": fcf_yield,
                "fcf_trend": fcf_trend,
                "fcf_quality": fcf_quality,
            }

        except Exception as e:
            logger.error(f"Error analyzing cash flow: {e}")
            return {"error": str(e)}

    def get_comprehensive_analysis(self) -> dict[str, Any]:
        """Get comprehensive financial analysis.

        Returns:
            Dictionary with all financial analyses
        """
        profitability = self.get_profitability_analysis()
        growth = self.get_growth_analysis()
        leverage = self.get_leverage_analysis()
        cash_flow = self.get_cash_flow_analysis()
        value_creation = calculate_value_creation(self.ticker)
        quality = self._quality_analyzer.get_comprehensive_quality_analysis()

        # Calculate overall financial health score (1-10)
        scores = []

        # Profitability score
        prof_map = {"excellent": 9, "good": 7, "fair": 5, "poor": 3, "unprofitable": 1}
        scores.append(prof_map.get(profitability.get("profitability_quality"), 5))

        # Growth score
        growth_map = {"high_growth": 9, "moderate_growth": 7, "slow_growth": 5, "stagnant": 3, "declining": 2}
        scores.append(growth_map.get(growth.get("growth_quality"), 5))

        # Leverage score (inverse - lower is better)
        lev_map = {"conservative": 9, "moderate": 7, "elevated": 4, "high": 2}
        scores.append(lev_map.get(leverage.get("leverage_assessment"), 5))

        # Cash flow score
        cf_map = {"excellent": 9, "good": 7, "fair": 5, "low": 3, "negative": 1}
        scores.append(cf_map.get(cash_flow.get("fcf_quality"), 5))

        # Value creation score
        if value_creation.get("creates_value"):
            spread = value_creation.get("spread", 0)
            if spread > 10:
                scores.append(10)
            elif spread > 5:
                scores.append(8)
            elif spread > 0:
                scores.append(6)
        else:
            scores.append(3)

        # Quality score
        quality_score = quality.get("overall_quality_score", 5)
        scores.append(quality_score)

        overall_score = sum(scores) / len(scores)

        # Generate key insights
        insights = []
        if profitability.get("profitability_quality") in ["excellent", "good"]:
            insights.append("Strong profitability metrics")
        if growth.get("growth_quality") in ["high_growth", "moderate_growth"]:
            insights.append("Healthy revenue growth")
        if value_creation.get("creates_value"):
            insights.append(f"Creates shareholder value (ROIC-WACC spread: {value_creation.get('spread')}%)")
        if leverage.get("leverage_assessment") == "conservative":
            insights.append("Conservative capital structure")
        if cash_flow.get("fcf_quality") in ["excellent", "good"]:
            insights.append("Strong free cash flow generation")

        # Generate concerns
        concerns = []
        if profitability.get("profitability_quality") in ["poor", "unprofitable"]:
            concerns.append("Weak profitability")
        if growth.get("growth_quality") in ["stagnant", "declining"]:
            concerns.append("Revenue growth concerns")
        if not value_creation.get("creates_value"):
            concerns.append("Not creating shareholder value (ROIC < WACC)")
        if leverage.get("leverage_assessment") in ["elevated", "high"]:
            concerns.append("Elevated debt levels")
        if cash_flow.get("fcf_quality") in ["low", "negative"]:
            concerns.append("Weak cash flow generation")
        concerns.extend(quality.get("quality_flags", []))

        return {
            "ticker": self.ticker,
            "overall_score": round(overall_score, 1),
            "profitability": profitability,
            "growth": growth,
            "leverage": leverage,
            "cash_flow": cash_flow,
            "value_creation": value_creation,
            "earnings_quality": quality,
            "key_insights": insights,
            "key_concerns": concerns,
        }
