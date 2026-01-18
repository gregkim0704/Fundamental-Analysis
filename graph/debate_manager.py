"""Debate Manager for multi-agent discussion system."""
import asyncio
import logging
from typing import Any, Optional

from pydantic import BaseModel, Field

from models.agent_opinion import (
    AgentOpinion,
    AgentType,
    AgentResponse,
    CounterArgument,
    DebateRound,
    RiskLevel,
    Sentiment,
)

logger = logging.getLogger(__name__)


class DebateMessage(BaseModel):
    """A single message in the debate."""
    speaker: AgentType
    target: Optional[AgentType] = None
    message_type: str  # "challenge", "defense", "rebuttal", "concession", "clarification"
    content: str
    evidence: list[str] = Field(default_factory=list)
    score_adjustment: Optional[float] = None
    round_number: int = 1


class DebateTranscript(BaseModel):
    """Full transcript of the debate."""
    ticker: str
    messages: list[DebateMessage] = Field(default_factory=list)
    rounds: list[DebateRound] = Field(default_factory=list)
    initial_opinions: dict[str, AgentOpinion] = Field(default_factory=dict)
    final_opinions: dict[str, AgentOpinion] = Field(default_factory=dict)
    consensus_reached: bool = False
    key_disagreements: list[str] = Field(default_factory=list)
    resolved_issues: list[str] = Field(default_factory=list)


class DebateManager:
    """Manages structured debates between agents.

    토론 프로세스:
    1. Devil's Advocate가 각 에이전트의 분석에 대해 도전
    2. 각 에이전트가 자신의 입장을 방어
    3. Devil's Advocate가 재반박
    4. 에이전트들이 최종 입장 조정
    5. 3라운드 반복 후 Chairman이 정리
    """

    def __init__(self, agents: dict[str, Any], max_rounds: int = 3):
        """Initialize the debate manager.

        Args:
            agents: Dictionary of agent instances by type
            max_rounds: Maximum number of debate rounds
        """
        self.agents = agents
        self.max_rounds = max_rounds
        self.transcript = None

    async def run_debate(
        self,
        ticker: str,
        initial_opinions: dict[str, AgentOpinion],
        stock_context: dict[str, Any],
    ) -> DebateTranscript:
        """Run a full debate session.

        Args:
            ticker: Stock ticker
            initial_opinions: Initial opinions from all agents
            stock_context: Stock data context

        Returns:
            Complete debate transcript
        """
        logger.info(f"Starting debate for {ticker} with {len(initial_opinions)} agents")

        self.transcript = DebateTranscript(
            ticker=ticker,
            initial_opinions=initial_opinions,
        )

        current_opinions = initial_opinions.copy()

        for round_num in range(1, self.max_rounds + 1):
            logger.info(f"=== Debate Round {round_num} ===")

            debate_round = await self._execute_round(
                round_num=round_num,
                current_opinions=current_opinions,
                stock_context=stock_context,
            )

            self.transcript.rounds.append(debate_round)

            # Update opinions based on round results
            current_opinions = await self._update_opinions_after_round(
                current_opinions,
                debate_round,
            )

            # Check for early consensus
            if self._check_consensus(current_opinions):
                logger.info(f"Consensus reached after round {round_num}")
                self.transcript.consensus_reached = True
                break

        self.transcript.final_opinions = current_opinions
        self.transcript.key_disagreements = self._identify_key_disagreements(current_opinions)

        return self.transcript

    async def _execute_round(
        self,
        round_num: int,
        current_opinions: dict[str, AgentOpinion],
        stock_context: dict[str, Any],
    ) -> DebateRound:
        """Execute a single debate round.

        Each round consists of:
        1. Devil's Advocate challenges each agent
        2. Agents defend their positions
        3. Devil's Advocate rebuts
        4. Agents may adjust their positions
        """
        devils_advocate = self.agents.get("devils_advocate")
        if not devils_advocate:
            return DebateRound(round_number=round_num)

        counter_arguments = []
        responses = []

        # Phase 1: Devil's Advocate challenges each opinion
        for agent_type_str, opinion in current_opinions.items():
            if agent_type_str == "devils_advocate":
                continue

            challenge = await self._generate_challenge(
                devils_advocate=devils_advocate,
                target_opinion=opinion,
                round_num=round_num,
                stock_context=stock_context,
            )

            if challenge:
                counter_arguments.append(challenge)

                # Record the challenge message
                self.transcript.messages.append(DebateMessage(
                    speaker=AgentType.DEVILS_ADVOCATE,
                    target=opinion.agent_type,
                    message_type="challenge",
                    content=challenge.counter_argument,
                    evidence=challenge.evidence,
                    round_number=round_num,
                ))

        # Phase 2: Agents defend their positions
        for counter_arg in counter_arguments:
            target_agent = self.agents.get(counter_arg.target_agent.value)
            if not target_agent:
                continue

            response = await self._generate_defense(
                agent=target_agent,
                counter_argument=counter_arg,
                original_opinion=current_opinions.get(counter_arg.target_agent.value),
                stock_context=stock_context,
            )

            if response:
                responses.append(response)

                # Record the defense message
                self.transcript.messages.append(DebateMessage(
                    speaker=counter_arg.target_agent,
                    target=AgentType.DEVILS_ADVOCATE,
                    message_type="defense",
                    content=response.response,
                    score_adjustment=response.adjusted_score,
                    round_number=round_num,
                ))

        # Phase 3: Devil's Advocate rebuts weak defenses
        for response in responses:
            if not self._is_strong_defense(response):
                rebuttal = await self._generate_rebuttal(
                    devils_advocate=devils_advocate,
                    original_challenge=self._find_challenge(counter_arguments, response),
                    defense=response,
                    stock_context=stock_context,
                )

                if rebuttal:
                    self.transcript.messages.append(DebateMessage(
                        speaker=AgentType.DEVILS_ADVOCATE,
                        target=response.agent_type,
                        message_type="rebuttal",
                        content=rebuttal,
                        round_number=round_num,
                    ))

        # Identify resolved and remaining issues
        resolved = self._identify_resolved_issues(counter_arguments, responses)
        remaining = self._identify_remaining_concerns(counter_arguments, responses)

        return DebateRound(
            round_number=round_num,
            counter_arguments=counter_arguments,
            responses=responses,
            resolved_issues=resolved,
            remaining_concerns=remaining,
        )

    async def _generate_challenge(
        self,
        devils_advocate,
        target_opinion: AgentOpinion,
        round_num: int,
        stock_context: dict[str, Any],
    ) -> Optional[CounterArgument]:
        """Generate a challenge from Devil's Advocate."""
        try:
            # Prepare context for the challenge
            context = {
                "target_agent": target_opinion.agent_type.value,
                "target_score": target_opinion.score,
                "target_sentiment": target_opinion.sentiment.value,
                "target_summary": target_opinion.summary,
                "target_key_points": target_opinion.key_points,
                "round_number": round_num,
                "stock_info": stock_context,
            }

            # Use devil's advocate's rebut method
            if hasattr(devils_advocate, 'challenge'):
                result = await devils_advocate.challenge(context)
            else:
                result = await devils_advocate.analyze(context)

            if result and "counter_argument" in result:
                return CounterArgument(
                    target_agent=target_opinion.agent_type,
                    original_claim=target_opinion.summary,
                    counter_argument=result["counter_argument"],
                    evidence=result.get("evidence", []),
                    severity=RiskLevel(result.get("severity", "medium")),
                )

        except Exception as e:
            logger.error(f"Error generating challenge: {e}")

        return None

    async def _generate_defense(
        self,
        agent,
        counter_argument: CounterArgument,
        original_opinion: AgentOpinion,
        stock_context: dict[str, Any],
    ) -> Optional[AgentResponse]:
        """Generate a defense from the challenged agent."""
        try:
            context = {
                "original_opinion": original_opinion.model_dump() if original_opinion else {},
                "challenge": counter_argument.counter_argument,
                "challenge_evidence": counter_argument.evidence,
                "severity": counter_argument.severity.value,
                "stock_info": stock_context,
            }

            # Use agent's rebut method if available
            if hasattr(agent, 'rebut'):
                result = await agent.rebut(context)
            else:
                # Fallback: generate defense through analyze with defense context
                context["mode"] = "defense"
                result = await agent.analyze(context)

            if result:
                return AgentResponse(
                    agent_type=original_opinion.agent_type if original_opinion else AgentType.QUANT,
                    counter_argument_id=str(id(counter_argument)),
                    response=result.get("defense", result.get("summary", "")),
                    adjusted_score=result.get("adjusted_score"),
                    acknowledged_risks=result.get("acknowledged_risks", []),
                )

        except Exception as e:
            logger.error(f"Error generating defense: {e}")

        return None

    async def _generate_rebuttal(
        self,
        devils_advocate,
        original_challenge: Optional[CounterArgument],
        defense: AgentResponse,
        stock_context: dict[str, Any],
    ) -> Optional[str]:
        """Generate a rebuttal from Devil's Advocate for weak defenses."""
        try:
            context = {
                "original_challenge": original_challenge.counter_argument if original_challenge else "",
                "defense_response": defense.response,
                "acknowledged_risks": defense.acknowledged_risks,
                "stock_info": stock_context,
                "mode": "rebuttal",
            }

            if hasattr(devils_advocate, 'rebut_defense'):
                result = await devils_advocate.rebut_defense(context)
                return result.get("rebuttal", "")

        except Exception as e:
            logger.error(f"Error generating rebuttal: {e}")

        return None

    async def _update_opinions_after_round(
        self,
        current_opinions: dict[str, AgentOpinion],
        debate_round: DebateRound,
    ) -> dict[str, AgentOpinion]:
        """Update agent opinions based on debate round results."""
        updated = current_opinions.copy()

        for response in debate_round.responses:
            agent_key = response.agent_type.value
            if agent_key in updated and response.adjusted_score is not None:
                original = updated[agent_key]
                # Create updated opinion with adjusted score
                updated[agent_key] = AgentOpinion(
                    agent_type=original.agent_type,
                    ticker=original.ticker,
                    score=response.adjusted_score,
                    confidence=original.confidence * 0.95,  # Slight confidence reduction after debate
                    sentiment=self._adjust_sentiment(original.sentiment, response.adjusted_score),
                    summary=original.summary,
                    key_points=original.key_points + response.acknowledged_risks,
                    concerns=original.concerns + response.acknowledged_risks,
                    detailed_analysis=original.detailed_analysis,
                )

        return updated

    def _adjust_sentiment(self, original: Sentiment, new_score: float) -> Sentiment:
        """Adjust sentiment based on new score."""
        if new_score >= 8:
            return Sentiment.VERY_BULLISH
        elif new_score >= 6.5:
            return Sentiment.BULLISH
        elif new_score >= 4.5:
            return Sentiment.NEUTRAL
        elif new_score >= 3:
            return Sentiment.BEARISH
        else:
            return Sentiment.VERY_BEARISH

    def _check_consensus(self, opinions: dict[str, AgentOpinion]) -> bool:
        """Check if agents have reached consensus."""
        if len(opinions) < 2:
            return True

        scores = [op.score for op in opinions.values() if op.agent_type != AgentType.DEVILS_ADVOCATE]
        if not scores:
            return True

        # Consensus if score variance is low
        avg_score = sum(scores) / len(scores)
        variance = sum((s - avg_score) ** 2 for s in scores) / len(scores)

        return variance < 1.5  # Low variance indicates consensus

    def _is_strong_defense(self, response: AgentResponse) -> bool:
        """Check if a defense response is strong enough to not require rebuttal."""
        # Consider defense strong if it doesn't acknowledge too many risks
        # and maintains a reasonable score adjustment (not too big a drop)
        if len(response.acknowledged_risks) > 3:
            return False
        if response.adjusted_score and response.adjusted_score < 4:
            return False
        return True

    def _find_challenge(
        self,
        challenges: list[CounterArgument],
        response: AgentResponse,
    ) -> Optional[CounterArgument]:
        """Find the challenge that a response is addressing."""
        for challenge in challenges:
            if challenge.target_agent == response.agent_type:
                return challenge
        return None

    def _identify_resolved_issues(
        self,
        challenges: list[CounterArgument],
        responses: list[AgentResponse],
    ) -> list[str]:
        """Identify issues that were resolved in this round."""
        resolved = []
        for response in responses:
            if response.adjusted_score is None or response.adjusted_score >= 5:
                challenge = self._find_challenge(challenges, response)
                if challenge:
                    resolved.append(f"{challenge.target_agent.value}: {challenge.original_claim[:50]}...")
        return resolved

    def _identify_remaining_concerns(
        self,
        challenges: list[CounterArgument],
        responses: list[AgentResponse],
    ) -> list[str]:
        """Identify concerns that remain unresolved."""
        remaining = []
        for challenge in challenges:
            matching_response = next(
                (r for r in responses if r.agent_type == challenge.target_agent),
                None
            )
            if not matching_response or (
                matching_response.adjusted_score and matching_response.adjusted_score < 5
            ):
                remaining.append(challenge.counter_argument[:100] + "...")
        return remaining

    def _identify_key_disagreements(
        self,
        opinions: dict[str, AgentOpinion],
    ) -> list[str]:
        """Identify key remaining disagreements."""
        disagreements = []

        opinions_list = list(opinions.values())
        for i, op1 in enumerate(opinions_list):
            for op2 in opinions_list[i+1:]:
                if abs(op1.score - op2.score) >= 3:
                    disagreements.append(
                        f"{op1.agent_type.value} ({op1.score}/10) vs "
                        f"{op2.agent_type.value} ({op2.score}/10)"
                    )

        return disagreements

    def get_debate_summary(self) -> dict[str, Any]:
        """Get a summary of the debate for display."""
        if not self.transcript:
            return {}

        return {
            "ticker": self.transcript.ticker,
            "total_rounds": len(self.transcript.rounds),
            "total_messages": len(self.transcript.messages),
            "consensus_reached": self.transcript.consensus_reached,
            "key_disagreements": self.transcript.key_disagreements,
            "resolved_issues": self.transcript.resolved_issues,
            "score_changes": self._calculate_score_changes(),
            "debate_highlights": self._get_debate_highlights(),
        }

    def _calculate_score_changes(self) -> dict[str, dict]:
        """Calculate how scores changed through debate."""
        if not self.transcript:
            return {}

        changes = {}
        for agent_type, initial_op in self.transcript.initial_opinions.items():
            final_op = self.transcript.final_opinions.get(agent_type)
            if final_op:
                changes[agent_type] = {
                    "initial_score": initial_op.score,
                    "final_score": final_op.score,
                    "change": final_op.score - initial_op.score,
                }

        return changes

    def _get_debate_highlights(self) -> list[dict]:
        """Get the most significant moments from the debate."""
        if not self.transcript:
            return []

        highlights = []

        # Find challenges that led to significant score changes
        for msg in self.transcript.messages:
            if msg.message_type == "challenge" and msg.score_adjustment:
                if abs(msg.score_adjustment) >= 1:
                    highlights.append({
                        "type": "significant_challenge",
                        "from": msg.speaker.value,
                        "to": msg.target.value if msg.target else "unknown",
                        "content": msg.content[:200],
                        "impact": msg.score_adjustment,
                    })

        # Find strong defenses
        for msg in self.transcript.messages:
            if msg.message_type == "defense" and len(msg.evidence) >= 3:
                highlights.append({
                    "type": "strong_defense",
                    "from": msg.speaker.value,
                    "content": msg.content[:200],
                })

        return highlights[:10]  # Top 10 highlights
