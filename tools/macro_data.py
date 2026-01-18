"""Macroeconomic data tools using FRED and other sources."""
import logging
from datetime import datetime, timedelta
from typing import Any, Optional

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from config.settings import settings

logger = logging.getLogger(__name__)

# Try importing fredapi
try:
    from fredapi import Fred
    FRED_AVAILABLE = True
except ImportError:
    FRED_AVAILABLE = False
    logger.warning("fredapi not installed. FRED data will not be available.")


def _get_fred_client() -> Optional["Fred"]:
    """Get FRED client if available and configured."""
    if not FRED_AVAILABLE:
        return None
    if not settings.fred_api_key:
        logger.warning("FRED API key not configured")
        return None
    return Fred(api_key=settings.fred_api_key)


# Key FRED series IDs
FRED_SERIES = {
    # Interest rates
    "fed_funds_rate": "FEDFUNDS",
    "treasury_10y": "DGS10",
    "treasury_2y": "DGS2",
    "treasury_3m": "DTB3",
    "treasury_30y": "DGS30",
    "prime_rate": "DPRIME",

    # Yield spreads
    "yield_spread_10y2y": "T10Y2Y",
    "yield_spread_10y3m": "T10Y3M",

    # Credit spreads
    "baa_spread": "BAA10Y",  # BAA corporate - 10y treasury
    "high_yield_spread": "BAMLH0A0HYM2",  # ICE BofA High Yield spread

    # Money supply
    "m2": "M2SL",
    "m2_growth": "M2REAL",

    # Economic indicators
    "gdp_growth": "A191RL1Q225SBEA",  # Real GDP growth
    "cpi": "CPIAUCSL",
    "core_cpi": "CPILFESL",
    "pce": "PCEPI",
    "core_pce": "PCEPILFE",
    "unemployment": "UNRATE",
    "initial_claims": "ICSA",

    # Market indicators
    "vix": "VIXCLS",
    "sp500": "SP500",

    # Housing
    "case_shiller": "CSUSHPINSA",
    "housing_starts": "HOUST",

    # Business activity
    "industrial_production": "INDPRO",
    "capacity_utilization": "TCU",
    "ism_manufacturing": "MANEMP",

    # Consumer
    "consumer_sentiment": "UMCSENT",
    "retail_sales": "RSAFS",
    "personal_income": "PI",
}


class InterestRatesInput(BaseModel):
    """Input for interest rates tool."""
    lookback_days: int = Field(
        default=365,
        description="Number of days to look back for data"
    )


@tool(args_schema=InterestRatesInput)
def get_interest_rates(lookback_days: int = 365) -> dict[str, Any]:
    """Get current interest rates and yield curve data.

    Args:
        lookback_days: Number of days to look back

    Returns:
        Dictionary with interest rate data
    """
    fred = _get_fred_client()

    if fred is None:
        # Return mock data for development
        return {
            "source": "mock",
            "warning": "FRED API not available. Using mock data.",
            "current_rates": {
                "fed_funds_rate": 5.25,
                "treasury_3m": 5.20,
                "treasury_2y": 4.50,
                "treasury_10y": 4.20,
                "treasury_30y": 4.40,
                "prime_rate": 8.50,
            },
            "yield_spreads": {
                "10y_2y_spread": -0.30,
                "10y_3m_spread": -1.00,
            },
            "yield_curve_status": "inverted",
            "rate_environment": "restrictive",
        }

    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=lookback_days)

        # Fetch key rates
        rates_data = {}
        for name, series_id in [
            ("fed_funds_rate", "FEDFUNDS"),
            ("treasury_3m", "DTB3"),
            ("treasury_2y", "DGS2"),
            ("treasury_10y", "DGS10"),
            ("treasury_30y", "DGS30"),
            ("prime_rate", "DPRIME"),
        ]:
            try:
                series = fred.get_series(series_id, start_date, end_date)
                if not series.empty:
                    rates_data[name] = {
                        "current": round(series.iloc[-1], 2),
                        "period_start": round(series.iloc[0], 2),
                        "period_high": round(series.max(), 2),
                        "period_low": round(series.min(), 2),
                        "change": round(series.iloc[-1] - series.iloc[0], 2),
                    }
            except Exception as e:
                logger.warning(f"Failed to fetch {name}: {e}")

        # Fetch yield spreads
        spreads = {}
        try:
            spread_10y2y = fred.get_series("T10Y2Y", start_date, end_date)
            if not spread_10y2y.empty:
                spreads["10y_2y_spread"] = round(spread_10y2y.iloc[-1], 2)
        except Exception:
            pass

        try:
            spread_10y3m = fred.get_series("T10Y3M", start_date, end_date)
            if not spread_10y3m.empty:
                spreads["10y_3m_spread"] = round(spread_10y3m.iloc[-1], 2)
        except Exception:
            pass

        # Determine yield curve status
        spread_10y2y_val = spreads.get("10y_2y_spread", 0)
        if spread_10y2y_val < -0.5:
            yield_curve_status = "deeply_inverted"
        elif spread_10y2y_val < 0:
            yield_curve_status = "inverted"
        elif spread_10y2y_val < 0.5:
            yield_curve_status = "flat"
        else:
            yield_curve_status = "normal"

        # Determine rate environment
        fed_rate = rates_data.get("fed_funds_rate", {}).get("current", 0)
        if fed_rate >= 5:
            rate_environment = "restrictive"
        elif fed_rate >= 3:
            rate_environment = "neutral"
        elif fed_rate >= 1:
            rate_environment = "accommodative"
        else:
            rate_environment = "very_accommodative"

        return {
            "source": "FRED",
            "as_of": end_date.strftime("%Y-%m-%d"),
            "current_rates": {k: v.get("current") for k, v in rates_data.items()},
            "rate_details": rates_data,
            "yield_spreads": spreads,
            "yield_curve_status": yield_curve_status,
            "rate_environment": rate_environment,
        }

    except Exception as e:
        logger.error(f"Error fetching interest rates: {e}")
        return {"error": str(e)}


class EconomicIndicatorsInput(BaseModel):
    """Input for economic indicators tool."""
    indicators: list[str] = Field(
        default=["gdp_growth", "cpi", "unemployment", "consumer_sentiment"],
        description="List of indicators to fetch"
    )
    lookback_days: int = Field(default=365, description="Days to look back")


@tool(args_schema=EconomicIndicatorsInput)
def get_economic_indicators(
    indicators: list[str] = None,
    lookback_days: int = 365
) -> dict[str, Any]:
    """Get key economic indicators.

    Args:
        indicators: List of indicator names (gdp_growth, cpi, unemployment, etc.)
        lookback_days: Number of days to look back

    Returns:
        Dictionary with economic indicator data
    """
    if indicators is None:
        indicators = ["gdp_growth", "cpi", "unemployment", "consumer_sentiment"]

    fred = _get_fred_client()

    if fred is None:
        # Return mock data
        return {
            "source": "mock",
            "warning": "FRED API not available. Using mock data.",
            "indicators": {
                "gdp_growth": {"current": 2.5, "trend": "stable"},
                "cpi": {"current": 3.2, "trend": "declining"},
                "unemployment": {"current": 4.0, "trend": "stable"},
                "consumer_sentiment": {"current": 70.0, "trend": "improving"},
            },
            "economic_cycle_phase": "late_cycle",
        }

    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=lookback_days)

        results = {}
        for indicator in indicators:
            if indicator not in FRED_SERIES:
                continue

            series_id = FRED_SERIES[indicator]
            try:
                series = fred.get_series(series_id, start_date, end_date)
                if not series.empty:
                    # Calculate trend
                    if len(series) >= 3:
                        recent_avg = series.iloc[-3:].mean()
                        earlier_avg = series.iloc[:3].mean()
                        if recent_avg > earlier_avg * 1.02:
                            trend = "increasing"
                        elif recent_avg < earlier_avg * 0.98:
                            trend = "decreasing"
                        else:
                            trend = "stable"
                    else:
                        trend = "unknown"

                    results[indicator] = {
                        "current": round(series.iloc[-1], 2),
                        "period_start": round(series.iloc[0], 2),
                        "period_high": round(series.max(), 2),
                        "period_low": round(series.min(), 2),
                        "trend": trend,
                    }
            except Exception as e:
                logger.warning(f"Failed to fetch {indicator}: {e}")

        # Determine economic cycle phase
        gdp = results.get("gdp_growth", {}).get("current", 0)
        unemployment = results.get("unemployment", {}).get("current", 5)

        if gdp > 3 and unemployment < 4:
            cycle_phase = "expansion"
        elif gdp > 1.5 and unemployment < 5:
            cycle_phase = "late_cycle"
        elif gdp > 0:
            cycle_phase = "slowdown"
        else:
            cycle_phase = "contraction"

        return {
            "source": "FRED",
            "as_of": end_date.strftime("%Y-%m-%d"),
            "indicators": results,
            "economic_cycle_phase": cycle_phase,
        }

    except Exception as e:
        logger.error(f"Error fetching economic indicators: {e}")
        return {"error": str(e)}


def get_macro_environment_summary() -> dict[str, Any]:
    """Get comprehensive macro environment summary (non-tool function).

    Returns:
        Dictionary with macro environment assessment
    """
    # Get interest rates
    rates = get_interest_rates.invoke({"lookback_days": 365})

    # Get economic indicators
    indicators = get_economic_indicators.invoke({
        "indicators": ["gdp_growth", "cpi", "unemployment", "consumer_sentiment", "vix"],
        "lookback_days": 365
    })

    # Compile summary
    summary = {
        "interest_rates": rates,
        "economic_indicators": indicators,
        "overall_assessment": {
            "yield_curve": rates.get("yield_curve_status", "unknown"),
            "rate_environment": rates.get("rate_environment", "unknown"),
            "economic_cycle": indicators.get("economic_cycle_phase", "unknown"),
        }
    }

    # Determine favorable sectors based on environment
    rate_env = rates.get("rate_environment", "neutral")
    cycle = indicators.get("economic_cycle_phase", "late_cycle")

    if rate_env == "restrictive":
        summary["favorable_sectors"] = ["utilities", "healthcare", "consumer_staples"]
        summary["unfavorable_sectors"] = ["real_estate", "high_growth_tech", "small_caps"]
    elif rate_env in ["accommodative", "very_accommodative"]:
        summary["favorable_sectors"] = ["technology", "real_estate", "small_caps"]
        summary["unfavorable_sectors"] = ["utilities", "banks"]
    else:
        summary["favorable_sectors"] = ["quality_growth", "industrials"]
        summary["unfavorable_sectors"] = ["speculative_growth"]

    if cycle == "late_cycle":
        summary["cycle_positioning"] = "defensive positioning recommended"
    elif cycle == "expansion":
        summary["cycle_positioning"] = "risk-on positioning favorable"
    elif cycle == "contraction":
        summary["cycle_positioning"] = "highly defensive positioning"
    else:
        summary["cycle_positioning"] = "balanced positioning"

    return summary
