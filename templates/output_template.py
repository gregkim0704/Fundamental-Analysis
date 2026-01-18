"""투자자 출력 자료 템플릿 - 실질적으로 유용한 분석 결과 형식.

이 모듈은 AI 투자위원회가 생성하는 분석 결과의 표준 형식을 정의합니다.
투자 의사결정에 직접적으로 활용할 수 있도록 구조화되어 있습니다.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


# =============================================================================
# 1. 자료 검토 결과 (Data Validation Output)
# =============================================================================

class BiasCheckOutputTemplate(BaseModel):
    """개별 자료 편향 검토 결과."""

    document_title: str = Field(..., description="검토한 자료 제목")
    reliability_score: int = Field(..., ge=1, le=10, description="신뢰도 점수 (1-10)")

    detected_biases: list[str] = Field(
        default_factory=list,
        description="발견된 편향 유형",
        example=["bullish_bias", "conflict_of_interest"]
    )

    bias_severity: str = Field(
        ...,
        description="편향 심각도",
        json_schema_extra={"enum": ["low", "medium", "high"]}
    )

    bias_explanation: str = Field(
        ...,
        description="편향에 대한 상세 설명",
        example="증권사 리포트 특성상 매수 의견에 편향되어 있으며, 목표가가 현재가 대비 40% 이상 높게 제시됨"
    )

    outdated_info: list[str] = Field(
        default_factory=list,
        description="발견된 오래된 정보",
        example=["2023년 3분기 실적 기준으로 분석됨 (6개월 전 데이터)"]
    )

    unverifiable_claims: list[str] = Field(
        default_factory=list,
        description="검증 불가한 주장들",
        example=["'업계 관계자에 따르면'이라는 익명 출처 인용"]
    )

    usage_recommendation: str = Field(
        ...,
        description="이 자료 활용 방법 권장",
        example="긍정적 전망의 근거 자료로 참고하되, 독립적인 데이터로 교차 검증 필요"
    )

    caveats: list[str] = Field(
        default_factory=list,
        description="주의사항",
        example=["증권사 고객사 관계로 인한 이해충돌 가능성 고려 필요"]
    )


class ResearchValidationOutputTemplate(BaseModel):
    """전체 자료 검토 결과."""

    overall_reliability: dict = Field(
        ...,
        description="전체 신뢰도 평가",
        example={
            "score": 6.5,
            "level": "medium",
            "total_documents": 3,
            "high_bias_documents": 1
        }
    )

    bias_results: list[BiasCheckOutputTemplate] = Field(
        default_factory=list,
        description="개별 자료 검토 결과"
    )

    cross_validation: dict = Field(
        default_factory=dict,
        description="자료 간 교차 검증 결과",
        example={
            "contradictions": [
                {
                    "topic": "HBM 수율",
                    "doc1_claim": "수율 60% 수준",
                    "doc2_claim": "수율 개선으로 70% 근접",
                    "significance": "high"
                }
            ],
            "consensus_points": ["AI 반도체 수요 증가", "하반기 실적 개선 전망"],
            "target_price_range": {"min": 80000, "max": 100000, "median": 90000}
        }
    )


# =============================================================================
# 2. 개별 에이전트 분석 결과
# =============================================================================

class AgentAnalysisOutputTemplate(BaseModel):
    """개별 에이전트 분석 결과."""

    agent_name: str = Field(..., description="에이전트 이름")
    agent_role: str = Field(..., description="에이전트 역할")

    # 핵심 분석 결과
    summary: str = Field(
        ...,
        description="분석 요약 (2-3문장)",
        example="삼성전자는 HBM 기술력 강화와 AI 수요 증가로 메모리 사업의 구조적 개선이 예상됩니다. 다만 파운드리 사업의 지속적인 적자가 전사 수익성에 부담이 될 수 있습니다."
    )

    key_findings: list[str] = Field(
        default_factory=list,
        description="핵심 발견사항",
        example=[
            "HBM3E 양산으로 고부가 메모리 매출 비중 30% 돌파 전망",
            "파운드리 사업 적자 폭 확대 (2024년 -3조원 예상)",
            "잉여현금흐름(FCF) 기준 투자 여력 충분"
        ]
    )

    # 투자의견
    sentiment: str = Field(
        ...,
        description="투자 의견",
        json_schema_extra={"enum": ["bullish", "neutral", "bearish"]}
    )

    confidence_score: int = Field(
        ...,
        ge=1,
        le=10,
        description="확신도 점수 (1-10)"
    )

    target_price: Optional[float] = Field(
        None,
        description="목표 주가"
    )

    # 근거
    supporting_evidence: list[str] = Field(
        default_factory=list,
        description="의견 근거",
        example=[
            "HBM 시장 CAGR 30% 성장 전망",
            "엔비디아 AI GPU 판매 급증으로 HBM 수요 확대"
        ]
    )

    risks_identified: list[str] = Field(
        default_factory=list,
        description="식별된 리스크",
        example=[
            "SK하이닉스 대비 HBM 기술 격차 존재",
            "중국 매출 비중 감소 추세"
        ]
    )

    # 사용자 자료 활용
    user_research_references: list[str] = Field(
        default_factory=list,
        description="참고한 사용자 제공 자료",
        example=["미래에셋 리포트의 HBM 매출 전망 수치 활용", "매일경제 기사의 수율 이슈 고려"]
    )


# =============================================================================
# 3. 토론 결과 (Debate Output)
# =============================================================================

class DebateExchangeTemplate(BaseModel):
    """토론 공방 내용."""

    topic: str = Field(..., description="토론 주제")

    devils_advocate_challenge: str = Field(
        ...,
        description="악마의 변호인 도전",
        example="HBM 기술 격차가 여전히 존재하는데, 어떻게 삼성전자가 2025년에 시장 점유율 40%를 달성할 수 있다고 보십니까? 현재 수율 문제를 고려하면 지나치게 낙관적인 전망 아닙니까?"
    )

    agent_defense: str = Field(
        ...,
        description="에이전트 방어",
        example="삼성전자의 장비 투자 확대와 기술 로드맵을 고려하면 2024년 하반기 수율 개선이 가시화될 것입니다. 또한 HBM4 세대에서는 기술 격차가 크게 좁혀질 것으로 예상됩니다."
    )

    rebuttal: str = Field(
        ...,
        description="재반박",
        example="수율 개선 계획은 이해하지만, 과거에도 유사한 계획이 지연된 사례가 있습니다. 현재 시점에서 확실한 것은 SK하이닉스가 선두를 유지하고 있다는 사실입니다."
    )

    resolution: str = Field(
        ...,
        description="결론/합의점",
        example="HBM 기술 격차는 리스크 요인으로 인정하되, 삼성전자의 기술력과 자본력을 고려하면 중기적 회복 가능성은 유효함. 단, 목표 점유율은 35%로 보수적 조정 권장."
    )


class DebateRoundOutputTemplate(BaseModel):
    """토론 라운드 결과."""

    round_number: int = Field(..., description="라운드 번호")
    theme: str = Field(..., description="라운드 주제")

    exchanges: list[DebateExchangeTemplate] = Field(
        default_factory=list,
        description="토론 공방 내용"
    )

    score_changes: dict[str, int] = Field(
        default_factory=dict,
        description="이 라운드 후 에이전트별 확신도 변화",
        example={"quant_agent": -1, "qualitative_agent": 0, "industry_agent": -1}
    )

    key_concessions: list[str] = Field(
        default_factory=list,
        description="인정된 약점들",
        example=["HBM 수율 리스크 인정", "파운드리 턴어라운드 시점 불확실성 인정"]
    )


class FullDebateOutputTemplate(BaseModel):
    """전체 토론 결과."""

    total_rounds: int = Field(default=3, description="총 토론 라운드 수")

    debate_rounds: list[DebateRoundOutputTemplate] = Field(
        default_factory=list,
        description="각 라운드별 토론 내용"
    )

    devils_advocate_summary: str = Field(
        ...,
        description="악마의 변호인 최종 정리",
        example="3라운드 토론 결과, HBM 기술 격차와 파운드리 적자 리스크가 주요 약점으로 확인되었습니다. 강세 의견의 에이전트들도 이 부분에 대해서는 리스크를 인정하였습니다."
    )

    unresolved_issues: list[str] = Field(
        default_factory=list,
        description="해결되지 않은 쟁점",
        example=["HBM 수율 개선 속도에 대한 이견", "파운드리 사업 분사 가능성"]
    )

    consensus_reached: list[str] = Field(
        default_factory=list,
        description="합의된 사항",
        example=["AI 반도체 수요는 구조적 성장", "현재 주가는 부분적 저평가 상태"]
    )


# =============================================================================
# 4. 최종 위원회 결정 (Committee Decision Output)
# =============================================================================

class CommitteeDecisionOutputTemplate(BaseModel):
    """AI 투자위원회 최종 결정."""

    # 최종 투자의견
    final_recommendation: str = Field(
        ...,
        description="최종 투자의견",
        example="매수 (BUY)",
        json_schema_extra={"enum": ["적극 매수", "매수", "보유", "매도", "적극 매도"]}
    )

    confidence_level: str = Field(
        ...,
        description="확신도 수준",
        json_schema_extra={"enum": ["높음", "중간", "낮음"]}
    )

    confidence_score: float = Field(
        ...,
        ge=0,
        le=10,
        description="위원회 평균 확신도 점수"
    )

    # 목표가
    target_price: float = Field(..., description="목표 주가")

    target_price_range: dict = Field(
        ...,
        description="목표가 범위",
        example={"low": 80000, "base": 90000, "high": 105000}
    )

    upside_potential: float = Field(
        ...,
        description="현재가 대비 상승 여력 (%)",
        example=25.5
    )

    # 투표 결과
    vote_result: dict = Field(
        ...,
        description="에이전트별 투표 결과",
        example={
            "bullish": ["quant_agent", "qualitative_agent", "industry_agent"],
            "neutral": ["macro_agent"],
            "bearish": ["risk_agent"],
            "abstain": []
        }
    )

    # 핵심 근거
    key_reasons: list[str] = Field(
        default_factory=list,
        description="투자의견 핵심 근거 (3-5개)",
        example=[
            "HBM 중심의 메모리 실적 턴어라운드 예상",
            "AI 인프라 투자 확대의 구조적 수혜",
            "현재 주가는 실적 개선을 충분히 반영하지 못한 상태",
            "배당 수익률 2%대로 하방 지지",
            "반도체 업황 회복기 진입"
        ]
    )

    # 리스크 요약
    key_risks: list[str] = Field(
        default_factory=list,
        description="주요 리스크 요인 (3-5개)",
        example=[
            "HBM 기술 경쟁에서 SK하이닉스 대비 열위 지속 가능성",
            "파운드리 사업 적자 지속",
            "글로벌 경기 침체 시 IT 투자 감소",
            "중국 수출 규제 강화",
            "원화 강세 시 수익성 악화"
        ]
    )

    # 반대 의견
    dissenting_opinions: list[dict] = Field(
        default_factory=list,
        description="소수 의견 및 반대 논거",
        example=[
            {
                "agent": "risk_agent",
                "opinion": "보유",
                "reason": "HBM 기술 리스크와 파운드리 적자를 감안하면 현재 주가 수준에서 추가 상승 여력 제한적"
            }
        ]
    )


# =============================================================================
# 5. 실행 가이드 (Action Guide Output)
# =============================================================================

class ActionGuideOutputTemplate(BaseModel):
    """투자 실행 가이드."""

    # 매수/매도 가이드
    action_recommendation: str = Field(
        ...,
        description="실행 권고",
        example="분할 매수 권장"
    )

    entry_strategy: dict = Field(
        ...,
        description="진입 전략",
        example={
            "current_price": 72000,
            "target_entry_price": 70000,
            "buy_zone": {"start": 68000, "end": 72000},
            "strategy": "현재가 부근에서 50% 매수 후, 68,000원 이하에서 나머지 50% 추가 매수"
        }
    )

    exit_strategy: dict = Field(
        ...,
        description="청산 전략",
        example={
            "target_price": 90000,
            "stop_loss": 62000,
            "partial_profit_taking": [
                {"price": 80000, "portion": "30%"},
                {"price": 90000, "portion": "50%"},
                {"price": 100000, "portion": "20%"}
            ]
        }
    )

    position_sizing: dict = Field(
        ...,
        description="포지션 사이즈 권고",
        example={
            "recommended_weight": "7-10%",
            "max_weight": "15%",
            "rationale": "중간 확신도를 감안하여 포트폴리오 비중 10% 이내 권장"
        }
    )

    # 모니터링 포인트
    monitoring_triggers: list[dict] = Field(
        default_factory=list,
        description="모니터링 트리거",
        example=[
            {
                "trigger": "HBM 수율 70% 돌파 확인",
                "action": "목표가 상향 검토",
                "timeline": "2024년 4분기"
            },
            {
                "trigger": "파운드리 분기 적자 5천억 초과",
                "action": "포지션 축소 검토",
                "timeline": "분기 실적 발표 시"
            },
            {
                "trigger": "주가 60,000원 이탈",
                "action": "손절 실행",
                "timeline": "즉시"
            }
        ]
    )

    # 시나리오별 대응
    scenario_actions: list[dict] = Field(
        default_factory=list,
        description="시나리오별 대응 전략",
        example=[
            {
                "scenario": "Bull Case - HBM 점유율 40% 달성",
                "probability": "30%",
                "target_price": 105000,
                "action": "목표가까지 보유 후 분할 매도"
            },
            {
                "scenario": "Base Case - 점진적 실적 개선",
                "probability": "50%",
                "target_price": 90000,
                "action": "목표가 도달 시 50% 매도"
            },
            {
                "scenario": "Bear Case - HBM 경쟁 열위 지속",
                "probability": "20%",
                "target_price": 65000,
                "action": "65,000원 이탈 시 전량 매도"
            }
        ]
    )


# =============================================================================
# 6. 사용자 질문 답변 (Q&A Output)
# =============================================================================

class QAOutputTemplate(BaseModel):
    """사용자 질문에 대한 답변."""

    question: str = Field(..., description="사용자 질문")

    answer: str = Field(
        ...,
        description="위원회 답변",
        example="현재 주가 72,000원 수준은 2024년 예상 실적 기준 PER 12배로, 과거 5년 평균 PER 14배 대비 저평가 상태입니다. 다만 HBM 기술 리스크를 감안하면 적정가치에 근접한 것으로 판단됩니다."
    )

    confidence: str = Field(
        ...,
        description="답변 확신도",
        json_schema_extra={"enum": ["높음", "중간", "낮음"]}
    )

    supporting_analysis: list[str] = Field(
        default_factory=list,
        description="근거 분석",
        example=["밸류에이션 분석 결과 참조", "동종 업계 비교 분석 참조"]
    )

    caveats: list[str] = Field(
        default_factory=list,
        description="주의사항",
        example=["실적 추정치 변동에 따라 밸류에이션 달라질 수 있음"]
    )


# =============================================================================
# 7. 전체 출력 템플릿 (통합)
# =============================================================================

class FullOutputTemplate(BaseModel):
    """AI 투자위원회 전체 분석 결과."""

    # 메타 정보
    ticker: str = Field(..., description="분석 대상 종목")
    company_name: str = Field(..., description="회사명")
    analysis_date: datetime = Field(default_factory=datetime.now, description="분석 일시")
    current_price: float = Field(..., description="분석 시점 주가")

    # 1. Executive Summary (경영진 요약)
    executive_summary: dict = Field(
        ...,
        description="핵심 요약",
        example={
            "recommendation": "매수",
            "target_price": 90000,
            "upside": "25%",
            "confidence": "중간",
            "one_liner": "AI 반도체 수요 확대로 메모리 실적 턴어라운드 예상, 현재 주가는 저평가"
        }
    )

    # 2. 자료 검토 결과
    research_validation: ResearchValidationOutputTemplate = Field(
        ...,
        description="사용자 제공 자료 검토 결과"
    )

    # 3. 개별 에이전트 분석
    agent_analyses: list[AgentAnalysisOutputTemplate] = Field(
        default_factory=list,
        description="각 에이전트별 분석 결과"
    )

    # 4. 토론 결과
    debate_results: FullDebateOutputTemplate = Field(
        ...,
        description="AI 위원회 토론 결과"
    )

    # 5. 최종 위원회 결정
    committee_decision: CommitteeDecisionOutputTemplate = Field(
        ...,
        description="위원회 최종 결정"
    )

    # 6. 실행 가이드
    action_guide: ActionGuideOutputTemplate = Field(
        ...,
        description="투자 실행 가이드"
    )

    # 7. Q&A
    qa_responses: list[QAOutputTemplate] = Field(
        default_factory=list,
        description="사용자 질문에 대한 답변"
    )

    # 8. 추가 리서치 권장
    further_research: list[str] = Field(
        default_factory=list,
        description="추가로 조사하면 좋을 영역",
        example=[
            "삼성전자 HBM4 개발 현황 추적",
            "엔비디아 차세대 GPU 공급망 변화 모니터링",
            "파운드리 사업 구조조정 계획 확인"
        ]
    )

    # 9. 면책 조항
    disclaimer: str = Field(
        default="본 분석은 AI 투자위원회의 의견이며 투자 조언이 아닙니다. 투자 결정은 본인의 판단과 책임 하에 이루어져야 합니다.",
        description="면책 조항"
    )


# =============================================================================
# 샘플 데이터 (실제 사용 예시)
# =============================================================================

SAMPLE_OUTPUT = FullOutputTemplate(
    ticker="005930.KS",
    company_name="삼성전자",
    analysis_date=datetime.now(),
    current_price=72000,
    executive_summary={
        "recommendation": "매수",
        "target_price": 90000,
        "upside": "25%",
        "confidence": "중간",
        "one_liner": "AI 반도체 수요 확대로 메모리 실적 턴어라운드 예상, 현재 주가는 저평가"
    },
    research_validation=ResearchValidationOutputTemplate(
        overall_reliability={
            "score": 6.5,
            "level": "medium",
            "total_documents": 2,
            "high_bias_documents": 1
        },
        bias_results=[
            BiasCheckOutputTemplate(
                document_title="삼성전자 2024년 하반기 전망",
                reliability_score=7,
                detected_biases=["bullish_bias"],
                bias_severity="medium",
                bias_explanation="증권사 리포트 특성상 매수 의견 편향",
                usage_recommendation="긍정적 시나리오 근거로 참고"
            )
        ],
        cross_validation={
            "contradictions": [],
            "consensus_points": ["AI 반도체 수요 증가"],
            "target_price_range": {"min": 80000, "max": 100000}
        }
    ),
    agent_analyses=[
        AgentAnalysisOutputTemplate(
            agent_name="Quant Agent",
            agent_role="정량 분석 전문가",
            summary="재무지표 기준 저평가 상태, 실적 개선 모멘텀 유효",
            key_findings=["PER 12배로 역사적 저점", "ROE 개선 추세"],
            sentiment="bullish",
            confidence_score=7,
            target_price=92000,
            supporting_evidence=["매출 성장률 12%", "영업이익률 개선"],
            risks_identified=["파운드리 적자"]
        )
    ],
    debate_results=FullDebateOutputTemplate(
        total_rounds=3,
        debate_rounds=[
            DebateRoundOutputTemplate(
                round_number=1,
                theme="HBM 경쟁력",
                exchanges=[
                    DebateExchangeTemplate(
                        topic="HBM 기술 격차",
                        devils_advocate_challenge="SK하이닉스 대비 기술 열위 해소 가능한가?",
                        agent_defense="장비 투자와 인력 확보로 격차 축소 중",
                        rebuttal="과거에도 유사 계획 지연된 바 있음",
                        resolution="리스크로 인정하되 중기 회복 가능성 유효"
                    )
                ],
                key_concessions=["HBM 수율 리스크 인정"]
            )
        ],
        devils_advocate_summary="HBM 기술 격차와 파운드리 적자가 주요 리스크로 확인",
        unresolved_issues=["HBM 수율 개선 속도"],
        consensus_reached=["AI 반도체 수요는 구조적 성장"]
    ),
    committee_decision=CommitteeDecisionOutputTemplate(
        final_recommendation="매수",
        confidence_level="중간",
        confidence_score=6.8,
        target_price=90000,
        target_price_range={"low": 80000, "base": 90000, "high": 105000},
        upside_potential=25.0,
        vote_result={
            "bullish": ["quant_agent", "qualitative_agent"],
            "neutral": ["macro_agent"],
            "bearish": ["risk_agent"]
        },
        key_reasons=[
            "HBM 중심 메모리 실적 턴어라운드",
            "AI 인프라 투자 확대 수혜",
            "현재 주가 저평가"
        ],
        key_risks=[
            "HBM 기술 경쟁 열위",
            "파운드리 적자 지속"
        ],
        dissenting_opinions=[
            {
                "agent": "risk_agent",
                "opinion": "보유",
                "reason": "HBM 리스크 감안 시 상승 여력 제한적"
            }
        ]
    ),
    action_guide=ActionGuideOutputTemplate(
        action_recommendation="분할 매수 권장",
        entry_strategy={
            "current_price": 72000,
            "buy_zone": {"start": 68000, "end": 72000},
            "strategy": "50% 매수 후 추가 하락 시 50% 추가"
        },
        exit_strategy={
            "target_price": 90000,
            "stop_loss": 62000
        },
        position_sizing={
            "recommended_weight": "7-10%",
            "max_weight": "15%"
        },
        monitoring_triggers=[
            {"trigger": "HBM 수율 70% 돌파", "action": "목표가 상향"}
        ],
        scenario_actions=[
            {"scenario": "Bull", "probability": "30%", "target_price": 105000}
        ]
    ),
    qa_responses=[
        QAOutputTemplate(
            question="현재 주가에서 매수해도 되는가?",
            answer="네, 현재 주가는 저평가 상태로 분할 매수 권장합니다.",
            confidence="중간",
            supporting_analysis=["밸류에이션 분석"],
            caveats=["HBM 리스크 존재"]
        )
    ],
    further_research=[
        "HBM4 개발 현황 추적",
        "엔비디아 공급망 변화 모니터링"
    ]
)


def get_output_template_json() -> dict:
    """출력 템플릿을 JSON 형태로 반환."""
    return SAMPLE_OUTPUT.model_dump()


if __name__ == "__main__":
    import json
    print("=== 투자 분석 출력 템플릿 (샘플) ===")
    print(json.dumps(get_output_template_json(), ensure_ascii=False, indent=2, default=str))
