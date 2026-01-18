"""Valuation Agent - 밸류에이션 전문가."""
import json
import logging
from typing import Any, Optional

from agents.base_agent import BaseAgent, AgentConfig
from models.agent_opinion import AgentType, Sentiment
from models.analysis_result import ValuationAnalysis, ValuationScenario
from core.valuation_models import get_comprehensive_valuation
from tools.stock_price import get_stock_info

logger = logging.getLogger(__name__)


class ValuationAgent(BaseAgent):
    """Valuation analysis agent."""

    def __init__(self, config: Optional[AgentConfig] = None):
        """Initialize Valuation Agent."""
        if config is None:
            config = AgentConfig(
                agent_type=AgentType.VALUATION,
                prompt_file="prompts/valuation.md",
            )
        super().__init__(config)

    def _get_default_prompt(self) -> str:
        """Get default system prompt."""
        return """You are a valuation expert. Apply multiple valuation methodologies
to determine fair value range for the stock.

Methods to use:
1. DCF (Discounted Cash Flow)
2. Relative valuation (P/E, P/B, EV/EBITDA)
3. Scenario analysis (Bear/Base/Bull cases)

Provide your analysis in JSON format with score (1-10), confidence (0-100),
sentiment, target prices, and detailed methodology."""

    async def analyze(self, context: dict[str, Any]) -> dict[str, Any]:
        """Perform valuation analysis.

        Args:
            context: Analysis context including stock info and other agent results

        Returns:
            Valuation analysis result
        """
        ticker = context.get("ticker", "")

        try:
            # Get comprehensive valuation
            valuation_data = get_comprehensive_valuation(ticker)

            # Get stock info for current price
            stock_info = get_stock_info.invoke({"ticker": ticker})
            current_price = stock_info.get("current_price") or valuation_data.get("current_price")
            currency = stock_info.get("info", {}).get("currency", "USD") if isinstance(stock_info.get("info"), dict) else "USD"

            # Get other agent analyses from context
            quant_analysis = context.get("quant_analysis", {})
            industry_analysis = context.get("industry_analysis", {})

            # Build analysis prompt
            prompt = f"""Analyze the valuation for {ticker}:

Current Price: {current_price} {currency}

Valuation Data:
{json.dumps(valuation_data, indent=2, default=str)}

Quant Analysis Context:
{json.dumps(quant_analysis, indent=2, default=str)}

Industry Analysis Context:
{json.dumps(industry_analysis, indent=2, default=str)}

Please provide a comprehensive valuation analysis in JSON format:
{{
    "score": <1-10>,
    "confidence": <0-100>,
    "sentiment": "<very_bullish|bullish|neutral|bearish|very_bearish>",
    "summary": "<1-2 sentence summary>",
    "current_vs_historical": "<below_average|near_average|above_average>",
    "bear_case": {{
        "probability": 20,
        "target_price": <number>,
        "key_assumptions": ["<assumption1>", "<assumption2>"],
        "upside_downside": <percentage>
    }},
    "base_case": {{
        "probability": 60,
        "target_price": <number>,
        "key_assumptions": ["<assumption1>", "<assumption2>"],
        "upside_downside": <percentage>
    }},
    "bull_case": {{
        "probability": 20,
        "target_price": <number>,
        "key_assumptions": ["<assumption1>", "<assumption2>"],
        "upside_downside": <percentage>
    }},
    "methodology_weights": {{
        "dcf": <0-100>,
        "per": <0-100>,
        "pbr": <0-100>,
        "ev_ebitda": <0-100>
    }},
    "margin_of_safety": <percentage or null>,
    "key_points": ["<point1>", "<point2>"],
    "concerns": ["<concern1>", "<concern2>"],
    "catalysts": ["<catalyst1>", "<catalyst2>"]
}}"""

            response = await self.invoke(prompt)
            result = self._parse_json_response(response)

            # Extract target prices
            dcf_data = valuation_data.get("dcf_valuation", {}).get("base_case", {})
            target_range = valuation_data.get("target_price_range", {})

            target_low = result.get("bear_case", {}).get("target_price") or target_range.get("low")
            target_mid = result.get("base_case", {}).get("target_price") or target_range.get("mid")
            target_high = result.get("bull_case", {}).get("target_price") or target_range.get("high")

            # Calculate expected return
            expected_return = 0
            if current_price and target_mid:
                expected_return = ((target_mid - current_price) / current_price) * 100

            # Create scenario objects
            bear_case = ValuationScenario(
                name="Bear Case",
                probability=result.get("bear_case", {}).get("probability", 20),
                target_price=target_low or current_price * 0.8,
                upside_downside=result.get("bear_case", {}).get("upside_downside", -20),
                key_assumptions=result.get("bear_case", {}).get("key_assumptions", []),
            )

            base_case = ValuationScenario(
                name="Base Case",
                probability=result.get("base_case", {}).get("probability", 60),
                target_price=target_mid or current_price,
                upside_downside=result.get("base_case", {}).get("upside_downside", 0),
                key_assumptions=result.get("base_case", {}).get("key_assumptions", []),
            )

            bull_case = ValuationScenario(
                name="Bull Case",
                probability=result.get("bull_case", {}).get("probability", 20),
                target_price=target_high or current_price * 1.3,
                upside_downside=result.get("bull_case", {}).get("upside_downside", 30),
                key_assumptions=result.get("bull_case", {}).get("key_assumptions", []),
            )

            # Create ValuationAnalysis object
            analysis = ValuationAnalysis(
                score=result.get("score", 5),
                sentiment=self._map_sentiment(result.get("sentiment", "neutral")),
                summary=result.get("summary", ""),
                current_price=current_price or 0,
                currency=currency,
                dcf_value=dcf_data.get("intrinsic_value"),
                dcf_assumptions=dcf_data.get("assumptions", {}),
                peer_pe_average=valuation_data.get("relative_valuation", {}).get("current_multiples", {}).get("pe_ratio"),
                peer_pb_average=valuation_data.get("relative_valuation", {}).get("current_multiples", {}).get("pb_ratio"),
                peer_ev_ebitda_average=valuation_data.get("relative_valuation", {}).get("current_multiples", {}).get("ev_ebitda"),
                current_vs_historical=result.get("current_vs_historical", "near_average"),
                bear_case=bear_case,
                base_case=base_case,
                bull_case=bull_case,
                target_price_low=target_low or current_price * 0.8,
                target_price_mid=target_mid or current_price,
                target_price_high=target_high or current_price * 1.3,
                expected_return=round(expected_return, 1),
                methodology_weights=result.get("methodology_weights", {}),
                margin_of_safety=result.get("margin_of_safety"),
            )

            return {
                "analysis": analysis.model_dump(),
                "raw_data": valuation_data,
                "opinion": self.create_opinion(
                    ticker=ticker,
                    score=result.get("score", 5),
                    confidence=result.get("confidence", 75),
                    summary=result.get("summary", ""),
                    key_points=result.get("key_points", []),
                    concerns=result.get("concerns", []),
                    detailed_analysis={
                        **result,
                        "catalysts": result.get("catalysts", []),
                    },
                ).model_dump(),
            }

        except Exception as e:
            logger.error(f"Error in valuation analysis: {e}")
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
