"""Industry data and analysis tools."""
import logging
from typing import Any, Optional

import yfinance as yf
from langchain_core.tools import tool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# Industry classification and peer mapping
INDUSTRY_PEERS = {
    "technology": {
        "semiconductors": ["NVDA", "AMD", "INTC", "AVGO", "QCOM", "TSM"],
        "software": ["MSFT", "ORCL", "CRM", "ADBE", "NOW", "INTU"],
        "internet": ["GOOGL", "META", "AMZN", "NFLX", "SNAP", "PINS"],
        "hardware": ["AAPL", "DELL", "HPQ", "CSCO", "ANET"],
    },
    "healthcare": {
        "pharmaceuticals": ["JNJ", "PFE", "MRK", "ABBV", "LLY", "BMY"],
        "biotech": ["AMGN", "GILD", "BIIB", "VRTX", "REGN", "MRNA"],
        "medical_devices": ["MDT", "ABT", "SYK", "BSX", "EW", "ISRG"],
    },
    "financials": {
        "banks": ["JPM", "BAC", "WFC", "C", "GS", "MS"],
        "insurance": ["BRK-B", "UNH", "PGR", "AIG", "MET", "PRU"],
        "asset_management": ["BLK", "BX", "KKR", "APO", "SCHW", "TROW"],
    },
    "consumer": {
        "consumer_discretionary": ["AMZN", "TSLA", "HD", "NKE", "MCD", "SBUX"],
        "consumer_staples": ["PG", "KO", "PEP", "WMT", "COST", "PM"],
        "retail": ["WMT", "TGT", "COST", "DG", "DLTR", "ROST"],
    },
    "industrials": {
        "aerospace_defense": ["BA", "LMT", "RTX", "NOC", "GD", "GE"],
        "machinery": ["CAT", "DE", "EMR", "HON", "MMM", "ITW"],
        "transportation": ["UNP", "UPS", "FDX", "CSX", "NSC", "DAL"],
    },
    "energy": {
        "oil_gas": ["XOM", "CVX", "COP", "EOG", "SLB", "PXD"],
        "renewable": ["NEE", "ENPH", "FSLR", "SEDG", "RUN"],
    },
}


class IndustryPeersInput(BaseModel):
    """Input for industry peers tool."""
    ticker: str = Field(..., description="Stock ticker to find peers for")


@tool(args_schema=IndustryPeersInput)
def get_industry_peers(ticker: str) -> dict[str, Any]:
    """Get industry peers for a given stock.

    Args:
        ticker: Stock ticker

    Returns:
        Dictionary with peer information
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        sector = info.get("sector", "")
        industry = info.get("industry", "")

        # Find peers from our mapping
        peers = []
        for sector_name, industries in INDUSTRY_PEERS.items():
            for ind_name, tickers in industries.items():
                if ticker.upper() in tickers:
                    peers = [t for t in tickers if t != ticker.upper()]
                    break
            if peers:
                break

        # If no peers found, try to get from yfinance recommendations
        if not peers:
            try:
                recommendations = stock.recommendations
                if recommendations is not None and not recommendations.empty:
                    # This is a simplification - actual implementation would need more logic
                    pass
            except Exception:
                pass

        # Get basic info for peers
        peer_data = []
        for peer_ticker in peers[:5]:  # Limit to 5 peers
            try:
                peer = yf.Ticker(peer_ticker)
                peer_info = peer.info
                peer_data.append({
                    "ticker": peer_ticker,
                    "name": peer_info.get("shortName", peer_ticker),
                    "market_cap": peer_info.get("marketCap"),
                    "pe_ratio": peer_info.get("trailingPE"),
                    "pb_ratio": peer_info.get("priceToBook"),
                    "profit_margin": peer_info.get("profitMargins"),
                    "roe": peer_info.get("returnOnEquity"),
                })
            except Exception as e:
                logger.warning(f"Failed to get data for peer {peer_ticker}: {e}")

        return {
            "ticker": ticker,
            "company_name": info.get("shortName", ticker),
            "sector": sector,
            "industry": industry,
            "peers": peer_data,
            "peer_count": len(peer_data),
        }

    except Exception as e:
        logger.error(f"Error getting industry peers for {ticker}: {e}")
        return {"error": str(e)}


class PeerComparisonInput(BaseModel):
    """Input for peer comparison tool."""
    ticker: str = Field(..., description="Primary stock ticker")
    peer_tickers: list[str] = Field(..., description="List of peer tickers to compare")


@tool(args_schema=PeerComparisonInput)
def compare_with_peers(ticker: str, peer_tickers: list[str]) -> dict[str, Any]:
    """Compare a stock with its peers on key metrics.

    Args:
        ticker: Primary stock ticker
        peer_tickers: List of peer tickers

    Returns:
        Dictionary with peer comparison
    """
    try:
        all_tickers = [ticker] + peer_tickers
        comparison_data = []

        for t in all_tickers:
            try:
                stock = yf.Ticker(t)
                info = stock.info

                comparison_data.append({
                    "ticker": t,
                    "name": info.get("shortName", t),
                    "market_cap": info.get("marketCap"),
                    "pe_ratio": info.get("trailingPE"),
                    "forward_pe": info.get("forwardPE"),
                    "pb_ratio": info.get("priceToBook"),
                    "ps_ratio": info.get("priceToSalesTrailing12Months"),
                    "ev_ebitda": info.get("enterpriseToEbitda"),
                    "profit_margin": info.get("profitMargins"),
                    "operating_margin": info.get("operatingMargins"),
                    "roe": info.get("returnOnEquity"),
                    "roa": info.get("returnOnAssets"),
                    "debt_to_equity": info.get("debtToEquity"),
                    "revenue_growth": info.get("revenueGrowth"),
                    "earnings_growth": info.get("earningsGrowth"),
                })
            except Exception as e:
                logger.warning(f"Failed to get data for {t}: {e}")

        # Calculate peer averages (excluding the primary ticker)
        peer_only = [d for d in comparison_data if d["ticker"] != ticker]
        primary = next((d for d in comparison_data if d["ticker"] == ticker), None)

        peer_averages = {}
        for key in ["pe_ratio", "forward_pe", "pb_ratio", "ps_ratio", "ev_ebitda",
                    "profit_margin", "operating_margin", "roe", "roa", "debt_to_equity"]:
            values = [d[key] for d in peer_only if d[key] is not None]
            if values:
                peer_averages[key] = sum(values) / len(values)

        # Compare primary to peer averages
        vs_peers = {}
        if primary:
            for key, peer_avg in peer_averages.items():
                primary_val = primary.get(key)
                if primary_val is not None and peer_avg != 0:
                    vs_peers[key] = {
                        "company": round(primary_val, 2) if isinstance(primary_val, float) else primary_val,
                        "peer_avg": round(peer_avg, 2),
                        "premium_discount": round((primary_val / peer_avg - 1) * 100, 1),
                    }

        return {
            "primary_ticker": ticker,
            "peer_tickers": peer_tickers,
            "comparison_data": comparison_data,
            "peer_averages": {k: round(v, 2) for k, v in peer_averages.items()},
            "vs_peers": vs_peers,
        }

    except Exception as e:
        logger.error(f"Error comparing with peers: {e}")
        return {"error": str(e)}


def get_industry_analysis(ticker: str) -> dict[str, Any]:
    """Get comprehensive industry analysis (non-tool function).

    Args:
        ticker: Stock ticker

    Returns:
        Dictionary with industry analysis
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        sector = info.get("sector", "Unknown")
        industry = info.get("industry", "Unknown")

        # Get peers
        peers_result = get_industry_peers.invoke({"ticker": ticker})

        # Determine industry lifecycle based on growth metrics
        revenue_growth = info.get("revenueGrowth", 0) or 0
        if revenue_growth > 0.20:
            lifecycle = "growth"
        elif revenue_growth > 0.05:
            lifecycle = "mature"
        elif revenue_growth > 0:
            lifecycle = "mature_slow"
        else:
            lifecycle = "decline"

        # Market structure assessment
        peer_count = peers_result.get("peer_count", 0)
        if peer_count <= 3:
            market_structure = "oligopoly"
        elif peer_count <= 6:
            market_structure = "competitive"
        else:
            market_structure = "fragmented"

        analysis = {
            "ticker": ticker,
            "sector": sector,
            "industry": industry,
            "industry_lifecycle": lifecycle,
            "market_structure": market_structure,
            "peers": peers_result.get("peers", []),
            "company_position": {
                "market_cap": info.get("marketCap"),
                "revenue": info.get("totalRevenue"),
                "employees": info.get("fullTimeEmployees"),
            },
            "competitive_factors": {
                "profit_margin": info.get("profitMargins"),
                "operating_margin": info.get("operatingMargins"),
                "gross_margin": info.get("grossMargins"),
                "roe": info.get("returnOnEquity"),
            },
        }

        # Add peer comparison if peers exist
        if peers_result.get("peers"):
            peer_tickers = [p["ticker"] for p in peers_result["peers"][:5]]
            if peer_tickers:
                comparison = compare_with_peers.invoke({
                    "ticker": ticker,
                    "peer_tickers": peer_tickers
                })
                analysis["peer_comparison"] = comparison.get("vs_peers", {})

        return analysis

    except Exception as e:
        logger.error(f"Error getting industry analysis for {ticker}: {e}")
        return {"error": str(e)}
