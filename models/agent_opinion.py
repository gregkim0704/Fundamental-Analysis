"""Agent opinion and voting models."""
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class Sentiment(str, Enum):
    """Sentiment enumeration."""
    VERY_BULLISH = "very_bullish"
    BULLISH = "bullish"
    NEUTRAL = "neutral"
    BEARISH = "bearish"
    VERY_BEARISH = "very_bearish"


class RiskLevel(str, Enum):
    """Risk level enumeration."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class MoatStrength(str, Enum):
    """Moat strength enumeration."""
    NONE = "none"
    NARROW = "narrow"
    WIDE = "wide"


class AgentType(str, Enum):
    """Agent type enumeration."""
    CHAIRMAN = "chairman"
    MACRO = "macro"
    QUANT = "quant"
    QUALITATIVE = "qualitative"
    INDUSTRY = "industry"
    VALUATION = "valuation"
    RISK = "risk"
    DEVILS_ADVOCATE = "devils_advocate"


class AgentOpinion(BaseModel):
    """Individual agent's opinion on a stock."""
    agent_type: AgentType = Field(..., description="Type of agent providing opinion")
    ticker: str = Field(..., description="Stock ticker analyzed")

    # Score and sentiment
    score: float = Field(..., ge=1, le=10, description="Score from 1-10")
    confidence: float = Field(..., ge=0, le=100, description="Confidence level (%)")
    sentiment: Sentiment = Field(..., description="Overall sentiment")

    # Analysis summary
    summary: str = Field(..., description="Brief summary of analysis")
    key_points: list[str] = Field(default_factory=list, description="Key analysis points")
    concerns: list[str] = Field(default_factory=list, description="Concerns or risks identified")

    # Detailed analysis (agent-specific)
    detailed_analysis: Optional[dict] = Field(None, description="Detailed analysis data")

    # Metadata
    timestamp: datetime = Field(default_factory=datetime.now, description="Analysis timestamp")

    @property
    def is_positive(self) -> bool:
        """Check if sentiment is positive."""
        return self.sentiment in [Sentiment.BULLISH, Sentiment.VERY_BULLISH]

    @property
    def is_negative(self) -> bool:
        """Check if sentiment is negative."""
        return self.sentiment in [Sentiment.BEARISH, Sentiment.VERY_BEARISH]


class AgentVote(BaseModel):
    """Agent's vote in the investment committee."""
    agent_type: AgentType = Field(..., description="Voting agent type")
    score: float = Field(..., ge=1, le=10, description="Score from 1-10")
    confidence: float = Field(..., ge=0, le=100, description="Confidence level (%)")
    sentiment: Sentiment = Field(..., description="Vote sentiment")
    rationale: str = Field(..., description="Brief rationale for vote")

    @property
    def weighted_score(self) -> float:
        """Calculate confidence-weighted score."""
        return self.score * (self.confidence / 100)


class CounterArgument(BaseModel):
    """Counter argument from Devil's Advocate."""
    target_agent: AgentType = Field(..., description="Agent being challenged")
    original_claim: str = Field(..., description="Original claim being challenged")
    counter_argument: str = Field(..., description="Counter argument")
    evidence: list[str] = Field(default_factory=list, description="Supporting evidence")
    severity: RiskLevel = Field(default=RiskLevel.MEDIUM, description="Severity of concern")


class AgentResponse(BaseModel):
    """Agent's response to a counter argument."""
    agent_type: AgentType = Field(..., description="Responding agent type")
    counter_argument_id: str = Field(..., description="ID of counter argument being addressed")
    response: str = Field(..., description="Response to counter argument")
    adjusted_score: Optional[float] = Field(None, ge=1, le=10, description="Adjusted score if any")
    acknowledged_risks: list[str] = Field(default_factory=list, description="Acknowledged risks")


class DebateRound(BaseModel):
    """A single round of debate in the investment committee."""
    round_number: int = Field(..., ge=1, le=3, description="Debate round number")
    counter_arguments: list[CounterArgument] = Field(
        default_factory=list,
        description="Counter arguments raised"
    )
    responses: list[AgentResponse] = Field(
        default_factory=list,
        description="Responses to counter arguments"
    )
    resolved_issues: list[str] = Field(
        default_factory=list,
        description="Issues resolved in this round"
    )
    remaining_concerns: list[str] = Field(
        default_factory=list,
        description="Concerns remaining after this round"
    )


class CommitteeDecision(BaseModel):
    """Final investment committee decision."""
    ticker: str = Field(..., description="Stock ticker")
    company_name: str = Field(..., description="Company name")

    # Voting results
    votes: list[AgentVote] = Field(..., description="Individual agent votes")
    weighted_average_score: float = Field(..., description="Weighted average score")
    consensus_level: float = Field(..., ge=0, le=100, description="Consensus level (%)")

    # Final recommendation
    final_sentiment: Sentiment = Field(..., description="Final committee sentiment")
    recommendation: str = Field(..., description="Investment recommendation")
    target_price_low: Optional[float] = Field(None, description="Target price (low)")
    target_price_mid: Optional[float] = Field(None, description="Target price (mid/base)")
    target_price_high: Optional[float] = Field(None, description="Target price (high)")

    # Risk assessment
    risk_level: RiskLevel = Field(..., description="Overall risk level")
    key_risks: list[str] = Field(default_factory=list, description="Key risks to monitor")

    # Action items
    action_items: list[str] = Field(default_factory=list, description="Recommended actions")
    monitoring_points: list[str] = Field(
        default_factory=list,
        description="Points to monitor going forward"
    )

    # Debate summary
    debate_rounds: list[DebateRound] = Field(default_factory=list, description="Debate history")
    dissenting_opinions: list[str] = Field(
        default_factory=list,
        description="Minority/dissenting opinions"
    )

    # Metadata
    analysis_date: datetime = Field(default_factory=datetime.now, description="Analysis date")

    @property
    def has_consensus(self) -> bool:
        """Check if committee reached consensus (>70% agreement)."""
        return self.consensus_level >= 70

    @property
    def is_buy_recommendation(self) -> bool:
        """Check if recommendation is to buy."""
        return self.final_sentiment in [Sentiment.BULLISH, Sentiment.VERY_BULLISH]

    @property
    def is_sell_recommendation(self) -> bool:
        """Check if recommendation is to sell."""
        return self.final_sentiment in [Sentiment.BEARISH, Sentiment.VERY_BEARISH]

    def get_upside_potential(self, current_price: float) -> Optional[float]:
        """Calculate upside potential from current price to mid target."""
        if self.target_price_mid and current_price > 0:
            return ((self.target_price_mid - current_price) / current_price) * 100
        return None
