"""Stock price data tools using yfinance."""
import logging
from datetime import datetime, timedelta
from typing import Any, Optional

import yfinance as yf
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from models.stock import MarketType, Stock, StockInfo

logger = logging.getLogger(__name__)


def _determine_market_type(ticker: str, info: dict) -> MarketType:
    """Determine market type from ticker and info."""
    exchange = info.get("exchange", "").upper()
    country = info.get("country", "").lower()

    if exchange in ["KSC", "KOE"] or ticker.endswith(".KS"):
        return MarketType.KOREA_KOSPI
    elif exchange in ["KOQ"] or ticker.endswith(".KQ"):
        return MarketType.KOREA_KOSDAQ
    elif exchange in ["NYQ", "NYSE"]:
        return MarketType.US_NYSE
    elif exchange in ["NMS", "NGM", "NASDAQ"]:
        return MarketType.US_NASDAQ
    elif exchange in ["ASE", "AMEX"]:
        return MarketType.US_AMEX
    elif "japan" in country or exchange in ["JPX", "TYO"]:
        return MarketType.JAPAN_TSE
    elif exchange in ["HKG", "HKEX"]:
        return MarketType.HONG_KONG_HKEX
    elif exchange in ["SHH", "SSE"]:
        return MarketType.CHINA_SSE
    elif exchange in ["SHZ", "SZSE"]:
        return MarketType.CHINA_SZSE
    else:
        return MarketType.OTHER


def _get_currency(market: MarketType) -> str:
    """Get currency for market type."""
    currency_map = {
        MarketType.KOREA_KOSPI: "KRW",
        MarketType.KOREA_KOSDAQ: "KRW",
        MarketType.US_NYSE: "USD",
        MarketType.US_NASDAQ: "USD",
        MarketType.US_AMEX: "USD",
        MarketType.JAPAN_TSE: "JPY",
        MarketType.CHINA_SSE: "CNY",
        MarketType.CHINA_SZSE: "CNY",
        MarketType.HONG_KONG_HKEX: "HKD",
    }
    return currency_map.get(market, "USD")


def _get_country(market: MarketType) -> str:
    """Get country code for market type."""
    country_map = {
        MarketType.KOREA_KOSPI: "KR",
        MarketType.KOREA_KOSDAQ: "KR",
        MarketType.US_NYSE: "US",
        MarketType.US_NASDAQ: "US",
        MarketType.US_AMEX: "US",
        MarketType.JAPAN_TSE: "JP",
        MarketType.CHINA_SSE: "CN",
        MarketType.CHINA_SZSE: "CN",
        MarketType.HONG_KONG_HKEX: "HK",
    }
    return country_map.get(market, "US")


class StockInfoInput(BaseModel):
    """Input for stock info tool."""
    ticker: str = Field(..., description="Stock ticker symbol (e.g., 'AAPL', '005930.KS')")


@tool(args_schema=StockInfoInput)
def get_stock_info(ticker: str) -> dict[str, Any]:
    """Get comprehensive stock information including price and fundamental data.

    Args:
        ticker: Stock ticker symbol

    Returns:
        Dictionary with stock information
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        if not info or "symbol" not in info:
            return {"error": f"Could not find stock with ticker: {ticker}"}

        market = _determine_market_type(ticker, info)

        stock_info = StockInfo(
            ticker=ticker,
            name=info.get("longName", info.get("shortName", ticker)),
            market=market,
            sector=info.get("sector"),
            industry=info.get("industry"),
            currency=info.get("currency", _get_currency(market)),
            country=info.get("country", _get_country(market)),
        )

        stock_data = Stock(
            info=stock_info,
            current_price=info.get("currentPrice") or info.get("regularMarketPrice"),
            prev_close=info.get("previousClose") or info.get("regularMarketPreviousClose"),
            market_cap=info.get("marketCap"),
            volume=info.get("volume") or info.get("regularMarketVolume"),
            avg_volume=info.get("averageVolume"),
            price_52w_high=info.get("fiftyTwoWeekHigh"),
            price_52w_low=info.get("fiftyTwoWeekLow"),
            beta=info.get("beta"),
            pe_ratio=info.get("trailingPE"),
            forward_pe=info.get("forwardPE"),
            pb_ratio=info.get("priceToBook"),
            ps_ratio=info.get("priceToSalesTrailing12Months"),
            ev_ebitda=info.get("enterpriseToEbitda"),
            peg_ratio=info.get("pegRatio"),
            dividend_yield=info.get("dividendYield", 0) * 100 if info.get("dividendYield") else None,
            dividend_payout_ratio=info.get("payoutRatio"),
            roe=info.get("returnOnEquity", 0) * 100 if info.get("returnOnEquity") else None,
            roa=info.get("returnOnAssets", 0) * 100 if info.get("returnOnAssets") else None,
            profit_margin=info.get("profitMargins", 0) * 100 if info.get("profitMargins") else None,
            operating_margin=info.get("operatingMargins", 0) * 100 if info.get("operatingMargins") else None,
            gross_margin=info.get("grossMargins", 0) * 100 if info.get("grossMargins") else None,
            current_ratio=info.get("currentRatio"),
            quick_ratio=info.get("quickRatio"),
            debt_to_equity=info.get("debtToEquity"),
            revenue_growth=info.get("revenueGrowth", 0) * 100 if info.get("revenueGrowth") else None,
            earnings_growth=info.get("earningsGrowth", 0) * 100 if info.get("earningsGrowth") else None,
            operating_cash_flow=info.get("operatingCashflow"),
            free_cash_flow=info.get("freeCashflow"),
        )

        return stock_data.model_dump()

    except Exception as e:
        logger.error(f"Error fetching stock info for {ticker}: {e}")
        return {"error": str(e)}


class StockPriceInput(BaseModel):
    """Input for stock price tool."""
    ticker: str = Field(..., description="Stock ticker symbol")


@tool(args_schema=StockPriceInput)
def get_stock_price(ticker: str) -> dict[str, Any]:
    """Get current stock price and basic price metrics.

    Args:
        ticker: Stock ticker symbol

    Returns:
        Dictionary with price information
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        return {
            "ticker": ticker,
            "current_price": info.get("currentPrice") or info.get("regularMarketPrice"),
            "previous_close": info.get("previousClose"),
            "open": info.get("open") or info.get("regularMarketOpen"),
            "day_high": info.get("dayHigh") or info.get("regularMarketDayHigh"),
            "day_low": info.get("dayLow") or info.get("regularMarketDayLow"),
            "volume": info.get("volume") or info.get("regularMarketVolume"),
            "avg_volume": info.get("averageVolume"),
            "market_cap": info.get("marketCap"),
            "52w_high": info.get("fiftyTwoWeekHigh"),
            "52w_low": info.get("fiftyTwoWeekLow"),
            "currency": info.get("currency", "USD"),
        }

    except Exception as e:
        logger.error(f"Error fetching stock price for {ticker}: {e}")
        return {"error": str(e)}


class PriceHistoryInput(BaseModel):
    """Input for price history tool."""
    ticker: str = Field(..., description="Stock ticker symbol")
    period: str = Field(
        default="1y",
        description="Time period: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max"
    )
    interval: str = Field(
        default="1d",
        description="Data interval: 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo"
    )


@tool(args_schema=PriceHistoryInput)
def get_price_history(
    ticker: str,
    period: str = "1y",
    interval: str = "1d"
) -> dict[str, Any]:
    """Get historical price data for a stock.

    Args:
        ticker: Stock ticker symbol
        period: Time period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
        interval: Data interval (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)

    Returns:
        Dictionary with historical price data
    """
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period, interval=interval)

        if hist.empty:
            return {"error": f"No historical data found for {ticker}"}

        # Convert to list of dictionaries
        records = []
        for date, row in hist.iterrows():
            records.append({
                "date": date.strftime("%Y-%m-%d"),
                "open": round(row["Open"], 2),
                "high": round(row["High"], 2),
                "low": round(row["Low"], 2),
                "close": round(row["Close"], 2),
                "volume": int(row["Volume"]),
            })

        # Calculate basic statistics
        closes = hist["Close"]
        stats = {
            "period_start": records[0]["date"] if records else None,
            "period_end": records[-1]["date"] if records else None,
            "start_price": records[0]["close"] if records else None,
            "end_price": records[-1]["close"] if records else None,
            "period_return": round(
                ((closes.iloc[-1] - closes.iloc[0]) / closes.iloc[0]) * 100, 2
            ) if len(closes) > 0 else None,
            "period_high": round(closes.max(), 2),
            "period_low": round(closes.min(), 2),
            "avg_price": round(closes.mean(), 2),
            "volatility": round(closes.pct_change().std() * (252 ** 0.5) * 100, 2),  # Annualized
            "total_records": len(records),
        }

        return {
            "ticker": ticker,
            "period": period,
            "interval": interval,
            "statistics": stats,
            "data": records[-30:] if len(records) > 30 else records,  # Last 30 records
        }

    except Exception as e:
        logger.error(f"Error fetching price history for {ticker}: {e}")
        return {"error": str(e)}


def get_stock_data_for_analysis(ticker: str) -> Optional[Stock]:
    """Get complete stock data for analysis (non-tool function).

    Args:
        ticker: Stock ticker symbol

    Returns:
        Stock object or None if error
    """
    result = get_stock_info.invoke({"ticker": ticker})
    if "error" in result:
        logger.error(f"Failed to get stock data: {result['error']}")
        return None

    try:
        # Reconstruct Stock from dict
        info_data = result.pop("info")
        stock_info = StockInfo(**info_data)
        return Stock(info=stock_info, **result)
    except Exception as e:
        logger.error(f"Error creating Stock object: {e}")
        return None
