"""투자자 입력 자료 템플릿 - 실질적으로 유용한 형식.

이 모듈은 투자자가 AI 투자위원회에 제공할 자료의 표준 형식을 정의합니다.
실제 투자 의사결정에 도움이 되도록 구조화되어 있습니다.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


# =============================================================================
# 1. 기본 참고 자료 입력 템플릿
# =============================================================================

class ResearchDocumentTemplate(BaseModel):
    """개별 참고 자료 입력 형식.

    투자자가 분석에 참고할 각종 자료를 입력하는 표준 형식입니다.
    증권사 리포트, 뉴스, IR 자료 등 다양한 출처의 자료를 통일된 형식으로 입력합니다.
    """

    # 필수 정보
    title: str = Field(
        ...,
        description="자료 제목",
        example="삼성전자 2024년 하반기 전망 - AI 반도체가 이끄는 실적 턴어라운드"
    )

    source_type: str = Field(
        ...,
        description="자료 유형",
        example="analyst_report",
        json_schema_extra={
            "enum": [
                "company_ir",           # 회사 IR 자료 (실적발표, 사업설명회)
                "analyst_report",       # 증권사 애널리스트 리포트
                "news_article",         # 뉴스 기사
                "financial_statement",  # 재무제표 (감사보고서, 분기보고서)
                "industry_report",      # 산업 보고서 (시장조사 기관)
                "earnings_call",        # 실적 발표 컨퍼런스 콜 스크립트
                "regulatory_filing",    # 공시 자료 (DART, SEC filing)
                "social_media",         # SNS/커뮤니티 의견
                "expert_opinion",       # 전문가 인터뷰/칼럼
                "user_analysis",        # 투자자 본인의 분석
                "other",               # 기타
            ]
        }
    )

    source_name: str = Field(
        ...,
        description="출처명 (기관/매체명)",
        example="미래에셋증권"
    )

    content: str = Field(
        ...,
        description="자료 내용 또는 요약 (최대 5000자 권장)",
        example="""
        [투자의견] 매수 유지, 목표주가 85,000원 → 95,000원 상향

        ■ HBM3E 양산 본격화로 2024년 하반기 실적 턴어라운드 예상
        - 3분기 메모리 부문 영업이익 4.5조원 전망 (QoQ +45%)
        - HBM 매출 비중 30% 돌파 예상

        ■ AI 서버용 메모리 수요 증가가 실적 개선 핵심 동력
        - 엔비디아 H100/H200 향 HBM 공급 확대
        - 2025년 HBM 매출 20조원 전망

        ■ 리스크 요인
        - 중국 화웨이의 자체 AI칩 개발로 인한 점유율 경쟁
        - DDR5 전환 지연에 따른 범용 DRAM ASP 하락 압력
        """
    )

    # 선택 정보 - 가치 평가에 중요
    publish_date: Optional[datetime] = Field(
        None,
        description="발행일 (자료 최신성 판단에 중요)",
        example="2024-06-15"
    )

    author: Optional[str] = Field(
        None,
        description="저자/애널리스트명",
        example="김철수 애널리스트"
    )

    # 핵심 투자 정보
    key_claims: list[str] = Field(
        default_factory=list,
        description="핵심 주장 목록 (이 자료가 말하고자 하는 핵심)",
        example=[
            "HBM3E 기술력에서 SK하이닉스 대비 6개월 격차 해소",
            "2024년 하반기부터 메모리 업황 회복 본격화",
            "AI 반도체가 2025년 전체 매출의 25% 차지 전망"
        ]
    )

    data_points: list[str] = Field(
        default_factory=list,
        description="인용된 구체적 수치/데이터",
        example=[
            "2024년 예상 매출: 302조원 (YoY +12%)",
            "2024년 예상 영업이익: 35조원 (YoY +250%)",
            "HBM 시장 점유율: 2024년 말 기준 40% 목표"
        ]
    )

    target_price: Optional[float] = Field(
        None,
        description="목표 주가 (있는 경우)",
        example=95000
    )

    recommendation: Optional[str] = Field(
        None,
        description="투자의견",
        example="Buy",
        json_schema_extra={
            "enum": ["Strong Buy", "Buy", "Hold", "Sell", "Strong Sell", None]
        }
    )

    # 투자자 메모
    url: Optional[str] = Field(
        None,
        description="원본 자료 링크",
        example="https://securities.miraeasset.com/reports/123456"
    )

    user_notes: Optional[str] = Field(
        None,
        description="투자자 본인의 메모/생각",
        example="경쟁사 리포트와 비교 시 다소 낙관적인 전망으로 보임"
    )

    user_trust_level: int = Field(
        default=5,
        ge=1,
        le=10,
        description="투자자가 생각하는 이 자료의 신뢰도 (1-10)",
        example=7
    )


# =============================================================================
# 2. 투자 가설 및 질문 템플릿
# =============================================================================

class InvestmentHypothesisTemplate(BaseModel):
    """투자 가설 및 질문 입력 형식.

    투자자의 투자 아이디어와 고민을 AI 위원회에 전달하는 형식입니다.
    """

    hypothesis: Optional[str] = Field(
        None,
        description="투자 가설 - 왜 이 종목에 관심이 있는가?",
        example="""
        AI 인프라 투자 확대로 HBM 수요가 폭발적으로 증가하면서,
        삼성전자가 메모리 반도체 슈퍼사이클의 최대 수혜를 받을 것이다.
        현재 주가는 실적 턴어라운드를 충분히 반영하지 못하고 있어 저평가 상태라고 판단.
        """
    )

    bull_case: Optional[str] = Field(
        None,
        description="낙관적 시나리오 - 최선의 경우",
        example="""
        - HBM 기술 격차 해소로 엔비디아 차세대 GPU 공급업체 지위 확보
        - AI 서버 외에도 On-device AI 시장 확대로 모바일 DRAM 수요 증가
        - 파운드리 수율 개선으로 시스템 반도체 부문도 흑자 전환
        """
    )

    bear_case: Optional[str] = Field(
        None,
        description="비관적 시나리오 - 최악의 경우",
        example="""
        - HBM 경쟁에서 SK하이닉스에 지속 열위, 점유율 회복 실패
        - 중국 반도체 규제 강화로 중국 매출 급감
        - 파운드리 적자 지속으로 전사 수익성 악화
        """
    )

    concerns: list[str] = Field(
        default_factory=list,
        description="주요 우려사항 목록",
        example=[
            "SK하이닉스 대비 HBM 기술 격차가 실제로 해소되고 있는지 불확실",
            "파운드리 사업의 지속적인 적자가 메모리 수익을 갉아먹고 있음",
            "현재 주가가 이미 실적 개선을 상당부분 선반영한 것 아닌지",
            "글로벌 경기 침체 시 IT 투자 축소로 반도체 수요 감소 가능성"
        ]
    )

    questions: list[str] = Field(
        default_factory=list,
        description="AI 위원회에게 물어보고 싶은 질문들",
        example=[
            "현재 주가 수준에서 매수해도 되는 적정한 시점인가?",
            "목표 주가를 얼마로 설정하는 것이 합리적인가?",
            "삼성전자 vs SK하이닉스, 메모리 투자로 어느 쪽이 더 유망한가?",
            "언제쯤 파운드리 사업이 턴어라운드할 것으로 예상되는가?",
            "포트폴리오 비중을 얼마나 가져가는 것이 적절한가?"
        ]
    )


# =============================================================================
# 3. 투자 컨텍스트 템플릿
# =============================================================================

class InvestmentContextTemplate(BaseModel):
    """투자 컨텍스트 입력 형식.

    투자자의 상황과 제약조건을 전달하여 맞춤형 분석을 받습니다.
    """

    investment_horizon: str = Field(
        default="중기 (1-3년)",
        description="투자 기간",
        json_schema_extra={
            "enum": ["단기 (1년 이내)", "중기 (1-3년)", "장기 (3년 이상)"]
        }
    )

    risk_tolerance: str = Field(
        default="중립",
        description="위험 허용도",
        json_schema_extra={
            "enum": ["보수적", "중립", "공격적"]
        }
    )

    position_context: Optional[str] = Field(
        None,
        description="현재 포지션 상황",
        example="현재 포트폴리오의 5% 보유 중. 추가 매수 검토 중이며 최대 10%까지 확대 고려"
    )

    investment_style: Optional[str] = Field(
        None,
        description="투자 스타일",
        example="성장주 중심 투자, 배당보다는 자본 이득 선호"
    )

    constraints: list[str] = Field(
        default_factory=list,
        description="투자 제약사항",
        example=[
            "월 추가 투자금 200만원 한도",
            "개별 종목 비중 15% 이내 유지",
            "국내 주식만 투자 가능"
        ]
    )


# =============================================================================
# 4. 전체 입력 템플릿 (통합)
# =============================================================================

class FullInputTemplate(BaseModel):
    """투자 분석 요청 전체 입력 형식.

    AI 투자위원회에 분석을 요청할 때 제출하는 전체 데이터 형식입니다.
    """

    # 분석 대상
    ticker: str = Field(
        ...,
        description="분석 대상 종목 코드",
        example="005930.KS"
    )

    company_name: Optional[str] = Field(
        None,
        description="회사명",
        example="삼성전자"
    )

    # 참고 자료들
    documents: list[ResearchDocumentTemplate] = Field(
        default_factory=list,
        description="참고 자료 목록 (최소 1개 이상 권장)"
    )

    # 투자 가설
    hypothesis: InvestmentHypothesisTemplate = Field(
        default_factory=InvestmentHypothesisTemplate,
        description="투자 가설 및 질문"
    )

    # 투자 컨텍스트
    context: InvestmentContextTemplate = Field(
        default_factory=InvestmentContextTemplate,
        description="투자 컨텍스트"
    )

    # 추가 요청사항
    focus_areas: list[str] = Field(
        default_factory=list,
        description="특별히 집중 분석을 원하는 영역",
        example=["HBM 경쟁력 분석", "파운드리 사업 전망", "배당 정책 변화"]
    )

    additional_context: Optional[str] = Field(
        None,
        description="기타 추가 정보",
        example="최근 언론에서 삼성전자의 HBM 수율 문제가 보도되었는데, 실제 심각성이 궁금합니다."
    )


# =============================================================================
# 샘플 데이터 (실제 사용 예시)
# =============================================================================

SAMPLE_INPUT = FullInputTemplate(
    ticker="005930.KS",
    company_name="삼성전자",
    documents=[
        ResearchDocumentTemplate(
            title="삼성전자 2024년 하반기 전망 - HBM이 이끄는 실적 턴어라운드",
            source_type="analyst_report",
            source_name="미래에셋증권",
            content="""
            [투자의견] 매수, 목표주가 95,000원

            ■ 핵심 투자포인트
            1. HBM3E 양산 본격화로 메모리 실적 턴어라운드
            2. AI 서버 수요 증가로 고부가 메모리 비중 확대
            3. 2025년 HBM 매출 20조원 전망

            ■ 실적 전망
            - 2024년 매출 302조원 (YoY +12%)
            - 2024년 영업이익 35조원 (YoY +250%)

            ■ 리스크 요인
            - SK하이닉스 대비 HBM 기술 격차
            - 파운드리 사업 지속 적자
            """,
            publish_date=datetime(2024, 6, 15),
            author="김애널 애널리스트",
            key_claims=[
                "HBM3E 양산으로 하반기 실적 턴어라운드",
                "2025년 HBM 매출 20조원 전망",
                "목표주가 95,000원 제시"
            ],
            data_points=[
                "2024년 예상 매출: 302조원",
                "2024년 예상 영업이익: 35조원",
                "HBM 매출 비중: 30% 전망"
            ],
            target_price=95000,
            recommendation="Buy",
            user_trust_level=7,
            user_notes="증권사 리포트라 다소 낙관적일 수 있음"
        ),
        ResearchDocumentTemplate(
            title="삼성전자 HBM 수율 문제 보도",
            source_type="news_article",
            source_name="매일경제",
            content="""
            삼성전자의 HBM3E 수율이 목표치를 하회하는 것으로 알려졌다.
            업계에 따르면 삼성전자의 HBM3E 수율은 50-60% 수준으로,
            SK하이닉스의 80% 대비 크게 낮은 상황이다.

            이에 따라 엔비디아의 차세대 GPU인 B100 향 HBM 공급에서
            삼성전자가 배제될 수 있다는 우려가 제기되고 있다.
            """,
            publish_date=datetime(2024, 6, 20),
            key_claims=[
                "삼성전자 HBM3E 수율 50-60% 수준",
                "SK하이닉스 대비 20%p 이상 수율 격차",
                "엔비디아 B100 공급 배제 우려"
            ],
            user_trust_level=5,
            user_notes="언론 보도라 정확성 검증 필요"
        )
    ],
    hypothesis=InvestmentHypothesisTemplate(
        hypothesis="AI 인프라 투자 확대로 HBM 수요 폭발, 삼성전자 실적 턴어라운드 예상",
        bull_case="HBM 기술 격차 해소, 엔비디아 공급업체 지위 확보",
        bear_case="HBM 경쟁 열위 지속, 파운드리 적자 지속",
        concerns=[
            "HBM 수율 문제 실제 심각성",
            "SK하이닉스 대비 경쟁력",
            "파운드리 사업 전망"
        ],
        questions=[
            "현재 주가에서 매수해도 되는가?",
            "적정 목표 주가는?",
            "삼성전자 vs SK하이닉스 비교"
        ]
    ),
    context=InvestmentContextTemplate(
        investment_horizon="중기 (1-3년)",
        risk_tolerance="중립",
        position_context="현재 포트폴리오의 5% 보유 중, 추가 매수 검토"
    ),
    focus_areas=["HBM 경쟁력", "파운드리 전망"]
)


def get_input_template_json() -> dict:
    """입력 템플릿을 JSON 형태로 반환."""
    return SAMPLE_INPUT.model_dump()


if __name__ == "__main__":
    import json
    print("=== 투자 분석 입력 템플릿 (샘플) ===")
    print(json.dumps(get_input_template_json(), ensure_ascii=False, indent=2, default=str))
