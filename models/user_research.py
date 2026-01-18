"""User research input models - 사용자가 제공하는 참고 자료 모델."""
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class SourceType(str, Enum):
    """자료 출처 유형."""
    COMPANY_IR = "company_ir"  # 회사 IR 자료
    ANALYST_REPORT = "analyst_report"  # 증권사 리포트
    NEWS_ARTICLE = "news_article"  # 뉴스 기사
    FINANCIAL_STATEMENT = "financial_statement"  # 재무제표
    INDUSTRY_REPORT = "industry_report"  # 산업 보고서
    EARNINGS_CALL = "earnings_call"  # 실적 발표 콜
    REGULATORY_FILING = "regulatory_filing"  # 공시 자료
    SOCIAL_MEDIA = "social_media"  # SNS/커뮤니티
    EXPERT_OPINION = "expert_opinion"  # 전문가 의견
    USER_ANALYSIS = "user_analysis"  # 사용자 자체 분석
    OTHER = "other"


class BiasType(str, Enum):
    """편향 유형."""
    NONE = "none"  # 편향 없음
    BULLISH_BIAS = "bullish_bias"  # 낙관적 편향
    BEARISH_BIAS = "bearish_bias"  # 비관적 편향
    RECENCY_BIAS = "recency_bias"  # 최근성 편향
    CONFIRMATION_BIAS = "confirmation_bias"  # 확증 편향
    SURVIVORSHIP_BIAS = "survivorship_bias"  # 생존 편향
    SELECTION_BIAS = "selection_bias"  # 선택 편향
    OUTDATED = "outdated"  # 오래된 정보
    CONFLICT_OF_INTEREST = "conflict_of_interest"  # 이해충돌
    INCOMPLETE = "incomplete"  # 불완전한 정보
    UNVERIFIED = "unverified"  # 미검증 정보


class ResearchDocument(BaseModel):
    """개별 참고 자료."""
    id: str = Field(default_factory=lambda: datetime.now().strftime("%Y%m%d%H%M%S"))
    title: str = Field(..., description="자료 제목")
    source_type: SourceType = Field(..., description="자료 유형")
    source_name: str = Field(..., description="출처명 (예: 삼성증권, Bloomberg)")
    content: str = Field(..., description="자료 내용 또는 요약")

    # 메타데이터
    publish_date: Optional[datetime] = Field(None, description="발행일")
    author: Optional[str] = Field(None, description="저자/애널리스트")
    url: Optional[str] = Field(None, description="원본 링크")

    # 핵심 주장
    key_claims: list[str] = Field(default_factory=list, description="핵심 주장들")
    data_points: list[str] = Field(default_factory=list, description="인용된 데이터 포인트")
    target_price: Optional[float] = Field(None, description="목표가 (있는 경우)")
    recommendation: Optional[str] = Field(None, description="투자의견 (있는 경우)")

    # 사용자 메모
    user_notes: Optional[str] = Field(None, description="사용자 메모")
    user_trust_level: int = Field(default=5, ge=1, le=10, description="사용자가 판단한 신뢰도 (1-10)")


class BiasCheckResult(BaseModel):
    """자료 편향 검토 결과."""
    document_id: str = Field(..., description="검토 대상 자료 ID")
    document_title: str = Field(..., description="자료 제목")

    # 편향 분석
    detected_biases: list[BiasType] = Field(default_factory=list, description="발견된 편향")
    bias_severity: str = Field(default="low", description="편향 심각도: low/medium/high")
    bias_explanation: str = Field(default="", description="편향 설명")

    # 데이터 검증
    data_accuracy: float = Field(default=0.0, ge=0, le=100, description="데이터 정확도 추정 (%)")
    outdated_info: list[str] = Field(default_factory=list, description="오래된 정보 목록")
    unverifiable_claims: list[str] = Field(default_factory=list, description="검증 불가 주장")
    contradictions: list[str] = Field(default_factory=list, description="다른 자료와의 모순")

    # 권장사항
    reliability_score: float = Field(default=5.0, ge=1, le=10, description="신뢰도 점수")
    usage_recommendation: str = Field(default="", description="활용 권장사항")
    caveats: list[str] = Field(default_factory=list, description="주의사항")

    # AI 분석
    ai_notes: str = Field(default="", description="AI 분석 노트")


class UserResearchInput(BaseModel):
    """사용자 제공 연구 자료 종합."""
    ticker: str = Field(..., description="분석 대상 종목")

    # 제공된 자료들
    documents: list[ResearchDocument] = Field(default_factory=list, description="참고 자료 목록")

    # 사용자 가설
    user_hypothesis: Optional[str] = Field(None, description="사용자의 투자 가설")
    user_concerns: list[str] = Field(default_factory=list, description="사용자의 우려사항")
    user_questions: list[str] = Field(default_factory=list, description="사용자가 알고 싶은 점")

    # 투자 컨텍스트
    investment_horizon: Optional[str] = Field(None, description="투자 기간 (단기/중기/장기)")
    risk_tolerance: Optional[str] = Field(None, description="위험 허용도 (보수적/중립/공격적)")
    position_context: Optional[str] = Field(None, description="현재 포지션 상황")

    # 검토 결과
    bias_check_results: list[BiasCheckResult] = Field(
        default_factory=list,
        description="편향 검토 결과"
    )
    overall_data_quality: float = Field(default=5.0, ge=1, le=10, description="전체 자료 품질")

    # 메타데이터
    submitted_at: datetime = Field(default_factory=datetime.now)

    def get_all_key_claims(self) -> list[str]:
        """모든 자료의 핵심 주장 수집."""
        claims = []
        for doc in self.documents:
            claims.extend(doc.key_claims)
        return claims

    def get_all_data_points(self) -> list[str]:
        """모든 자료의 데이터 포인트 수집."""
        points = []
        for doc in self.documents:
            points.extend(doc.data_points)
        return points

    def get_documents_by_type(self, source_type: SourceType) -> list[ResearchDocument]:
        """특정 유형의 자료만 필터링."""
        return [doc for doc in self.documents if doc.source_type == source_type]

    def get_high_reliability_documents(self, min_score: float = 7.0) -> list[ResearchDocument]:
        """신뢰도 높은 자료만 필터링."""
        high_rel_ids = {
            result.document_id
            for result in self.bias_check_results
            if result.reliability_score >= min_score
        }
        return [doc for doc in self.documents if doc.id in high_rel_ids]


class ResearchSynthesis(BaseModel):
    """자료 종합 분석 결과."""
    ticker: str

    # 자료 요약
    total_documents: int = Field(default=0)
    documents_by_type: dict[str, int] = Field(default_factory=dict)
    average_reliability: float = Field(default=0.0)

    # 합의된 관점
    consensus_points: list[str] = Field(default_factory=list, description="자료들이 동의하는 점")
    divergent_points: list[str] = Field(default_factory=list, description="자료 간 의견 차이")

    # 데이터 기반 사실
    verified_facts: list[str] = Field(default_factory=list, description="검증된 사실")
    disputed_claims: list[str] = Field(default_factory=list, description="논쟁이 있는 주장")

    # 정보 격차
    information_gaps: list[str] = Field(default_factory=list, description="추가 조사 필요 영역")

    # 종합 평가
    overall_sentiment: str = Field(default="neutral", description="자료들의 전반적 논조")
    key_takeaways: list[str] = Field(default_factory=list, description="핵심 시사점")

    # 에이전트 활용 가이드
    recommended_focus_areas: list[str] = Field(
        default_factory=list,
        description="에이전트들이 집중해야 할 영역"
    )
