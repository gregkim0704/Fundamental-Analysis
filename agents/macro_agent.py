"""Macro Agent - 거시경제 전문가."""
import json
import logging
from typing import Any, Optional

from agents.base_agent import BaseAgent, AgentConfig
from models.agent_opinion import AgentType, Sentiment
from models.analysis_result import MacroAnalysis
from tools.macro_data import get_interest_rates, get_economic_indicators, get_macro_environment_summary

logger = logging.getLogger(__name__)


class MacroAgent(BaseAgent):
    """Macro environment analysis agent."""

    def __init__(self, config: Optional[AgentConfig] = None):
        """Initialize Macro Agent."""
        if config is None:
            config = AgentConfig(
                agent_type=AgentType.MACRO,
                prompt_file="prompts/macro.md",
            )
        super().__init__(config, tools=[get_interest_rates, get_economic_indicators])

    def _get_default_prompt(self) -> str:
        """Get default system prompt."""
        return """You are a macroeconomic analysis expert. Analyze the macro environment
and its impact on the target stock from a top-down perspective.

Focus on:
1. Interest rate cycle and monetary policy
2. Liquidity environment
3. Economic cycle phase
4. Sector rotation positioning
5. Policy and geopolitical factors

Provide your analysis in JSON format with score (1-10), confidence (0-100),
sentiment, and detailed analysis."""

    async def analyze(self, context: dict[str, Any]) -> dict[str, Any]:
        """Perform macro environment analysis.

        Args:
            context: Analysis context including stock info

        Returns:
            Macro analysis result
        """
        ticker = context.get("ticker", "")
        stock_info = context.get("stock_info", {})
        sector = stock_info.get("info", {}).get("sector", "Unknown")
        industry = stock_info.get("info", {}).get("industry", "Unknown")

        # Get macro data
        macro_summary = get_macro_environment_summary()

        # Build analysis prompt
        prompt = f"""Analyze the macro environment impact on the following stock:

Ticker: {ticker}
Sector: {sector}
Industry: {industry}

Current Macro Environment:
{json.dumps(macro_summary, indent=2, default=str)}

Please provide a comprehensive macro analysis in JSON format following this structure:
{{
    "score": <1-10>,
    "confidence": <0-100>,
    "sentiment": "<very_bullish|bullish|neutral|bearish|very_bearish>",
    "summary": "<1-2 sentence summary>",
    "interest_rate_analysis": {{
        "current_phase": "<description>",
        "central_bank_stance": "<description>",
        "yield_curve": "<description>",
        "impact_on_stock": "<description>"
    }},
    "liquidity_analysis": {{
        "assessment": "<description>",
        "impact": "<description>"
    }},
    "economic_cycle": {{
        "current_phase": "<description>",
        "sector_positioning": "<description>"
    }},
    "policy_factors": {{
        "fiscal_policy": "<description>",
        "industry_policy": "<description>"
    }},
    "geopolitical_risks": ["<risk1>", "<risk2>"],
    "stock_specific_impact": {{
        "tailwinds": ["<tailwind1>", "<tailwind2>"],
        "headwinds": ["<headwind1>", "<headwind2>"],
        "overall_impact": "<description>"
    }},
    "key_points": ["<point1>", "<point2>"],
    "concerns": ["<concern1>", "<concern2>"]
}}"""

        try:
            response = await self.invoke(prompt)
            # Parse JSON from response
            result = self._parse_json_response(response)

            # Create MacroAnalysis object
            analysis = MacroAnalysis(
                score=result.get("score", 5),
                sentiment=self._map_sentiment(result.get("sentiment", "neutral")),
                summary=result.get("summary", ""),
                interest_rate_phase=result.get("interest_rate_analysis", {}).get("current_phase", ""),
                central_bank_stance=result.get("interest_rate_analysis", {}).get("central_bank_stance", ""),
                yield_curve_status=result.get("interest_rate_analysis", {}).get("yield_curve", ""),
                liquidity_assessment=result.get("liquidity_analysis", {}).get("assessment", ""),
                credit_spread_status=result.get("liquidity_analysis", {}).get("impact", ""),
                sector_rotation_phase=result.get("economic_cycle", {}).get("current_phase", ""),
                favorable_sectors=macro_summary.get("favorable_sectors", []),
                unfavorable_sectors=macro_summary.get("unfavorable_sectors", []),
                key_policy_impacts=[
                    result.get("policy_factors", {}).get("fiscal_policy", ""),
                    result.get("policy_factors", {}).get("industry_policy", ""),
                ],
                geopolitical_risks=result.get("geopolitical_risks", []),
                stock_specific_impact=result.get("stock_specific_impact", {}).get("overall_impact", ""),
                tailwinds=result.get("stock_specific_impact", {}).get("tailwinds", []),
                headwinds=result.get("stock_specific_impact", {}).get("headwinds", []),
            )

            return {
                "analysis": analysis.model_dump(),
                "raw_result": result,
                "opinion": self.create_opinion(
                    ticker=ticker,
                    score=result.get("score", 5),
                    confidence=result.get("confidence", 70),
                    summary=result.get("summary", ""),
                    key_points=result.get("key_points", []),
                    concerns=result.get("concerns", []),
                    detailed_analysis=result,
                ).model_dump(),
            }

        except Exception as e:
            logger.error(f"Error in macro analysis: {e}")
            return {
                "error": str(e),
                "analysis": None,
            }

    def _parse_json_response(self, response: str) -> dict[str, Any]:
        """Parse JSON from LLM response."""
        try:
            # Try direct JSON parse
            return json.loads(response)
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code block
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0]
                return json.loads(json_str)
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0]
                return json.loads(json_str)
            else:
                # Return default structure
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
