"""News and information search tools."""
import logging
from datetime import datetime, timedelta
from typing import Any, Optional

import yfinance as yf
from langchain_core.tools import tool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class NewsSearchInput(BaseModel):
    """Input for news search tool."""
    ticker: str = Field(..., description="Stock ticker to search news for")
    limit: int = Field(default=10, description="Maximum number of news items")


@tool(args_schema=NewsSearchInput)
def get_stock_news(ticker: str, limit: int = 10) -> dict[str, Any]:
    """Get recent news for a stock.

    Args:
        ticker: Stock ticker
        limit: Maximum number of news items

    Returns:
        Dictionary with news items
    """
    try:
        stock = yf.Ticker(ticker)
        news = stock.news

        if not news:
            return {
                "ticker": ticker,
                "news": [],
                "message": "No recent news found"
            }

        news_items = []
        for item in news[:limit]:
            news_items.append({
                "title": item.get("title", ""),
                "publisher": item.get("publisher", ""),
                "link": item.get("link", ""),
                "published": datetime.fromtimestamp(
                    item.get("providerPublishTime", 0)
                ).strftime("%Y-%m-%d %H:%M") if item.get("providerPublishTime") else None,
                "type": item.get("type", ""),
                "thumbnail": item.get("thumbnail", {}).get("resolutions", [{}])[0].get("url") if item.get("thumbnail") else None,
            })

        return {
            "ticker": ticker,
            "news_count": len(news_items),
            "news": news_items,
        }

    except Exception as e:
        logger.error(f"Error fetching news for {ticker}: {e}")
        return {"error": str(e)}


class CompanyInfoInput(BaseModel):
    """Input for company info tool."""
    ticker: str = Field(..., description="Stock ticker")


@tool(args_schema=CompanyInfoInput)
def get_company_info(ticker: str) -> dict[str, Any]:
    """Get detailed company information.

    Args:
        ticker: Stock ticker

    Returns:
        Dictionary with company information
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        return {
            "ticker": ticker,
            "basic_info": {
                "name": info.get("longName") or info.get("shortName"),
                "sector": info.get("sector"),
                "industry": info.get("industry"),
                "country": info.get("country"),
                "website": info.get("website"),
                "employees": info.get("fullTimeEmployees"),
            },
            "business_summary": info.get("longBusinessSummary"),
            "officers": [
                {
                    "name": officer.get("name"),
                    "title": officer.get("title"),
                    "age": officer.get("age"),
                }
                for officer in info.get("companyOfficers", [])[:5]
            ],
            "address": {
                "address1": info.get("address1"),
                "city": info.get("city"),
                "state": info.get("state"),
                "zip": info.get("zip"),
                "country": info.get("country"),
                "phone": info.get("phone"),
            },
        }

    except Exception as e:
        logger.error(f"Error fetching company info for {ticker}: {e}")
        return {"error": str(e)}


@tool(args_schema=CompanyInfoInput)
def get_analyst_recommendations(ticker: str) -> dict[str, Any]:
    """Get analyst recommendations and price targets.

    Args:
        ticker: Stock ticker

    Returns:
        Dictionary with analyst data
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        # Get recommendations
        try:
            recommendations = stock.recommendations
            if recommendations is not None and not recommendations.empty:
                recent_recs = recommendations.tail(10).to_dict("records")
            else:
                recent_recs = []
        except Exception:
            recent_recs = []

        # Get recommendation trend
        try:
            rec_trend = stock.recommendations_summary
            if rec_trend is not None and not rec_trend.empty:
                trend_data = rec_trend.to_dict("records")
            else:
                trend_data = []
        except Exception:
            trend_data = []

        return {
            "ticker": ticker,
            "price_targets": {
                "current_price": info.get("currentPrice") or info.get("regularMarketPrice"),
                "target_high": info.get("targetHighPrice"),
                "target_low": info.get("targetLowPrice"),
                "target_mean": info.get("targetMeanPrice"),
                "target_median": info.get("targetMedianPrice"),
                "number_of_analysts": info.get("numberOfAnalystOpinions"),
            },
            "recommendation": {
                "recommendation_key": info.get("recommendationKey"),
                "recommendation_mean": info.get("recommendationMean"),
            },
            "recent_recommendations": recent_recs,
            "recommendation_trend": trend_data,
        }

    except Exception as e:
        logger.error(f"Error fetching analyst recommendations for {ticker}: {e}")
        return {"error": str(e)}


@tool(args_schema=CompanyInfoInput)
def get_insider_transactions(ticker: str) -> dict[str, Any]:
    """Get insider trading information.

    Args:
        ticker: Stock ticker

    Returns:
        Dictionary with insider transaction data
    """
    try:
        stock = yf.Ticker(ticker)

        # Get insider transactions
        try:
            insider_trans = stock.insider_transactions
            if insider_trans is not None and not insider_trans.empty:
                transactions = insider_trans.head(20).to_dict("records")
            else:
                transactions = []
        except Exception:
            transactions = []

        # Get insider holders
        try:
            insider_holders = stock.insider_holders
            if insider_holders is not None and not insider_holders.empty:
                holders = insider_holders.to_dict("records")
            else:
                holders = []
        except Exception:
            holders = []

        # Get institutional holders
        try:
            inst_holders = stock.institutional_holders
            if inst_holders is not None and not inst_holders.empty:
                institutional = inst_holders.head(10).to_dict("records")
            else:
                institutional = []
        except Exception:
            institutional = []

        # Analyze insider sentiment
        buy_count = sum(1 for t in transactions if "buy" in str(t.get("Transaction", "")).lower() or "purchase" in str(t.get("Transaction", "")).lower())
        sell_count = sum(1 for t in transactions if "sale" in str(t.get("Transaction", "")).lower() or "sell" in str(t.get("Transaction", "")).lower())

        if buy_count > sell_count * 2:
            insider_sentiment = "bullish"
        elif sell_count > buy_count * 2:
            insider_sentiment = "bearish"
        else:
            insider_sentiment = "neutral"

        return {
            "ticker": ticker,
            "insider_transactions": transactions,
            "insider_holders": holders,
            "institutional_holders": institutional,
            "insider_sentiment": insider_sentiment,
            "transaction_summary": {
                "buy_transactions": buy_count,
                "sell_transactions": sell_count,
            },
        }

    except Exception as e:
        logger.error(f"Error fetching insider transactions for {ticker}: {e}")
        return {"error": str(e)}


@tool(args_schema=CompanyInfoInput)
def get_earnings_history(ticker: str) -> dict[str, Any]:
    """Get earnings history and estimates.

    Args:
        ticker: Stock ticker

    Returns:
        Dictionary with earnings data
    """
    try:
        stock = yf.Ticker(ticker)

        # Get earnings history
        try:
            earnings_hist = stock.earnings_history
            if earnings_hist is not None and not earnings_hist.empty:
                history = earnings_hist.to_dict("records")
            else:
                history = []
        except Exception:
            history = []

        # Get earnings dates
        try:
            earnings_dates = stock.earnings_dates
            if earnings_dates is not None and not earnings_dates.empty:
                dates = earnings_dates.head(8).to_dict("records")
            else:
                dates = []
        except Exception:
            dates = []

        # Calculate beat/miss statistics
        beats = sum(1 for h in history if h.get("surprisePercent", 0) > 0)
        misses = sum(1 for h in history if h.get("surprisePercent", 0) < 0)

        return {
            "ticker": ticker,
            "earnings_history": history,
            "upcoming_earnings": dates,
            "beat_miss_summary": {
                "beats": beats,
                "misses": misses,
                "total": len(history),
                "beat_rate": round(beats / len(history) * 100, 1) if history else 0,
            },
        }

    except Exception as e:
        logger.error(f"Error fetching earnings history for {ticker}: {e}")
        return {"error": str(e)}
