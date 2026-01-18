"""유튜브 콘텐츠 생성 모델.

시청자 성향별로 맞춤화된 다양한 콘텐츠를 생성하기 위한 모델입니다.
"""
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import uuid4
from pydantic import BaseModel, Field


# =============================================================================
# 시청자 페르소나 (Viewer Personas)
# =============================================================================

class ViewerPersona(str, Enum):
    """시청자 페르소나 - 콘텐츠 타겟 유형."""

    # 투자 경험 기반
    ABSOLUTE_BEGINNER = "absolute_beginner"      # 주식 왕초보 (계좌도 없음)
    BEGINNER = "beginner"                        # 초보 투자자 (1년 미만)
    INTERMEDIATE = "intermediate"                # 중급 투자자 (1-5년)
    ADVANCED = "advanced"                        # 고급 투자자 (5년+)
    PROFESSIONAL = "professional"                # 전문 투자자/기관

    # 투자 스타일 기반
    VALUE_INVESTOR = "value_investor"            # 가치투자자 (버핏 스타일)
    GROWTH_INVESTOR = "growth_investor"          # 성장주 투자자
    DIVIDEND_HUNTER = "dividend_hunter"          # 배당주 투자자
    MOMENTUM_TRADER = "momentum_trader"          # 모멘텀/추세 트레이더
    SWING_TRADER = "swing_trader"                # 스윙 트레이더
    DAY_TRADER = "day_trader"                    # 데이 트레이더

    # 관심사 기반
    TECH_ENTHUSIAST = "tech_enthusiast"          # 기술주/테크 마니아
    DIVIDEND_SEEKER = "dividend_seeker"          # 안정적 배당 추구
    HIGH_RISK_TAKER = "high_risk_taker"          # 고위험 고수익 추구
    PASSIVE_INVESTOR = "passive_investor"        # 장기 패시브 투자자

    # 콘텐츠 선호 기반
    DATA_NERD = "data_nerd"                      # 데이터/숫자 마니아
    STORY_LOVER = "story_lover"                  # 스토리/서사 선호
    QUICK_LEARNER = "quick_learner"              # 숏폼/요약 선호
    DEEP_DIVER = "deep_diver"                    # 딥다이브/심층 분석 선호
    ENTERTAINMENT_SEEKER = "entertainment"       # 재미/오락 추구


class ContentFormat(str, Enum):
    """콘텐츠 포맷."""

    # 길이별
    SHORTS = "shorts"                    # 60초 이하 숏폼
    SHORT_VIDEO = "short_video"          # 5-10분 짧은 영상
    STANDARD_VIDEO = "standard_video"    # 15-25분 표준 영상
    LONG_FORM = "long_form"              # 30분+ 롱폼
    LIVE_STREAM = "live_stream"          # 라이브 스트리밍

    # 형식별
    TALKING_HEAD = "talking_head"        # 진행자 중심
    SCREEN_SHARE = "screen_share"        # 화면 공유 중심
    ANIMATION = "animation"              # 애니메이션/모션그래픽
    DOCUMENTARY = "documentary"          # 다큐멘터리 스타일
    DEBATE_SHOW = "debate_show"          # 토론쇼 형식
    NEWS_STYLE = "news_style"            # 뉴스 형식
    TUTORIAL = "tutorial"                # 튜토리얼/교육
    REACTION = "reaction"                # 리액션 영상


class ContentTone(str, Enum):
    """콘텐츠 톤앤매너."""

    SERIOUS_PROFESSIONAL = "serious"      # 진지하고 전문적
    CASUAL_FRIENDLY = "casual"            # 캐주얼하고 친근한
    ENTERTAINING_FUN = "entertaining"     # 재미있고 유쾌한
    DRAMATIC_INTENSE = "dramatic"         # 드라마틱하고 긴장감
    EDUCATIONAL_CALM = "educational"      # 교육적이고 차분한
    PROVOCATIVE_BOLD = "provocative"      # 도발적이고 대담한
    EMPATHETIC_WARM = "empathetic"        # 공감적이고 따뜻한


# =============================================================================
# 콘텐츠 유형 (Content Types)
# =============================================================================

class ContentType(str, Enum):
    """콘텐츠 유형."""

    # AI vs Human 대결 시리즈
    AI_BATTLE_FULL = "ai_battle_full"              # 풀버전 대결
    AI_BATTLE_HIGHLIGHTS = "ai_battle_highlights"  # 하이라이트
    AI_BATTLE_RESULT = "ai_battle_result"          # 결과 발표

    # AI 투자위원회 시리즈
    COMMITTEE_DEBATE = "committee_debate"          # 위원회 토론
    DEVILS_ADVOCATE = "devils_advocate"            # 악마의 변호인 특집
    AGENT_SPOTLIGHT = "agent_spotlight"            # 특정 에이전트 심층

    # 종목 분석 시리즈
    STOCK_DEEP_DIVE = "stock_deep_dive"           # 종목 심층 분석
    STOCK_QUICK_TAKE = "stock_quick_take"         # 종목 퀵 분석
    EARNINGS_REVIEW = "earnings_review"            # 실적 리뷰
    STOCK_COMPARISON = "stock_comparison"          # 종목 비교

    # 자료 검증 시리즈
    REPORT_FACT_CHECK = "report_fact_check"       # 리포트 팩트체크
    NEWS_VERIFICATION = "news_verification"        # 뉴스 검증
    YOUTUBER_REVIEW = "youtuber_review"           # 유튜버 분석 리뷰

    # 교육 콘텐츠
    INVESTING_101 = "investing_101"                # 투자 기초
    ANALYSIS_TUTORIAL = "analysis_tutorial"        # 분석 방법 튜토리얼
    TERM_EXPLAINED = "term_explained"              # 용어 설명

    # 이벤트/특집
    MARKET_OUTLOOK = "market_outlook"              # 시장 전망
    SECTOR_ANALYSIS = "sector_analysis"            # 섹터 분석
    CRISIS_RESPONSE = "crisis_response"            # 위기 대응 특집
    PREDICTION_REVIEW = "prediction_review"        # 예측 적중률 리뷰


# =============================================================================
# 콘텐츠 구성 요소
# =============================================================================

class ThumbnailSpec(BaseModel):
    """썸네일 사양."""

    headline: str = Field(..., description="메인 헤드라인 (최대 20자)")
    sub_headline: Optional[str] = Field(None, description="서브 헤드라인")

    style: str = Field(
        default="dramatic",
        description="스타일",
        json_schema_extra={"enum": ["dramatic", "clean", "meme", "news", "versus", "question"]}
    )

    color_scheme: str = Field(
        default="red_black",
        description="색상 테마",
        json_schema_extra={"enum": ["red_black", "blue_white", "green_gold", "purple_pink", "orange_dark"]}
    )

    elements: list[str] = Field(
        default_factory=list,
        description="포함 요소",
        example=["stock_chart", "ai_robot", "human_face", "money_icon", "arrow_up", "arrow_down", "question_mark"]
    )

    emotion: str = Field(
        default="surprised",
        description="표현 감정",
        json_schema_extra={"enum": ["surprised", "serious", "happy", "worried", "confident", "thinking"]}
    )

    text_elements: list[dict] = Field(
        default_factory=list,
        description="텍스트 요소들",
        example=[
            {"text": "AI가 예측한", "position": "top", "size": "medium"},
            {"text": "삼성전자", "position": "center", "size": "large", "highlight": True},
            {"text": "목표가 충격!", "position": "bottom", "size": "medium"}
        ]
    )


class ScriptSection(BaseModel):
    """스크립트 섹션."""

    section_type: str = Field(
        ...,
        description="섹션 유형",
        json_schema_extra={"enum": [
            "hook", "intro", "context", "main_content", "analysis",
            "debate", "reaction", "summary", "cta", "outro"
        ]}
    )

    duration_seconds: int = Field(..., description="예상 길이 (초)")

    script_text: str = Field(..., description="대본 텍스트")

    visual_direction: str = Field(
        default="",
        description="영상 연출 지시"
    )

    on_screen_text: list[str] = Field(
        default_factory=list,
        description="화면에 표시할 텍스트"
    )

    b_roll_suggestions: list[str] = Field(
        default_factory=list,
        description="B-roll 제안"
    )

    sound_effects: list[str] = Field(
        default_factory=list,
        description="효과음 제안"
    )

    music_mood: Optional[str] = Field(
        None,
        description="BGM 분위기"
    )


class FullScript(BaseModel):
    """전체 스크립트."""

    title: str = Field(..., description="영상 제목")
    description: str = Field(..., description="영상 설명")
    tags: list[str] = Field(default_factory=list, description="태그")

    total_duration_seconds: int = Field(..., description="총 길이 (초)")

    sections: list[ScriptSection] = Field(
        default_factory=list,
        description="스크립트 섹션들"
    )

    key_timestamps: list[dict] = Field(
        default_factory=list,
        description="주요 타임스탬프",
        example=[
            {"time": "0:00", "label": "AI vs 인간 대결 시작"},
            {"time": "3:25", "label": "AI 분석 결과"},
            {"time": "7:10", "label": "승자 발표"}
        ]
    )

    end_screen_suggestions: list[str] = Field(
        default_factory=list,
        description="엔드스크린 추천 영상"
    )


class VisualAsset(BaseModel):
    """시각 자료."""

    asset_type: str = Field(
        ...,
        description="자료 유형",
        json_schema_extra={"enum": [
            "chart", "table", "infographic", "comparison",
            "timeline", "scorecard", "quote_card", "stat_highlight"
        ]}
    )

    title: str = Field(..., description="자료 제목")
    data: dict = Field(default_factory=dict, description="데이터")
    style_notes: str = Field(default="", description="스타일 노트")


# =============================================================================
# 완성된 콘텐츠 패키지
# =============================================================================

class YouTubeContentPackage(BaseModel):
    """유튜브 콘텐츠 패키지 - 영상 제작에 필요한 모든 것."""

    # 메타 정보
    content_id: str = Field(default_factory=lambda: str(uuid4())[:8])
    created_at: datetime = Field(default_factory=datetime.now)

    # 타겟 설정
    target_persona: ViewerPersona = Field(..., description="타겟 시청자")
    content_type: ContentType = Field(..., description="콘텐츠 유형")
    content_format: ContentFormat = Field(..., description="콘텐츠 포맷")
    content_tone: ContentTone = Field(..., description="콘텐츠 톤")

    # 기본 정보
    ticker: str = Field(..., description="종목 코드")
    company_name: str = Field(..., description="회사명")

    # 제목 옵션들
    title_options: list[dict] = Field(
        default_factory=list,
        description="제목 옵션들 (A/B 테스트용)",
        example=[
            {"title": "AI가 예측한 삼성전자 목표가, 충격적인 결과", "style": "curiosity"},
            {"title": "삼성전자 AI vs 인간 분석 대결 결과 공개!", "style": "announcement"},
            {"title": "[긴급] AI 투자위원회가 삼성전자에 내린 판결", "style": "urgent"}
        ]
    )

    # 썸네일
    thumbnail_specs: list[ThumbnailSpec] = Field(
        default_factory=list,
        description="썸네일 사양들 (A/B 테스트용)"
    )

    # 스크립트
    full_script: Optional[FullScript] = Field(None, description="전체 스크립트")

    # 시각 자료
    visual_assets: list[VisualAsset] = Field(
        default_factory=list,
        description="시각 자료들"
    )

    # 하이라이트 클립
    highlight_clips: list[dict] = Field(
        default_factory=list,
        description="하이라이트 클립 정보",
        example=[
            {"start": 125, "end": 180, "title": "악마의 변호인 반박 장면", "for_shorts": True},
            {"start": 420, "end": 480, "title": "최종 결과 발표", "for_shorts": True}
        ]
    )

    # 커뮤니티 포스트
    community_post: Optional[dict] = Field(
        None,
        description="커뮤니티 탭 포스트",
        example={
            "text": "새 영상 업로드! AI가 분석한 삼성전자, 결과가 어떻게 됐을까요?",
            "poll": {"question": "AI vs 인간, 누가 이길까요?", "options": ["AI 승", "인간 승", "무승부"]}
        }
    )

    # SEO
    seo_keywords: list[str] = Field(default_factory=list, description="SEO 키워드")
    hashtags: list[str] = Field(default_factory=list, description="해시태그")


# =============================================================================
# 페르소나별 콘텐츠 설정
# =============================================================================

PERSONA_CONTENT_SETTINGS = {
    ViewerPersona.ABSOLUTE_BEGINNER: {
        "preferred_formats": [ContentFormat.SHORT_VIDEO, ContentFormat.TUTORIAL],
        "preferred_tone": ContentTone.EMPATHETIC_WARM,
        "complexity_level": 1,
        "jargon_allowed": False,
        "example_heavy": True,
        "pace": "slow",
        "hook_style": "relatable_problem",
        "cta_style": "gentle_encouragement",
    },
    ViewerPersona.BEGINNER: {
        "preferred_formats": [ContentFormat.STANDARD_VIDEO, ContentFormat.TUTORIAL],
        "preferred_tone": ContentTone.EDUCATIONAL_CALM,
        "complexity_level": 2,
        "jargon_allowed": False,
        "example_heavy": True,
        "pace": "moderate",
        "hook_style": "curiosity",
        "cta_style": "learning_journey",
    },
    ViewerPersona.INTERMEDIATE: {
        "preferred_formats": [ContentFormat.STANDARD_VIDEO, ContentFormat.DEBATE_SHOW],
        "preferred_tone": ContentTone.CASUAL_FRIENDLY,
        "complexity_level": 3,
        "jargon_allowed": True,
        "example_heavy": False,
        "pace": "moderate",
        "hook_style": "insight_tease",
        "cta_style": "community",
    },
    ViewerPersona.ADVANCED: {
        "preferred_formats": [ContentFormat.LONG_FORM, ContentFormat.DEBATE_SHOW],
        "preferred_tone": ContentTone.SERIOUS_PROFESSIONAL,
        "complexity_level": 4,
        "jargon_allowed": True,
        "example_heavy": False,
        "pace": "fast",
        "hook_style": "contrarian_take",
        "cta_style": "discussion",
    },
    ViewerPersona.PROFESSIONAL: {
        "preferred_formats": [ContentFormat.LONG_FORM, ContentFormat.DOCUMENTARY],
        "preferred_tone": ContentTone.SERIOUS_PROFESSIONAL,
        "complexity_level": 5,
        "jargon_allowed": True,
        "example_heavy": False,
        "pace": "fast",
        "hook_style": "data_driven",
        "cta_style": "professional_network",
    },
    ViewerPersona.DATA_NERD: {
        "preferred_formats": [ContentFormat.LONG_FORM, ContentFormat.SCREEN_SHARE],
        "preferred_tone": ContentTone.SERIOUS_PROFESSIONAL,
        "complexity_level": 5,
        "jargon_allowed": True,
        "data_visualization_heavy": True,
        "pace": "moderate",
        "hook_style": "surprising_statistic",
        "cta_style": "data_download",
    },
    ViewerPersona.STORY_LOVER: {
        "preferred_formats": [ContentFormat.DOCUMENTARY, ContentFormat.STANDARD_VIDEO],
        "preferred_tone": ContentTone.DRAMATIC_INTENSE,
        "complexity_level": 3,
        "narrative_driven": True,
        "pace": "cinematic",
        "hook_style": "story_opening",
        "cta_style": "next_episode",
    },
    ViewerPersona.QUICK_LEARNER: {
        "preferred_formats": [ContentFormat.SHORTS, ContentFormat.SHORT_VIDEO],
        "preferred_tone": ContentTone.ENTERTAINING_FUN,
        "complexity_level": 2,
        "bullet_point_heavy": True,
        "pace": "very_fast",
        "hook_style": "instant_value",
        "cta_style": "quick_follow",
    },
    ViewerPersona.ENTERTAINMENT_SEEKER: {
        "preferred_formats": [ContentFormat.SHORTS, ContentFormat.REACTION],
        "preferred_tone": ContentTone.ENTERTAINING_FUN,
        "complexity_level": 2,
        "meme_friendly": True,
        "pace": "dynamic",
        "hook_style": "shock_value",
        "cta_style": "entertainment",
    },
    ViewerPersona.HIGH_RISK_TAKER: {
        "preferred_formats": [ContentFormat.SHORT_VIDEO, ContentFormat.LIVE_STREAM],
        "preferred_tone": ContentTone.PROVOCATIVE_BOLD,
        "complexity_level": 3,
        "risk_focused": True,
        "pace": "fast",
        "hook_style": "bold_prediction",
        "cta_style": "action_oriented",
    },
    ViewerPersona.VALUE_INVESTOR: {
        "preferred_formats": [ContentFormat.LONG_FORM, ContentFormat.DOCUMENTARY],
        "preferred_tone": ContentTone.EDUCATIONAL_CALM,
        "complexity_level": 4,
        "fundamental_focused": True,
        "pace": "thoughtful",
        "hook_style": "timeless_principle",
        "cta_style": "long_term_thinking",
    },
    ViewerPersona.GROWTH_INVESTOR: {
        "preferred_formats": [ContentFormat.STANDARD_VIDEO, ContentFormat.NEWS_STYLE],
        "preferred_tone": ContentTone.CASUAL_FRIENDLY,
        "complexity_level": 3,
        "trend_focused": True,
        "pace": "energetic",
        "hook_style": "future_vision",
        "cta_style": "growth_mindset",
    },
}


# =============================================================================
# 콘텐츠 유형별 템플릿
# =============================================================================

CONTENT_TYPE_TEMPLATES = {
    ContentType.AI_BATTLE_FULL: {
        "duration_range": (900, 1500),  # 15-25분
        "sections": [
            {"type": "hook", "duration": 30, "description": "대결 티저"},
            {"type": "intro", "duration": 60, "description": "대결 소개 및 규칙"},
            {"type": "context", "duration": 120, "description": "종목 배경 설명"},
            {"type": "main_content", "duration": 300, "description": "인간 분석 과정"},
            {"type": "main_content", "duration": 300, "description": "AI 분석 과정"},
            {"type": "debate", "duration": 300, "description": "비교 및 토론"},
            {"type": "summary", "duration": 120, "description": "결과 발표"},
            {"type": "cta", "duration": 60, "description": "마무리 및 CTA"},
        ],
        "required_visuals": ["comparison_table", "score_card", "chart"],
    },
    ContentType.AI_BATTLE_HIGHLIGHTS: {
        "duration_range": (180, 420),  # 3-7분
        "sections": [
            {"type": "hook", "duration": 15, "description": "결과 티저"},
            {"type": "main_content", "duration": 180, "description": "핵심 대결 장면"},
            {"type": "summary", "duration": 60, "description": "결과 및 교훈"},
            {"type": "cta", "duration": 30, "description": "풀버전 유도"},
        ],
    },
    ContentType.COMMITTEE_DEBATE: {
        "duration_range": (600, 1200),  # 10-20분
        "sections": [
            {"type": "hook", "duration": 30, "description": "논쟁 티저"},
            {"type": "context", "duration": 90, "description": "종목 및 쟁점 소개"},
            {"type": "debate", "duration": 600, "description": "에이전트 토론"},
            {"type": "summary", "duration": 90, "description": "합의점 및 결론"},
            {"type": "cta", "duration": 30, "description": "마무리"},
        ],
    },
    ContentType.DEVILS_ADVOCATE: {
        "duration_range": (480, 720),  # 8-12분
        "sections": [
            {"type": "hook", "duration": 20, "description": "반전 티저"},
            {"type": "intro", "duration": 60, "description": "악마의 변호인 소개"},
            {"type": "main_content", "duration": 300, "description": "반박 포인트들"},
            {"type": "reaction", "duration": 120, "description": "다른 에이전트 반응"},
            {"type": "summary", "duration": 60, "description": "결론"},
        ],
    },
    ContentType.STOCK_QUICK_TAKE: {
        "duration_range": (60, 180),  # 1-3분 (숏폼 가능)
        "sections": [
            {"type": "hook", "duration": 10, "description": "핵심 메시지"},
            {"type": "main_content", "duration": 90, "description": "3가지 포인트"},
            {"type": "summary", "duration": 20, "description": "결론"},
        ],
    },
    ContentType.REPORT_FACT_CHECK: {
        "duration_range": (600, 900),  # 10-15분
        "sections": [
            {"type": "hook", "duration": 30, "description": "검증 대상 소개"},
            {"type": "context", "duration": 60, "description": "리포트 내용 요약"},
            {"type": "analysis", "duration": 360, "description": "편향 및 사실 검증"},
            {"type": "summary", "duration": 90, "description": "신뢰도 점수 및 결론"},
            {"type": "cta", "duration": 30, "description": "마무리"},
        ],
    },
}


# =============================================================================
# 후킹 템플릿
# =============================================================================

HOOK_TEMPLATES = {
    "curiosity": [
        "이 종목, AI가 분석한 결과가 충격적입니다",
        "{company}에 대해 AI가 내린 판결, 예상하셨나요?",
        "왜 AI 6명이 이 종목 두고 싸웠을까요?",
    ],
    "contrarian_take": [
        "모두가 {direction}라고 할 때, AI는 반대로 봤습니다",
        "증권사 리포트와 완전히 다른 AI의 분석",
        "시장의 컨센서스가 틀렸을 수도 있는 이유",
    ],
    "surprising_statistic": [
        "이 숫자 보셨나요? {stat}",
        "{company}의 {metric}가 {value}라는 사실, 알고 계셨나요?",
        "데이터가 보여주는 불편한 진실",
    ],
    "story_opening": [
        "2024년, 한 투자자가 AI에게 도전장을 내밀었습니다",
        "{company}를 둘러싼 논쟁, 오늘 결론이 납니다",
        "6명의 AI 애널리스트가 회의실에 모였습니다",
    ],
    "instant_value": [
        "{company} 1분 정리",
        "AI가 본 {company}, 딱 3가지만 기억하세요",
        "30초 만에 파악하는 {company} 핵심",
    ],
    "shock_value": [
        "AI가 이 종목에 '매도' 의견을 냈습니다",
        "충격! AI vs 인간 대결 결과",
        "예상을 완전히 뒤엎은 AI의 분석",
    ],
    "bold_prediction": [
        "AI가 예측한 {company} 6개월 후 주가",
        "이 목표가, 실현될까요?",
        "{company}, {target_price}원 간다? AI의 대담한 예측",
    ],
    "relatable_problem": [
        "{company} 지금 사도 될까요? 저도 고민했습니다",
        "주식 처음 하시는 분들, 이것만 보세요",
        "투자 결정 못 하시겠죠? AI한테 물어봤습니다",
    ],
}
