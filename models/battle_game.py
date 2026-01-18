"""AI vs Human 투자 대결 게임 모델.

AI 투자위원회와 인간 투자자의 분석 대결을 게임화하여
흥미롭게 비교하고 학습할 수 있는 시스템입니다.
"""
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import uuid4
from pydantic import BaseModel, Field


class BattleStatus(str, Enum):
    """대결 상태."""
    PENDING = "pending"           # 대기 중 (인간 분석 입력 대기)
    IN_PROGRESS = "in_progress"   # 진행 중 (AI 분석 중)
    JUDGING = "judging"           # 심판 중 (결과 대기)
    COMPLETED = "completed"       # 완료
    EXPIRED = "expired"           # 만료 (검증 기간 종료)


class BattleCategory(str, Enum):
    """대결 카테고리."""
    TARGET_PRICE = "target_price"           # 목표가 대결
    DIRECTION = "direction"                 # 방향성 대결 (상승/하락)
    RISK_IDENTIFICATION = "risk"            # 리스크 식별
    TIMING = "timing"                       # 매매 타이밍
    OVERALL = "overall"                     # 종합 대결


class HumanAnalysis(BaseModel):
    """인간 투자자의 분석."""

    analyst_name: str = Field(..., description="분석자 이름/닉네임")
    analyst_experience: str = Field(
        default="intermediate",
        description="투자 경험",
        json_schema_extra={"enum": ["beginner", "intermediate", "expert", "professional"]}
    )

    # 투자 의견
    recommendation: str = Field(
        ...,
        description="투자 의견",
        json_schema_extra={"enum": ["Strong Buy", "Buy", "Hold", "Sell", "Strong Sell"]}
    )

    target_price: float = Field(..., description="목표 주가")

    confidence_score: int = Field(
        ...,
        ge=1,
        le=10,
        description="확신도 (1-10)"
    )

    time_horizon: str = Field(
        ...,
        description="투자 기간",
        json_schema_extra={"enum": ["1개월", "3개월", "6개월", "1년", "1년 이상"]}
    )

    # 분석 근거
    bull_thesis: list[str] = Field(
        default_factory=list,
        description="매수 근거 (최소 3개)"
    )

    bear_thesis: list[str] = Field(
        default_factory=list,
        description="매도/리스크 근거 (최소 3개)"
    )

    key_catalysts: list[str] = Field(
        default_factory=list,
        description="핵심 촉매/이벤트"
    )

    key_risks: list[str] = Field(
        default_factory=list,
        description="주요 리스크"
    )

    analysis_summary: str = Field(
        ...,
        description="분석 요약 (200자 이상)"
    )

    # 메타 정보
    analysis_time_minutes: Optional[int] = Field(
        None,
        description="분석 소요 시간 (분)"
    )

    sources_used: list[str] = Field(
        default_factory=list,
        description="참고한 자료 출처"
    )


class AIAnalysisSummary(BaseModel):
    """AI 투자위원회 분석 요약 (대결용)."""

    recommendation: str = Field(..., description="투자 의견")
    target_price: float = Field(..., description="목표 주가")
    confidence_score: float = Field(..., description="확신도")

    bull_thesis: list[str] = Field(default_factory=list, description="매수 근거")
    bear_thesis: list[str] = Field(default_factory=list, description="매도/리스크 근거")
    key_catalysts: list[str] = Field(default_factory=list, description="핵심 촉매")
    key_risks: list[str] = Field(default_factory=list, description="주요 리스크")

    analysis_summary: str = Field(..., description="분석 요약")

    # AI 특성
    agents_involved: list[str] = Field(default_factory=list, description="참여 에이전트")
    debate_rounds: int = Field(default=3, description="토론 라운드 수")
    consensus_level: str = Field(..., description="합의 수준")


class BattleRound(BaseModel):
    """개별 대결 라운드 (카테고리별 승부)."""

    category: BattleCategory = Field(..., description="대결 카테고리")
    category_name_kr: str = Field(..., description="카테고리 한글명")

    # 각자의 주장
    human_position: str = Field(..., description="인간의 주장")
    ai_position: str = Field(..., description="AI의 주장")

    # 점수 (심판 후)
    human_score: Optional[int] = Field(None, ge=0, le=100, description="인간 점수")
    ai_score: Optional[int] = Field(None, ge=0, le=100, description="AI 점수")

    # 평가 (실제 결과 또는 논리성 평가)
    winner: Optional[str] = Field(None, description="승자 (human/ai/draw)")
    judge_comment: Optional[str] = Field(None, description="심판 코멘트")


class BattleResult(BaseModel):
    """대결 결과."""

    # 최종 승자
    final_winner: str = Field(..., description="최종 승자 (human/ai/draw)")

    # 점수
    human_total_score: int = Field(..., description="인간 총점")
    ai_total_score: int = Field(..., description="AI 총점")

    # 카테고리별 결과
    round_results: list[BattleRound] = Field(
        default_factory=list,
        description="라운드별 결과"
    )

    # 실제 시장 결과 (사후 검증)
    actual_price_after_1m: Optional[float] = Field(None, description="1개월 후 실제 가격")
    actual_price_after_3m: Optional[float] = Field(None, description="3개월 후 실제 가격")
    actual_price_after_6m: Optional[float] = Field(None, description="6개월 후 실제 가격")

    # 정확도 평가
    human_target_accuracy: Optional[float] = Field(None, description="인간 목표가 정확도 %")
    ai_target_accuracy: Optional[float] = Field(None, description="AI 목표가 정확도 %")
    human_direction_correct: Optional[bool] = Field(None, description="인간 방향성 정확")
    ai_direction_correct: Optional[bool] = Field(None, description="AI 방향성 정확")

    # 학습 포인트
    lessons_learned: list[str] = Field(
        default_factory=list,
        description="이번 대결에서 배운 점"
    )

    # 배지/보상
    badges_earned: list[str] = Field(
        default_factory=list,
        description="획득한 배지"
    )


class InvestmentBattle(BaseModel):
    """AI vs Human 투자 대결."""

    # 대결 ID
    battle_id: str = Field(default_factory=lambda: str(uuid4())[:8])

    # 대결 상태
    status: BattleStatus = Field(default=BattleStatus.PENDING)

    # 대결 대상
    ticker: str = Field(..., description="종목 코드")
    company_name: str = Field(..., description="회사명")
    start_price: float = Field(..., description="대결 시작 시점 주가")

    # 대결 일시
    created_at: datetime = Field(default_factory=datetime.now)
    battle_date: datetime = Field(default_factory=datetime.now)
    verification_date: Optional[datetime] = Field(None, description="검증 예정일")

    # 참가자
    human_analysis: Optional[HumanAnalysis] = Field(None, description="인간 분석")
    ai_analysis: Optional[AIAnalysisSummary] = Field(None, description="AI 분석")

    # 대결 결과
    result: Optional[BattleResult] = Field(None, description="대결 결과")

    # 통계
    spectator_votes: dict = Field(
        default_factory=lambda: {"human": 0, "ai": 0},
        description="관전자 투표"
    )

    comments: list[dict] = Field(default_factory=list, description="댓글")


class BattleStatistics(BaseModel):
    """대결 통계 (전적)."""

    user_id: str = Field(..., description="사용자 ID")
    username: str = Field(..., description="사용자명")

    # 전적
    total_battles: int = Field(default=0)
    wins: int = Field(default=0)
    losses: int = Field(default=0)
    draws: int = Field(default=0)

    win_rate: float = Field(default=0.0, description="승률 %")

    # 카테고리별 전적
    category_stats: dict[str, dict] = Field(
        default_factory=dict,
        description="카테고리별 통계"
    )

    # 정확도
    avg_target_price_accuracy: float = Field(default=0.0)
    direction_accuracy_rate: float = Field(default=0.0)

    # 랭킹
    rank: int = Field(default=0, description="전체 순위")
    tier: str = Field(default="Bronze", description="티어")

    # 배지
    badges: list[dict] = Field(default_factory=list, description="획득 배지")

    # 연속 기록
    current_streak: int = Field(default=0, description="현재 연승/연패")
    best_streak: int = Field(default=0, description="최고 연승")


class Leaderboard(BaseModel):
    """리더보드."""

    period: str = Field(..., description="기간 (weekly/monthly/all-time)")
    updated_at: datetime = Field(default_factory=datetime.now)

    # 종합 순위
    overall_rankings: list[dict] = Field(
        default_factory=list,
        description="종합 순위",
        example=[
            {"rank": 1, "username": "투자고수", "wins": 45, "win_rate": 75.0, "tier": "Diamond"},
            {"rank": 2, "username": "가치투자자", "wins": 38, "win_rate": 68.5, "tier": "Platinum"}
        ]
    )

    # AI 상대 최다 승리
    most_ai_wins: list[dict] = Field(default_factory=list)

    # 정확도 랭킹
    accuracy_rankings: list[dict] = Field(default_factory=list)

    # 카테고리별 챔피언
    category_champions: dict[str, dict] = Field(default_factory=dict)


class BattleChallenge(BaseModel):
    """대결 도전장."""

    challenge_id: str = Field(default_factory=lambda: str(uuid4())[:8])
    challenger: str = Field(..., description="도전자")

    # 대결 조건
    ticker: str = Field(..., description="종목")
    battle_type: str = Field(
        default="standard",
        description="대결 유형",
        json_schema_extra={"enum": ["standard", "speed", "deep_dive", "contrarian"]}
    )

    time_limit_minutes: Optional[int] = Field(
        None,
        description="시간 제한 (분)"
    )

    stakes: str = Field(
        default="normal",
        description="배팅 크기",
        json_schema_extra={"enum": ["practice", "normal", "high", "championship"]}
    )

    # 상태
    created_at: datetime = Field(default_factory=datetime.now)
    expires_at: datetime = Field(...)
    is_active: bool = Field(default=True)


# =============================================================================
# 티어 및 배지 시스템
# =============================================================================

TIERS = {
    "Bronze": {"min_wins": 0, "icon": "🥉", "color": "#CD7F32"},
    "Silver": {"min_wins": 10, "icon": "🥈", "color": "#C0C0C0"},
    "Gold": {"min_wins": 25, "icon": "🥇", "color": "#FFD700"},
    "Platinum": {"min_wins": 50, "icon": "💎", "color": "#E5E4E2"},
    "Diamond": {"min_wins": 100, "icon": "💠", "color": "#B9F2FF"},
    "Master": {"min_wins": 200, "icon": "👑", "color": "#FF6B6B"},
    "Grandmaster": {"min_wins": 500, "icon": "🏆", "color": "#9B59B6"},
}

BADGES = {
    # 승리 배지
    "first_blood": {"name": "첫 승리", "icon": "🩸", "description": "AI와의 첫 대결에서 승리"},
    "ai_slayer": {"name": "AI 슬레이어", "icon": "⚔️", "description": "AI를 10회 격파"},
    "ai_nemesis": {"name": "AI 천적", "icon": "🔱", "description": "AI를 50회 격파"},
    "unbeatable": {"name": "무적", "icon": "🛡️", "description": "10연승 달성"},

    # 정확도 배지
    "sniper": {"name": "스나이퍼", "icon": "🎯", "description": "목표가 오차 5% 이내 적중"},
    "prophet": {"name": "예언자", "icon": "🔮", "description": "방향성 10연속 적중"},
    "eagle_eye": {"name": "독수리 눈", "icon": "🦅", "description": "리스크 사전 식별 성공"},

    # 특수 배지
    "contrarian": {"name": "역발상 투자자", "icon": "🔄", "description": "AI와 반대 의견으로 승리"},
    "speed_demon": {"name": "스피드 악마", "icon": "⚡", "description": "스피드 대결에서 승리"},
    "deep_thinker": {"name": "깊은 사색가", "icon": "🧠", "description": "딥다이브 대결에서 승리"},
    "comeback_king": {"name": "역전왕", "icon": "👑", "description": "3연패 후 승리"},

    # 참여 배지
    "regular": {"name": "단골", "icon": "☕", "description": "50회 대결 참여"},
    "veteran": {"name": "베테랑", "icon": "🎖️", "description": "100회 대결 참여"},
    "legend": {"name": "레전드", "icon": "🌟", "description": "500회 대결 참여"},
}

BATTLE_TYPES = {
    "standard": {
        "name": "표준 대결",
        "description": "30분 시간 제한, 종합 분석 비교",
        "time_limit": 30,
        "points": 100
    },
    "speed": {
        "name": "스피드 대결",
        "description": "10분 내 빠른 분석, 핵심만 비교",
        "time_limit": 10,
        "points": 50
    },
    "deep_dive": {
        "name": "딥다이브 대결",
        "description": "시간 무제한, 심층 분석 비교",
        "time_limit": None,
        "points": 200
    },
    "contrarian": {
        "name": "역발상 대결",
        "description": "AI 의견의 반대로 분석",
        "time_limit": 30,
        "points": 150
    }
}


def calculate_tier(wins: int) -> str:
    """승리 수에 따른 티어 계산."""
    current_tier = "Bronze"
    for tier_name, tier_info in TIERS.items():
        if wins >= tier_info["min_wins"]:
            current_tier = tier_name
    return current_tier


def calculate_target_accuracy(predicted: float, actual: float) -> float:
    """목표가 정확도 계산 (%)."""
    if actual == 0:
        return 0.0
    error = abs(predicted - actual) / actual * 100
    accuracy = max(0, 100 - error)
    return round(accuracy, 1)


def determine_direction(start_price: float, end_price: float) -> str:
    """방향성 결정."""
    if end_price > start_price * 1.02:
        return "up"
    elif end_price < start_price * 0.98:
        return "down"
    return "flat"
