"""Devil's Advocate Agent - 반대 논거 전문가."""
import json
import logging
from typing import Any, Optional

from agents.base_agent import BaseAgent, AgentConfig
from models.agent_opinion import AgentType, RiskLevel, Sentiment
from models.analysis_result import DevilsAdvocateAnalysis

logger = logging.getLogger(__name__)


class DevilsAdvocateAgent(BaseAgent):
    """Devil's Advocate agent - challenges other agents' analyses."""

    def __init__(self, config: Optional[AgentConfig] = None):
        """Initialize Devil's Advocate Agent."""
        if config is None:
            config = AgentConfig(
                agent_type=AgentType.DEVILS_ADVOCATE,
                prompt_file="prompts/devils_advocate.md",
                temperature=0.5,  # Slightly higher for more creative challenges
            )
        super().__init__(config)

    def _get_default_prompt(self) -> str:
        """Get default system prompt."""
        return """You are the Devil's Advocate. Your role is to intentionally challenge
and question other agents' analyses to identify blind spots and weaknesses.

Core questions to ask:
1. "Why is it at this price?" - What's the market's logic?
2. "Is this already known?" - Do we have an information edge?
3. "What's the worst case?" - Pre-mortem analysis
4. "What historical precedents exist?" - Similar failure cases

Be constructively critical, not just negative. Provide evidence-based counter-arguments."""

    async def analyze(self, context: dict[str, Any]) -> dict[str, Any]:
        """Generate counter-arguments to other agents' analyses.

        Args:
            context: Analysis context including all other agent results

        Returns:
            Devil's advocate analysis result
        """
        ticker = context.get("ticker", "")
        current_price = context.get("current_price", 0)

        # Get other agents' analyses
        macro_analysis = context.get("macro_analysis", {})
        quant_analysis = context.get("quant_analysis", {})
        qualitative_analysis = context.get("qualitative_analysis", {})
        industry_analysis = context.get("industry_analysis", {})
        valuation_analysis = context.get("valuation_analysis", {})

        # Build analysis prompt
        prompt = f"""As Devil's Advocate, challenge the following investment analyses for {ticker}:

Current Price: {current_price}

=== MACRO ANALYSIS ===
{json.dumps(macro_analysis, indent=2, default=str)}

=== QUANT ANALYSIS ===
{json.dumps(quant_analysis, indent=2, default=str)}

=== QUALITATIVE ANALYSIS ===
{json.dumps(qualitative_analysis, indent=2, default=str)}

=== INDUSTRY ANALYSIS ===
{json.dumps(industry_analysis, indent=2, default=str)}

=== VALUATION ANALYSIS ===
{json.dumps(valuation_analysis, indent=2, default=str)}

Provide your devil's advocate analysis in JSON format:
{{
    "score": <1-10, where 10 = most concerns>,
    "confidence": <0-100>,
    "sentiment": "<very_bullish|bullish|neutral|bearish|very_bearish>",
    "summary": "<1-2 sentence summary of key concerns>",
    "why_this_price": "<analysis of why current price exists>",
    "what_market_knows": "<what's already priced in>",
    "potential_blind_spots": ["<blind_spot1>", "<blind_spot2>"],
    "macro_counter_arguments": ["<counter1>", "<counter2>"],
    "quant_counter_arguments": ["<counter1>", "<counter2>"],
    "qualitative_counter_arguments": ["<counter1>", "<counter2>"],
    "industry_counter_arguments": ["<counter1>", "<counter2>"],
    "valuation_counter_arguments": ["<counter1>", "<counter2>"],
    "pre_mortem_scenarios": [
        "<scenario where investment fails 1>",
        "<scenario where investment fails 2>"
    ],
    "historical_precedents": ["<similar failure case>"],
    "red_flags": ["<red flag 1>", "<red flag 2>"],
    "warning_signals": ["<signal to monitor 1>", "<signal to monitor 2>"],
    "key_points": ["<key concern 1>", "<key concern 2>"],
    "concerns": ["<serious concern 1>", "<serious concern 2>"],
    "questions_to_answer": ["<question needing verification>"]
}}"""

        try:
            response = await self.invoke(prompt)
            result = self._parse_json_response(response)

            # Create DevilsAdvocateAnalysis object
            analysis = DevilsAdvocateAnalysis(
                score=result.get("score", 5),
                sentiment=self._map_sentiment(result.get("sentiment", "neutral")),
                summary=result.get("summary", ""),
                why_this_price=result.get("why_this_price", ""),
                what_market_knows=result.get("what_market_knows", ""),
                potential_blind_spots=result.get("potential_blind_spots", []),
                macro_counter_arguments=result.get("macro_counter_arguments", []),
                quant_counter_arguments=result.get("quant_counter_arguments", []),
                qualitative_counter_arguments=result.get("qualitative_counter_arguments", []),
                industry_counter_arguments=result.get("industry_counter_arguments", []),
                valuation_counter_arguments=result.get("valuation_counter_arguments", []),
                pre_mortem_scenarios=result.get("pre_mortem_scenarios", []),
                historical_precedents=result.get("historical_precedents", []),
                red_flags=result.get("red_flags", []),
                warning_signals=result.get("warning_signals", []),
            )

            return {
                "analysis": analysis.model_dump(),
                "raw_result": result,
                "opinion": self.create_opinion(
                    ticker=ticker,
                    score=10 - result.get("score", 5),  # Invert score for opinion
                    confidence=result.get("confidence", 75),
                    summary=result.get("summary", ""),
                    key_points=result.get("key_points", []),
                    concerns=result.get("concerns", []),
                    detailed_analysis=result,
                ).model_dump(),
            }

        except Exception as e:
            logger.error(f"Error in devil's advocate analysis: {e}")
            return {
                "error": str(e),
                "analysis": None,
            }

    async def generate_counter_argument(
        self,
        agent_type: str,
        original_claim: str,
        evidence: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        """Generate a specific counter-argument to a claim.

        Args:
            agent_type: Type of agent making the claim
            original_claim: The claim to challenge
            evidence: Optional supporting evidence for the claim

        Returns:
            Counter-argument details
        """
        prompt = f"""Generate a counter-argument to the following claim:

Agent: {agent_type}
Claim: {original_claim}
Supporting Evidence: {json.dumps(evidence or [])}

Provide your counter-argument in JSON format:
{{
    "counter_argument": "<your counter-argument>",
    "severity": "<low|medium|high|critical>",
    "evidence_against": ["<evidence1>", "<evidence2>"],
    "questions_raised": ["<question1>", "<question2>"]
}}"""

        try:
            response = await self.invoke(prompt)
            return self._parse_json_response(response)
        except Exception as e:
            logger.error(f"Error generating counter-argument: {e}")
            return {
                "counter_argument": "Unable to generate counter-argument",
                "severity": "low",
                "evidence_against": [],
                "questions_raised": [],
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

    async def challenge(self, context: dict[str, Any]) -> dict[str, Any]:
        """토론에서 특정 에이전트의 분석에 도전합니다.

        Args:
            context:
                - target_agent: 도전 대상 에이전트
                - target_score: 대상의 점수
                - target_sentiment: 대상의 sentiment
                - target_summary: 대상의 분석 요약
                - target_key_points: 대상의 핵심 포인트
                - round_number: 토론 라운드 번호
                - stock_info: 주식 정보

        Returns:
            도전 내용:
                - counter_argument: 반박 논리
                - evidence: 증거
                - severity: 심각도
                - questions: 답해야 할 질문들
        """
        target_agent = context.get("target_agent", "unknown")
        target_score = context.get("target_score", 5)
        target_summary = context.get("target_summary", "")
        target_key_points = context.get("target_key_points", [])
        round_number = context.get("round_number", 1)
        stock_info = context.get("stock_info", {})

        # 사용자 제공 자료 컨텍스트
        user_research = context.get("user_research", {})
        research_synthesis = context.get("research_synthesis", {})

        # 라운드별로 도전 강도 조절
        intensity = ["moderate", "aggressive", "final_verification"][min(round_number - 1, 2)]

        # 사용자 자료 섹션 생성
        user_research_section = ""
        if user_research and user_research.get("documents"):
            user_research_section = f"""
## 📚 사용자 제공 자료 (참조용)
- 총 {user_research.get('total_documents', 0)}개 자료
- 평균 신뢰도: {user_research.get('avg_reliability', 'N/A')}/10
- 신뢰도 수준: {user_research.get('reliability_level', 'unknown')}

### 자료 요약
{json.dumps(user_research.get('documents', [])[:5], ensure_ascii=False, indent=2)}

### 사용자 가설
{user_research.get('user_hypothesis', '없음')}

### 사용자 우려사항
{json.dumps(user_research.get('user_concerns', []), ensure_ascii=False)}

### ⚠️ 편향 경고 (높은 편향 자료)
{json.dumps(user_research.get('bias_warnings', []), ensure_ascii=False, indent=2) if user_research.get('bias_warnings') else '없음'}
"""

        # 종합 분석 섹션
        synthesis_section = ""
        if research_synthesis:
            synthesis_section = f"""
## 📊 자료 종합 분석
### 자료들이 동의하는 점
{json.dumps(research_synthesis.get('consensus_points', []), ensure_ascii=False)}

### 자료 간 의견 차이
{json.dumps(research_synthesis.get('divergent_points', []), ensure_ascii=False)}

### 정보 격차 (추가 조사 필요)
{json.dumps(research_synthesis.get('information_gaps', []), ensure_ascii=False)}
"""

        prompt = f"""당신은 투자위원회의 Devil's Advocate입니다.
{target_agent} 에이전트의 분석에 도전해야 합니다.

## 대상 분석
- 에이전트: {target_agent}
- 점수: {target_score}/10
- 요약: {target_summary}
- 핵심 포인트: {json.dumps(target_key_points, ensure_ascii=False)}

## 주식 정보
{json.dumps(stock_info, ensure_ascii=False, indent=2) if stock_info else "정보 없음"}
{user_research_section}
{synthesis_section}
## 토론 라운드: {round_number}/3 (강도: {intensity})

---

당신의 역할:
1. 이 분석의 약점과 맹점을 찾으세요
2. 시장이 이미 알고 있는 것과 새로운 인사이트를 구분하세요
3. Pre-mortem: 이 투자가 실패할 수 있는 시나리오를 제시하세요
4. 역사적 선례와 유사한 실패 사례를 찾으세요
5. **사용자 제공 자료에서 편향이 발견된 경우, 이를 지적하세요**
6. **자료 간 의견 차이가 있는 부분에 대해 질문하세요**

{f"Round {round_number}: 더 날카롭고 구체적인 도전을 하세요. 이전 라운드에서 해결되지 않은 문제에 집중하세요." if round_number > 1 else ""}

다음 JSON 형식으로 응답하세요:
{{
    "counter_argument": "핵심 반박 논리 (구체적이고 데이터 기반으로, 최소 3문장)",
    "evidence": ["반박을 뒷받침하는 증거 1", "증거 2", "증거 3"],
    "severity": "low" 또는 "medium" 또는 "high" 또는 "critical",
    "questions": ["이 에이전트가 답해야 할 질문 1", "질문 2"],
    "blind_spots": ["이 분석이 놓친 것 1", "놓친 것 2"],
    "worst_case_scenario": "최악의 시나리오 설명",
    "historical_parallel": "유사한 역사적 사례 (있다면)",
    "user_research_concerns": ["사용자 자료에서 발견된 문제점 (있다면)"],
    "cited_sources": ["인용한 사용자 자료 제목 (있다면)"]
}}"""

        try:
            response = await self.invoke(prompt)
            result = self._parse_json_response(response)

            return {
                "counter_argument": result.get("counter_argument", "도전 생성 실패"),
                "evidence": result.get("evidence", []),
                "severity": result.get("severity", "medium"),
                "questions": result.get("questions", []),
                "blind_spots": result.get("blind_spots", []),
                "worst_case": result.get("worst_case_scenario", ""),
                "historical_parallel": result.get("historical_parallel", ""),
            }

        except Exception as e:
            logger.error(f"Error generating challenge: {e}")
            return {
                "counter_argument": f"도전 생성 중 오류: {e}",
                "evidence": [],
                "severity": "low",
                "questions": [],
            }

    async def rebut_defense(self, context: dict[str, Any]) -> dict[str, Any]:
        """에이전트의 방어에 대해 재반박합니다.

        Args:
            context:
                - original_challenge: 원래 도전 내용
                - defense_response: 에이전트의 방어 응답
                - acknowledged_risks: 인정된 리스크
                - stock_info: 주식 정보

        Returns:
            재반박 내용:
                - rebuttal: 재반박 논리
                - remaining_concerns: 남은 우려 사항
                - accepted_defense: 받아들인 방어 포인트
        """
        original = context.get("original_challenge", "")
        defense = context.get("defense_response", "")
        acknowledged = context.get("acknowledged_risks", [])

        prompt = f"""당신은 Devil's Advocate입니다.
에이전트가 당신의 도전에 대해 방어했습니다. 이 방어를 평가하세요.

## 원래 도전
{original}

## 에이전트의 방어
{defense}

## 인정된 리스크
{json.dumps(acknowledged, ensure_ascii=False)}

---

이 방어가 충분한지 평가하세요:
1. 방어가 논리적이고 증거에 기반했는가?
2. 핵심 우려사항이 해소되었는가?
3. 추가로 제기해야 할 점이 있는가?

다음 JSON 형식으로 응답하세요:
{{
    "rebuttal": "재반박 또는 수용 메시지",
    "defense_quality": "weak" 또는 "moderate" 또는 "strong",
    "remaining_concerns": ["해소되지 않은 우려 1", "우려 2"],
    "accepted_points": ["인정하는 방어 포인트 1", "포인트 2"],
    "final_verdict": "방어가 충분함" 또는 "부분적으로 충분함" 또는 "방어가 불충분함"
}}"""

        try:
            response = await self.invoke(prompt)
            result = self._parse_json_response(response)

            return {
                "rebuttal": result.get("rebuttal", ""),
                "defense_quality": result.get("defense_quality", "moderate"),
                "remaining_concerns": result.get("remaining_concerns", []),
                "accepted_points": result.get("accepted_points", []),
                "verdict": result.get("final_verdict", "부분적으로 충분함"),
            }

        except Exception as e:
            logger.error(f"Error in rebut_defense: {e}")
            return {
                "rebuttal": "재반박 생성 실패",
                "defense_quality": "unknown",
                "remaining_concerns": [],
                "accepted_points": [],
            }
