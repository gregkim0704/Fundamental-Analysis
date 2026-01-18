"""유튜브 콘텐츠 스튜디오 UI.

시청자 페르소나별 맞춤 콘텐츠를 생성하고 관리하는 Streamlit UI입니다.
"""
import streamlit as st
from datetime import datetime
from typing import Optional
import json

from models.youtube_content import (
    ViewerPersona,
    ContentFormat,
    ContentTone,
    ContentType,
    YouTubeContentPackage,
    PERSONA_CONTENT_SETTINGS,
    CONTENT_TYPE_TEMPLATES,
)
from services.thumbnail_generator import (
    ThumbnailGenerator,
    generate_visual_asset_html,
)


# =============================================================================
# 페르소나 정보
# =============================================================================

PERSONA_INFO = {
    ViewerPersona.ABSOLUTE_BEGINNER: {
        "name": "주린이 (왕초보)",
        "icon": "🌱",
        "description": "주식 계좌도 없는 완전 초보",
        "content_tips": "쉬운 용어, 친절한 설명, 기초부터 차근차근"
    },
    ViewerPersona.BEGINNER: {
        "name": "초보 투자자",
        "icon": "🌿",
        "description": "투자 경험 1년 미만",
        "content_tips": "기본 개념 설명, 실수 방지 팁, 따라하기 쉬운 가이드"
    },
    ViewerPersona.INTERMEDIATE: {
        "name": "중급 투자자",
        "icon": "🌳",
        "description": "투자 경험 1-5년",
        "content_tips": "인사이트 중심, 적당한 전문용어, 실전 팁"
    },
    ViewerPersona.ADVANCED: {
        "name": "고급 투자자",
        "icon": "🎄",
        "description": "투자 경험 5년 이상",
        "content_tips": "심층 분석, 데이터 중심, 빠른 전달"
    },
    ViewerPersona.PROFESSIONAL: {
        "name": "전문 투자자",
        "icon": "🏆",
        "description": "기관/전문가 수준",
        "content_tips": "고급 분석, 업계 인사이트, 네트워킹"
    },
    ViewerPersona.DATA_NERD: {
        "name": "데이터 마니아",
        "icon": "📊",
        "description": "숫자와 데이터를 사랑하는 분",
        "content_tips": "차트, 통계, 정량적 분석 강조"
    },
    ViewerPersona.STORY_LOVER: {
        "name": "스토리 러버",
        "icon": "📖",
        "description": "이야기와 서사를 좋아하는 분",
        "content_tips": "드라마틱한 전개, 캐릭터, 내러티브"
    },
    ViewerPersona.QUICK_LEARNER: {
        "name": "효율 추구형",
        "icon": "⚡",
        "description": "핵심만 빠르게 파악하고 싶은 분",
        "content_tips": "숏폼, 요약, 불릿포인트"
    },
    ViewerPersona.ENTERTAINMENT_SEEKER: {
        "name": "재미 추구형",
        "icon": "🎮",
        "description": "재미있는 콘텐츠를 원하는 분",
        "content_tips": "밈, 유머, 리액션, 서프라이즈"
    },
    ViewerPersona.HIGH_RISK_TAKER: {
        "name": "공격적 투자자",
        "icon": "🔥",
        "description": "고위험 고수익을 추구하는 분",
        "content_tips": "대담한 예측, 액션 중심, 긴박감"
    },
    ViewerPersona.VALUE_INVESTOR: {
        "name": "가치투자자",
        "icon": "💎",
        "description": "워런 버핏 스타일 장기 투자자",
        "content_tips": "펀더멘털 분석, 장기 관점, 인내심"
    },
    ViewerPersona.GROWTH_INVESTOR: {
        "name": "성장주 투자자",
        "icon": "🚀",
        "description": "성장 기업에 투자하는 분",
        "content_tips": "트렌드, 미래 비전, 혁신 기업"
    },
}

CONTENT_TYPE_INFO = {
    ContentType.AI_BATTLE_FULL: {
        "name": "AI vs 인간 대결 (풀버전)",
        "icon": "⚔️",
        "duration": "15-25분",
        "description": "AI와 인간 투자자의 치열한 분석 대결 전체 과정"
    },
    ContentType.AI_BATTLE_HIGHLIGHTS: {
        "name": "AI vs 인간 대결 (하이라이트)",
        "icon": "🎬",
        "duration": "3-7분",
        "description": "대결의 핵심 장면만 압축"
    },
    ContentType.COMMITTEE_DEBATE: {
        "name": "AI 투자위원회 토론",
        "icon": "🏛️",
        "duration": "10-20분",
        "description": "6명의 AI 에이전트가 벌이는 토론"
    },
    ContentType.DEVILS_ADVOCATE: {
        "name": "악마의 변호인 특집",
        "icon": "😈",
        "duration": "8-12분",
        "description": "AI 반박 전문가의 날카로운 분석"
    },
    ContentType.STOCK_DEEP_DIVE: {
        "name": "종목 심층 분석",
        "icon": "🔬",
        "duration": "20-30분",
        "description": "한 종목에 대한 완벽 분석"
    },
    ContentType.STOCK_QUICK_TAKE: {
        "name": "종목 퀵테이크",
        "icon": "⚡",
        "duration": "1-3분",
        "description": "핵심만 짚는 숏폼 분석"
    },
    ContentType.REPORT_FACT_CHECK: {
        "name": "리포트 팩트체크",
        "icon": "🔍",
        "duration": "10-15분",
        "description": "증권사 리포트 검증"
    },
}


def render_youtube_studio_header():
    """유튜브 스튜디오 헤더."""
    st.markdown("""
    <div style="text-align: center; padding: 20px; background: linear-gradient(135deg, #ff0000 0%, #1a1a2e 100%); border-radius: 15px; margin-bottom: 20px;">
        <h1 style="color: #ffffff; margin: 0;">🎬 AI 콘텐츠 스튜디오</h1>
        <p style="color: #ffffff88; margin: 5px 0 0 0;">시청자 맞춤형 유튜브 콘텐츠 생성기</p>
    </div>
    """, unsafe_allow_html=True)


def render_persona_selector() -> ViewerPersona:
    """시청자 페르소나 선택."""
    st.markdown("### 🎯 타겟 시청자 선택")
    st.markdown("어떤 시청자를 위한 콘텐츠인가요?")

    # 카테고리별 분류
    categories = {
        "경험 수준별": [
            ViewerPersona.ABSOLUTE_BEGINNER,
            ViewerPersona.BEGINNER,
            ViewerPersona.INTERMEDIATE,
            ViewerPersona.ADVANCED,
            ViewerPersona.PROFESSIONAL,
        ],
        "투자 스타일별": [
            ViewerPersona.VALUE_INVESTOR,
            ViewerPersona.GROWTH_INVESTOR,
            ViewerPersona.HIGH_RISK_TAKER,
        ],
        "콘텐츠 선호별": [
            ViewerPersona.DATA_NERD,
            ViewerPersona.STORY_LOVER,
            ViewerPersona.QUICK_LEARNER,
            ViewerPersona.ENTERTAINMENT_SEEKER,
        ],
    }

    selected_persona = None

    for category_name, personas in categories.items():
        st.markdown(f"**{category_name}**")
        cols = st.columns(len(personas))

        for i, persona in enumerate(personas):
            info = PERSONA_INFO.get(persona, {})
            with cols[i]:
                if st.button(
                    f"{info.get('icon', '👤')}\n{info.get('name', persona.value)}",
                    key=f"persona_{persona.value}",
                    use_container_width=True,
                    help=info.get('description', '')
                ):
                    st.session_state.selected_persona = persona
                    selected_persona = persona

    # 선택된 페르소나 표시
    current_persona = st.session_state.get('selected_persona', ViewerPersona.INTERMEDIATE)
    info = PERSONA_INFO.get(current_persona, {})

    st.markdown(f"""
    <div style="padding: 15px; background: #1a1a2e; border-radius: 10px; margin-top: 15px;">
        <h4 style="color: #4fc3f7; margin: 0;">{info.get('icon', '')} 선택된 타겟: {info.get('name', '')}</h4>
        <p style="color: #ffffff88; margin: 5px 0 0 0;">{info.get('description', '')}</p>
        <p style="color: #ffd700; margin: 5px 0 0 0;">💡 {info.get('content_tips', '')}</p>
    </div>
    """, unsafe_allow_html=True)

    return current_persona


def render_content_type_selector() -> ContentType:
    """콘텐츠 유형 선택."""
    st.markdown("### 📺 콘텐츠 유형 선택")

    cols = st.columns(3)
    selected_type = None

    content_types = list(CONTENT_TYPE_INFO.keys())

    for i, content_type in enumerate(content_types):
        info = CONTENT_TYPE_INFO.get(content_type, {})
        col_idx = i % 3

        with cols[col_idx]:
            if st.button(
                f"{info.get('icon', '📺')}\n{info.get('name', '')}\n({info.get('duration', '')})",
                key=f"content_type_{content_type.value}",
                use_container_width=True,
            ):
                st.session_state.selected_content_type = content_type
                selected_type = content_type

    current_type = st.session_state.get('selected_content_type', ContentType.AI_BATTLE_FULL)
    info = CONTENT_TYPE_INFO.get(current_type, {})

    st.info(f"**{info.get('name', '')}**: {info.get('description', '')}")

    return current_type


def render_content_package_preview(package: YouTubeContentPackage):
    """콘텐츠 패키지 미리보기."""
    st.markdown("## 🎬 생성된 콘텐츠 패키지")

    # 탭 구성
    tabs = st.tabs(["📝 제목/썸네일", "📜 스크립트", "🎨 시각자료", "📊 SEO", "📤 내보내기"])

    # 제목/썸네일 탭
    with tabs[0]:
        render_title_thumbnail_tab(package)

    # 스크립트 탭
    with tabs[1]:
        render_script_tab(package)

    # 시각자료 탭
    with tabs[2]:
        render_visual_assets_tab(package)

    # SEO 탭
    with tabs[3]:
        render_seo_tab(package)

    # 내보내기 탭
    with tabs[4]:
        render_export_tab(package)


def render_title_thumbnail_tab(package: YouTubeContentPackage):
    """제목/썸네일 탭."""
    st.markdown("### 🏷️ 제목 옵션 (A/B 테스트용)")

    for i, title_opt in enumerate(package.title_options, 1):
        style_badge = {
            "curiosity": "🤔 호기심",
            "urgent": "🚨 긴급",
            "value": "💎 가치",
            "emotional": "💓 감정",
            "contrarian": "🔄 역발상",
        }.get(title_opt.get('style', ''), '📺')

        st.markdown(f"""
        <div style="padding: 15px; background: #1a1a2e; border-radius: 10px; margin-bottom: 10px;">
            <span style="background: #4fc3f7; color: #000; padding: 3px 8px; border-radius: 5px; font-size: 12px;">{style_badge}</span>
            <h3 style="color: #ffffff; margin: 10px 0 5px 0;">{title_opt.get('title', '')}</h3>
            <p style="color: #ffffff66; margin: 0; font-size: 14px;">후킹 포인트: {title_opt.get('hook_element', '')}</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("### 🖼️ 썸네일 미리보기")

    thumbnail_generator = ThumbnailGenerator()

    for i, spec in enumerate(package.thumbnail_specs, 1):
        with st.expander(f"썸네일 옵션 {i}: {spec.style} 스타일"):
            # 썸네일 HTML 생성 및 표시
            additional_data = {
                "ticker": package.ticker,
                "target_price": "₩90,000",  # 예시
                "price_info": "+15.5%",
                "human_info": "목표가 ₩85,000",
                "ai_info": "목표가 ₩95,000",
            }

            html = thumbnail_generator.generate_thumbnail_html(spec, additional_data)

            # 스케일 다운하여 표시
            st.markdown(f"""
            <div style="transform: scale(0.5); transform-origin: top left; width: 640px; height: 360px; overflow: hidden;">
                {html}
            </div>
            """, unsafe_allow_html=True)

            st.json({
                "headline": spec.headline,
                "sub_headline": spec.sub_headline,
                "style": spec.style,
                "color_scheme": spec.color_scheme,
                "emotion": spec.emotion,
            })


def render_script_tab(package: YouTubeContentPackage):
    """스크립트 탭."""
    if not package.full_script:
        st.warning("스크립트가 생성되지 않았습니다.")
        return

    script = package.full_script

    st.markdown(f"### 📜 {script.title}")
    st.markdown(f"**설명:** {script.description}")
    st.markdown(f"**총 길이:** {script.total_duration_seconds // 60}분 {script.total_duration_seconds % 60}초")

    # 타임스탬프
    if script.key_timestamps:
        st.markdown("#### ⏱️ 타임스탬프")
        timestamps_text = "\n".join([f"{ts['time']} - {ts['label']}" for ts in script.key_timestamps])
        st.code(timestamps_text)

    # 섹션별 스크립트
    st.markdown("#### 📝 섹션별 스크립트")

    for i, section in enumerate(script.sections, 1):
        section_icon = {
            "hook": "🪝",
            "intro": "👋",
            "context": "📋",
            "main_content": "📺",
            "debate": "⚔️",
            "reaction": "😮",
            "summary": "📊",
            "cta": "📢",
            "outro": "👋",
        }.get(section.section_type, "📝")

        with st.expander(f"{section_icon} {section.section_type.upper()} ({section.duration_seconds}초)"):
            st.markdown("**대본:**")
            st.markdown(f"> {section.script_text}")

            if section.visual_direction:
                st.markdown(f"**🎬 영상 연출:** {section.visual_direction}")

            if section.on_screen_text:
                st.markdown("**📺 화면 텍스트:**")
                for text in section.on_screen_text:
                    st.markdown(f"- {text}")

            if section.b_roll_suggestions:
                st.markdown("**🎞️ B-roll 제안:**")
                for broll in section.b_roll_suggestions:
                    st.markdown(f"- {broll}")

            if section.sound_effects:
                st.markdown(f"**🔊 효과음:** {', '.join(section.sound_effects)}")

            if section.music_mood:
                st.markdown(f"**🎵 BGM 분위기:** {section.music_mood}")


def render_visual_assets_tab(package: YouTubeContentPackage):
    """시각자료 탭."""
    st.markdown("### 🎨 시각 자료")

    if not package.visual_assets:
        st.info("생성된 시각 자료가 없습니다.")
        return

    for asset in package.visual_assets:
        with st.expander(f"📊 {asset.title} ({asset.asset_type})"):
            # HTML 렌더링
            html = generate_visual_asset_html(asset)
            st.markdown(html, unsafe_allow_html=True)

            # 데이터 표시
            st.markdown("**원본 데이터:**")
            st.json(asset.data)

    # 하이라이트 클립
    if package.highlight_clips:
        st.markdown("### ✂️ 하이라이트 클립 (숏폼용)")

        for clip in package.highlight_clips:
            shorts_badge = "📱 Shorts 가능" if clip.get('for_shorts') else ""
            st.markdown(f"""
            <div style="padding: 10px; background: #1a1a2e; border-radius: 8px; margin-bottom: 8px;">
                <strong>{clip.get('title', '')}</strong> {shorts_badge}
                <br/>
                <span style="color: #888;">⏱️ {clip.get('start', 0)//60}:{clip.get('start', 0)%60:02d} - {clip.get('end', 0)//60}:{clip.get('end', 0)%60:02d}</span>
            </div>
            """, unsafe_allow_html=True)


def render_seo_tab(package: YouTubeContentPackage):
    """SEO 탭."""
    st.markdown("### 🔍 SEO 최적화")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**🏷️ 키워드**")
        st.code(", ".join(package.seo_keywords))

    with col2:
        st.markdown("**#️⃣ 해시태그**")
        st.code(" ".join(package.hashtags))

    # 커뮤니티 포스트
    if package.community_post:
        st.markdown("### 📝 커뮤니티 포스트")
        st.text_area(
            "포스트 내용",
            value=package.community_post.get('text', ''),
            height=100,
            disabled=True,
        )

        if package.community_post.get('poll'):
            poll = package.community_post['poll']
            st.markdown(f"**📊 투표:** {poll.get('question', '')}")
            for opt in poll.get('options', []):
                st.markdown(f"- {opt}")


def render_export_tab(package: YouTubeContentPackage):
    """내보내기 탭."""
    st.markdown("### 📤 내보내기")

    # JSON 다운로드
    st.markdown("#### 📄 전체 패키지 (JSON)")

    package_json = package.model_dump_json(indent=2)
    st.download_button(
        label="📥 JSON 다운로드",
        data=package_json,
        file_name=f"youtube_content_{package.ticker}_{package.content_id}.json",
        mime="application/json",
    )

    # 스크립트 텍스트 다운로드
    if package.full_script:
        st.markdown("#### 📝 스크립트 (TXT)")

        script_text = f"# {package.full_script.title}\n\n"
        script_text += f"설명: {package.full_script.description}\n"
        script_text += f"태그: {', '.join(package.full_script.tags)}\n\n"
        script_text += "---\n\n"

        for section in package.full_script.sections:
            script_text += f"## [{section.section_type.upper()}] ({section.duration_seconds}초)\n\n"
            script_text += f"{section.script_text}\n\n"
            if section.visual_direction:
                script_text += f"[연출] {section.visual_direction}\n\n"
            script_text += "---\n\n"

        st.download_button(
            label="📥 스크립트 다운로드",
            data=script_text,
            file_name=f"script_{package.ticker}_{package.content_id}.txt",
            mime="text/plain",
        )

    # 제목 옵션
    st.markdown("#### 🏷️ 제목 옵션 (복사용)")
    titles_text = "\n".join([f"- {t.get('title', '')}" for t in package.title_options])
    st.text_area("제목들", value=titles_text, height=150)


def render_quick_content_generator():
    """빠른 콘텐츠 생성 (데모용)."""
    st.markdown("### ⚡ 빠른 콘텐츠 생성")

    col1, col2 = st.columns(2)

    with col1:
        ticker = st.text_input("종목 코드", value="005930.KS", key="yt_quick_ticker")
        company_name = st.text_input("회사명", value="삼성전자", key="yt_quick_company")

    with col2:
        recommendation = st.selectbox(
            "투자의견",
            options=["매수", "보유", "매도"],
            key="yt_quick_rec"
        )
        target_price = st.number_input("목표가", value=90000, key="yt_quick_target")

    if st.button("🚀 콘텐츠 생성 (데모)", type="primary", use_container_width=True):
        with st.spinner("AI가 콘텐츠를 생성하고 있습니다..."):
            # 데모용 패키지 생성
            demo_package = create_demo_package(
                ticker=ticker,
                company_name=company_name,
                recommendation=recommendation,
                target_price=target_price,
                persona=st.session_state.get('selected_persona', ViewerPersona.INTERMEDIATE),
                content_type=st.session_state.get('selected_content_type', ContentType.AI_BATTLE_FULL),
            )

            st.session_state.generated_package = demo_package
            st.success("콘텐츠 생성 완료!")
            st.balloons()


def create_demo_package(
    ticker: str,
    company_name: str,
    recommendation: str,
    target_price: float,
    persona: ViewerPersona,
    content_type: ContentType,
) -> YouTubeContentPackage:
    """데모 패키지 생성."""
    from models.youtube_content import (
        ThumbnailSpec, ScriptSection, FullScript, VisualAsset
    )

    persona_info = PERSONA_INFO.get(persona, {})

    # 제목 옵션
    title_options = [
        {"title": f"🤖 AI가 분석한 {company_name}, 결과가 충격적입니다", "style": "curiosity", "hook_element": "충격적인 결과"},
        {"title": f"[긴급] {company_name} AI 투자위원회 판결 공개!", "style": "urgent", "hook_element": "긴급성"},
        {"title": f"{company_name} {recommendation} vs AI 의견 대결 결과", "style": "contrarian", "hook_element": "대결"},
    ]

    # 썸네일
    thumbnail_specs = [
        ThumbnailSpec(
            headline=company_name[:6],
            sub_headline="AI가 분석한",
            style="dramatic",
            color_scheme="green_gold" if "매수" in recommendation else "red_black",
            elements=["stock_chart", "ai_robot"],
            emotion="confident" if "매수" in recommendation else "worried",
        ),
        ThumbnailSpec(
            headline="AI vs 인간",
            sub_headline=f"{company_name} 대결",
            style="versus",
            color_scheme="purple_pink",
            elements=["ai_robot", "human_face", "vs_badge"],
            emotion="surprised",
        ),
    ]

    # 스크립트
    full_script = FullScript(
        title=f"{company_name} AI 투자위원회 분석 결과",
        description=f"AI 투자위원회가 {company_name}을 분석한 결과를 공개합니다.",
        tags=[company_name, ticker, "AI분석", "주식"],
        total_duration_seconds=900,
        sections=[
            ScriptSection(
                section_type="hook",
                duration_seconds=30,
                script_text=f"여러분, AI 투자위원회가 {company_name}에 대해 내린 판결이 나왔습니다. 과연 {recommendation}이 맞을까요? 끝까지 시청하시면 AI의 숨겨진 분석 포인트를 알려드립니다.",
                visual_direction="긴장감 있는 BGM, 차트 화면",
                on_screen_text=[f"{company_name} AI 분석", "결과는?"],
                music_mood="tense",
            ),
            ScriptSection(
                section_type="intro",
                duration_seconds=60,
                script_text=f"안녕하세요, AI 투자위원회입니다. 오늘은 {company_name}에 대한 분석 결과를 공유드리려고 합니다. 6명의 AI 애널리스트가 치열하게 토론한 결과입니다.",
                visual_direction="채널 로고, 진행자 화면",
                on_screen_text=["AI 투자위원회", "6명의 AI 애널리스트"],
            ),
            ScriptSection(
                section_type="main_content",
                duration_seconds=300,
                script_text=f"먼저 퀀트 에이전트의 분석을 보시죠. {company_name}의 재무제표를 분석한 결과, PER은 현재 12배 수준으로 역사적 평균 대비 저평가 상태입니다.",
                visual_direction="재무 데이터 차트, 비교 그래프",
                b_roll_suggestions=["재무제표 클로즈업", "차트 애니메이션"],
            ),
            ScriptSection(
                section_type="debate",
                duration_seconds=300,
                script_text="하지만 여기서 악마의 변호인이 반박합니다. 정말 이 밸류에이션이 정당한 것인가? 경쟁사 대비 기술 격차를 고려하면 프리미엄을 줘야 하는 것 아닌가?",
                visual_direction="토론 화면, 에이전트 아바타",
                sound_effects=["tension_rise"],
            ),
            ScriptSection(
                section_type="summary",
                duration_seconds=120,
                script_text=f"결론적으로, AI 투자위원회는 {company_name}에 대해 {recommendation} 의견을 제시합니다. 목표가는 {target_price:,.0f}원입니다.",
                visual_direction="결론 카드, 목표가 강조",
                on_screen_text=[recommendation, f"목표가: ₩{target_price:,.0f}"],
            ),
            ScriptSection(
                section_type="cta",
                duration_seconds=60,
                script_text="이 영상이 도움이 되셨다면 구독과 좋아요 부탁드립니다. 다음 영상에서는 또 다른 종목 분석으로 찾아뵙겠습니다.",
                visual_direction="구독 버튼 애니메이션",
                on_screen_text=["구독", "좋아요"],
            ),
        ],
        key_timestamps=[
            {"time": "0:00", "label": "AI 분석 티저"},
            {"time": "0:30", "label": "분석 시작"},
            {"time": "5:30", "label": "AI 토론"},
            {"time": "10:30", "label": "최종 결론"},
        ],
    )

    # 시각 자료
    visual_assets = [
        VisualAsset(
            asset_type="scorecard",
            title="AI 투자위원회 스코어카드",
            data={
                "recommendation": recommendation,
                "target_price": target_price,
                "confidence": 7.5,
                "vote_result": {"bullish": ["quant", "qualitative"], "neutral": ["macro"], "bearish": []},
            },
        ),
        VisualAsset(
            asset_type="stat_highlight",
            title="핵심 투자 포인트",
            data={
                "points": [
                    "AI 반도체 수요 증가 수혜",
                    "현재 주가 저평가 상태",
                    "배당 수익률 2% 이상",
                ],
            },
        ),
    ]

    return YouTubeContentPackage(
        target_persona=persona,
        content_type=content_type,
        content_format=ContentFormat.STANDARD_VIDEO,
        content_tone=ContentTone.CASUAL_FRIENDLY,
        ticker=ticker,
        company_name=company_name,
        title_options=title_options,
        thumbnail_specs=thumbnail_specs,
        full_script=full_script,
        visual_assets=visual_assets,
        highlight_clips=[
            {"start": 330, "end": 390, "title": "AI 토론 하이라이트", "for_shorts": True},
            {"start": 630, "end": 690, "title": "최종 결론", "for_shorts": True},
        ],
        community_post={
            "text": f"🤖 {company_name} AI 분석 결과 공개!\n\nAI 투자위원회가 내린 결론은?",
            "poll": {"question": f"{company_name} 어떻게 보시나요?", "options": ["매수", "보유", "매도"]},
        },
        seo_keywords=[company_name, ticker, "AI분석", "주식분석", "투자"],
        hashtags=[f"#{company_name}", f"#{ticker.replace('.', '')}", "#AI분석", "#주식투자"],
    )


def render_youtube_studio_main():
    """유튜브 스튜디오 메인 페이지."""
    render_youtube_studio_header()

    # 사이드바: 설정
    with st.sidebar:
        st.markdown("### ⚙️ 콘텐츠 설정")
        persona = render_persona_selector()
        content_type = render_content_type_selector()

    # 메인 영역
    tab1, tab2 = st.tabs(["🎬 콘텐츠 생성", "📦 생성된 패키지"])

    with tab1:
        render_quick_content_generator()

    with tab2:
        if 'generated_package' in st.session_state:
            render_content_package_preview(st.session_state.generated_package)
        else:
            st.info("아직 생성된 콘텐츠가 없습니다. '콘텐츠 생성' 탭에서 시작하세요.")
