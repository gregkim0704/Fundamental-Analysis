"""AI vs Human 대결 아레나 UI 컴포넌트.

AI 투자위원회와 인간 투자자의 치열한 분석 대결을 위한
Streamlit UI 컴포넌트입니다.
"""
import streamlit as st
from datetime import datetime, timedelta
from typing import Optional

from models.battle_game import (
    InvestmentBattle,
    HumanAnalysis,
    AIAnalysisSummary,
    BattleResult,
    BattleRound,
    BattleCategory,
    BattleStatus,
    BattleStatistics,
    TIERS,
    BADGES,
    BATTLE_TYPES,
    calculate_tier,
)


def render_battle_arena_header():
    """대결 아레나 헤더 렌더링."""
    st.markdown("""
    <div style="text-align: center; padding: 20px; background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); border-radius: 15px; margin-bottom: 20px;">
        <h1 style="color: #e94560; margin: 0;">⚔️ AI vs HUMAN ⚔️</h1>
        <h2 style="color: #0f3460; margin: 5px 0;">투자 분석 대결</h2>
        <p style="color: #aaa; margin: 0;">인공지능 투자위원회 vs 인간 투자자의 분석 대결</p>
    </div>
    """, unsafe_allow_html=True)


def render_battle_type_selector() -> str:
    """대결 유형 선택."""
    st.markdown("### 🎮 대결 유형 선택")

    cols = st.columns(len(BATTLE_TYPES))
    selected_type = "standard"

    for i, (type_key, type_info) in enumerate(BATTLE_TYPES.items()):
        with cols[i]:
            icon = {"standard": "⚖️", "speed": "⚡", "deep_dive": "🔬", "contrarian": "🔄"}.get(type_key, "🎯")
            time_text = f"{type_info['time_limit']}분" if type_info['time_limit'] else "무제한"

            if st.button(
                f"{icon}\n{type_info['name']}\n({time_text})",
                key=f"battle_type_{type_key}",
                use_container_width=True
            ):
                selected_type = type_key
                st.session_state.battle_type = type_key

    return st.session_state.get("battle_type", "standard")


def render_ticker_selection() -> Optional[str]:
    """종목 선택."""
    st.markdown("### 📊 대결 종목 선택")

    col1, col2 = st.columns([2, 1])

    with col1:
        ticker = st.text_input(
            "종목 코드 입력",
            placeholder="예: AAPL, 005930.KS",
            key="battle_ticker"
        )

    with col2:
        # 인기 종목 퀵 선택
        popular = st.selectbox(
            "인기 종목",
            options=["직접 입력", "AAPL", "NVDA", "MSFT", "005930.KS", "000660.KS"],
            key="popular_ticker"
        )
        if popular != "직접 입력":
            ticker = popular

    return ticker if ticker else None


def render_human_analysis_form(ticker: str) -> Optional[HumanAnalysis]:
    """인간 분석 입력 폼."""
    st.markdown("### 🧠 당신의 분석을 입력하세요")
    st.markdown("AI와 대결하기 위해 아래 분석을 완성하세요.")

    # 타이머 표시
    if "battle_start_time" not in st.session_state:
        st.session_state.battle_start_time = datetime.now()

    elapsed = (datetime.now() - st.session_state.battle_start_time).seconds // 60
    battle_type = st.session_state.get("battle_type", "standard")
    time_limit = BATTLE_TYPES[battle_type]["time_limit"]

    if time_limit:
        remaining = max(0, time_limit - elapsed)
        color = "green" if remaining > 10 else "orange" if remaining > 5 else "red"
        st.markdown(f"""
        <div style="text-align: center; padding: 10px; background: #1a1a2e; border-radius: 10px; margin-bottom: 20px;">
            <h3 style="color: {color}; margin: 0;">⏱️ 남은 시간: {remaining}분</h3>
        </div>
        """, unsafe_allow_html=True)

    # 기본 정보
    col1, col2 = st.columns(2)

    with col1:
        analyst_name = st.text_input("분석자 이름", key="analyst_name", placeholder="닉네임")
        experience = st.selectbox(
            "투자 경험",
            options=["beginner", "intermediate", "expert", "professional"],
            format_func=lambda x: {"beginner": "🌱 초보 (1년 미만)", "intermediate": "🌿 중급 (1-5년)",
                                   "expert": "🌳 전문가 (5-10년)", "professional": "🏆 프로 (10년+)"}.get(x, x),
            key="experience"
        )

    with col2:
        recommendation = st.selectbox(
            "투자 의견",
            options=["Strong Buy", "Buy", "Hold", "Sell", "Strong Sell"],
            format_func=lambda x: {"Strong Buy": "🚀 적극 매수", "Buy": "📈 매수",
                                   "Hold": "⏸️ 보유", "Sell": "📉 매도", "Strong Sell": "🔻 적극 매도"}.get(x, x),
            key="recommendation"
        )
        target_price = st.number_input("목표 주가", min_value=0.0, key="target_price")

    col3, col4 = st.columns(2)

    with col3:
        confidence = st.slider("확신도", 1, 10, 5, key="confidence")

    with col4:
        time_horizon = st.selectbox(
            "투자 기간",
            options=["1개월", "3개월", "6개월", "1년", "1년 이상"],
            key="time_horizon"
        )

    # 분석 근거
    st.markdown("#### 📝 분석 근거")

    bull_thesis = st.text_area(
        "매수 근거 (줄바꿈으로 구분, 최소 3개)",
        key="bull_thesis",
        height=100,
        placeholder="1. 첫 번째 매수 근거\n2. 두 번째 매수 근거\n3. 세 번째 매수 근거"
    )

    bear_thesis = st.text_area(
        "매도/리스크 근거 (줄바꿈으로 구분, 최소 3개)",
        key="bear_thesis",
        height=100,
        placeholder="1. 첫 번째 리스크\n2. 두 번째 리스크\n3. 세 번째 리스크"
    )

    col5, col6 = st.columns(2)

    with col5:
        catalysts = st.text_area(
            "핵심 촉매/이벤트",
            key="catalysts",
            height=80,
            placeholder="주가 상승을 이끌 핵심 이벤트들"
        )

    with col6:
        risks = st.text_area(
            "주요 리스크",
            key="risks",
            height=80,
            placeholder="투자 리스크 요인들"
        )

    analysis_summary = st.text_area(
        "분석 요약 (200자 이상)",
        key="analysis_summary",
        height=150,
        placeholder="전체 분석 내용을 요약해주세요..."
    )

    # 제출 버튼
    if st.button("⚔️ AI와 대결 시작!", type="primary", use_container_width=True):
        # 유효성 검사
        bull_list = [b.strip() for b in bull_thesis.split("\n") if b.strip()]
        bear_list = [b.strip() for b in bear_thesis.split("\n") if b.strip()]

        if not analyst_name:
            st.error("분석자 이름을 입력해주세요.")
            return None
        if target_price <= 0:
            st.error("목표 주가를 입력해주세요.")
            return None
        if len(bull_list) < 3:
            st.error("매수 근거를 최소 3개 이상 입력해주세요.")
            return None
        if len(bear_list) < 3:
            st.error("매도/리스크 근거를 최소 3개 이상 입력해주세요.")
            return None
        if len(analysis_summary) < 200:
            st.error(f"분석 요약은 200자 이상이어야 합니다. (현재 {len(analysis_summary)}자)")
            return None

        analysis_time = (datetime.now() - st.session_state.battle_start_time).seconds // 60

        return HumanAnalysis(
            analyst_name=analyst_name,
            analyst_experience=experience,
            recommendation=recommendation,
            target_price=target_price,
            confidence_score=confidence,
            time_horizon=time_horizon,
            bull_thesis=bull_list,
            bear_thesis=bear_list,
            key_catalysts=[c.strip() for c in catalysts.split("\n") if c.strip()],
            key_risks=[r.strip() for r in risks.split("\n") if r.strip()],
            analysis_summary=analysis_summary,
            analysis_time_minutes=analysis_time
        )

    return None


def render_battle_comparison(battle: InvestmentBattle):
    """AI vs Human 분석 비교 렌더링."""
    st.markdown("## ⚔️ 분석 대결 비교")

    human = battle.human_analysis
    ai = battle.ai_analysis

    if not human or not ai:
        st.warning("대결 데이터가 완전하지 않습니다.")
        return

    # 헤더
    col1, col2, col3 = st.columns([2, 1, 2])

    with col1:
        st.markdown(f"""
        <div style="text-align: center; padding: 20px; background: #1e3a5f; border-radius: 15px;">
            <h2>🧠 {human.analyst_name}</h2>
            <p>인간 분석가</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div style="text-align: center; padding: 20px;">
            <h1>VS</h1>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div style="text-align: center; padding: 20px; background: #5f1e3a; border-radius: 15px;">
            <h2>🤖 AI 위원회</h2>
            <p>인공지능 투자위원회</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # 투자의견 비교
    st.markdown("### 📊 투자의견 비교")

    col1, col2 = st.columns(2)

    with col1:
        recommendation_color = {
            "Strong Buy": "green", "Buy": "lightgreen",
            "Hold": "gray", "Sell": "orange", "Strong Sell": "red"
        }.get(human.recommendation, "gray")

        st.markdown(f"""
        <div style="text-align: center; padding: 15px; background: #1a1a2e; border-radius: 10px; border: 2px solid {recommendation_color};">
            <h3 style="color: {recommendation_color};">{human.recommendation}</h3>
            <h2>₩{human.target_price:,.0f}</h2>
            <p>확신도: {human.confidence_score}/10</p>
            <p>투자기간: {human.time_horizon}</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        ai_rec_color = {
            "Strong Buy": "green", "Buy": "lightgreen", "적극 매수": "green", "매수": "lightgreen",
            "Hold": "gray", "보유": "gray",
            "Sell": "orange", "매도": "orange",
            "Strong Sell": "red", "적극 매도": "red"
        }.get(ai.recommendation, "gray")

        st.markdown(f"""
        <div style="text-align: center; padding: 15px; background: #1a1a2e; border-radius: 10px; border: 2px solid {ai_rec_color};">
            <h3 style="color: {ai_rec_color};">{ai.recommendation}</h3>
            <h2>₩{ai.target_price:,.0f}</h2>
            <p>확신도: {ai.confidence_score:.1f}/10</p>
            <p>합의수준: {ai.consensus_level}</p>
        </div>
        """, unsafe_allow_html=True)

    # 목표가 차이
    price_diff = abs(human.target_price - ai.target_price)
    price_diff_pct = price_diff / min(human.target_price, ai.target_price) * 100

    if price_diff_pct > 20:
        st.error(f"⚡ 목표가 차이: {price_diff_pct:.1f}% - 치열한 의견 대립!")
    elif price_diff_pct > 10:
        st.warning(f"💥 목표가 차이: {price_diff_pct:.1f}% - 상당한 의견 차이")
    else:
        st.info(f"🤝 목표가 차이: {price_diff_pct:.1f}% - 비교적 유사한 의견")

    # 매수 근거 비교
    st.markdown("### 📈 매수 근거")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**🧠 인간 분석가**")
        for i, thesis in enumerate(human.bull_thesis, 1):
            st.success(f"{i}. {thesis}")

    with col2:
        st.markdown("**🤖 AI 위원회**")
        for i, thesis in enumerate(ai.bull_thesis, 1):
            st.success(f"{i}. {thesis}")

    # 리스크 비교
    st.markdown("### 📉 리스크 요인")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**🧠 인간 분석가**")
        for i, risk in enumerate(human.bear_thesis, 1):
            st.error(f"{i}. {risk}")

    with col2:
        st.markdown("**🤖 AI 위원회**")
        for i, risk in enumerate(ai.bear_thesis, 1):
            st.error(f"{i}. {risk}")

    # 분석 요약 비교
    st.markdown("### 📝 분석 요약")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**🧠 인간 분석가**")
        st.info(human.analysis_summary)

    with col2:
        st.markdown("**🤖 AI 위원회**")
        st.info(ai.analysis_summary)


def render_battle_result(battle: InvestmentBattle):
    """대결 결과 렌더링."""
    if not battle.result:
        st.warning("아직 결과가 없습니다.")
        return

    result = battle.result

    # 승자 발표
    st.markdown("## 🏆 대결 결과")

    winner_text = {
        "human": f"🎉 {battle.human_analysis.analyst_name} 승리!",
        "ai": "🤖 AI 위원회 승리!",
        "draw": "🤝 무승부!"
    }.get(result.final_winner, "결과 대기 중")

    winner_color = {
        "human": "#4CAF50",
        "ai": "#E91E63",
        "draw": "#FFC107"
    }.get(result.final_winner, "#9E9E9E")

    st.markdown(f"""
    <div style="text-align: center; padding: 30px; background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); border-radius: 20px; border: 3px solid {winner_color};">
        <h1 style="color: {winner_color};">{winner_text}</h1>
        <h2>점수: 🧠 {result.human_total_score} vs 🤖 {result.ai_total_score}</h2>
    </div>
    """, unsafe_allow_html=True)

    # 라운드별 결과
    st.markdown("### 📊 카테고리별 결과")

    for round_result in result.round_results:
        with st.expander(f"{round_result.category_name_kr} - {round_result.winner or '진행 중'}"):
            col1, col2 = st.columns(2)

            with col1:
                st.markdown(f"**🧠 인간:** {round_result.human_position}")
                if round_result.human_score:
                    st.metric("점수", round_result.human_score)

            with col2:
                st.markdown(f"**🤖 AI:** {round_result.ai_position}")
                if round_result.ai_score:
                    st.metric("점수", round_result.ai_score)

            if round_result.judge_comment:
                st.info(f"**심판 코멘트:** {round_result.judge_comment}")

    # 획득 배지
    if result.badges_earned:
        st.markdown("### 🏅 획득 배지")
        badge_cols = st.columns(len(result.badges_earned))
        for i, badge_id in enumerate(result.badges_earned):
            badge = BADGES.get(badge_id, {})
            with badge_cols[i]:
                st.markdown(f"""
                <div style="text-align: center; padding: 15px; background: #1a1a2e; border-radius: 10px;">
                    <h1>{badge.get('icon', '🎖️')}</h1>
                    <p>{badge.get('name', badge_id)}</p>
                </div>
                """, unsafe_allow_html=True)

    # 학습 포인트
    if result.lessons_learned:
        st.markdown("### 📚 이번 대결에서 배운 점")
        for lesson in result.lessons_learned:
            st.info(f"💡 {lesson}")


def render_user_stats(stats: BattleStatistics):
    """사용자 통계 렌더링."""
    st.markdown("## 📈 나의 대결 기록")

    tier_info = TIERS.get(stats.tier, TIERS["Bronze"])

    # 프로필 카드
    st.markdown(f"""
    <div style="text-align: center; padding: 20px; background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); border-radius: 15px; border: 2px solid {tier_info['color']};">
        <h1>{tier_info['icon']} {stats.tier}</h1>
        <h2>{stats.username}</h2>
        <p>순위: #{stats.rank}</p>
    </div>
    """, unsafe_allow_html=True)

    # 전적
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("총 대결", stats.total_battles)
    with col2:
        st.metric("승리", stats.wins, delta=f"{stats.win_rate:.1f}%")
    with col3:
        st.metric("패배", stats.losses)
    with col4:
        st.metric("연승", stats.current_streak)

    # 정확도
    col1, col2 = st.columns(2)

    with col1:
        st.metric("목표가 정확도", f"{stats.avg_target_price_accuracy:.1f}%")
    with col2:
        st.metric("방향성 정확도", f"{stats.direction_accuracy_rate:.1f}%")

    # 배지 컬렉션
    if stats.badges:
        st.markdown("### 🏅 배지 컬렉션")
        badge_cols = st.columns(min(5, len(stats.badges)))
        for i, badge_info in enumerate(stats.badges[:5]):
            badge = BADGES.get(badge_info.get("id", ""), {})
            with badge_cols[i]:
                st.markdown(f"""
                <div style="text-align: center; padding: 10px; background: #1a1a2e; border-radius: 10px;">
                    <span style="font-size: 2em;">{badge.get('icon', '🎖️')}</span>
                    <p style="font-size: 0.8em;">{badge.get('name', '')}</p>
                </div>
                """, unsafe_allow_html=True)


def render_leaderboard():
    """리더보드 렌더링."""
    st.markdown("## 🏆 리더보드")

    period = st.radio(
        "기간",
        options=["weekly", "monthly", "all-time"],
        format_func=lambda x: {"weekly": "이번 주", "monthly": "이번 달", "all-time": "전체"}.get(x, x),
        horizontal=True
    )

    # 샘플 리더보드 데이터
    sample_rankings = [
        {"rank": 1, "username": "투자의신", "wins": 45, "win_rate": 78.5, "tier": "Diamond", "icon": "💠"},
        {"rank": 2, "username": "가치투자자", "wins": 38, "win_rate": 72.0, "tier": "Platinum", "icon": "💎"},
        {"rank": 3, "username": "퀀트마스터", "wins": 35, "win_rate": 68.5, "tier": "Gold", "icon": "🥇"},
        {"rank": 4, "username": "버핏워너비", "wins": 30, "win_rate": 65.0, "tier": "Gold", "icon": "🥇"},
        {"rank": 5, "username": "테슬라불", "wins": 28, "win_rate": 62.0, "tier": "Silver", "icon": "🥈"},
    ]

    for ranking in sample_rankings:
        medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(ranking["rank"], "")
        st.markdown(f"""
        <div style="display: flex; align-items: center; padding: 15px; background: #1a1a2e; border-radius: 10px; margin-bottom: 10px;">
            <div style="width: 50px; text-align: center; font-size: 1.5em;">{medal} #{ranking['rank']}</div>
            <div style="flex: 1; padding-left: 15px;">
                <strong>{ranking['username']}</strong>
                <span style="color: #888;"> | {ranking['icon']} {ranking['tier']}</span>
            </div>
            <div style="text-align: right;">
                <span style="color: #4CAF50;">{ranking['wins']}승</span>
                <span style="color: #888;"> ({ranking['win_rate']}%)</span>
            </div>
        </div>
        """, unsafe_allow_html=True)


def render_spectator_voting(battle: InvestmentBattle):
    """관전자 투표 렌더링."""
    st.markdown("### 🗳️ 누가 이길 것 같나요?")

    total_votes = battle.spectator_votes["human"] + battle.spectator_votes["ai"]
    human_pct = (battle.spectator_votes["human"] / total_votes * 100) if total_votes > 0 else 50
    ai_pct = (battle.spectator_votes["ai"] / total_votes * 100) if total_votes > 0 else 50

    col1, col2 = st.columns(2)

    with col1:
        if st.button(f"🧠 인간 ({human_pct:.0f}%)", use_container_width=True):
            st.session_state.voted = "human"
            st.success("투표 완료!")

    with col2:
        if st.button(f"🤖 AI ({ai_pct:.0f}%)", use_container_width=True):
            st.session_state.voted = "ai"
            st.success("투표 완료!")

    # 투표 현황 바
    st.markdown(f"""
    <div style="display: flex; height: 30px; border-radius: 15px; overflow: hidden;">
        <div style="width: {human_pct}%; background: #1e3a5f;"></div>
        <div style="width: {ai_pct}%; background: #5f1e3a;"></div>
    </div>
    <p style="text-align: center; color: #888;">{total_votes}명 투표</p>
    """, unsafe_allow_html=True)


def render_battle_arena_main():
    """대결 아레나 메인 페이지."""
    render_battle_arena_header()

    # 탭 구성
    tabs = st.tabs(["⚔️ 새 대결", "📊 진행 중", "🏆 리더보드", "📈 내 기록"])

    with tabs[0]:
        # 대결 유형 선택
        battle_type = render_battle_type_selector()
        st.markdown(f"**선택된 대결:** {BATTLE_TYPES[battle_type]['name']}")
        st.caption(BATTLE_TYPES[battle_type]['description'])

        # 종목 선택
        ticker = render_ticker_selection()

        if ticker:
            st.success(f"대결 종목: {ticker}")

            # 인간 분석 입력
            human_analysis = render_human_analysis_form(ticker)

            if human_analysis:
                st.session_state.human_analysis = human_analysis
                st.success("분석 제출 완료! AI와 대결을 시작합니다...")
                st.balloons()

    with tabs[1]:
        st.markdown("### 🔄 진행 중인 대결")
        st.info("진행 중인 대결이 없습니다. 새 대결을 시작하세요!")

    with tabs[2]:
        render_leaderboard()

    with tabs[3]:
        # 샘플 통계
        sample_stats = BattleStatistics(
            user_id="sample",
            username="테스트유저",
            total_battles=25,
            wins=15,
            losses=8,
            draws=2,
            win_rate=60.0,
            avg_target_price_accuracy=72.5,
            direction_accuracy_rate=68.0,
            rank=42,
            tier="Gold",
            current_streak=3,
            best_streak=7,
            badges=[{"id": "first_blood"}, {"id": "sniper"}]
        )
        render_user_stats(sample_stats)
