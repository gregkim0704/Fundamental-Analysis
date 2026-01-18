"""Pytest configuration and fixtures."""
import pytest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture
def sample_stock_info():
    """Sample stock info for testing."""
    return {
        "info": {
            "ticker": "TEST",
            "name": "Test Company",
            "market": "US_NYSE",
            "sector": "Technology",
            "industry": "Software",
            "currency": "USD",
            "country": "US",
        },
        "current_price": 150.0,
        "prev_close": 148.0,
        "market_cap": 1000000000000,
        "pe_ratio": 25.0,
        "pb_ratio": 10.0,
        "roe": 25.0,
        "roa": 15.0,
    }


@pytest.fixture
def sample_financial_data():
    """Sample financial data for testing."""
    return {
        "revenue": 100000000000,
        "operating_income": 25000000000,
        "net_income": 20000000000,
        "total_assets": 200000000000,
        "total_equity": 100000000000,
        "total_debt": 50000000000,
        "operating_cash_flow": 22000000000,
        "free_cash_flow": 18000000000,
    }


@pytest.fixture
def sample_agent_opinion():
    """Sample agent opinion for testing."""
    return {
        "agent_type": "quant",
        "ticker": "TEST",
        "score": 7.5,
        "confidence": 80,
        "sentiment": "bullish",
        "summary": "Strong financial metrics",
        "key_points": ["High ROIC", "Strong FCF"],
        "concerns": ["High valuation"],
    }
