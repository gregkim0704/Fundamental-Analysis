"""LangGraph state definitions for the multi-agent workflow."""
from datetime import datetime
from typing import Annotated, Any, Optional

from langgraph.graph import add_messages
from pydantic import BaseModel, Field

from models.agent_opinion import (
    AgentOpinion,
    AgentType,
    CommitteeDecision,
    CounterArgument,
    DebateRound,
)
from models.analysis_result import (
    AnalysisResult,
    DevilsAdvocateAnalysis,
    IndustryAnalysis,
    MacroAnalysis,
    QualitativeAnalysis,
    QuantAnalysis,
    RiskAnalysis,
    ValuationAnalysis,
)
from models.stock import Stock
from models.user_research import UserResearchInput


class AnalysisRequest(BaseModel):
    """User's analysis request."""
    ticker: str = Field(..., description="Stock ticker to analyze")
    company_name: Optional[str] = Field(None, description="Company name")
    focus_areas: list[str] = Field(
        default_factory=list,
        description="Specific areas to focus on"
    )
    additional_context: Optional[str] = Field(
        None,
        description="Additional context from user"
    )
    # 사용자 제공 자료
    user_research: Optional[UserResearchInput] = Field(
        None,
        description="User-provided research documents"
    )


class AgentState(BaseModel):
    """State for the multi-agent analysis workflow."""

    # Request information
    request: AnalysisRequest = Field(..., description="Analysis request")

    # Stock data
    stock: Optional[Stock] = Field(None, description="Stock data")

    # Messages for conversation history (using LangGraph's message reducer)
    messages: Annotated[list, add_messages] = Field(
        default_factory=list,
        description="Conversation messages"
    )

    # Phase tracking
    current_phase: str = Field(
        default="initialization",
        description="Current analysis phase"
    )

    # Individual agent analyses (Phase 1)
    macro_analysis: Optional[MacroAnalysis] = Field(None, description="Macro analysis")
    quant_analysis: Optional[QuantAnalysis] = Field(None, description="Quant analysis")
    qualitative_analysis: Optional[QualitativeAnalysis] = Field(
        None, description="Qualitative analysis"
    )
    industry_analysis: Optional[IndustryAnalysis] = Field(None, description="Industry analysis")
    valuation_analysis: Optional[ValuationAnalysis] = Field(None, description="Valuation analysis")
    risk_analysis: Optional[RiskAnalysis] = Field(None, description="Risk analysis")

    # Agent opinions
    agent_opinions: dict[str, AgentOpinion] = Field(
        default_factory=dict,
        description="Collected agent opinions"
    )

    # Debate state (Phase 2)
    current_debate_round: int = Field(default=0, description="Current debate round (1-3)")
    devils_advocate_analysis: Optional[DevilsAdvocateAnalysis] = Field(
        None, description="Devil's advocate analysis"
    )
    counter_arguments: list[CounterArgument] = Field(
        default_factory=list,
        description="Counter arguments raised"
    )
    debate_rounds: list[DebateRound] = Field(
        default_factory=list,
        description="Completed debate rounds"
    )

    # Final decision (Phase 3)
    committee_decision: Optional[CommitteeDecision] = Field(
        None, description="Final committee decision"
    )
    analysis_result: Optional[AnalysisResult] = Field(
        None, description="Complete analysis result"
    )

    # 사용자 자료 검토 결과
    user_research_validation: Optional[dict] = Field(
        None,
        description="User research validation results"
    )
    research_synthesis: Optional[dict] = Field(
        None,
        description="Synthesized research findings"
    )

    # Error handling
    errors: list[str] = Field(default_factory=list, description="Errors encountered")
    warnings: list[str] = Field(default_factory=list, description="Warnings")

    # Metadata
    started_at: datetime = Field(default_factory=datetime.now, description="Start time")
    completed_at: Optional[datetime] = Field(None, description="Completion time")

    class Config:
        arbitrary_types_allowed = True

    def get_analysis_by_agent(self, agent_type: AgentType) -> Optional[Any]:
        """Get analysis result by agent type."""
        mapping = {
            AgentType.MACRO: self.macro_analysis,
            AgentType.QUANT: self.quant_analysis,
            AgentType.QUALITATIVE: self.qualitative_analysis,
            AgentType.INDUSTRY: self.industry_analysis,
            AgentType.VALUATION: self.valuation_analysis,
            AgentType.RISK: self.risk_analysis,
            AgentType.DEVILS_ADVOCATE: self.devils_advocate_analysis,
        }
        return mapping.get(agent_type)

    def all_primary_analyses_complete(self) -> bool:
        """Check if all primary agent analyses are complete."""
        return all([
            self.macro_analysis is not None,
            self.quant_analysis is not None,
            self.qualitative_analysis is not None,
            self.industry_analysis is not None,
        ])

    def all_analyses_complete(self) -> bool:
        """Check if all analyses including valuation and risk are complete."""
        return all([
            self.all_primary_analyses_complete(),
            self.valuation_analysis is not None,
            self.risk_analysis is not None,
        ])


class WorkflowConfig(BaseModel):
    """Configuration for the analysis workflow."""
    max_debate_rounds: int = Field(default=3, description="Maximum debate rounds")
    parallel_analysis: bool = Field(
        default=True,
        description="Run primary analyses in parallel"
    )
    include_devils_advocate: bool = Field(
        default=True,
        description="Include devil's advocate analysis"
    )
    timeout_seconds: int = Field(default=300, description="Timeout per agent")
    model_name: str = Field(
        default="claude-opus-4-5-20251101",
        description="LLM model to use"
    )
    temperature: float = Field(default=0.3, description="LLM temperature")
