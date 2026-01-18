"""Chairman Agent - 투자위원회 의장."""
import json
import logging
from datetime import datetime
from typing import Any, Optional

from agents.base_agent import BaseAgent, AgentConfig
from models.agent_opinion import (
    AgentOpinion,
    AgentType,
    AgentVote,
    CommitteeDecision,
    DebateRound,
    RiskLevel,
    Sentiment,
)

logger = logging.getLogger(__name__)


class ChairmanAgent(BaseAgent):
    """Chairman agent - orchestrates the investment committee."""

    def __init__(self, config: Optional[AgentConfig] = None):
        """Initialize Chairman Agent."""
        if config is None:
            config = AgentConfig(
                agent_type=AgentType.CHAIRMAN,
                prompt_file="prompts/chairman.md",
            )
        super().__init__(config)

    def _get_default_prompt(self) -> str:
        """Get default system prompt."""
        return """You are the Chairman of the AI Investment Committee. Your responsibilities:
1. Orchestrate the analysis process
2. Mediate debates between agents
3. Synthesize all analyses into a final investment decision
4. Ensure transparency in the decision-making process

Provide balanced, well-reasoned investment recommendations based on all inputs."""

    async def analyze(self, context: dict[str, Any]) -> dict[str, Any]:
        """Synthesize all agent analyses into final decision.

        Args:
            context: Analysis context with all agent results

        Returns:
            Final committee decision
        """
        ticker = context.get("ticker", "")
        company_name = context.get("company_name", ticker)
        current_price = context.get("current_price", 0)

        # Collect all agent opinions
        agent_opinions = context.get("agent_opinions", {})
        debate_rounds = context.get("debate_rounds", [])

        # Build synthesis prompt
        prompt = f"""As Chairman, synthesize the following analyses for {ticker} ({company_name}):

Current Price: {current_price}

=== AGENT OPINIONS ===
{json.dumps(agent_opinions, indent=2, default=str)}

=== DEBATE ROUNDS ===
{json.dumps(debate_rounds, indent=2, default=str)}

Please provide the final committee decision in JSON format:
{{
    "weighted_average_score": <1-10>,
    "consensus_level": <0-100>,
    "final_sentiment": "<very_bullish|bullish|neutral|bearish|very_bearish>",
    "recommendation": "<Strong Buy|Buy|Hold|Sell|Strong Sell>",
    "executive_summary": "<2-3 sentence summary>",
    "investment_thesis": "<brief investment thesis>",
    "target_price_low": <number>,
    "target_price_mid": <number>,
    "target_price_high": <number>,
    "risk_level": "<low|medium|high|critical>",
    "key_strengths": ["<strength1>", "<strength2>"],
    "key_risks": ["<risk1>", "<risk2>"],
    "dissenting_opinions": ["<dissent1>", "<dissent2>"],
    "action_items": ["<action1>", "<action2>"],
    "monitoring_points": ["<point1>", "<point2>"],
    "conviction_level": "<low|medium|high>"
}}"""

        try:
            response = await self.invoke(prompt)
            result = self._parse_json_response(response)

            # Create agent votes from opinions
            votes = self._create_votes_from_opinions(agent_opinions)

            # Calculate weighted average score
            weighted_score = self._calculate_weighted_score(votes)

            # Calculate consensus level
            consensus = self._calculate_consensus(votes)

            # Create CommitteeDecision
            decision = CommitteeDecision(
                ticker=ticker,
                company_name=company_name,
                votes=votes,
                weighted_average_score=result.get("weighted_average_score", weighted_score),
                consensus_level=result.get("consensus_level", consensus),
                final_sentiment=self._map_sentiment(result.get("final_sentiment", "neutral")),
                recommendation=result.get("recommendation", "Hold"),
                target_price_low=result.get("target_price_low"),
                target_price_mid=result.get("target_price_mid"),
                target_price_high=result.get("target_price_high"),
                risk_level=self._map_risk_level(result.get("risk_level", "medium")),
                key_risks=result.get("key_risks", []),
                action_items=result.get("action_items", []),
                monitoring_points=result.get("monitoring_points", []),
                debate_rounds=[DebateRound(**dr) if isinstance(dr, dict) else dr for dr in debate_rounds],
                dissenting_opinions=result.get("dissenting_opinions", []),
            )

            return {
                "decision": decision.model_dump(),
                "raw_result": result,
                "summary": {
                    "ticker": ticker,
                    "recommendation": decision.recommendation,
                    "weighted_score": decision.weighted_average_score,
                    "consensus": decision.consensus_level,
                    "target_price": decision.target_price_mid,
                    "risk_level": decision.risk_level.value,
                    "executive_summary": result.get("executive_summary", ""),
                    "investment_thesis": result.get("investment_thesis", ""),
                    "key_strengths": result.get("key_strengths", []),
                    "key_risks": result.get("key_risks", []),
                    "conviction_level": result.get("conviction_level", "medium"),
                },
            }

        except Exception as e:
            logger.error(f"Error in chairman synthesis: {e}")
            return {
                "error": str(e),
                "decision": None,
            }

    def _create_votes_from_opinions(self, opinions: dict[str, Any]) -> list[AgentVote]:
        """Create AgentVote objects from agent opinions."""
        votes = []
        for agent_type_str, opinion_data in opinions.items():
            try:
                if isinstance(opinion_data, dict) and "score" in opinion_data:
                    vote = AgentVote(
                        agent_type=AgentType(agent_type_str),
                        score=opinion_data.get("score", 5),
                        confidence=opinion_data.get("confidence", 70),
                        sentiment=self._map_sentiment(opinion_data.get("sentiment", "neutral")),
                        rationale=opinion_data.get("summary", ""),
                    )
                    votes.append(vote)
            except (ValueError, KeyError) as e:
                logger.warning(f"Could not create vote for {agent_type_str}: {e}")
        return votes

    def _calculate_weighted_score(self, votes: list[AgentVote]) -> float:
        """Calculate confidence-weighted average score."""
        if not votes:
            return 5.0

        total_weighted_score = sum(v.score * v.confidence for v in votes)
        total_confidence = sum(v.confidence for v in votes)

        if total_confidence == 0:
            return sum(v.score for v in votes) / len(votes)

        return round(total_weighted_score / total_confidence, 1)

    def _calculate_consensus(self, votes: list[AgentVote]) -> float:
        """Calculate consensus level based on score variance."""
        if not votes or len(votes) < 2:
            return 100.0

        scores = [v.score for v in votes]
        mean_score = sum(scores) / len(scores)
        variance = sum((s - mean_score) ** 2 for s in scores) / len(scores)

        # Convert variance to consensus percentage
        # Lower variance = higher consensus
        # Max variance for 1-10 scale is ~20, so normalize
        max_variance = 20
        consensus = max(0, 100 - (variance / max_variance * 100))

        return round(consensus, 1)

    async def mediate_debate(
        self,
        counter_arguments: list[dict],
        responses: list[dict],
    ) -> dict[str, Any]:
        """Mediate a debate round between agents.

        Args:
            counter_arguments: Counter-arguments from Devil's Advocate
            responses: Responses from other agents

        Returns:
            Debate round summary with resolutions
        """
        prompt = f"""As Chairman, mediate the following debate:

Counter-Arguments:
{json.dumps(counter_arguments, indent=2)}

Responses:
{json.dumps(responses, indent=2)}

Provide your mediation in JSON format:
{{
    "resolved_issues": ["<issue that was satisfactorily addressed>"],
    "remaining_concerns": ["<concern that needs further attention>"],
    "weight_adjustments": {{
        "<agent_type>": <adjustment factor 0.5-1.5>
    }},
    "summary": "<brief summary of debate outcome>"
}}"""

        try:
            response = await self.invoke(prompt)
            return self._parse_json_response(response)
        except Exception as e:
            logger.error(f"Error in debate mediation: {e}")
            return {
                "resolved_issues": [],
                "remaining_concerns": [],
                "weight_adjustments": {},
                "summary": "Debate mediation failed",
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
                    "weighted_average_score": 5,
                    "consensus_level": 50,
                    "final_sentiment": "neutral",
                    "recommendation": "Hold",
                    "executive_summary": response[:200],
                }

    def _map_sentiment(self, sentiment_str: str) -> Sentiment:
        """Map string sentiment to Sentiment enum."""
        if isinstance(sentiment_str, Sentiment):
            return sentiment_str
        mapping = {
            "very_bullish": Sentiment.VERY_BULLISH,
            "bullish": Sentiment.BULLISH,
            "neutral": Sentiment.NEUTRAL,
            "bearish": Sentiment.BEARISH,
            "very_bearish": Sentiment.VERY_BEARISH,
        }
        return mapping.get(str(sentiment_str).lower(), Sentiment.NEUTRAL)

    def _map_risk_level(self, risk_str: str) -> RiskLevel:
        """Map string risk level to RiskLevel enum."""
        if isinstance(risk_str, RiskLevel):
            return risk_str
        mapping = {
            "low": RiskLevel.LOW,
            "medium": RiskLevel.MEDIUM,
            "high": RiskLevel.HIGH,
            "critical": RiskLevel.CRITICAL,
        }
        return mapping.get(str(risk_str).lower(), RiskLevel.MEDIUM)
