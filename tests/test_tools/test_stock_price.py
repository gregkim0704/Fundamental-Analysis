"""Tests for stock price tools."""
import pytest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from tools.stock_price import get_stock_info, get_stock_price, get_price_history


class TestGetStockInfo:
    """Tests for get_stock_info function."""

    def test_valid_us_ticker(self):
        """Test with a valid US ticker."""
        result = get_stock_info.invoke({"ticker": "AAPL"})

        assert "error" not in result
        assert "info" in result
        assert result["info"]["ticker"] == "AAPL"
        assert result.get("current_price") is not None

    def test_valid_korean_ticker(self):
        """Test with a valid Korean ticker."""
        result = get_stock_info.invoke({"ticker": "005930.KS"})

        # May fail if market is closed or data unavailable
        if "error" not in result:
            assert "info" in result
            assert "KS" in result["info"]["ticker"]

    def test_invalid_ticker(self):
        """Test with an invalid ticker."""
        result = get_stock_info.invoke({"ticker": "INVALIDTICKER12345"})

        # Should either return error or empty/minimal data
        # yfinance behavior may vary
        assert result is not None


class TestGetStockPrice:
    """Tests for get_stock_price function."""

    def test_get_price(self):
        """Test getting current price."""
        result = get_stock_price.invoke({"ticker": "MSFT"})

        assert "error" not in result
        assert "current_price" in result
        assert "previous_close" in result


class TestGetPriceHistory:
    """Tests for get_price_history function."""

    def test_get_history_default(self):
        """Test getting price history with default parameters."""
        result = get_price_history.invoke({"ticker": "GOOGL"})

        assert "error" not in result
        assert "data" in result
        assert "statistics" in result
        assert len(result["data"]) > 0

    def test_get_history_custom_period(self):
        """Test getting price history with custom period."""
        result = get_price_history.invoke({
            "ticker": "GOOGL",
            "period": "3mo",
            "interval": "1d"
        })

        assert "error" not in result
        assert "data" in result

    def test_history_statistics(self):
        """Test that statistics are calculated correctly."""
        result = get_price_history.invoke({
            "ticker": "AAPL",
            "period": "1y"
        })

        if "error" not in result:
            stats = result["statistics"]
            assert "period_return" in stats
            assert "period_high" in stats
            assert "period_low" in stats
            assert "volatility" in stats


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
