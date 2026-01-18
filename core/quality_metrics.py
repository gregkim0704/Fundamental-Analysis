"""Earnings quality and cash flow quality metrics."""
import logging
from typing import Any, Optional

import yfinance as yf
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class EarningsQualityAnalyzer:
    """Analyze earnings quality and detect potential manipulation."""

    def __init__(self, ticker: str):
        """Initialize earnings quality analyzer.

        Args:
            ticker: Stock ticker symbol
        """
        self.ticker = ticker
        self._stock = yf.Ticker(ticker)
        self._income = self._stock.income_stmt
        self._balance = self._stock.balance_sheet
        self._cashflow = self._stock.cashflow

    def calculate_accrual_ratio(self) -> dict[str, Any]:
        """Calculate accrual ratio to detect earnings manipulation.

        Accrual Ratio = (Net Income - Operating Cash Flow) / Average Total Assets

        High accrual ratios (> 10%) may indicate earnings manipulation.

        Returns:
            Dictionary with accrual ratio analysis
        """
        try:
            if self._income.empty or self._balance.empty or self._cashflow.empty:
                return {"error": "Insufficient data"}

            # Get latest data
            net_income = None
            for key in ["Net Income", "Net Income Common Stockholders"]:
                if key in self._income.index:
                    net_income = self._income.iloc[:, 0][key]
                    break

            operating_cf = None
            for key in ["Operating Cash Flow", "Cash Flow From Operating Activities"]:
                if key in self._cashflow.index:
                    operating_cf = self._cashflow.iloc[:, 0][key]
                    break

            total_assets_current = self._balance.iloc[:, 0].get("Total Assets")
            total_assets_prior = self._balance.iloc[:, 1].get("Total Assets") if len(self._balance.columns) > 1 else total_assets_current

            if None in [net_income, operating_cf, total_assets_current, total_assets_prior]:
                return {"error": "Missing required data"}

            avg_assets = (total_assets_current + total_assets_prior) / 2
            accruals = net_income - operating_cf
            accrual_ratio = accruals / avg_assets if avg_assets != 0 else 0

            # Assessment
            abs_ratio = abs(accrual_ratio)
            if abs_ratio < 0.05:
                quality = "high"
                flag = None
            elif abs_ratio < 0.10:
                quality = "moderate"
                flag = "Watch accruals"
            elif abs_ratio < 0.15:
                quality = "low"
                flag = "High accruals - investigate"
            else:
                quality = "poor"
                flag = "Very high accruals - potential manipulation"

            return {
                "ticker": self.ticker,
                "accrual_ratio": round(accrual_ratio * 100, 2),
                "net_income": net_income,
                "operating_cash_flow": operating_cf,
                "accruals": accruals,
                "avg_total_assets": avg_assets,
                "quality": quality,
                "flag": flag,
            }

        except Exception as e:
            logger.error(f"Error calculating accrual ratio: {e}")
            return {"error": str(e)}

    def calculate_cash_conversion(self) -> dict[str, Any]:
        """Calculate cash conversion quality metrics.

        Returns:
            Dictionary with cash conversion analysis
        """
        try:
            if self._income.empty or self._cashflow.empty:
                return {"error": "Insufficient data"}

            results = []
            num_periods = min(4, len(self._income.columns), len(self._cashflow.columns))

            for i in range(num_periods):
                income_col = self._income.iloc[:, i]
                cf_col = self._cashflow.iloc[:, i]

                # Get values
                net_income = None
                for key in ["Net Income", "Net Income Common Stockholders"]:
                    if key in income_col.index:
                        net_income = income_col[key]
                        break

                operating_income = income_col.get("Operating Income")

                operating_cf = None
                for key in ["Operating Cash Flow", "Cash Flow From Operating Activities"]:
                    if key in cf_col.index:
                        operating_cf = cf_col[key]
                        break

                if net_income and operating_cf:
                    ni_conversion = operating_cf / net_income if net_income != 0 else 0
                else:
                    ni_conversion = None

                if operating_income and operating_cf:
                    oi_conversion = operating_cf / operating_income if operating_income != 0 else 0
                else:
                    oi_conversion = None

                period = self._income.columns[i]
                year = period.year if hasattr(period, "year") else str(period)

                results.append({
                    "year": year,
                    "net_income": net_income,
                    "operating_income": operating_income,
                    "operating_cf": operating_cf,
                    "ni_to_ocf_ratio": round(ni_conversion, 2) if ni_conversion else None,
                    "oi_to_ocf_ratio": round(oi_conversion, 2) if oi_conversion else None,
                })

            # Calculate averages
            ni_ratios = [r["ni_to_ocf_ratio"] for r in results if r["ni_to_ocf_ratio"] is not None]
            oi_ratios = [r["oi_to_ocf_ratio"] for r in results if r["oi_to_ocf_ratio"] is not None]

            avg_ni_conversion = sum(ni_ratios) / len(ni_ratios) if ni_ratios else None
            avg_oi_conversion = sum(oi_ratios) / len(oi_ratios) if oi_ratios else None

            # Assessment
            if avg_oi_conversion:
                if avg_oi_conversion >= 1.0:
                    quality = "excellent"
                elif avg_oi_conversion >= 0.8:
                    quality = "good"
                elif avg_oi_conversion >= 0.6:
                    quality = "fair"
                else:
                    quality = "poor"
            else:
                quality = "unknown"

            return {
                "ticker": self.ticker,
                "history": results,
                "avg_ni_to_ocf": round(avg_ni_conversion, 2) if avg_ni_conversion else None,
                "avg_oi_to_ocf": round(avg_oi_conversion, 2) if avg_oi_conversion else None,
                "cash_conversion_quality": quality,
            }

        except Exception as e:
            logger.error(f"Error calculating cash conversion: {e}")
            return {"error": str(e)}

    def analyze_working_capital(self) -> dict[str, Any]:
        """Analyze working capital trends.

        Returns:
            Dictionary with working capital analysis
        """
        try:
            if self._balance.empty or self._income.empty:
                return {"error": "Insufficient data"}

            results = []
            num_periods = min(4, len(self._balance.columns))

            for i in range(num_periods):
                balance_col = self._balance.iloc[:, i]

                # Get components
                receivables = balance_col.get("Accounts Receivable") or balance_col.get("Net Receivables") or 0
                inventory = balance_col.get("Inventory") or 0
                payables = balance_col.get("Accounts Payable") or 0

                # Get revenue for turnover calculations
                if i < len(self._income.columns):
                    revenue = self._income.iloc[:, i].get("Total Revenue") or 0
                    cogs = abs(self._income.iloc[:, i].get("Cost Of Revenue") or 0)
                else:
                    revenue = 0
                    cogs = 0

                # Calculate days outstanding (annualized)
                dso = (receivables / (revenue / 365)) if revenue > 0 else None
                dio = (inventory / (cogs / 365)) if cogs > 0 else None
                dpo = (payables / (cogs / 365)) if cogs > 0 else None

                ccc = None
                if all(x is not None for x in [dso, dio, dpo]):
                    ccc = dso + dio - dpo

                period = self._balance.columns[i]
                year = period.year if hasattr(period, "year") else str(period)

                results.append({
                    "year": year,
                    "receivables": receivables,
                    "inventory": inventory,
                    "payables": payables,
                    "dso": round(dso, 1) if dso else None,
                    "dio": round(dio, 1) if dio else None,
                    "dpo": round(dpo, 1) if dpo else None,
                    "cash_conversion_cycle": round(ccc, 1) if ccc else None,
                })

            # Trend analysis
            if len(results) >= 2:
                recent_ccc = results[0].get("cash_conversion_cycle")
                oldest_ccc = results[-1].get("cash_conversion_cycle")

                if recent_ccc and oldest_ccc:
                    if recent_ccc < oldest_ccc - 5:
                        trend = "improving"
                    elif recent_ccc > oldest_ccc + 5:
                        trend = "deteriorating"
                    else:
                        trend = "stable"
                else:
                    trend = "unknown"
            else:
                trend = "unknown"

            return {
                "ticker": self.ticker,
                "history": results,
                "trend": trend,
            }

        except Exception as e:
            logger.error(f"Error analyzing working capital: {e}")
            return {"error": str(e)}

    def analyze_capex_quality(self) -> dict[str, Any]:
        """Analyze capital expenditure quality.

        Returns:
            Dictionary with CAPEX analysis
        """
        try:
            if self._cashflow.empty or self._income.empty:
                return {"error": "Insufficient data"}

            results = []
            num_periods = min(5, len(self._cashflow.columns))

            for i in range(num_periods):
                cf_col = self._cashflow.iloc[:, i]
                income_col = self._income.iloc[:, i] if i < len(self._income.columns) else None

                capex = abs(cf_col.get("Capital Expenditure") or 0)
                depreciation = abs(cf_col.get("Depreciation And Amortization") or
                                   (income_col.get("Depreciation And Amortization") if income_col is not None else 0) or 0)

                operating_cf = None
                for key in ["Operating Cash Flow", "Cash Flow From Operating Activities"]:
                    if key in cf_col.index:
                        operating_cf = cf_col[key]
                        break

                revenue = income_col.get("Total Revenue") if income_col is not None else 0

                # Calculate ratios
                capex_to_depr = capex / depreciation if depreciation > 0 else None
                capex_to_revenue = capex / revenue * 100 if revenue and revenue > 0 else None
                capex_to_ocf = capex / operating_cf * 100 if operating_cf and operating_cf > 0 else None

                period = self._cashflow.columns[i]
                year = period.year if hasattr(period, "year") else str(period)

                results.append({
                    "year": year,
                    "capex": capex,
                    "depreciation": depreciation,
                    "capex_to_depreciation": round(capex_to_depr, 2) if capex_to_depr else None,
                    "capex_to_revenue_pct": round(capex_to_revenue, 2) if capex_to_revenue else None,
                    "capex_to_ocf_pct": round(capex_to_ocf, 2) if capex_to_ocf else None,
                })

            # Analysis
            avg_capex_to_depr = np.mean([
                r["capex_to_depreciation"] for r in results
                if r["capex_to_depreciation"] is not None
            ]) if results else None

            if avg_capex_to_depr:
                if avg_capex_to_depr > 1.5:
                    investment_mode = "heavy_investment"
                elif avg_capex_to_depr > 1.0:
                    investment_mode = "growth_investment"
                elif avg_capex_to_depr > 0.7:
                    investment_mode = "maintenance"
                else:
                    investment_mode = "underinvestment"
            else:
                investment_mode = "unknown"

            return {
                "ticker": self.ticker,
                "history": results,
                "avg_capex_to_depreciation": round(avg_capex_to_depr, 2) if avg_capex_to_depr else None,
                "investment_mode": investment_mode,
            }

        except Exception as e:
            logger.error(f"Error analyzing CAPEX: {e}")
            return {"error": str(e)}

    def get_comprehensive_quality_analysis(self) -> dict[str, Any]:
        """Get comprehensive earnings quality analysis.

        Returns:
            Dictionary with all quality metrics
        """
        accrual = self.calculate_accrual_ratio()
        cash_conversion = self.calculate_cash_conversion()
        working_capital = self.analyze_working_capital()
        capex = self.analyze_capex_quality()

        # Calculate overall quality score (1-10)
        scores = []

        if "quality" in accrual:
            quality_map = {"high": 9, "moderate": 7, "low": 4, "poor": 2}
            scores.append(quality_map.get(accrual["quality"], 5))

        if "cash_conversion_quality" in cash_conversion:
            quality_map = {"excellent": 10, "good": 8, "fair": 5, "poor": 3, "unknown": 5}
            scores.append(quality_map.get(cash_conversion["cash_conversion_quality"], 5))

        if "trend" in working_capital:
            trend_map = {"improving": 8, "stable": 6, "deteriorating": 3, "unknown": 5}
            scores.append(trend_map.get(working_capital["trend"], 5))

        overall_score = sum(scores) / len(scores) if scores else 5

        # Generate flags/warnings
        flags = []
        if accrual.get("flag"):
            flags.append(accrual["flag"])
        if working_capital.get("trend") == "deteriorating":
            flags.append("Working capital efficiency deteriorating")
        if capex.get("investment_mode") == "underinvestment":
            flags.append("Potential underinvestment in assets")

        return {
            "ticker": self.ticker,
            "overall_quality_score": round(overall_score, 1),
            "accrual_analysis": accrual,
            "cash_conversion_analysis": cash_conversion,
            "working_capital_analysis": working_capital,
            "capex_analysis": capex,
            "quality_flags": flags,
        }
