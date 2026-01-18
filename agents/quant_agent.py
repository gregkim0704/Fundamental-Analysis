"""Quant Agent - 재무분석 전문가."""
import json
import logging
from typing import Any, Optional

from agents.base_agent import BaseAgent, AgentConfig
from models.agent_opinion import AgentType, RiskLevel, Sentiment
from models.analysis_result import QuantAnalysis
from core.financial_analysis import FinancialAnalyzer
from core.roic_wacc import calculate_value_creation
from core.quality_metrics import EarningsQualityAnalyzer

logger = logging.getLogger(__name__)


class QuantAgent(BaseAgent):
    """Quantitative financial analysis agent."""

    def __init__(self, config: Optional[AgentConfig] = None):
        """Initialize Quant Agent."""
        if config is None:
            config = AgentConfig(
                agent_type=AgentType.QUANT,
                prompt_file="prompts/quant.md",
            )
        super().__init__(config)

    def _get_default_prompt(self) -> str:
        """Get default system prompt."""
        return """You are a quantitative financial analysis expert. Analyze financial statements
to evaluate the company's financial health, profitability, and value creation ability.

Focus on:
1. Value creation (ROIC vs WACC)
2. Earnings quality (accrual ratio, cash conversion)
3. Cash flow quality
4. Working capital efficiency
5. Capital allocation
6. Financial health (leverage, liquidity)

Provide your analysis in JSON format with score (1-10), confidence (0-100),
sentiment, and detailed analysis."""

    async def analyze(self, context: dict[str, Any]) -> dict[str, Any]:
        """Perform quantitative financial analysis.

        Args:
            context: Analysis context including stock info

        Returns:
            Quant analysis result
        """
        ticker = context.get("ticker", "")

        try:
            # Get comprehensive financial analysis
            analyzer = FinancialAnalyzer(ticker)
            financial_data = analyzer.get_comprehensive_analysis()

            # Get value creation metrics
            value_creation = calculate_value_creation(ticker)

            # Get earnings quality
            quality_analyzer = EarningsQualityAnalyzer(ticker)
            earnings_quality = quality_analyzer.get_comprehensive_quality_analysis()

            # Build analysis prompt
            prompt = f"""Analyze the financial data for {ticker}:

Financial Analysis:
{json.dumps(financial_data, indent=2, default=str)}

Value Creation Metrics:
{json.dumps(value_creation, indent=2, default=str)}

Earnings Quality Analysis:
{json.dumps(earnings_quality, indent=2, default=str)}

Please provide a comprehensive quantitative analysis in JSON format:
{{
    "score": <1-10>,
    "confidence": <0-100>,
    "sentiment": "<very_bullish|bullish|neutral|bearish|very_bearish>",
    "summary": "<1-2 sentence summary>",
    "value_creation_assessment": "<description>",
    "earnings_quality_score": <1-10>,
    "earnings_manipulation_risk": "<low|medium|high|critical>",
    "fcf_trend": "<growing|stable|declining>",
    "cash_conversion_assessment": "<description>",
    "working_capital_trend": "<improving|stable|deteriorating>",
    "capital_allocation_assessment": "<description>",
    "leverage_assessment": "<conservative|moderate|elevated|high>",
    "key_points": ["<point1>", "<point2>"],
    "concerns": ["<concern1>", "<concern2>"],
    "quality_flags": ["<flag1>", "<flag2>"]
}}"""

            response = await self.invoke(prompt)
            result = self._parse_json_response(response)

            # Create QuantAnalysis object
            analysis = QuantAnalysis(
                score=result.get("score", 5),
                sentiment=self._map_sentiment(result.get("sentiment", "neutral")),
                summary=result.get("summary", ""),
                roic=value_creation.get("roic"),
                wacc=value_creation.get("wacc"),
                roic_wacc_spread=value_creation.get("spread"),
                eva=value_creation.get("eva"),
                value_creation_assessment=result.get("value_creation_assessment", ""),
                ocf_to_operating_income=financial_data.get("cash_flow", {}).get("history", [{}])[0].get("operating_cf"),
                fcf_trend=result.get("fcf_trend", "stable"),
                fcf_margin=financial_data.get("cash_flow", {}).get("fcf_yield"),
                cash_conversion_assessment=result.get("cash_conversion_assessment", ""),
                accrual_ratio=earnings_quality.get("accrual_analysis", {}).get("accrual_ratio"),
                earnings_quality_score=result.get("earnings_quality_score", 5),
                earnings_manipulation_risk=self._map_risk_level(result.get("earnings_manipulation_risk", "low")),
                quality_flags=result.get("quality_flags", []),
                capex_to_depreciation=earnings_quality.get("capex_analysis", {}).get("avg_capex_to_depreciation"),
                capital_allocation_assessment=result.get("capital_allocation_assessment", ""),
                days_sales_outstanding=earnings_quality.get("working_capital_analysis", {}).get("history", [{}])[0].get("dso"),
                days_inventory_outstanding=earnings_quality.get("working_capital_analysis", {}).get("history", [{}])[0].get("dio"),
                days_payable_outstanding=earnings_quality.get("working_capital_analysis", {}).get("history", [{}])[0].get("dpo"),
                cash_conversion_cycle=earnings_quality.get("working_capital_analysis", {}).get("history", [{}])[0].get("cash_conversion_cycle"),
                working_capital_trend=result.get("working_capital_trend", "stable"),
                debt_to_equity=financial_data.get("leverage", {}).get("metrics", {}).get("debt_to_equity"),
                interest_coverage=financial_data.get("leverage", {}).get("metrics", {}).get("interest_coverage"),
                current_ratio=financial_data.get("leverage", {}).get("metrics", {}).get("current_ratio"),
                leverage_assessment=result.get("leverage_assessment", "moderate"),
                key_metrics=financial_data.get("profitability", {}).get("current_metrics", {}),
            )

            return {
                "analysis": analysis.model_dump(),
                "raw_data": {
                    "financial_data": financial_data,
                    "value_creation": value_creation,
                    "earnings_quality": earnings_quality,
                },
                "opinion": self.create_opinion(
                    ticker=ticker,
                    score=result.get("score", 5),
                    confidence=result.get("confidence", 75),
                    summary=result.get("summary", ""),
                    key_points=result.get("key_points", []),
                    concerns=result.get("concerns", []),
                    detailed_analysis=result,
                ).model_dump(),
            }

        except Exception as e:
            logger.error(f"Error in quant analysis: {e}")
            return {
                "error": str(e),
                "analysis": None,
            }

    def _parse_json_response(self, response: str) -> dict[str, Any]:
        """Parse JSON from LLM response."""
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0]
                return json.loads(json_str)
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0]
                return json.loads(json_str)
            else:
                return {
                    "score": 5,
                    "confidence": 50,
                    "sentiment": "neutral",
                    "summary": response[:200],
                    "key_points": [],
                    "concerns": [],
                }

    def _map_sentiment(self, sentiment_str: str) -> Sentiment:
        """Map string sentiment to Sentiment enum."""
        mapping = {
            "very_bullish": Sentiment.VERY_BULLISH,
            "bullish": Sentiment.BULLISH,
            "neutral": Sentiment.NEUTRAL,
            "bearish": Sentiment.BEARISH,
            "very_bearish": Sentiment.VERY_BEARISH,
        }
        return mapping.get(sentiment_str.lower(), Sentiment.NEUTRAL)

    def _map_risk_level(self, risk_str: str) -> RiskLevel:
        """Map string risk level to RiskLevel enum."""
        mapping = {
            "low": RiskLevel.LOW,
            "medium": RiskLevel.MEDIUM,
            "high": RiskLevel.HIGH,
            "critical": RiskLevel.CRITICAL,
        }
        return mapping.get(risk_str.lower(), RiskLevel.MEDIUM)
