"""Analysis result models for each agent type."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from models.agent_opinion import MoatStrength, RiskLevel, Sentiment


class MacroAnalysis(BaseModel):
    """Macro environment analysis result."""
    # Overall assessment
    score: float = Field(..., ge=1, le=10, description="Macro environment score")
    sentiment: Sentiment = Field(..., description="Macro sentiment")
    summary: str = Field(..., description="Summary of macro analysis")

    # Interest rate cycle
    interest_rate_phase: str = Field(..., description="Current interest rate cycle phase")
    central_bank_stance: str = Field(..., description="Central bank monetary policy stance")
    yield_curve_status: str = Field(..., description="Yield curve status (normal/inverted/flat)")

    # Liquidity environment
    liquidity_assessment: str = Field(..., description="Market liquidity assessment")
    credit_spread_status: str = Field(..., description="Credit spread status")
    m2_growth_trend: Optional[str] = Field(None, description="M2 money supply trend")

    # Sector impact
    sector_rotation_phase: str = Field(..., description="Current sector rotation phase")
    favorable_sectors: list[str] = Field(default_factory=list, description="Favorable sectors")
    unfavorable_sectors: list[str] = Field(default_factory=list, description="Unfavorable sectors")

    # Policy & geopolitical
    key_policy_impacts: list[str] = Field(default_factory=list, description="Key policy impacts")
    geopolitical_risks: list[str] = Field(default_factory=list, description="Geopolitical risks")

    # Impact on target stock
    stock_specific_impact: str = Field(..., description="How macro affects target stock")
    tailwinds: list[str] = Field(default_factory=list, description="Macro tailwinds")
    headwinds: list[str] = Field(default_factory=list, description="Macro headwinds")


class QuantAnalysis(BaseModel):
    """Quantitative financial analysis result."""
    # Overall assessment
    score: float = Field(..., ge=1, le=10, description="Financial health score")
    sentiment: Sentiment = Field(..., description="Financial sentiment")
    summary: str = Field(..., description="Summary of financial analysis")

    # Value creation metrics
    roic: Optional[float] = Field(None, description="Return on Invested Capital (%)")
    wacc: Optional[float] = Field(None, description="Weighted Average Cost of Capital (%)")
    roic_wacc_spread: Optional[float] = Field(None, description="ROIC - WACC spread")
    eva: Optional[float] = Field(None, description="Economic Value Added")
    value_creation_assessment: str = Field(..., description="Value creation assessment")

    # Cash flow quality
    ocf_to_operating_income: Optional[float] = Field(
        None, description="Operating CF / Operating Income ratio"
    )
    fcf_trend: str = Field(..., description="FCF trend assessment")
    fcf_margin: Optional[float] = Field(None, description="FCF margin (%)")
    cash_conversion_assessment: str = Field(..., description="Cash conversion quality")

    # Earnings quality
    accrual_ratio: Optional[float] = Field(None, description="Accrual ratio")
    earnings_quality_score: float = Field(..., ge=1, le=10, description="Earnings quality score")
    earnings_manipulation_risk: RiskLevel = Field(..., description="Earnings manipulation risk")
    quality_flags: list[str] = Field(default_factory=list, description="Quality warning flags")

    # Capital allocation
    capex_to_depreciation: Optional[float] = Field(
        None, description="CAPEX / Depreciation ratio"
    )
    reinvestment_rate: Optional[float] = Field(None, description="Reinvestment rate")
    capital_allocation_assessment: str = Field(..., description="Capital allocation assessment")

    # Working capital
    days_sales_outstanding: Optional[float] = Field(None, description="DSO")
    days_inventory_outstanding: Optional[float] = Field(None, description="DIO")
    days_payable_outstanding: Optional[float] = Field(None, description="DPO")
    cash_conversion_cycle: Optional[float] = Field(None, description="Cash conversion cycle")
    working_capital_trend: str = Field(..., description="Working capital trend")

    # Leverage & liquidity
    debt_to_equity: Optional[float] = Field(None, description="D/E ratio")
    interest_coverage: Optional[float] = Field(None, description="Interest coverage ratio")
    current_ratio: Optional[float] = Field(None, description="Current ratio")
    leverage_assessment: str = Field(..., description="Leverage assessment")

    # Key metrics table (for display)
    key_metrics: dict = Field(default_factory=dict, description="Key financial metrics")


class QualitativeAnalysis(BaseModel):
    """Qualitative analysis result."""
    # Overall assessment
    score: float = Field(..., ge=1, le=10, description="Qualitative score")
    sentiment: Sentiment = Field(..., description="Qualitative sentiment")
    summary: str = Field(..., description="Summary of qualitative analysis")

    # Moat analysis
    moat_strength: MoatStrength = Field(..., description="Competitive moat strength")
    moat_sources: list[str] = Field(default_factory=list, description="Sources of moat")
    moat_durability: str = Field(..., description="Assessment of moat durability")

    # Cost advantage
    has_cost_advantage: bool = Field(False, description="Has cost advantage")
    cost_advantage_details: Optional[str] = Field(None, description="Cost advantage details")

    # Switching costs
    has_switching_costs: bool = Field(False, description="Has switching costs")
    switching_cost_details: Optional[str] = Field(None, description="Switching cost details")

    # Network effects
    has_network_effects: bool = Field(False, description="Has network effects")
    network_effect_details: Optional[str] = Field(None, description="Network effect details")

    # Intangible assets
    has_intangible_assets: bool = Field(False, description="Has valuable intangible assets")
    intangible_asset_details: Optional[str] = Field(None, description="Intangible asset details")

    # Management quality
    management_score: float = Field(..., ge=1, le=10, description="Management quality score")
    management_track_record: str = Field(..., description="Management track record assessment")
    capital_allocation_history: str = Field(..., description="Capital allocation history")
    insider_activity: str = Field(..., description="Recent insider activity")
    compensation_alignment: str = Field(..., description="Exec compensation alignment")

    # Corporate governance
    governance_score: float = Field(..., ge=1, le=10, description="Governance score")
    governance_concerns: list[str] = Field(default_factory=list, description="Governance concerns")

    # Porter's Five Forces (1-5 scale, 5 = most favorable for company)
    threat_new_entrants: int = Field(..., ge=1, le=5, description="Threat of new entrants (5=low)")
    threat_substitutes: int = Field(..., ge=1, le=5, description="Threat of substitutes (5=low)")
    supplier_power: int = Field(..., ge=1, le=5, description="Supplier bargaining power (5=low)")
    buyer_power: int = Field(..., ge=1, le=5, description="Buyer bargaining power (5=low)")
    competitive_rivalry: int = Field(..., ge=1, le=5, description="Competitive rivalry (5=low)")

    # ESG considerations
    esg_assessment: Optional[str] = Field(None, description="ESG assessment")
    esg_risks: list[str] = Field(default_factory=list, description="ESG risks")


class IndustryAnalysis(BaseModel):
    """Industry analysis result."""
    # Overall assessment
    score: float = Field(..., ge=1, le=10, description="Industry attractiveness score")
    sentiment: Sentiment = Field(..., description="Industry sentiment")
    summary: str = Field(..., description="Summary of industry analysis")

    # Industry basics
    industry_name: str = Field(..., description="Industry name")
    industry_lifecycle: str = Field(
        ..., description="Lifecycle stage (introduction/growth/mature/decline)"
    )

    # Market size and growth
    global_market_size: Optional[str] = Field(None, description="Global market size")
    market_growth_rate: Optional[str] = Field(None, description="Market growth rate (CAGR)")
    regional_breakdown: dict = Field(default_factory=dict, description="Regional market breakdown")

    # Competitive landscape
    market_structure: str = Field(
        ..., description="Market structure (monopoly/oligopoly/fragmented)"
    )
    top_players: list[str] = Field(default_factory=list, description="Top industry players")
    market_share_concentration: str = Field(..., description="Market share concentration")
    consolidation_trend: str = Field(..., description="Industry consolidation trend")

    # Value chain
    value_chain_position: str = Field(..., description="Company's value chain position")
    upstream_risks: list[str] = Field(default_factory=list, description="Upstream supply risks")
    downstream_risks: list[str] = Field(default_factory=list, description="Downstream demand risks")
    margin_structure: str = Field(..., description="Industry margin structure by segment")

    # Demand drivers
    key_demand_drivers: list[str] = Field(default_factory=list, description="Key demand drivers")
    substitute_threats: list[str] = Field(default_factory=list, description="Substitute threats")
    technology_disruption_risk: str = Field(..., description="Technology disruption risk")

    # Regulatory environment
    regulatory_environment: str = Field(..., description="Regulatory environment assessment")
    key_regulations: list[str] = Field(default_factory=list, description="Key regulations")

    # Company positioning
    company_market_share: Optional[str] = Field(None, description="Company's market share")
    competitive_position: str = Field(..., description="Company's competitive position")
    competitive_advantages: list[str] = Field(
        default_factory=list, description="Competitive advantages vs peers"
    )
    competitive_disadvantages: list[str] = Field(
        default_factory=list, description="Competitive disadvantages vs peers"
    )


class ValuationScenario(BaseModel):
    """Valuation scenario (bear/base/bull)."""
    name: str = Field(..., description="Scenario name")
    probability: float = Field(..., ge=0, le=100, description="Probability (%)")
    target_price: float = Field(..., description="Target price")
    upside_downside: float = Field(..., description="Upside/downside from current (%)")
    key_assumptions: list[str] = Field(default_factory=list, description="Key assumptions")


class ValuationAnalysis(BaseModel):
    """Valuation analysis result."""
    # Overall assessment
    score: float = Field(..., ge=1, le=10, description="Valuation attractiveness score")
    sentiment: Sentiment = Field(..., description="Valuation sentiment")
    summary: str = Field(..., description="Summary of valuation analysis")

    # Current valuation
    current_price: float = Field(..., description="Current stock price")
    currency: str = Field(default="USD", description="Currency")

    # DCF valuation
    dcf_value: Optional[float] = Field(None, description="DCF intrinsic value")
    dcf_assumptions: dict = Field(default_factory=dict, description="DCF key assumptions")

    # Relative valuation
    peer_pe_average: Optional[float] = Field(None, description="Peer average P/E")
    peer_pb_average: Optional[float] = Field(None, description="Peer average P/B")
    peer_ev_ebitda_average: Optional[float] = Field(None, description="Peer average EV/EBITDA")

    # Historical valuation bands
    historical_pe_range: Optional[tuple[float, float]] = Field(
        None, description="5-year P/E range (min, max)"
    )
    historical_pb_range: Optional[tuple[float, float]] = Field(
        None, description="5-year P/B range (min, max)"
    )
    current_vs_historical: str = Field(..., description="Current vs historical valuation")

    # Scenario analysis
    bear_case: ValuationScenario = Field(..., description="Bear case scenario")
    base_case: ValuationScenario = Field(..., description="Base case scenario")
    bull_case: ValuationScenario = Field(..., description="Bull case scenario")

    # Target price
    target_price_low: float = Field(..., description="Target price (low)")
    target_price_mid: float = Field(..., description="Target price (mid)")
    target_price_high: float = Field(..., description="Target price (high)")
    expected_return: float = Field(..., description="Expected return to mid target (%)")

    # Valuation methodology weights
    methodology_weights: dict = Field(
        default_factory=dict, description="Weights assigned to each methodology"
    )

    # Margin of safety
    margin_of_safety: Optional[float] = Field(
        None, description="Margin of safety vs intrinsic value (%)"
    )


class RiskFactor(BaseModel):
    """Individual risk factor."""
    category: str = Field(..., description="Risk category")
    description: str = Field(..., description="Risk description")
    severity: RiskLevel = Field(..., description="Risk severity")
    probability: str = Field(..., description="Probability assessment")
    potential_impact: str = Field(..., description="Potential impact description")
    mitigants: list[str] = Field(default_factory=list, description="Risk mitigants")


class RiskAnalysis(BaseModel):
    """Risk analysis result."""
    # Overall assessment
    score: float = Field(..., ge=1, le=10, description="Risk-adjusted score (10=lowest risk)")
    overall_risk_level: RiskLevel = Field(..., description="Overall risk level")
    sentiment: Sentiment = Field(..., description="Risk sentiment")
    summary: str = Field(..., description="Summary of risk analysis")

    # Business risks
    business_risks: list[RiskFactor] = Field(default_factory=list, description="Business risks")
    business_risk_level: RiskLevel = Field(..., description="Business risk level")

    # Financial risks
    financial_risks: list[RiskFactor] = Field(default_factory=list, description="Financial risks")
    financial_risk_level: RiskLevel = Field(..., description="Financial risk level")

    # Regulatory risks
    regulatory_risks: list[RiskFactor] = Field(default_factory=list, description="Regulatory risks")
    regulatory_risk_level: RiskLevel = Field(..., description="Regulatory risk level")

    # Market risks
    market_risks: list[RiskFactor] = Field(default_factory=list, description="Market risks")
    market_risk_level: RiskLevel = Field(..., description="Market risk level")

    # ESG risks
    esg_risks: list[RiskFactor] = Field(default_factory=list, description="ESG risks")
    esg_risk_level: RiskLevel = Field(..., description="ESG risk level")

    # Quantitative risk metrics
    var_95: Optional[float] = Field(None, description="Value at Risk (95%)")
    max_drawdown: Optional[float] = Field(None, description="Historical max drawdown (%)")
    volatility: Optional[float] = Field(None, description="Annualized volatility (%)")
    sharpe_ratio: Optional[float] = Field(None, description="Sharpe ratio")

    # Key risk summary
    top_risks: list[str] = Field(default_factory=list, description="Top 3-5 key risks")
    risk_triggers: list[str] = Field(default_factory=list, description="Risk triggers to watch")


class DevilsAdvocateAnalysis(BaseModel):
    """Devil's Advocate analysis result."""
    # Overall assessment
    score: float = Field(..., ge=1, le=10, description="Contrarian risk score (10=most concerns)")
    sentiment: Sentiment = Field(..., description="Contrarian sentiment")
    summary: str = Field(..., description="Summary of contrarian analysis")

    # Core challenge questions
    why_this_price: str = Field(
        ..., description="Analysis of why the stock is at current price"
    )
    what_market_knows: str = Field(
        ..., description="What information is already priced in"
    )
    potential_blind_spots: list[str] = Field(
        default_factory=list, description="Potential blind spots in bull case"
    )

    # Counter arguments by agent
    macro_counter_arguments: list[str] = Field(
        default_factory=list, description="Counter arguments to macro analysis"
    )
    quant_counter_arguments: list[str] = Field(
        default_factory=list, description="Counter arguments to financial analysis"
    )
    qualitative_counter_arguments: list[str] = Field(
        default_factory=list, description="Counter arguments to qualitative analysis"
    )
    industry_counter_arguments: list[str] = Field(
        default_factory=list, description="Counter arguments to industry analysis"
    )
    valuation_counter_arguments: list[str] = Field(
        default_factory=list, description="Counter arguments to valuation"
    )

    # Pre-mortem analysis
    pre_mortem_scenarios: list[str] = Field(
        default_factory=list, description="Scenarios where investment fails"
    )
    historical_precedents: list[str] = Field(
        default_factory=list, description="Historical cases of similar failures"
    )

    # Warning signals
    red_flags: list[str] = Field(default_factory=list, description="Red flags identified")
    warning_signals: list[str] = Field(
        default_factory=list, description="Early warning signals to monitor"
    )

    # Short interest & market sentiment
    short_interest_analysis: Optional[str] = Field(
        None, description="Short interest analysis"
    )
    market_sentiment_analysis: Optional[str] = Field(
        None, description="Market sentiment analysis"
    )


class AnalysisResult(BaseModel):
    """Complete analysis result combining all agent analyses."""
    # Stock information
    ticker: str = Field(..., description="Stock ticker")
    company_name: str = Field(..., description="Company name")
    current_price: float = Field(..., description="Current stock price")
    currency: str = Field(default="USD", description="Currency")

    # Individual analyses
    macro_analysis: Optional[MacroAnalysis] = Field(None, description="Macro analysis")
    quant_analysis: Optional[QuantAnalysis] = Field(None, description="Quant analysis")
    qualitative_analysis: Optional[QualitativeAnalysis] = Field(
        None, description="Qualitative analysis"
    )
    industry_analysis: Optional[IndustryAnalysis] = Field(None, description="Industry analysis")
    valuation_analysis: Optional[ValuationAnalysis] = Field(None, description="Valuation analysis")
    risk_analysis: Optional[RiskAnalysis] = Field(None, description="Risk analysis")
    devils_advocate_analysis: Optional[DevilsAdvocateAnalysis] = Field(
        None, description="Devil's advocate analysis"
    )

    # Metadata
    analysis_date: datetime = Field(default_factory=datetime.now, description="Analysis date")
    analysis_version: str = Field(default="1.0", description="Analysis version")

    @property
    def average_score(self) -> float:
        """Calculate simple average of all agent scores."""
        scores = []
        if self.macro_analysis:
            scores.append(self.macro_analysis.score)
        if self.quant_analysis:
            scores.append(self.quant_analysis.score)
        if self.qualitative_analysis:
            scores.append(self.qualitative_analysis.score)
        if self.industry_analysis:
            scores.append(self.industry_analysis.score)
        if self.valuation_analysis:
            scores.append(self.valuation_analysis.score)
        if self.risk_analysis:
            scores.append(self.risk_analysis.score)
        return sum(scores) / len(scores) if scores else 0


class FinalDecision(BaseModel):
    """Final investment decision combining all analyses."""
    # Analysis result
    analysis_result: AnalysisResult = Field(..., description="Complete analysis result")

    # Committee decision
    committee_decision: "CommitteeDecision" = Field(..., description="Committee decision")

    # Executive summary
    executive_summary: str = Field(..., description="Executive summary")
    investment_thesis: str = Field(..., description="Investment thesis")

    # Recommendation
    recommendation: str = Field(..., description="Final recommendation")
    conviction_level: str = Field(..., description="Conviction level (low/medium/high)")

    # Action plan
    entry_strategy: str = Field(..., description="Suggested entry strategy")
    position_sizing: str = Field(..., description="Position sizing recommendation")
    exit_criteria: list[str] = Field(default_factory=list, description="Exit criteria")
    stop_loss_level: Optional[float] = Field(None, description="Suggested stop loss level")

    # Monitoring
    key_metrics_to_monitor: list[str] = Field(
        default_factory=list, description="Key metrics to monitor"
    )
    catalyst_calendar: list[str] = Field(
        default_factory=list, description="Upcoming catalysts/events"
    )

    # Report generation timestamp
    generated_at: datetime = Field(default_factory=datetime.now, description="Report generation time")


# Import at the end to avoid circular import
from models.agent_opinion import CommitteeDecision  # noqa: E402

FinalDecision.model_rebuild()
