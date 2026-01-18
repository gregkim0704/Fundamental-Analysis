"""Main LangGraph workflow for multi-agent analysis."""
import asyncio
import logging
from datetime import datetime
from typing import Any, Literal

from langgraph.graph import StateGraph, END

from agents.chairman import ChairmanAgent
from agents.macro_agent import MacroAgent
from agents.quant_agent import QuantAgent
from agents.valuation_agent import ValuationAgent
from agents.devils_advocate import DevilsAdvocateAgent
from agents.data_validator_agent import DataValidatorAgent
from graph.state import AgentState, AnalysisRequest, WorkflowConfig
from models.agent_opinion import DebateRound, CounterArgument, AgentResponse, AgentType, RiskLevel
from tools.stock_price import get_stock_info

logger = logging.getLogger(__name__)


class AnalysisWorkflow:
    """Multi-agent analysis workflow using LangGraph."""

    def __init__(self, config: WorkflowConfig = None):
        """Initialize the workflow.

        Args:
            config: Workflow configuration
        """
        self.config = config or WorkflowConfig()
        self._graph = None

        # Initialize agents
        self.chairman = ChairmanAgent()
        self.macro_agent = MacroAgent()
        self.quant_agent = QuantAgent()
        self.valuation_agent = ValuationAgent()
        self.devils_advocate = DevilsAdvocateAgent()
        self.data_validator = DataValidatorAgent()

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow."""
        # Create state graph
        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("validate_user_research", self._validate_user_research)
        workflow.add_node("fetch_stock_data", self._fetch_stock_data)
        workflow.add_node("parallel_analysis", self._parallel_analysis)
        workflow.add_node("valuation_analysis", self._valuation_analysis)
        workflow.add_node("devils_advocate", self._devils_advocate_analysis)
        workflow.add_node("debate_round", self._debate_round)
        workflow.add_node("final_decision", self._final_decision)

        # Set entry point - 자료 검토부터 시작
        workflow.set_entry_point("validate_user_research")

        # Add edges
        workflow.add_edge("validate_user_research", "fetch_stock_data")
        workflow.add_edge("fetch_stock_data", "parallel_analysis")
        workflow.add_edge("parallel_analysis", "valuation_analysis")
        workflow.add_edge("valuation_analysis", "devils_advocate")

        # Conditional edge for debate rounds
        workflow.add_conditional_edges(
            "devils_advocate",
            self._should_continue_debate,
            {
                "continue": "debate_round",
                "finish": "final_decision",
            }
        )
        workflow.add_conditional_edges(
            "debate_round",
            self._should_continue_debate,
            {
                "continue": "debate_round",
                "finish": "final_decision",
            }
        )

        workflow.add_edge("final_decision", END)

        return workflow

    @property
    def graph(self) -> StateGraph:
        """Get or build the workflow graph."""
        if self._graph is None:
            self._graph = self._build_graph()
        return self._graph

    async def _validate_user_research(self, state: AgentState) -> dict[str, Any]:
        """사용자 제공 자료 검토 및 편향 분석.

        이 단계에서:
        1. 각 자료의 신뢰성 평가
        2. 편향 탐지
        3. 자료 간 교차 검증
        4. 종합 분석 생성
        """
        user_research = state.request.user_research

        if not user_research or not user_research.documents:
            logger.info("사용자 제공 자료 없음 - 검토 단계 건너뜀")
            return {
                "current_phase": "data_collection",
                "user_research_validation": None,
                "research_synthesis": None,
            }

        logger.info(f"=== 사용자 자료 검토 시작 ({len(user_research.documents)}개 자료) ===")

        try:
            # DataValidatorAgent를 통한 자료 검토
            validation_result = await self.data_validator.analyze({
                "user_research": user_research,
                "stock_info": {},  # 아직 주식 데이터 없음
            })

            # 검토 결과 로깅
            overall_reliability = validation_result.get("overall_reliability", {})
            logger.info(f"전체 자료 신뢰도: {overall_reliability.get('score', 'N/A')}/10")
            logger.info(f"신뢰도 수준: {overall_reliability.get('level', 'unknown')}")

            # 편향 발견 시 경고
            bias_results = validation_result.get("bias_results", [])
            high_bias_docs = [
                r for r in bias_results
                if r.get("bias_severity") == "high"
            ]
            if high_bias_docs:
                logger.warning(f"높은 편향 발견: {len(high_bias_docs)}개 자료")
                for doc in high_bias_docs:
                    logger.warning(f"  - {doc.get('document_title')}: {doc.get('bias_explanation', '')[:100]}")

            # 종합 분석 로깅
            synthesis = validation_result.get("synthesis", {})
            if synthesis:
                logger.info("=== 자료 종합 분석 ===")
                for point in synthesis.get("consensus_points", [])[:3]:
                    logger.info(f"  [합의] {point}")
                for point in synthesis.get("divergent_points", [])[:3]:
                    logger.info(f"  [의견차] {point}")
                for gap in synthesis.get("information_gaps", [])[:3]:
                    logger.info(f"  [정보격차] {gap}")

            logger.info("=== 사용자 자료 검토 완료 ===")

            return {
                "current_phase": "data_collection",
                "user_research_validation": validation_result,
                "research_synthesis": synthesis,
            }

        except Exception as e:
            logger.error(f"자료 검토 중 오류: {e}")
            return {
                "current_phase": "data_collection",
                "warnings": state.warnings + [f"자료 검토 실패: {e}"],
                "user_research_validation": None,
            }

    async def _fetch_stock_data(self, state: AgentState) -> dict[str, Any]:
        """Fetch stock data node."""
        logger.info(f"Fetching stock data for {state.request.ticker}")

        try:
            stock_data = get_stock_info.invoke({"ticker": state.request.ticker})

            if "error" in stock_data:
                return {
                    "errors": state.errors + [f"Failed to fetch stock data: {stock_data['error']}"],
                    "current_phase": "error",
                }

            return {
                "stock": stock_data,
                "current_phase": "primary_analysis",
            }
        except Exception as e:
            logger.error(f"Error fetching stock data: {e}")
            return {
                "errors": state.errors + [str(e)],
                "current_phase": "error",
            }

    async def _parallel_analysis(self, state: AgentState) -> dict[str, Any]:
        """Run primary analyses in parallel."""
        logger.info("Running parallel primary analyses")

        context = {
            "ticker": state.request.ticker,
            "stock_info": state.stock,
        }

        # Run analyses in parallel
        results = await asyncio.gather(
            self.macro_agent.analyze(context),
            self.quant_agent.analyze(context),
            return_exceptions=True,
        )

        macro_result, quant_result = results

        # Collect opinions
        agent_opinions = {}
        updates = {"current_phase": "secondary_analysis"}

        if isinstance(macro_result, dict) and "opinion" in macro_result:
            updates["macro_analysis"] = macro_result.get("analysis")
            agent_opinions["macro"] = macro_result.get("opinion")

        if isinstance(quant_result, dict) and "opinion" in quant_result:
            updates["quant_analysis"] = quant_result.get("analysis")
            agent_opinions["quant"] = quant_result.get("opinion")

        updates["agent_opinions"] = {**state.agent_opinions, **agent_opinions}

        return updates

    async def _valuation_analysis(self, state: AgentState) -> dict[str, Any]:
        """Run valuation analysis."""
        logger.info("Running valuation analysis")

        context = {
            "ticker": state.request.ticker,
            "stock_info": state.stock,
            "current_price": state.stock.get("current_price") if state.stock else None,
            "quant_analysis": state.quant_analysis,
        }

        try:
            result = await self.valuation_agent.analyze(context)

            updates = {"current_phase": "devils_advocate"}

            if "opinion" in result:
                updates["valuation_analysis"] = result.get("analysis")
                updates["agent_opinions"] = {
                    **state.agent_opinions,
                    "valuation": result.get("opinion"),
                }

            return updates

        except Exception as e:
            logger.error(f"Error in valuation analysis: {e}")
            return {
                "warnings": state.warnings + [f"Valuation analysis failed: {e}"],
                "current_phase": "devils_advocate",
            }

    async def _devils_advocate_analysis(self, state: AgentState) -> dict[str, Any]:
        """Run devil's advocate analysis."""
        logger.info("Running devil's advocate analysis")

        context = {
            "ticker": state.request.ticker,
            "current_price": state.stock.get("current_price") if state.stock else None,
            "macro_analysis": state.agent_opinions.get("macro"),
            "quant_analysis": state.agent_opinions.get("quant"),
            "qualitative_analysis": state.agent_opinions.get("qualitative"),
            "industry_analysis": state.agent_opinions.get("industry"),
            "valuation_analysis": state.agent_opinions.get("valuation"),
        }

        try:
            result = await self.devils_advocate.analyze(context)

            updates = {
                "current_phase": "debate",
                "current_debate_round": 1,
            }

            if "opinion" in result:
                updates["devils_advocate_analysis"] = result.get("analysis")
                updates["agent_opinions"] = {
                    **state.agent_opinions,
                    "devils_advocate": result.get("opinion"),
                }

            return updates

        except Exception as e:
            logger.error(f"Error in devil's advocate analysis: {e}")
            return {
                "warnings": state.warnings + [f"Devil's advocate analysis failed: {e}"],
                "current_phase": "final_decision",
            }

    def _should_continue_debate(self, state: AgentState) -> Literal["continue", "finish"]:
        """Determine if debate should continue."""
        if state.current_debate_round >= self.config.max_debate_rounds:
            return "finish"
        if not self.config.include_devils_advocate:
            return "finish"
        # Continue if there are unresolved concerns
        if state.debate_rounds and len(state.debate_rounds) > 0:
            last_round = state.debate_rounds[-1]
            if hasattr(last_round, 'remaining_concerns') and len(last_round.remaining_concerns) > 0:
                return "continue"
        return "continue" if state.current_debate_round < self.config.max_debate_rounds else "finish"

    async def _debate_round(self, state: AgentState) -> dict[str, Any]:
        """Execute a debate round with actual agent interactions.

        토론 프로세스:
        1. Devil's Advocate가 각 에이전트에게 도전 (사용자 자료 참조)
        2. 각 에이전트가 자신의 입장을 방어 (자료 인용 가능)
        3. Devil's Advocate가 방어를 평가하고 재반박
        4. 점수 조정 및 다음 라운드 준비
        """
        round_num = state.current_debate_round
        logger.info(f"=== 토론 라운드 {round_num} 시작 ===")

        stock_context = state.stock or {}
        counter_arguments = []
        responses = []
        debate_messages = []

        # 사용자 자료 컨텍스트 준비
        user_research_context = self._prepare_research_context(state)
        if user_research_context:
            logger.info(f"[자료 참조] {user_research_context.get('total_documents', 0)}개 자료, 신뢰도: {user_research_context.get('avg_reliability', 'N/A')}")

        # Phase 1: Devil's Advocate challenges each agent
        agents_to_challenge = ["macro", "quant", "valuation"]

        for agent_key in agents_to_challenge:
            opinion = state.agent_opinions.get(agent_key)
            if not opinion:
                continue

            logger.info(f"[Round {round_num}] Devil's Advocate → {agent_key} 도전 중...")

            # Generate challenge - 사용자 자료 포함
            challenge_context = {
                "target_agent": agent_key,
                "target_score": opinion.get("score", 5) if isinstance(opinion, dict) else getattr(opinion, 'score', 5),
                "target_sentiment": opinion.get("sentiment", "neutral") if isinstance(opinion, dict) else getattr(opinion, 'sentiment', 'neutral'),
                "target_summary": opinion.get("summary", "") if isinstance(opinion, dict) else getattr(opinion, 'summary', ''),
                "target_key_points": opinion.get("key_points", []) if isinstance(opinion, dict) else getattr(opinion, 'key_points', []),
                "round_number": round_num,
                "stock_info": stock_context,
                # 사용자 자료 추가
                "user_research": user_research_context,
                "research_synthesis": state.research_synthesis,
            }

            try:
                challenge_result = await self.devils_advocate.challenge(challenge_context)

                counter_arg = CounterArgument(
                    target_agent=AgentType(agent_key),
                    original_claim=challenge_context["target_summary"],
                    counter_argument=challenge_result.get("counter_argument", ""),
                    evidence=challenge_result.get("evidence", []),
                    severity=RiskLevel(challenge_result.get("severity", "medium")),
                )
                counter_arguments.append(counter_arg)

                # Log the challenge
                debate_messages.append({
                    "speaker": "devils_advocate",
                    "target": agent_key,
                    "type": "challenge",
                    "content": challenge_result.get("counter_argument", ""),
                    "severity": challenge_result.get("severity", "medium"),
                    "round": round_num,
                })

                logger.info(f"[도전] {agent_key}에게: {challenge_result.get('counter_argument', '')[:100]}...")

            except Exception as e:
                logger.error(f"Error challenging {agent_key}: {e}")
                continue

        # Phase 2: Each agent defends
        for counter_arg in counter_arguments:
            agent_key = counter_arg.target_agent.value
            agent = self._get_agent_by_key(agent_key)
            opinion = state.agent_opinions.get(agent_key)

            if not agent or not opinion:
                continue

            logger.info(f"[Round {round_num}] {agent_key} 방어 중...")

            defense_context = {
                "original_opinion": opinion if isinstance(opinion, dict) else opinion.model_dump() if hasattr(opinion, 'model_dump') else {},
                "challenge": counter_arg.counter_argument,
                "challenge_evidence": counter_arg.evidence,
                "severity": counter_arg.severity.value,
                "stock_info": stock_context,
                # 방어 시에도 사용자 자료 참조 가능
                "user_research": user_research_context,
                "research_synthesis": state.research_synthesis,
            }

            try:
                defense_result = await agent.rebut(defense_context)

                response = AgentResponse(
                    agent_type=counter_arg.target_agent,
                    counter_argument_id=str(id(counter_arg)),
                    response=defense_result.get("defense", ""),
                    adjusted_score=defense_result.get("adjusted_score"),
                    acknowledged_risks=defense_result.get("acknowledged_risks", []),
                )
                responses.append(response)

                # Log the defense
                debate_messages.append({
                    "speaker": agent_key,
                    "target": "devils_advocate",
                    "type": "defense",
                    "content": defense_result.get("defense", ""),
                    "adjusted_score": defense_result.get("adjusted_score"),
                    "stance": defense_result.get("stance", "maintain"),
                    "round": round_num,
                })

                logger.info(f"[방어] {agent_key}: {defense_result.get('defense', '')[:100]}...")
                if defense_result.get("adjusted_score"):
                    logger.info(f"  → 점수 조정: {defense_result.get('adjusted_score')}")

            except Exception as e:
                logger.error(f"Error in {agent_key} defense: {e}")
                continue

        # Phase 3: Devil's Advocate rebuts weak defenses
        for response in responses:
            if response.adjusted_score and response.adjusted_score < 5:
                # Weak defense, need rebuttal
                counter_arg = next(
                    (ca for ca in counter_arguments if ca.target_agent == response.agent_type),
                    None
                )

                if counter_arg:
                    logger.info(f"[Round {round_num}] Devil's Advocate → {response.agent_type.value} 재반박...")

                    rebuttal_context = {
                        "original_challenge": counter_arg.counter_argument,
                        "defense_response": response.response,
                        "acknowledged_risks": response.acknowledged_risks,
                        "stock_info": stock_context,
                    }

                    try:
                        rebuttal_result = await self.devils_advocate.rebut_defense(rebuttal_context)

                        debate_messages.append({
                            "speaker": "devils_advocate",
                            "target": response.agent_type.value,
                            "type": "rebuttal",
                            "content": rebuttal_result.get("rebuttal", ""),
                            "defense_quality": rebuttal_result.get("defense_quality", "unknown"),
                            "verdict": rebuttal_result.get("verdict", ""),
                            "round": round_num,
                        })

                        logger.info(f"[재반박] {response.agent_type.value}에게: {rebuttal_result.get('rebuttal', '')[:100]}...")

                    except Exception as e:
                        logger.error(f"Error in rebuttal: {e}")

        # Create debate round summary
        resolved_issues = []
        remaining_concerns = []

        for response in responses:
            if response.adjusted_score is None or response.adjusted_score >= 6:
                resolved_issues.append(f"{response.agent_type.value}: 방어 성공")
            else:
                remaining_concerns.extend(response.acknowledged_risks)

        debate_round = DebateRound(
            round_number=round_num,
            counter_arguments=counter_arguments,
            responses=responses,
            resolved_issues=resolved_issues,
            remaining_concerns=remaining_concerns,
        )

        # Update agent opinions with adjusted scores
        updated_opinions = dict(state.agent_opinions)
        for response in responses:
            if response.adjusted_score is not None:
                agent_key = response.agent_type.value
                if agent_key in updated_opinions:
                    opinion = updated_opinions[agent_key]
                    if isinstance(opinion, dict):
                        opinion["score"] = response.adjusted_score
                        opinion["concerns"] = opinion.get("concerns", []) + response.acknowledged_risks

        logger.info(f"=== 토론 라운드 {round_num} 완료 ===")
        logger.info(f"  해결된 이슈: {len(resolved_issues)}")
        logger.info(f"  남은 우려: {len(remaining_concerns)}")

        return {
            "current_debate_round": round_num + 1,
            "debate_rounds": state.debate_rounds + [debate_round],
            "agent_opinions": updated_opinions,
            "current_phase": "debate",
        }

    def _get_agent_by_key(self, key: str):
        """Get agent instance by key."""
        mapping = {
            "macro": self.macro_agent,
            "quant": self.quant_agent,
            "valuation": self.valuation_agent,
        }
        return mapping.get(key)

    def _prepare_research_context(self, state: AgentState) -> dict:
        """토론에서 사용할 자료 컨텍스트 준비.

        Args:
            state: 현재 워크플로우 상태

        Returns:
            에이전트들이 참조할 수 있는 자료 요약
        """
        user_research = state.request.user_research
        validation = state.user_research_validation

        if not user_research or not user_research.documents:
            return {}

        # 자료 요약 생성
        doc_summaries = []
        for doc in user_research.documents:
            doc_summaries.append({
                "id": doc.id,
                "title": doc.title,
                "source": doc.source_name,
                "type": doc.source_type.value,
                "key_claims": doc.key_claims[:5],  # 상위 5개만
                "target_price": doc.target_price,
                "recommendation": doc.recommendation,
                "user_trust": doc.user_trust_level,
            })

        # 편향 검토 결과 요약
        bias_warnings = []
        if validation and "bias_results" in validation:
            for result in validation["bias_results"]:
                if result.get("bias_severity") in ["high", "critical"]:
                    bias_warnings.append({
                        "document": result.get("document_title"),
                        "biases": result.get("detected_biases", []),
                        "warning": result.get("bias_explanation", "")[:200],
                    })

        # 신뢰도 정보
        reliability_info = {}
        if validation and "overall_reliability" in validation:
            reliability_info = validation["overall_reliability"]

        return {
            "total_documents": len(user_research.documents),
            "documents": doc_summaries,
            "user_hypothesis": user_research.user_hypothesis,
            "user_concerns": user_research.user_concerns,
            "user_questions": user_research.user_questions,
            "bias_warnings": bias_warnings,
            "avg_reliability": reliability_info.get("score", "N/A"),
            "reliability_level": reliability_info.get("level", "unknown"),
            "high_bias_count": reliability_info.get("high_bias_documents", 0),
        }

    async def _final_decision(self, state: AgentState) -> dict[str, Any]:
        """Generate final investment decision."""
        logger.info("Generating final decision")

        context = {
            "ticker": state.request.ticker,
            "company_name": state.stock.get("info", {}).get("name", state.request.ticker) if state.stock else state.request.ticker,
            "current_price": state.stock.get("current_price") if state.stock else None,
            "agent_opinions": state.agent_opinions,
            "debate_rounds": [dr.model_dump() if hasattr(dr, 'model_dump') else dr for dr in state.debate_rounds],
        }

        try:
            result = await self.chairman.analyze(context)

            return {
                "committee_decision": result.get("decision"),
                "current_phase": "complete",
                "completed_at": datetime.now(),
            }

        except Exception as e:
            logger.error(f"Error in final decision: {e}")
            return {
                "errors": state.errors + [f"Final decision failed: {e}"],
                "current_phase": "error",
            }

    async def run(self, request: AnalysisRequest) -> dict[str, Any]:
        """Run the full analysis workflow.

        Args:
            request: Analysis request

        Returns:
            Complete analysis result
        """
        logger.info(f"Starting analysis workflow for {request.ticker}")

        # Initialize state
        initial_state = AgentState(
            request=request,
            current_phase="initialization",
        )

        # Compile and run the graph
        compiled = self.graph.compile()

        # Execute workflow
        final_state = None
        async for state in compiled.astream(initial_state):
            final_state = state
            logger.debug(f"Workflow state: {list(state.keys())}")

        # Extract final results
        if final_state:
            # Get the last node's output
            last_output = list(final_state.values())[-1] if final_state else {}

            return {
                "ticker": request.ticker,
                "status": "complete" if not last_output.get("errors") else "error",
                "committee_decision": last_output.get("committee_decision"),
                "agent_opinions": last_output.get("agent_opinions", {}),
                "errors": last_output.get("errors", []),
                "warnings": last_output.get("warnings", []),
            }

        return {
            "ticker": request.ticker,
            "status": "error",
            "errors": ["Workflow failed to complete"],
        }


async def analyze_stock(ticker: str, **kwargs) -> dict[str, Any]:
    """Convenience function to analyze a stock.

    Args:
        ticker: Stock ticker symbol
        **kwargs: Additional analysis parameters

    Returns:
        Analysis result
    """
    request = AnalysisRequest(
        ticker=ticker,
        focus_areas=kwargs.get("focus_areas", []),
        additional_context=kwargs.get("additional_context"),
    )

    config = WorkflowConfig(
        max_debate_rounds=kwargs.get("debate_rounds", 3),
        include_devils_advocate=kwargs.get("include_devils_advocate", True),
    )

    workflow = AnalysisWorkflow(config)
    return await workflow.run(request)
