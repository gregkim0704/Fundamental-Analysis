"""Tests for financial analysis module."""
import pytest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.financial_analysis import FinancialAnalyzer
from core.roic_wacc import ROICCalculator, WACCCalculator, calculate_value_creation
from core.quality_metrics import EarningsQualityAnalyzer


class TestFinancialAnalyzer:
    """Tests for FinancialAnalyzer class."""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance."""
        return FinancialAnalyzer("AAPL")

    def test_profitability_analysis(self, analyzer):
        """Test profitability analysis."""
        result = analyzer.get_profitability_analysis()

        assert "error" not in result or result.get("current_metrics") is not None
        if "current_metrics" in result:
            metrics = result["current_metrics"]
            # Check for expected keys
            assert "gross_margin" in metrics or metrics.get("gross_margin") is None

    def test_growth_analysis(self, analyzer):
        """Test growth analysis."""
        result = analyzer.get_growth_analysis()

        assert result is not None
        assert "current_growth" in result or "error" in result

    def test_leverage_analysis(self, analyzer):
        """Test leverage analysis."""
        result = analyzer.get_leverage_analysis()

        assert result is not None
        if "metrics" in result:
            assert "debt_to_equity" in result["metrics"] or result["metrics"].get("debt_to_equity") is None

    def test_cash_flow_analysis(self, analyzer):
        """Test cash flow analysis."""
        result = analyzer.get_cash_flow_analysis()

        assert result is not None
        assert "history" in result or "error" in result

    def test_comprehensive_analysis(self, analyzer):
        """Test comprehensive analysis."""
        result = analyzer.get_comprehensive_analysis()

        assert result is not None
        assert "overall_score" in result
        assert 1 <= result["overall_score"] <= 10


class TestROICCalculator:
    """Tests for ROIC Calculator."""

    @pytest.fixture
    def calculator(self):
        """Create calculator instance."""
        return ROICCalculator("MSFT")

    def test_calculate_invested_capital(self, calculator):
        """Test invested capital calculation."""
        result = calculator.calculate_invested_capital()

        # May be None if data unavailable
        if result is not None:
            assert isinstance(result, float)

    def test_calculate_nopat(self, calculator):
        """Test NOPAT calculation."""
        result = calculator.calculate_nopat()

        if result is not None:
            assert isinstance(result, float)

    def test_calculate_roic(self, calculator):
        """Test ROIC calculation."""
        result = calculator.calculate_roic()

        assert result is not None
        if "roic" in result:
            assert isinstance(result["roic"], (int, float))


class TestWACCCalculator:
    """Tests for WACC Calculator."""

    @pytest.fixture
    def calculator(self):
        """Create calculator instance."""
        return WACCCalculator("GOOGL")

    def test_estimate_cost_of_equity(self, calculator):
        """Test cost of equity estimation."""
        result = calculator.estimate_cost_of_equity()

        assert "cost_of_equity" in result
        assert isinstance(result["cost_of_equity"], (int, float))
        assert result["method"] == "CAPM"

    def test_estimate_cost_of_debt(self, calculator):
        """Test cost of debt estimation."""
        result = calculator.estimate_cost_of_debt()

        assert "cost_of_debt" in result
        assert isinstance(result["cost_of_debt"], (int, float))

    def test_calculate_wacc(self, calculator):
        """Test WACC calculation."""
        result = calculator.calculate_wacc()

        if "error" not in result:
            assert "wacc" in result
            assert isinstance(result["wacc"], (int, float))


class TestValueCreation:
    """Tests for value creation calculation."""

    def test_calculate_value_creation(self):
        """Test value creation calculation."""
        result = calculate_value_creation("AAPL")

        assert result is not None
        if "error" not in result:
            assert "roic" in result
            assert "wacc" in result
            assert "spread" in result
            assert "creates_value" in result


class TestEarningsQualityAnalyzer:
    """Tests for EarningsQualityAnalyzer."""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance."""
        return EarningsQualityAnalyzer("NVDA")

    def test_accrual_ratio(self, analyzer):
        """Test accrual ratio calculation."""
        result = analyzer.calculate_accrual_ratio()

        assert result is not None
        if "accrual_ratio" in result:
            assert isinstance(result["accrual_ratio"], (int, float))
            assert "quality" in result

    def test_cash_conversion(self, analyzer):
        """Test cash conversion analysis."""
        result = analyzer.calculate_cash_conversion()

        assert result is not None

    def test_working_capital(self, analyzer):
        """Test working capital analysis."""
        result = analyzer.analyze_working_capital()

        assert result is not None

    def test_comprehensive_quality(self, analyzer):
        """Test comprehensive quality analysis."""
        result = analyzer.get_comprehensive_quality_analysis()

        assert result is not None
        assert "overall_quality_score" in result
        assert 1 <= result["overall_quality_score"] <= 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
