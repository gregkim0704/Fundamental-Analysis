"""Data Validator Agent - 자료 왜곡/편향 검토 에이전트."""
import json
import logging
from datetime import datetime
from typing import Any, Optional

from agents.base_agent import BaseAgent, AgentConfig
from models.agent_opinion import AgentType, Sentiment
from models.user_research import (
    BiasCheckResult,
    BiasType,
    ResearchDocument,
    ResearchSynthesis,
    SourceType,
    UserResearchInput,
)

logger = logging.getLogger(__name__)


class DataValidatorAgent(BaseAgent):
    """자료의 신뢰성과 편향을 검토하는 에이전트.

    역할:
    1. 각 자료의 출처 신뢰도 평가
    2. 편향(bias) 탐지 및 경고
    3. 데이터 정확성 교차 검증
    4. 자료 간 모순 발견
    5. 정보 격차 식별
    """

    def __init__(self, config: Optional[AgentConfig] = None):
        """Initialize Data Validator Agent."""
        if config is None:
            config = AgentConfig(
                agent_type=AgentType.CHAIRMAN,  # 임시로 CHAIRMAN 사용
                temperature=0.3,
            )
        super().__init__(config)

    def _get_default_prompt(self) -> str:
        """Get default system prompt."""
        return """당신은 30년 경력의 리서치 품질 관리 전문가입니다.

당신의 역할:
1. 투자 관련 자료의 신뢰성을 평가합니다
2. 숨겨진 편향(bias)을 탐지합니다
3. 데이터의 정확성을 검증합니다
4. 자료 간 모순을 발견합니다
5. 정보의 최신성을 확인합니다

편향 유형:
- bullish_bias: 지나치게 낙관적인 전망
- bearish_bias: 지나치게 비관적인 전망
- recency_bias: 최근 사건에 과도한 가중치
- confirmation_bias: 기존 견해를 지지하는 정보만 선택
- survivorship_bias: 실패 사례 누락
- selection_bias: 특정 데이터만 선택적 인용
- conflict_of_interest: 이해충돌 가능성
- outdated: 오래된 정보
- incomplete: 불완전한 분석

항상 객관적이고 비판적인 시각을 유지하세요."""

    async def analyze(self, context: dict[str, Any]) -> dict[str, Any]:
        """전체 자료 분석 및 종합.

        Args:
            context: 분석 컨텍스트
                - user_research: UserResearchInput 객체
                - stock_info: 주식 정보

        Returns:
            종합 분석 결과
        """
        user_research = context.get("user_research")
        stock_info = context.get("stock_info", {})

        if not user_research or not user_research.documents:
            return {
                "synthesis": None,
                "message": "분석할 자료가 없습니다.",
            }

        # 각 자료 개별 검토
        bias_results = []
        for doc in user_research.documents:
            result = await self.check_document_bias(doc, stock_info)
            bias_results.append(result)

        # 자료 간 교차 검증
        cross_validation = await self.cross_validate_documents(
            user_research.documents,
            stock_info,
        )

        # 종합 분석
        synthesis = await self.synthesize_research(
            user_research,
            bias_results,
            cross_validation,
        )

        return {
            "bias_results": [r.model_dump() for r in bias_results],
            "cross_validation": cross_validation,
            "synthesis": synthesis.model_dump() if synthesis else None,
            "overall_reliability": self._calculate_overall_reliability(bias_results),
        }

    async def check_document_bias(
        self,
        document: ResearchDocument,
        stock_info: dict[str, Any],
    ) -> BiasCheckResult:
        """개별 자료의 편향 검토.

        Args:
            document: 검토할 자료
            stock_info: 주식 정보

        Returns:
            편향 검토 결과
        """
        prompt = f"""다음 투자 관련 자료를 비판적으로 검토하세요.

## 자료 정보
- 제목: {document.title}
- 출처 유형: {document.source_type.value}
- 출처명: {document.source_name}
- 발행일: {document.publish_date.strftime('%Y-%m-%d') if document.publish_date else '불명'}
- 저자: {document.author or '불명'}

## 자료 내용
{document.content[:3000]}

## 핵심 주장
{json.dumps(document.key_claims, ensure_ascii=False)}

## 인용 데이터
{json.dumps(document.data_points, ensure_ascii=False)}

## 목표가/투자의견
- 목표가: {document.target_price or '없음'}
- 투자의견: {document.recommendation or '없음'}

## 현재 주식 정보 (비교용)
{json.dumps(stock_info, ensure_ascii=False, indent=2) if stock_info else '정보 없음'}

---

다음을 분석하세요:
1. 이 자료에 어떤 편향이 있는가?
2. 인용된 데이터가 정확하고 최신인가?
3. 논리적 비약이나 검증 불가한 주장이 있는가?
4. 이해충돌 가능성이 있는가?
5. 이 자료를 어떻게 활용해야 하는가?

다음 JSON 형식으로 응답하세요:
{{
    "detected_biases": ["bias_type1", "bias_type2"],
    "bias_severity": "low" 또는 "medium" 또는 "high",
    "bias_explanation": "편향에 대한 상세 설명",
    "data_accuracy": 0-100 사이의 숫자,
    "outdated_info": ["오래된 정보 1", "오래된 정보 2"],
    "unverifiable_claims": ["검증 불가 주장 1"],
    "reliability_score": 1-10 사이의 숫자,
    "usage_recommendation": "이 자료 활용 방법 권장",
    "caveats": ["주의사항 1", "주의사항 2"],
    "ai_notes": "추가 분석 노트"
}}"""

        try:
            response = await self.invoke(prompt)
            result = self._parse_json_response(response)

            # BiasType enum으로 변환
            detected_biases = []
            for bias_str in result.get("detected_biases", []):
                try:
                    detected_biases.append(BiasType(bias_str))
                except ValueError:
                    detected_biases.append(BiasType.OTHER if hasattr(BiasType, 'OTHER') else BiasType.UNVERIFIED)

            return BiasCheckResult(
                document_id=document.id,
                document_title=document.title,
                detected_biases=detected_biases,
                bias_severity=result.get("bias_severity", "low"),
                bias_explanation=result.get("bias_explanation", ""),
                data_accuracy=result.get("data_accuracy", 50),
                outdated_info=result.get("outdated_info", []),
                unverifiable_claims=result.get("unverifiable_claims", []),
                contradictions=[],  # 교차 검증에서 채움
                reliability_score=result.get("reliability_score", 5),
                usage_recommendation=result.get("usage_recommendation", ""),
                caveats=result.get("caveats", []),
                ai_notes=result.get("ai_notes", ""),
            )

        except Exception as e:
            logger.error(f"Error checking document bias: {e}")
            return BiasCheckResult(
                document_id=document.id,
                document_title=document.title,
                detected_biases=[BiasType.UNVERIFIED],
                bias_severity="medium",
                bias_explanation=f"분석 중 오류 발생: {e}",
                reliability_score=3,
            )

    async def cross_validate_documents(
        self,
        documents: list[ResearchDocument],
        stock_info: dict[str, Any],
    ) -> dict[str, Any]:
        """자료 간 교차 검증.

        Args:
            documents: 자료 목록
            stock_info: 주식 정보

        Returns:
            교차 검증 결과
        """
        if len(documents) < 2:
            return {
                "contradictions": [],
                "consensus": [],
                "divergent_views": [],
            }

        # 자료 요약 준비
        doc_summaries = []
        for doc in documents:
            doc_summaries.append({
                "id": doc.id,
                "title": doc.title,
                "source": doc.source_name,
                "type": doc.source_type.value,
                "key_claims": doc.key_claims,
                "target_price": doc.target_price,
                "recommendation": doc.recommendation,
            })

        prompt = f"""다음 여러 투자 자료들을 교차 검증하세요.

## 자료 목록
{json.dumps(doc_summaries, ensure_ascii=False, indent=2)}

## 현재 주가 정보
{json.dumps(stock_info, ensure_ascii=False, indent=2) if stock_info else '정보 없음'}

---

다음을 분석하세요:
1. 자료들 사이에 모순되는 주장이 있는가?
2. 자료들이 합의하는 점은 무엇인가?
3. 견해가 갈리는 부분은 무엇인가?
4. 목표가나 투자의견이 어떻게 분포되어 있는가?

다음 JSON 형식으로 응답하세요:
{{
    "contradictions": [
        {{
            "topic": "모순 주제",
            "doc1_id": "자료1 ID",
            "doc1_claim": "자료1 주장",
            "doc2_id": "자료2 ID",
            "doc2_claim": "자료2 주장",
            "significance": "low/medium/high"
        }}
    ],
    "consensus_points": ["합의점 1", "합의점 2"],
    "divergent_views": [
        {{
            "topic": "의견 갈림 주제",
            "views": ["관점 A", "관점 B"]
        }}
    ],
    "target_price_range": {{
        "min": 최소 목표가 또는 null,
        "max": 최대 목표가 또는 null,
        "median": 중간값 또는 null
    }},
    "recommendation_distribution": {{
        "bullish": 낙관적 자료 수,
        "neutral": 중립 자료 수,
        "bearish": 비관적 자료 수
    }},
    "reliability_notes": "교차 검증 결과 종합 노트"
}}"""

        try:
            response = await self.invoke(prompt)
            return self._parse_json_response(response)
        except Exception as e:
            logger.error(f"Error in cross validation: {e}")
            return {
                "contradictions": [],
                "consensus_points": [],
                "divergent_views": [],
                "error": str(e),
            }

    async def synthesize_research(
        self,
        user_research: UserResearchInput,
        bias_results: list[BiasCheckResult],
        cross_validation: dict[str, Any],
    ) -> ResearchSynthesis:
        """자료 종합 분석.

        Args:
            user_research: 사용자 입력 자료
            bias_results: 편향 검토 결과들
            cross_validation: 교차 검증 결과

        Returns:
            종합 분석 결과
        """
        # 유형별 자료 수 계산
        docs_by_type = {}
        for doc in user_research.documents:
            type_name = doc.source_type.value
            docs_by_type[type_name] = docs_by_type.get(type_name, 0) + 1

        # 평균 신뢰도 계산
        avg_reliability = (
            sum(r.reliability_score for r in bias_results) / len(bias_results)
            if bias_results else 5.0
        )

        prompt = f"""다음 자료 분석 결과를 종합하여 에이전트들이 활용할 가이드를 작성하세요.

## 자료 현황
- 총 자료 수: {len(user_research.documents)}
- 유형별: {json.dumps(docs_by_type, ensure_ascii=False)}
- 평균 신뢰도: {avg_reliability:.1f}/10

## 사용자 가설
{user_research.user_hypothesis or '없음'}

## 사용자 우려사항
{json.dumps(user_research.user_concerns, ensure_ascii=False)}

## 사용자 질문
{json.dumps(user_research.user_questions, ensure_ascii=False)}

## 편향 검토 요약
{json.dumps([{{'title': r.document_title, 'biases': [b.value for b in r.detected_biases], 'reliability': r.reliability_score}} for r in bias_results], ensure_ascii=False, indent=2)}

## 교차 검증 결과
{json.dumps(cross_validation, ensure_ascii=False, indent=2)}

---

다음 JSON 형식으로 종합 분석을 제공하세요:
{{
    "consensus_points": ["자료들이 동의하는 점"],
    "divergent_points": ["자료 간 의견 차이"],
    "verified_facts": ["검증된 사실"],
    "disputed_claims": ["논쟁이 있는 주장"],
    "information_gaps": ["추가 조사 필요 영역"],
    "overall_sentiment": "bullish" 또는 "neutral" 또는 "bearish",
    "key_takeaways": ["핵심 시사점 1", "시사점 2"],
    "recommended_focus_areas": ["에이전트들이 집중해야 할 영역"],
    "data_quality_notes": "자료 품질에 대한 종합 평가"
}}"""

        try:
            response = await self.invoke(prompt)
            result = self._parse_json_response(response)

            return ResearchSynthesis(
                ticker=user_research.ticker,
                total_documents=len(user_research.documents),
                documents_by_type=docs_by_type,
                average_reliability=avg_reliability,
                consensus_points=result.get("consensus_points", []),
                divergent_points=result.get("divergent_points", []),
                verified_facts=result.get("verified_facts", []),
                disputed_claims=result.get("disputed_claims", []),
                information_gaps=result.get("information_gaps", []),
                overall_sentiment=result.get("overall_sentiment", "neutral"),
                key_takeaways=result.get("key_takeaways", []),
                recommended_focus_areas=result.get("recommended_focus_areas", []),
            )

        except Exception as e:
            logger.error(f"Error synthesizing research: {e}")
            return ResearchSynthesis(
                ticker=user_research.ticker,
                total_documents=len(user_research.documents),
                documents_by_type=docs_by_type,
                average_reliability=avg_reliability,
            )

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
            return {}

    def _calculate_overall_reliability(
        self,
        bias_results: list[BiasCheckResult],
    ) -> dict[str, Any]:
        """전체 신뢰도 계산."""
        if not bias_results:
            return {"score": 5.0, "level": "unknown"}

        avg_score = sum(r.reliability_score for r in bias_results) / len(bias_results)
        high_bias_count = sum(1 for r in bias_results if r.bias_severity == "high")

        # 높은 편향 자료가 많으면 전체 신뢰도 하락
        adjusted_score = avg_score - (high_bias_count * 0.5)
        adjusted_score = max(1, min(10, adjusted_score))

        if adjusted_score >= 7:
            level = "high"
        elif adjusted_score >= 5:
            level = "medium"
        else:
            level = "low"

        return {
            "score": round(adjusted_score, 1),
            "level": level,
            "total_documents": len(bias_results),
            "high_bias_documents": high_bias_count,
        }
