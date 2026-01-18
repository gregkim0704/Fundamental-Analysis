"""Valuation calculation tools."""
import logging
from typing import Any, Optional

from langchain_core.tools import tool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class DCFInput(BaseModel):
    """Input for DCF calculation."""
    ticker: str = Field(..., description="Stock ticker")
    fcf_current: float = Field(..., description="Current free cash flow")
    growth_rate_high: float = Field(
        default=0.15,
        description="High growth rate for first phase (e.g., 0.15 for 15%)"
    )
    growth_rate_terminal: float = Field(
        default=0.03,
        description="Terminal growth rate (e.g., 0.03 for 3%)"
    )
    discount_rate: float = Field(
        default=0.10,
        description="Discount rate / WACC (e.g., 0.10 for 10%)"
    )
    high_growth_years: int = Field(default=5, description="Years of high growth")
    shares_outstanding: float = Field(..., description="Shares outstanding")
    net_debt: float = Field(default=0, description="Net debt (debt - cash)")


@tool(args_schema=DCFInput)
def calculate_dcf(
    ticker: str,
    fcf_current: float,
    growth_rate_high: float = 0.15,
    growth_rate_terminal: float = 0.03,
    discount_rate: float = 0.10,
    high_growth_years: int = 5,
    shares_outstanding: float = 1,
    net_debt: float = 0,
) -> dict[str, Any]:
    """Calculate intrinsic value using Discounted Cash Flow (DCF) model.

    Args:
        ticker: Stock ticker
        fcf_current: Current free cash flow
        growth_rate_high: Growth rate for high growth phase
        growth_rate_terminal: Terminal/perpetual growth rate
        discount_rate: Discount rate (WACC)
        high_growth_years: Number of high growth years
        shares_outstanding: Number of shares outstanding
        net_debt: Net debt (positive = debt, negative = net cash)

    Returns:
        Dictionary with DCF valuation results
    """
    try:
        # Validate inputs
        if discount_rate <= growth_rate_terminal:
            return {
                "error": "Discount rate must be greater than terminal growth rate"
            }

        if fcf_current <= 0:
            return {
                "ticker": ticker,
                "warning": "Negative or zero FCF - DCF may not be appropriate",
                "intrinsic_value_per_share": None,
            }

        # Project FCF for high growth period
        projected_fcf = []
        fcf = fcf_current
        for year in range(1, high_growth_years + 1):
            fcf = fcf * (1 + growth_rate_high)
            pv = fcf / ((1 + discount_rate) ** year)
            projected_fcf.append({
                "year": year,
                "fcf": round(fcf, 2),
                "pv_fcf": round(pv, 2),
            })

        # Calculate terminal value
        terminal_fcf = fcf * (1 + growth_rate_terminal)
        terminal_value = terminal_fcf / (discount_rate - growth_rate_terminal)
        pv_terminal = terminal_value / ((1 + discount_rate) ** high_growth_years)

        # Sum of PV of projected FCF
        pv_fcf_sum = sum(item["pv_fcf"] for item in projected_fcf)

        # Enterprise value
        enterprise_value = pv_fcf_sum + pv_terminal

        # Equity value
        equity_value = enterprise_value - net_debt

        # Per share value
        intrinsic_value_per_share = equity_value / shares_outstanding if shares_outstanding > 0 else 0

        return {
            "ticker": ticker,
            "methodology": "DCF",
            "assumptions": {
                "current_fcf": fcf_current,
                "high_growth_rate": f"{growth_rate_high * 100:.1f}%",
                "terminal_growth_rate": f"{growth_rate_terminal * 100:.1f}%",
                "discount_rate": f"{discount_rate * 100:.1f}%",
                "high_growth_years": high_growth_years,
                "shares_outstanding": shares_outstanding,
                "net_debt": net_debt,
            },
            "projected_fcf": projected_fcf,
            "terminal_value": round(terminal_value, 2),
            "pv_terminal_value": round(pv_terminal, 2),
            "pv_fcf_sum": round(pv_fcf_sum, 2),
            "enterprise_value": round(enterprise_value, 2),
            "equity_value": round(equity_value, 2),
            "intrinsic_value_per_share": round(intrinsic_value_per_share, 2),
        }

    except Exception as e:
        logger.error(f"Error calculating DCF for {ticker}: {e}")
        return {"error": str(e)}


class MultiplesInput(BaseModel):
    """Input for multiples calculation."""
    ticker: str = Field(..., description="Stock ticker")
    current_price: float = Field(..., description="Current stock price")
    eps: Optional[float] = Field(None, description="Earnings per share (TTM)")
    book_value_per_share: Optional[float] = Field(None, description="Book value per share")
    revenue_per_share: Optional[float] = Field(None, description="Revenue per share")
    ebitda_per_share: Optional[float] = Field(None, description="EBITDA per share")
    fcf_per_share: Optional[float] = Field(None, description="FCF per share")
    expected_growth: Optional[float] = Field(
        None, description="Expected EPS growth rate (e.g., 0.15 for 15%)"
    )
    peer_pe_range: Optional[tuple[float, float]] = Field(
        None, description="Peer P/E range (min, max)"
    )
    peer_pb_range: Optional[tuple[float, float]] = Field(
        None, description="Peer P/B range (min, max)"
    )


@tool(args_schema=MultiplesInput)
def calculate_multiples(
    ticker: str,
    current_price: float,
    eps: Optional[float] = None,
    book_value_per_share: Optional[float] = None,
    revenue_per_share: Optional[float] = None,
    ebitda_per_share: Optional[float] = None,
    fcf_per_share: Optional[float] = None,
    expected_growth: Optional[float] = None,
    peer_pe_range: Optional[tuple[float, float]] = None,
    peer_pb_range: Optional[tuple[float, float]] = None,
) -> dict[str, Any]:
    """Calculate valuation multiples and implied values.

    Args:
        ticker: Stock ticker
        current_price: Current stock price
        eps: Earnings per share (TTM)
        book_value_per_share: Book value per share
        revenue_per_share: Revenue per share
        ebitda_per_share: EBITDA per share
        fcf_per_share: Free cash flow per share
        expected_growth: Expected EPS growth rate
        peer_pe_range: Peer P/E range for comparison
        peer_pb_range: Peer P/B range for comparison

    Returns:
        Dictionary with multiples and implied values
    """
    try:
        result = {
            "ticker": ticker,
            "current_price": current_price,
            "multiples": {},
            "implied_values": {},
            "peer_comparison": {},
        }

        # P/E ratio
        if eps and eps > 0:
            pe_ratio = current_price / eps
            result["multiples"]["pe_ratio"] = round(pe_ratio, 2)

            # Implied values at different P/E
            result["implied_values"]["pe_based"] = {
                "at_15x": round(eps * 15, 2),
                "at_20x": round(eps * 20, 2),
                "at_25x": round(eps * 25, 2),
            }

            # Peer comparison
            if peer_pe_range:
                result["peer_comparison"]["pe"] = {
                    "peer_range": peer_pe_range,
                    "implied_price_range": (
                        round(eps * peer_pe_range[0], 2),
                        round(eps * peer_pe_range[1], 2)
                    ),
                    "current_vs_peer_avg": round(
                        pe_ratio / ((peer_pe_range[0] + peer_pe_range[1]) / 2) - 1, 2
                    ) * 100
                }

        # P/B ratio
        if book_value_per_share and book_value_per_share > 0:
            pb_ratio = current_price / book_value_per_share
            result["multiples"]["pb_ratio"] = round(pb_ratio, 2)

            result["implied_values"]["pb_based"] = {
                "at_1x": round(book_value_per_share * 1, 2),
                "at_1.5x": round(book_value_per_share * 1.5, 2),
                "at_2x": round(book_value_per_share * 2, 2),
            }

            if peer_pb_range:
                result["peer_comparison"]["pb"] = {
                    "peer_range": peer_pb_range,
                    "implied_price_range": (
                        round(book_value_per_share * peer_pb_range[0], 2),
                        round(book_value_per_share * peer_pb_range[1], 2)
                    ),
                }

        # P/S ratio
        if revenue_per_share and revenue_per_share > 0:
            ps_ratio = current_price / revenue_per_share
            result["multiples"]["ps_ratio"] = round(ps_ratio, 2)

        # EV/EBITDA (simplified - using per share)
        if ebitda_per_share and ebitda_per_share > 0:
            ev_ebitda = current_price / ebitda_per_share  # Simplified
            result["multiples"]["ev_ebitda_approx"] = round(ev_ebitda, 2)

        # P/FCF
        if fcf_per_share and fcf_per_share > 0:
            p_fcf = current_price / fcf_per_share
            result["multiples"]["p_fcf"] = round(p_fcf, 2)
            result["implied_values"]["fcf_yield"] = f"{round(100 / p_fcf, 2)}%"

        # PEG ratio
        if eps and eps > 0 and expected_growth and expected_growth > 0:
            pe_ratio = current_price / eps
            peg = pe_ratio / (expected_growth * 100)  # Convert growth to percentage
            result["multiples"]["peg_ratio"] = round(peg, 2)
            result["peg_assessment"] = (
                "undervalued" if peg < 1 else
                "fairly valued" if peg < 2 else
                "overvalued"
            )

        # Overall assessment
        assessments = []
        if "pe_ratio" in result["multiples"]:
            pe = result["multiples"]["pe_ratio"]
            if pe < 15:
                assessments.append(("P/E", "attractive"))
            elif pe < 25:
                assessments.append(("P/E", "fair"))
            else:
                assessments.append(("P/E", "expensive"))

        if "pb_ratio" in result["multiples"]:
            pb = result["multiples"]["pb_ratio"]
            if pb < 1:
                assessments.append(("P/B", "attractive"))
            elif pb < 3:
                assessments.append(("P/B", "fair"))
            else:
                assessments.append(("P/B", "expensive"))

        result["assessments"] = assessments

        return result

    except Exception as e:
        logger.error(f"Error calculating multiples for {ticker}: {e}")
        return {"error": str(e)}


def calculate_wacc(
    market_cap: float,
    total_debt: float,
    cost_of_equity: float,
    cost_of_debt: float,
    tax_rate: float = 0.25,
) -> dict[str, Any]:
    """Calculate Weighted Average Cost of Capital (WACC).

    Args:
        market_cap: Market capitalization (equity value)
        total_debt: Total debt
        cost_of_equity: Cost of equity (required return)
        cost_of_debt: Cost of debt (interest rate)
        tax_rate: Corporate tax rate

    Returns:
        Dictionary with WACC calculation
    """
    try:
        total_capital = market_cap + total_debt

        if total_capital <= 0:
            return {"error": "Total capital must be positive"}

        equity_weight = market_cap / total_capital
        debt_weight = total_debt / total_capital

        # After-tax cost of debt
        after_tax_cost_of_debt = cost_of_debt * (1 - tax_rate)

        # WACC
        wacc = (equity_weight * cost_of_equity) + (debt_weight * after_tax_cost_of_debt)

        return {
            "wacc": round(wacc * 100, 2),  # As percentage
            "equity_weight": round(equity_weight * 100, 2),
            "debt_weight": round(debt_weight * 100, 2),
            "cost_of_equity": round(cost_of_equity * 100, 2),
            "cost_of_debt": round(cost_of_debt * 100, 2),
            "after_tax_cost_of_debt": round(after_tax_cost_of_debt * 100, 2),
            "tax_rate": round(tax_rate * 100, 2),
        }

    except Exception as e:
        logger.error(f"Error calculating WACC: {e}")
        return {"error": str(e)}


def calculate_roic(
    operating_income: float,
    tax_rate: float,
    invested_capital: float,
) -> dict[str, Any]:
    """Calculate Return on Invested Capital (ROIC).

    Args:
        operating_income: Operating income (EBIT)
        tax_rate: Effective tax rate
        invested_capital: Total invested capital

    Returns:
        Dictionary with ROIC calculation
    """
    try:
        if invested_capital <= 0:
            return {"error": "Invested capital must be positive"}

        nopat = operating_income * (1 - tax_rate)
        roic = nopat / invested_capital

        return {
            "roic": round(roic * 100, 2),  # As percentage
            "operating_income": operating_income,
            "nopat": round(nopat, 2),
            "invested_capital": invested_capital,
            "tax_rate": round(tax_rate * 100, 2),
        }

    except Exception as e:
        logger.error(f"Error calculating ROIC: {e}")
        return {"error": str(e)}


def run_scenario_analysis(
    base_fcf: float,
    shares_outstanding: float,
    net_debt: float,
    discount_rate: float = 0.10,
) -> dict[str, Any]:
    """Run bear/base/bull scenario analysis.

    Args:
        base_fcf: Base case free cash flow
        shares_outstanding: Shares outstanding
        net_debt: Net debt
        discount_rate: Discount rate

    Returns:
        Dictionary with scenario analysis
    """
    scenarios = {
        "bear": {
            "growth_high": 0.05,
            "growth_terminal": 0.02,
            "probability": 0.20,
        },
        "base": {
            "growth_high": 0.12,
            "growth_terminal": 0.03,
            "probability": 0.60,
        },
        "bull": {
            "growth_high": 0.20,
            "growth_terminal": 0.04,
            "probability": 0.20,
        },
    }

    results = {}
    expected_value = 0

    for scenario_name, params in scenarios.items():
        dcf_result = calculate_dcf.invoke({
            "ticker": "SCENARIO",
            "fcf_current": base_fcf,
            "growth_rate_high": params["growth_high"],
            "growth_rate_terminal": params["growth_terminal"],
            "discount_rate": discount_rate,
            "shares_outstanding": shares_outstanding,
            "net_debt": net_debt,
        })

        if "error" not in dcf_result:
            intrinsic_value = dcf_result["intrinsic_value_per_share"]
            results[scenario_name] = {
                "intrinsic_value": intrinsic_value,
                "probability": params["probability"],
                "assumptions": {
                    "high_growth": f"{params['growth_high'] * 100:.0f}%",
                    "terminal_growth": f"{params['growth_terminal'] * 100:.0f}%",
                },
            }
            expected_value += intrinsic_value * params["probability"]

    results["expected_value"] = round(expected_value, 2)
    results["value_range"] = {
        "low": results.get("bear", {}).get("intrinsic_value"),
        "mid": results.get("base", {}).get("intrinsic_value"),
        "high": results.get("bull", {}).get("intrinsic_value"),
    }

    return results
