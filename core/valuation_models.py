"""Valuation models implementation."""
import logging
from typing import Any, Optional

import yfinance as yf
import numpy as np

from core.roic_wacc import WACCCalculator

logger = logging.getLogger(__name__)


class DCFModel:
    """Discounted Cash Flow valuation model."""

    def __init__(self, ticker: str):
        """Initialize DCF model.

        Args:
            ticker: Stock ticker symbol
        """
        self.ticker = ticker
        self._stock = yf.Ticker(ticker)
        self._info = self._stock.info
        self._cashflow = self._stock.cashflow

    def get_base_fcf(self) -> Optional[float]:
        """Get base free cash flow for projection.

        Returns:
            Base FCF or None
        """
        # Try from info first
        fcf = self._info.get("freeCashflow")
        if fcf:
            return float(fcf)

        # Calculate from cash flow statement
        if not self._cashflow.empty:
            latest = self._cashflow.iloc[:, 0]
            operating_cf = None
            for key in ["Operating Cash Flow", "Cash Flow From Operating Activities"]:
                if key in latest.index:
                    operating_cf = latest[key]
                    break

            capex = latest.get("Capital Expenditure")

            if operating_cf and capex:
                return float(operating_cf + capex)

        return None

    def get_shares_outstanding(self) -> Optional[float]:
        """Get shares outstanding.

        Returns:
            Shares outstanding or None
        """
        return self._info.get("sharesOutstanding")

    def get_net_debt(self) -> float:
        """Get net debt (debt - cash).

        Returns:
            Net debt
        """
        try:
            balance = self._stock.balance_sheet
            if balance.empty:
                return 0

            latest = balance.iloc[:, 0]
            total_debt = latest.get("Total Debt", 0) or 0
            cash = latest.get("Cash And Cash Equivalents", 0) or 0

            return float(total_debt - cash)
        except Exception:
            return 0

    def calculate_intrinsic_value(
        self,
        fcf: Optional[float] = None,
        growth_rate_high: float = 0.12,
        growth_rate_terminal: float = 0.03,
        wacc: Optional[float] = None,
        high_growth_years: int = 5,
    ) -> dict[str, Any]:
        """Calculate intrinsic value using DCF.

        Args:
            fcf: Base free cash flow (if None, will be fetched)
            growth_rate_high: High growth rate for first phase
            growth_rate_terminal: Terminal growth rate
            wacc: WACC (if None, will be calculated)
            high_growth_years: Years of high growth

        Returns:
            Dictionary with DCF valuation
        """
        # Get FCF
        if fcf is None:
            fcf = self.get_base_fcf()

        if fcf is None or fcf <= 0:
            return {
                "ticker": self.ticker,
                "error": "Cannot perform DCF - negative or missing FCF",
            }

        # Get WACC
        if wacc is None:
            wacc_calc = WACCCalculator(self.ticker)
            wacc_result = wacc_calc.calculate_wacc()
            if "error" in wacc_result:
                wacc = 0.10  # Default
            else:
                wacc = wacc_result["wacc_decimal"]

        if wacc <= growth_rate_terminal:
            return {
                "ticker": self.ticker,
                "error": "WACC must be greater than terminal growth rate",
            }

        # Project FCF
        projected_fcf = []
        current_fcf = fcf
        pv_sum = 0

        for year in range(1, high_growth_years + 1):
            current_fcf = current_fcf * (1 + growth_rate_high)
            pv = current_fcf / ((1 + wacc) ** year)
            pv_sum += pv
            projected_fcf.append({
                "year": year,
                "fcf": round(current_fcf, 0),
                "pv": round(pv, 0),
            })

        # Terminal value
        terminal_fcf = current_fcf * (1 + growth_rate_terminal)
        terminal_value = terminal_fcf / (wacc - growth_rate_terminal)
        pv_terminal = terminal_value / ((1 + wacc) ** high_growth_years)

        # Enterprise value
        enterprise_value = pv_sum + pv_terminal

        # Equity value
        net_debt = self.get_net_debt()
        equity_value = enterprise_value - net_debt

        # Per share value
        shares = self.get_shares_outstanding()
        if not shares or shares <= 0:
            return {
                "ticker": self.ticker,
                "error": "Cannot get shares outstanding",
            }

        intrinsic_value = equity_value / shares
        current_price = self._info.get("currentPrice") or self._info.get("regularMarketPrice")

        # Margin of safety
        margin_of_safety = None
        upside = None
        if current_price and current_price > 0:
            margin_of_safety = round((intrinsic_value - current_price) / intrinsic_value * 100, 1)
            upside = round((intrinsic_value - current_price) / current_price * 100, 1)

        return {
            "ticker": self.ticker,
            "intrinsic_value": round(intrinsic_value, 2),
            "current_price": current_price,
            "margin_of_safety": margin_of_safety,
            "upside_potential": upside,
            "assumptions": {
                "base_fcf": round(fcf, 0),
                "high_growth_rate": f"{growth_rate_high * 100:.1f}%",
                "terminal_growth_rate": f"{growth_rate_terminal * 100:.1f}%",
                "wacc": f"{wacc * 100:.1f}%",
                "high_growth_years": high_growth_years,
            },
            "valuation_components": {
                "pv_fcf_sum": round(pv_sum, 0),
                "terminal_value": round(terminal_value, 0),
                "pv_terminal": round(pv_terminal, 0),
                "enterprise_value": round(enterprise_value, 0),
                "net_debt": round(net_debt, 0),
                "equity_value": round(equity_value, 0),
                "shares_outstanding": shares,
            },
            "projected_fcf": projected_fcf,
        }

    def run_sensitivity_analysis(
        self,
        fcf: Optional[float] = None,
        wacc_range: tuple[float, float] = (0.08, 0.12),
        growth_range: tuple[float, float] = (0.02, 0.04),
    ) -> dict[str, Any]:
        """Run sensitivity analysis on DCF assumptions.

        Args:
            fcf: Base FCF
            wacc_range: Range of WACC values to test
            growth_range: Range of terminal growth rates to test

        Returns:
            Dictionary with sensitivity matrix
        """
        if fcf is None:
            fcf = self.get_base_fcf()

        if fcf is None or fcf <= 0:
            return {"error": "Cannot perform sensitivity - invalid FCF"}

        wacc_values = np.linspace(wacc_range[0], wacc_range[1], 5)
        growth_values = np.linspace(growth_range[0], growth_range[1], 5)

        matrix = []
        for wacc in wacc_values:
            row = []
            for growth in growth_values:
                if wacc > growth:
                    result = self.calculate_intrinsic_value(
                        fcf=fcf,
                        wacc=wacc,
                        growth_rate_terminal=growth,
                    )
                    row.append(result.get("intrinsic_value"))
                else:
                    row.append(None)
            matrix.append({
                "wacc": f"{wacc * 100:.1f}%",
                "values": row,
            })

        return {
            "ticker": self.ticker,
            "terminal_growth_rates": [f"{g * 100:.1f}%" for g in growth_values],
            "sensitivity_matrix": matrix,
        }


class RelativeValuationModel:
    """Relative valuation using multiples."""

    def __init__(self, ticker: str):
        """Initialize relative valuation model.

        Args:
            ticker: Stock ticker symbol
        """
        self.ticker = ticker
        self._stock = yf.Ticker(ticker)
        self._info = self._stock.info

    def get_current_multiples(self) -> dict[str, Any]:
        """Get current valuation multiples.

        Returns:
            Dictionary with current multiples
        """
        return {
            "ticker": self.ticker,
            "pe_ratio": self._info.get("trailingPE"),
            "forward_pe": self._info.get("forwardPE"),
            "pb_ratio": self._info.get("priceToBook"),
            "ps_ratio": self._info.get("priceToSalesTrailing12Months"),
            "ev_ebitda": self._info.get("enterpriseToEbitda"),
            "ev_revenue": self._info.get("enterpriseToRevenue"),
            "peg_ratio": self._info.get("pegRatio"),
            "price_to_fcf": self._calculate_price_to_fcf(),
        }

    def _calculate_price_to_fcf(self) -> Optional[float]:
        """Calculate price to free cash flow ratio."""
        market_cap = self._info.get("marketCap")
        fcf = self._info.get("freeCashflow")

        if market_cap and fcf and fcf > 0:
            return round(market_cap / fcf, 2)
        return None

    def get_historical_multiples(self, years: int = 5) -> dict[str, Any]:
        """Get historical valuation range (simplified).

        Note: Full historical multiples would require premium data.
        This provides estimates based on price history.

        Args:
            years: Number of years

        Returns:
            Dictionary with historical range estimates
        """
        try:
            hist = self._stock.history(period=f"{years}y")

            if hist.empty:
                return {"error": "No historical data"}

            current_eps = self._info.get("trailingEPS")
            book_value = self._info.get("bookValue")

            price_high = hist["Close"].max()
            price_low = hist["Close"].min()
            price_avg = hist["Close"].mean()

            result = {
                "ticker": self.ticker,
                "price_range": {
                    "high": round(price_high, 2),
                    "low": round(price_low, 2),
                    "average": round(price_avg, 2),
                },
            }

            # Estimate PE range (using current EPS as proxy)
            if current_eps and current_eps > 0:
                result["pe_range_estimate"] = {
                    "high": round(price_high / current_eps, 1),
                    "low": round(price_low / current_eps, 1),
                    "average": round(price_avg / current_eps, 1),
                }

            # Estimate PB range
            if book_value and book_value > 0:
                result["pb_range_estimate"] = {
                    "high": round(price_high / book_value, 2),
                    "low": round(price_low / book_value, 2),
                    "average": round(price_avg / book_value, 2),
                }

            return result

        except Exception as e:
            logger.error(f"Error getting historical multiples: {e}")
            return {"error": str(e)}

    def calculate_implied_values(
        self,
        target_pe: Optional[float] = None,
        target_pb: Optional[float] = None,
        target_ev_ebitda: Optional[float] = None,
    ) -> dict[str, Any]:
        """Calculate implied stock values at target multiples.

        Args:
            target_pe: Target P/E ratio
            target_pb: Target P/B ratio
            target_ev_ebitda: Target EV/EBITDA

        Returns:
            Dictionary with implied values
        """
        results = {"ticker": self.ticker}

        eps = self._info.get("trailingEPS")
        if target_pe and eps and eps > 0:
            results["pe_implied_value"] = round(eps * target_pe, 2)

        book_value = self._info.get("bookValue")
        if target_pb and book_value and book_value > 0:
            results["pb_implied_value"] = round(book_value * target_pb, 2)

        # EV/EBITDA requires more calculation
        if target_ev_ebitda:
            ebitda = self._info.get("ebitda")
            shares = self._info.get("sharesOutstanding")

            if ebitda and shares:
                try:
                    balance = self._stock.balance_sheet
                    if not balance.empty:
                        total_debt = balance.iloc[:, 0].get("Total Debt", 0) or 0
                        cash = balance.iloc[:, 0].get("Cash And Cash Equivalents", 0) or 0

                        implied_ev = ebitda * target_ev_ebitda
                        implied_equity = implied_ev - total_debt + cash
                        results["ev_ebitda_implied_value"] = round(implied_equity / shares, 2)
                except Exception:
                    pass

        return results

    def get_valuation_assessment(self) -> dict[str, Any]:
        """Get overall valuation assessment.

        Returns:
            Dictionary with valuation assessment
        """
        multiples = self.get_current_multiples()
        historical = self.get_historical_multiples()
        current_price = self._info.get("currentPrice") or self._info.get("regularMarketPrice")

        assessments = []

        # P/E assessment
        pe = multiples.get("pe_ratio")
        if pe:
            if pe < 10:
                assessments.append(("P/E", "undervalued", pe))
            elif pe < 20:
                assessments.append(("P/E", "fair", pe))
            elif pe < 30:
                assessments.append(("P/E", "expensive", pe))
            else:
                assessments.append(("P/E", "very_expensive", pe))

        # P/B assessment
        pb = multiples.get("pb_ratio")
        if pb:
            if pb < 1:
                assessments.append(("P/B", "undervalued", pb))
            elif pb < 3:
                assessments.append(("P/B", "fair", pb))
            else:
                assessments.append(("P/B", "expensive", pb))

        # PEG assessment
        peg = multiples.get("peg_ratio")
        if peg and peg > 0:
            if peg < 1:
                assessments.append(("PEG", "undervalued", peg))
            elif peg < 2:
                assessments.append(("PEG", "fair", peg))
            else:
                assessments.append(("PEG", "expensive", peg))

        # Historical comparison
        hist_pe = historical.get("pe_range_estimate", {})
        if hist_pe and pe:
            avg_pe = hist_pe.get("average")
            if avg_pe:
                if pe < avg_pe * 0.8:
                    assessments.append(("vs_history", "below_average", pe))
                elif pe > avg_pe * 1.2:
                    assessments.append(("vs_history", "above_average", pe))
                else:
                    assessments.append(("vs_history", "near_average", pe))

        # Overall verdict
        undervalued_count = sum(1 for a in assessments if a[1] in ["undervalued", "below_average"])
        expensive_count = sum(1 for a in assessments if a[1] in ["expensive", "very_expensive", "above_average"])

        if undervalued_count > expensive_count + 1:
            overall = "undervalued"
        elif expensive_count > undervalued_count + 1:
            overall = "overvalued"
        else:
            overall = "fairly_valued"

        return {
            "ticker": self.ticker,
            "current_price": current_price,
            "current_multiples": multiples,
            "historical_ranges": historical,
            "assessments": assessments,
            "overall_verdict": overall,
        }


def get_comprehensive_valuation(ticker: str) -> dict[str, Any]:
    """Get comprehensive valuation analysis.

    Args:
        ticker: Stock ticker symbol

    Returns:
        Dictionary with comprehensive valuation
    """
    dcf = DCFModel(ticker)
    relative = RelativeValuationModel(ticker)

    # DCF valuation - multiple scenarios
    base_dcf = dcf.calculate_intrinsic_value()

    # Conservative scenario
    conservative_dcf = dcf.calculate_intrinsic_value(
        growth_rate_high=0.08,
        growth_rate_terminal=0.02,
    )

    # Optimistic scenario
    optimistic_dcf = dcf.calculate_intrinsic_value(
        growth_rate_high=0.15,
        growth_rate_terminal=0.04,
    )

    # Relative valuation
    relative_assessment = relative.get_valuation_assessment()

    # Combine for target price range
    values = []
    if base_dcf.get("intrinsic_value"):
        values.append(base_dcf["intrinsic_value"])
    if conservative_dcf.get("intrinsic_value"):
        values.append(conservative_dcf["intrinsic_value"])
    if optimistic_dcf.get("intrinsic_value"):
        values.append(optimistic_dcf["intrinsic_value"])

    if values:
        target_low = min(values)
        target_high = max(values)
        target_mid = sum(values) / len(values)
    else:
        target_low = target_high = target_mid = None

    current_price = relative_assessment.get("current_price")

    return {
        "ticker": ticker,
        "current_price": current_price,
        "dcf_valuation": {
            "base_case": base_dcf,
            "conservative": conservative_dcf,
            "optimistic": optimistic_dcf,
        },
        "relative_valuation": relative_assessment,
        "target_price_range": {
            "low": round(target_low, 2) if target_low else None,
            "mid": round(target_mid, 2) if target_mid else None,
            "high": round(target_high, 2) if target_high else None,
        },
        "upside_potential": {
            "to_low": round((target_low - current_price) / current_price * 100, 1) if target_low and current_price else None,
            "to_mid": round((target_mid - current_price) / current_price * 100, 1) if target_mid and current_price else None,
            "to_high": round((target_high - current_price) / current_price * 100, 1) if target_high and current_price else None,
        },
    }
