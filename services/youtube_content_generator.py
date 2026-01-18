"""유튜브 콘텐츠 생성 서비스.

시청자 페르소나별로 맞춤화된 콘텐츠를 생성합니다.
"""
import json
import logging
from datetime import datetime
from typing import Any, Optional

from langchain_anthropic import ChatAnthropic

from models.youtube_content import (
    ViewerPersona,
    ContentFormat,
    ContentTone,
    ContentType,
    ThumbnailSpec,
    ScriptSection,
    FullScript,
    VisualAsset,
    YouTubeContentPackage,
    PERSONA_CONTENT_SETTINGS,
    CONTENT_TYPE_TEMPLATES,
    HOOK_TEMPLATES,
)
from models.battle_game import InvestmentBattle

logger = logging.getLogger(__name__)


class YouTubeContentGenerator:
    """유튜브 콘텐츠 생성기."""

    def __init__(self, model_name: str = "claude-opus-4-5-20251101"):
        """Initialize content generator."""
        self.llm = ChatAnthropic(
            model_name=model_name,
            temperature=0.7,  # 창의적인 콘텐츠를 위해 높은 온도
        )

    async def generate_content_package(
        self,
        analysis_result: dict,
        target_persona: ViewerPersona,
        content_type: ContentType,
        battle: Optional[InvestmentBattle] = None,
    ) -> YouTubeContentPackage:
        """전체 콘텐츠 패키지 생성.

        Args:
            analysis_result: AI 분석 결과
            target_persona: 타겟 시청자 페르소나
            content_type: 콘텐츠 유형
            battle: AI vs Human 대결 (있는 경우)

        Returns:
            완성된 콘텐츠 패키지
        """
        persona_settings = PERSONA_CONTENT_SETTINGS.get(
            target_persona,
            PERSONA_CONTENT_SETTINGS[ViewerPersona.INTERMEDIATE]
        )

        # 콘텐츠 포맷 및 톤 결정
        content_format = persona_settings["preferred_formats"][0]
        content_tone = persona_settings["preferred_tone"]

        ticker = analysis_result.get("ticker", "UNKNOWN")
        company_name = analysis_result.get("company_name", "Unknown Company")

        # 제목 옵션 생성
        title_options = await self._generate_title_options(
            analysis_result, target_persona, content_type, battle
        )

        # 썸네일 사양 생성
        thumbnail_specs = await self._generate_thumbnail_specs(
            analysis_result, target_persona, content_type, battle
        )

        # 스크립트 생성
        full_script = await self._generate_full_script(
            analysis_result, target_persona, content_type, content_format, content_tone, battle
        )

        # 시각 자료 생성
        visual_assets = await self._generate_visual_assets(
            analysis_result, target_persona, content_type, battle
        )

        # 하이라이트 클립 추출
        highlight_clips = self._extract_highlight_clips(full_script, content_type)

        # 커뮤니티 포스트 생성
        community_post = await self._generate_community_post(
            analysis_result, target_persona, content_type
        )

        # SEO 키워드 및 해시태그
        seo_keywords, hashtags = await self._generate_seo_elements(
            analysis_result, target_persona, content_type
        )

        return YouTubeContentPackage(
            target_persona=target_persona,
            content_type=content_type,
            content_format=content_format,
            content_tone=content_tone,
            ticker=ticker,
            company_name=company_name,
            title_options=title_options,
            thumbnail_specs=thumbnail_specs,
            full_script=full_script,
            visual_assets=visual_assets,
            highlight_clips=highlight_clips,
            community_post=community_post,
            seo_keywords=seo_keywords,
            hashtags=hashtags,
        )

    async def _generate_title_options(
        self,
        analysis_result: dict,
        persona: ViewerPersona,
        content_type: ContentType,
        battle: Optional[InvestmentBattle],
    ) -> list[dict]:
        """제목 옵션 생성 (A/B 테스트용)."""
        persona_settings = PERSONA_CONTENT_SETTINGS.get(persona, {})
        hook_style = persona_settings.get("hook_style", "curiosity")

        ticker = analysis_result.get("ticker", "")
        company_name = analysis_result.get("company_name", "")
        decision = analysis_result.get("committee_decision", {})
        recommendation = decision.get("final_recommendation", "")
        target_price = decision.get("target_price", 0)

        # 대결 정보
        battle_info = ""
        if battle and battle.result:
            winner = battle.result.final_winner
            battle_info = f"승자: {'인간' if winner == 'human' else 'AI' if winner == 'ai' else '무승부'}"

        prompt = f"""유튜브 영상 제목 5개를 생성하세요.

## 콘텐츠 정보
- 종목: {company_name} ({ticker})
- 콘텐츠 유형: {content_type.value}
- 투자의견: {recommendation}
- 목표가: {target_price:,.0f}원
- 대결 결과: {battle_info}

## 타겟 시청자
- 페르소나: {persona.value}
- 선호 후킹 스타일: {hook_style}

## 제목 스타일별 1개씩 생성
1. curiosity (호기심 자극)
2. urgent (긴급/시급함)
3. value (가치 제안)
4. emotional (감정 자극)
5. contrarian (역발상/반전)

## 규칙
- 40자 이내
- 이모지 1-2개 포함
- 클릭을 유도하되 낚시 제목은 지양
- 숫자나 구체적 정보 포함 권장

JSON 배열로 응답:
[
    {{"title": "제목1", "style": "curiosity", "hook_element": "핵심 후킹 요소"}},
    ...
]"""

        try:
            response = await self.llm.ainvoke(prompt)
            return json.loads(self._extract_json(response.content))
        except Exception as e:
            logger.error(f"Error generating titles: {e}")
            return [
                {"title": f"AI가 분석한 {company_name} 투자 전망", "style": "default"}
            ]

    async def _generate_thumbnail_specs(
        self,
        analysis_result: dict,
        persona: ViewerPersona,
        content_type: ContentType,
        battle: Optional[InvestmentBattle],
    ) -> list[ThumbnailSpec]:
        """썸네일 사양 생성."""
        company_name = analysis_result.get("company_name", "")
        decision = analysis_result.get("committee_decision", {})
        recommendation = decision.get("final_recommendation", "")

        # 콘텐츠 유형별 기본 스타일
        style_map = {
            ContentType.AI_BATTLE_FULL: "versus",
            ContentType.AI_BATTLE_HIGHLIGHTS: "versus",
            ContentType.COMMITTEE_DEBATE: "dramatic",
            ContentType.DEVILS_ADVOCATE: "dramatic",
            ContentType.STOCK_DEEP_DIVE: "clean",
            ContentType.REPORT_FACT_CHECK: "news",
        }
        base_style = style_map.get(content_type, "dramatic")

        # 투자의견별 색상
        if "매수" in recommendation or "Buy" in recommendation:
            color_scheme = "green_gold"
            emotion = "confident"
        elif "매도" in recommendation or "Sell" in recommendation:
            color_scheme = "red_black"
            emotion = "worried"
        else:
            color_scheme = "blue_white"
            emotion = "thinking"

        specs = []

        # 옵션 1: 드라마틱 스타일
        specs.append(ThumbnailSpec(
            headline=f"{company_name[:6]} AI 분석",
            sub_headline=recommendation,
            style="dramatic",
            color_scheme=color_scheme,
            elements=["stock_chart", "ai_robot", "arrow_up" if "매수" in recommendation else "arrow_down"],
            emotion=emotion,
            text_elements=[
                {"text": "AI가 예측한", "position": "top", "size": "small"},
                {"text": company_name[:8], "position": "center", "size": "large", "highlight": True},
                {"text": recommendation, "position": "bottom", "size": "medium"},
            ]
        ))

        # 옵션 2: VS 스타일 (대결 콘텐츠인 경우)
        if battle:
            specs.append(ThumbnailSpec(
                headline="AI vs 인간",
                sub_headline=f"승자는?",
                style="versus",
                color_scheme="purple_pink",
                elements=["ai_robot", "human_face", "vs_badge"],
                emotion="surprised",
                text_elements=[
                    {"text": "🤖 AI", "position": "left", "size": "large"},
                    {"text": "VS", "position": "center", "size": "large", "highlight": True},
                    {"text": "🧠 인간", "position": "right", "size": "large"},
                ]
            ))

        # 옵션 3: 질문형 스타일
        specs.append(ThumbnailSpec(
            headline=f"{company_name[:6]}",
            sub_headline="지금 사도 될까?",
            style="question",
            color_scheme="orange_dark",
            elements=["question_mark", "stock_chart", "money_icon"],
            emotion="thinking",
            text_elements=[
                {"text": company_name[:8], "position": "top", "size": "large"},
                {"text": "?", "position": "center", "size": "xlarge", "highlight": True},
                {"text": "AI의 판단은", "position": "bottom", "size": "medium"},
            ]
        ))

        return specs

    async def _generate_full_script(
        self,
        analysis_result: dict,
        persona: ViewerPersona,
        content_type: ContentType,
        content_format: ContentFormat,
        content_tone: ContentTone,
        battle: Optional[InvestmentBattle],
    ) -> FullScript:
        """전체 스크립트 생성."""
        persona_settings = PERSONA_CONTENT_SETTINGS.get(persona, {})
        template = CONTENT_TYPE_TEMPLATES.get(content_type, {})

        company_name = analysis_result.get("company_name", "")
        ticker = analysis_result.get("ticker", "")
        decision = analysis_result.get("committee_decision", {})
        debate_results = analysis_result.get("debate_results", {})
        agent_analyses = analysis_result.get("agent_analyses", [])

        # 대결 정보 준비
        battle_context = ""
        if battle:
            battle_context = f"""
## AI vs Human 대결 정보
- 인간 분석가: {battle.human_analysis.analyst_name if battle.human_analysis else 'N/A'}
- 인간 목표가: {battle.human_analysis.target_price if battle.human_analysis else 'N/A'}
- AI 목표가: {battle.ai_analysis.target_price if battle.ai_analysis else 'N/A'}
- 최종 승자: {battle.result.final_winner if battle.result else '진행 중'}
- 점수: 인간 {battle.result.human_total_score if battle.result else 0} vs AI {battle.result.ai_total_score if battle.result else 0}
"""

        prompt = f"""유튜브 영상 스크립트를 생성하세요.

## 콘텐츠 정보
- 종목: {company_name} ({ticker})
- 콘텐츠 유형: {content_type.value}
- 포맷: {content_format.value}
- 톤: {content_tone.value}

## 타겟 시청자
- 페르소나: {persona.value}
- 복잡도 수준: {persona_settings.get('complexity_level', 3)}/5
- 전문용어 허용: {persona_settings.get('jargon_allowed', True)}
- 속도: {persona_settings.get('pace', 'moderate')}

## AI 분석 결과 요약
- 최종 의견: {decision.get('final_recommendation', '')}
- 목표가: {decision.get('target_price', 0):,.0f}원
- 확신도: {decision.get('confidence_score', 0)}/10
- 주요 근거: {json.dumps(decision.get('key_reasons', [])[:3], ensure_ascii=False)}
- 주요 리스크: {json.dumps(decision.get('key_risks', [])[:3], ensure_ascii=False)}

## 토론 하이라이트
{json.dumps(debate_results.get('consensus_reached', [])[:3], ensure_ascii=False)}

{battle_context}

## 스크립트 섹션 구조
{json.dumps(template.get('sections', []), ensure_ascii=False)}

---

다음 JSON 형식으로 스크립트 생성:
{{
    "title": "영상 제목",
    "description": "영상 설명 (150자)",
    "tags": ["태그1", "태그2"],
    "total_duration_seconds": 총길이,
    "sections": [
        {{
            "section_type": "hook/intro/context/main_content/debate/reaction/summary/cta/outro",
            "duration_seconds": 길이,
            "script_text": "대본 내용 (말하는 그대로)",
            "visual_direction": "영상 연출 지시",
            "on_screen_text": ["화면 텍스트"],
            "b_roll_suggestions": ["B-roll 제안"],
            "sound_effects": ["효과음"],
            "music_mood": "BGM 분위기"
        }}
    ],
    "key_timestamps": [
        {{"time": "0:00", "label": "설명"}}
    ]
}}

## 스크립트 작성 규칙
1. 자연스러운 구어체 사용
2. 페르소나에 맞는 복잡도
3. {content_tone.value} 톤 유지
4. 각 섹션별 시각 연출 상세히
5. 시청자 참여 유도 요소 포함
"""

        try:
            response = await self.llm.ainvoke(prompt)
            result = json.loads(self._extract_json(response.content))

            sections = [
                ScriptSection(
                    section_type=s.get("section_type", "main_content"),
                    duration_seconds=s.get("duration_seconds", 60),
                    script_text=s.get("script_text", ""),
                    visual_direction=s.get("visual_direction", ""),
                    on_screen_text=s.get("on_screen_text", []),
                    b_roll_suggestions=s.get("b_roll_suggestions", []),
                    sound_effects=s.get("sound_effects", []),
                    music_mood=s.get("music_mood"),
                )
                for s in result.get("sections", [])
            ]

            return FullScript(
                title=result.get("title", f"{company_name} AI 분석"),
                description=result.get("description", ""),
                tags=result.get("tags", []),
                total_duration_seconds=result.get("total_duration_seconds", 600),
                sections=sections,
                key_timestamps=result.get("key_timestamps", []),
            )
        except Exception as e:
            logger.error(f"Error generating script: {e}")
            return FullScript(
                title=f"{company_name} AI 분석",
                description="AI 투자위원회의 분석 결과",
                tags=[company_name, ticker, "AI분석"],
                total_duration_seconds=600,
                sections=[],
            )

    async def _generate_visual_assets(
        self,
        analysis_result: dict,
        persona: ViewerPersona,
        content_type: ContentType,
        battle: Optional[InvestmentBattle],
    ) -> list[VisualAsset]:
        """시각 자료 생성."""
        assets = []
        company_name = analysis_result.get("company_name", "")
        decision = analysis_result.get("committee_decision", {})

        # 1. 스코어카드
        assets.append(VisualAsset(
            asset_type="scorecard",
            title="AI 투자위원회 스코어카드",
            data={
                "recommendation": decision.get("final_recommendation", ""),
                "target_price": decision.get("target_price", 0),
                "confidence": decision.get("confidence_score", 0),
                "vote_result": decision.get("vote_result", {}),
            },
            style_notes="그라디언트 배경, 큰 숫자 강조"
        ))

        # 2. 비교 테이블 (대결인 경우)
        if battle and battle.human_analysis and battle.ai_analysis:
            assets.append(VisualAsset(
                asset_type="comparison",
                title="AI vs 인간 분석 비교",
                data={
                    "human": {
                        "name": battle.human_analysis.analyst_name,
                        "recommendation": battle.human_analysis.recommendation,
                        "target_price": battle.human_analysis.target_price,
                        "confidence": battle.human_analysis.confidence_score,
                    },
                    "ai": {
                        "recommendation": battle.ai_analysis.recommendation,
                        "target_price": battle.ai_analysis.target_price,
                        "confidence": battle.ai_analysis.confidence_score,
                    },
                    "winner": battle.result.final_winner if battle.result else None,
                },
                style_notes="VS 스타일, 대비되는 색상"
            ))

        # 3. 핵심 수치 하이라이트
        key_reasons = decision.get("key_reasons", [])[:3]
        assets.append(VisualAsset(
            asset_type="stat_highlight",
            title="핵심 투자 포인트",
            data={
                "points": key_reasons,
                "company": company_name,
            },
            style_notes="아이콘 + 텍스트 조합"
        ))

        # 4. 리스크 인포그래픽
        key_risks = decision.get("key_risks", [])[:3]
        assets.append(VisualAsset(
            asset_type="infographic",
            title="주요 리스크 요인",
            data={
                "risks": key_risks,
            },
            style_notes="경고 색상, 위험 아이콘"
        ))

        # 5. 타임라인 (토론 과정)
        debate_results = analysis_result.get("debate_results", {})
        if debate_results.get("debate_rounds"):
            assets.append(VisualAsset(
                asset_type="timeline",
                title="AI 토론 과정",
                data={
                    "rounds": [
                        {"round": i+1, "theme": r.get("theme", "")}
                        for i, r in enumerate(debate_results.get("debate_rounds", []))
                    ],
                },
                style_notes="단계별 진행 표시"
            ))

        return assets

    def _extract_highlight_clips(
        self,
        script: FullScript,
        content_type: ContentType,
    ) -> list[dict]:
        """하이라이트 클립 추출."""
        clips = []
        current_time = 0

        for section in script.sections:
            # 하이라이트 가능한 섹션 타입
            highlight_types = ["hook", "debate", "reaction", "summary"]

            if section.section_type in highlight_types:
                clips.append({
                    "start": current_time,
                    "end": current_time + section.duration_seconds,
                    "title": f"{section.section_type} 하이라이트",
                    "for_shorts": section.duration_seconds <= 60,
                    "section_type": section.section_type,
                })

            current_time += section.duration_seconds

        return clips

    async def _generate_community_post(
        self,
        analysis_result: dict,
        persona: ViewerPersona,
        content_type: ContentType,
    ) -> dict:
        """커뮤니티 포스트 생성."""
        company_name = analysis_result.get("company_name", "")
        decision = analysis_result.get("committee_decision", {})

        # 투표형 포스트
        if content_type in [ContentType.AI_BATTLE_FULL, ContentType.AI_BATTLE_HIGHLIGHTS]:
            return {
                "text": f"🤖 vs 🧠 {company_name} 분석 대결!\n\nAI 투자위원회와 인간 투자자가 붙었습니다.\n결과가 궁금하시다면 새 영상을 확인하세요!",
                "poll": {
                    "question": "누가 이겼을 것 같나요?",
                    "options": ["🤖 AI 승리", "🧠 인간 승리", "🤝 무승부"]
                }
            }
        else:
            return {
                "text": f"📊 {company_name} AI 분석 결과가 나왔습니다!\n\n투자의견: {decision.get('final_recommendation', '')}\n목표가: {decision.get('target_price', 0):,.0f}원\n\n자세한 분석은 새 영상에서 확인하세요!",
                "poll": {
                    "question": f"{company_name}, 어떻게 보시나요?",
                    "options": ["매수 찬성", "보유 의견", "매도 의견", "잘 모르겠다"]
                }
            }

    async def _generate_seo_elements(
        self,
        analysis_result: dict,
        persona: ViewerPersona,
        content_type: ContentType,
    ) -> tuple[list[str], list[str]]:
        """SEO 키워드 및 해시태그 생성."""
        company_name = analysis_result.get("company_name", "")
        ticker = analysis_result.get("ticker", "")

        # 기본 키워드
        keywords = [
            company_name,
            ticker,
            "주식분석",
            "AI투자",
            "투자분석",
            "주식투자",
            "AI분석",
        ]

        # 콘텐츠 유형별 키워드
        type_keywords = {
            ContentType.AI_BATTLE_FULL: ["AI대결", "투자대결", "AIvsHuman"],
            ContentType.COMMITTEE_DEBATE: ["AI토론", "투자위원회", "애널리스트"],
            ContentType.DEVILS_ADVOCATE: ["반론", "리스크분석", "비판적사고"],
            ContentType.STOCK_DEEP_DIVE: ["심층분석", "종목분석", "기업분석"],
            ContentType.REPORT_FACT_CHECK: ["팩트체크", "리포트검증", "진실확인"],
        }
        keywords.extend(type_keywords.get(content_type, []))

        # 해시태그
        hashtags = [
            f"#{company_name}",
            f"#{ticker.replace('.', '')}",
            "#주식",
            "#투자",
            "#AI분석",
            "#주식분석",
            "#AI투자위원회",
        ]

        return keywords, hashtags

    def _extract_json(self, text: str) -> str:
        """텍스트에서 JSON 추출."""
        if "```json" in text:
            return text.split("```json")[1].split("```")[0]
        elif "```" in text:
            return text.split("```")[1].split("```")[0]
        return text


# =============================================================================
# 페르소나별 콘텐츠 생성 유틸리티
# =============================================================================

async def generate_multi_persona_content(
    analysis_result: dict,
    content_type: ContentType,
    personas: list[ViewerPersona],
    battle: Optional[InvestmentBattle] = None,
) -> dict[ViewerPersona, YouTubeContentPackage]:
    """여러 페르소나를 위한 콘텐츠 일괄 생성.

    Args:
        analysis_result: AI 분석 결과
        content_type: 콘텐츠 유형
        personas: 타겟 페르소나 목록
        battle: AI vs Human 대결

    Returns:
        페르소나별 콘텐츠 패키지 딕셔너리
    """
    generator = YouTubeContentGenerator()
    results = {}

    for persona in personas:
        try:
            package = await generator.generate_content_package(
                analysis_result=analysis_result,
                target_persona=persona,
                content_type=content_type,
                battle=battle,
            )
            results[persona] = package
        except Exception as e:
            logger.error(f"Error generating content for {persona}: {e}")

    return results


async def generate_content_series(
    analysis_result: dict,
    target_persona: ViewerPersona,
    battle: Optional[InvestmentBattle] = None,
) -> list[YouTubeContentPackage]:
    """하나의 분석으로 여러 콘텐츠 시리즈 생성.

    Args:
        analysis_result: AI 분석 결과
        target_persona: 타겟 페르소나
        battle: AI vs Human 대결

    Returns:
        콘텐츠 패키지 리스트 (숏폼, 하이라이트, 풀버전 등)
    """
    generator = YouTubeContentGenerator()
    packages = []

    # 콘텐츠 유형별 생성
    content_types = []

    if battle:
        content_types = [
            ContentType.AI_BATTLE_FULL,       # 풀버전
            ContentType.AI_BATTLE_HIGHLIGHTS, # 하이라이트
            ContentType.STOCK_QUICK_TAKE,     # 숏폼
        ]
    else:
        content_types = [
            ContentType.COMMITTEE_DEBATE,     # 토론 풀버전
            ContentType.DEVILS_ADVOCATE,      # 악마의 변호인 특집
            ContentType.STOCK_QUICK_TAKE,     # 숏폼
        ]

    for content_type in content_types:
        try:
            package = await generator.generate_content_package(
                analysis_result=analysis_result,
                target_persona=target_persona,
                content_type=content_type,
                battle=battle,
            )
            packages.append(package)
        except Exception as e:
            logger.error(f"Error generating {content_type}: {e}")

    return packages
