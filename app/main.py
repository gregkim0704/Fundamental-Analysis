"""Main Streamlit application for Fundamental Analysis Pro.

AI 투자위원회 - 멀티에이전트 기반 주식 분석 플랫폼
"""
import streamlit as st
from datetime import datetime
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Page configuration - MUST be first Streamlit command
st.set_page_config(
    page_title="AI 투자위원회 | Fundamental Analysis Pro",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/your-repo/fundamental-analysis',
        'Report a bug': 'https://github.com/your-repo/fundamental-analysis/issues',
        'About': '# AI 투자위원회\n멀티에이전트 기반 주식 분석 플랫폼'
    }
)

# Import pages after st.set_page_config
from app.pages.dashboard import render_dashboard
from app.pages.analysis import render_analysis_page
from app.components.battle_arena import render_battle_arena_main
from app.components.youtube_studio import render_youtube_studio_main

# Custom CSS for dark theme
st.markdown("""
<style>
    /* Global Styles */
    .stApp {
        max-width: 1600px;
        margin: 0 auto;
    }

    /* Header Styles */
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 1rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    /* Card Styles */
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 1rem;
        color: white;
        margin-bottom: 1rem;
    }

    .agent-card {
        background: #1a1a2e;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #667eea;
        margin-bottom: 0.5rem;
    }

    /* Score Colors */
    .score-high { color: #28a745; }
    .score-medium { color: #ffc107; }
    .score-low { color: #dc3545; }

    /* Sentiment Colors */
    .sentiment-bullish { color: #28a745; font-weight: bold; }
    .sentiment-neutral { color: #6c757d; }
    .sentiment-bearish { color: #dc3545; font-weight: bold; }

    /* Navigation Styles */
    .nav-link {
        padding: 0.5rem 1rem;
        border-radius: 0.5rem;
        margin-bottom: 0.25rem;
        transition: background 0.3s;
    }

    .nav-link:hover {
        background: #ffffff11;
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }

    ::-webkit-scrollbar-track {
        background: #1a1a2e;
    }

    ::-webkit-scrollbar-thumb {
        background: #667eea;
        border-radius: 4px;
    }
</style>
""", unsafe_allow_html=True)


def check_api_keys():
    """Check if required API keys are configured."""
    try:
        anthropic_key = st.secrets.get("ANTHROPIC_API_KEY", "")
        return bool(anthropic_key)
    except Exception:
        return False


def render_sidebar():
    """Render sidebar navigation."""
    with st.sidebar:
        # Logo and Title
        st.markdown("""
        <div style="text-align: center; padding: 1rem 0;">
            <h1 style="margin: 0; font-size: 2rem;">🏛️</h1>
            <h2 style="margin: 0; font-size: 1.2rem; color: #667eea;">AI 투자위원회</h2>
            <p style="margin: 0; font-size: 0.8rem; color: #888;">Fundamental Analysis Pro</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        # Navigation
        page = st.radio(
            "Navigation",
            [
                "📊 대시보드",
                "🔍 종목 분석",
                "⚔️ AI vs Human 대결",
                "🎬 콘텐츠 스튜디오",
                "📋 관심종목",
                "⚙️ 설정",
            ],
            label_visibility="collapsed",
            key="nav_page",
        )

        st.markdown("---")

        # Quick Analysis
        st.markdown("### ⚡ 빠른 분석")
        quick_ticker = st.text_input(
            "종목 코드",
            placeholder="예: AAPL, 005930.KS",
            key="quick_ticker",
            label_visibility="collapsed",
        )

        if st.button("🔍 분석 시작", key="quick_analyze", use_container_width=True):
            if quick_ticker:
                st.session_state["analysis_ticker"] = quick_ticker.upper()
                st.rerun()

        st.markdown("---")

        # Status
        api_status = "🟢 연결됨" if check_api_keys() else "🔴 API 키 필요"
        st.caption(f"API 상태: {api_status}")
        st.caption(f"업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

        # Footer
        st.markdown("---")
        st.markdown("""
        <div style="text-align: center; font-size: 0.7rem; color: #666;">
            <p>Made with ❤️ by AI Investment Committee</p>
            <p>v1.0.0</p>
        </div>
        """, unsafe_allow_html=True)

    return page


def render_watchlist_page():
    """Render the watchlist page."""
    st.markdown("# 📋 관심종목")

    # Initialize watchlist in session state
    if "watchlist" not in st.session_state:
        st.session_state["watchlist"] = []

    # Add ticker to watchlist
    col1, col2 = st.columns([3, 1])
    with col1:
        new_ticker = st.text_input(
            "종목 추가",
            placeholder="종목 코드 입력...",
            label_visibility="collapsed",
        )
    with col2:
        if st.button("➕ 추가", use_container_width=True):
            if new_ticker and new_ticker.upper() not in st.session_state["watchlist"]:
                st.session_state["watchlist"].append(new_ticker.upper())
                st.success(f"✅ {new_ticker.upper()} 추가됨")
                st.rerun()

    st.markdown("---")

    # Display watchlist
    if st.session_state["watchlist"]:
        for ticker in st.session_state["watchlist"]:
            col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
            with col1:
                st.markdown(f"### {ticker}")
            with col2:
                if st.button("🔍 분석", key=f"analyze_{ticker}", use_container_width=True):
                    st.session_state["analysis_ticker"] = ticker
                    st.rerun()
            with col3:
                if st.button("⚔️ 대결", key=f"battle_{ticker}", use_container_width=True):
                    st.session_state["battle_ticker"] = ticker
                    st.rerun()
            with col4:
                if st.button("🗑️", key=f"remove_{ticker}", use_container_width=True):
                    st.session_state["watchlist"].remove(ticker)
                    st.rerun()
            st.markdown("---")
    else:
        st.info("👆 관심종목을 추가하여 빠르게 분석하세요!")

        # 추천 종목
        st.markdown("### 💡 인기 종목")
        popular = ["AAPL", "NVDA", "MSFT", "005930.KS", "000660.KS"]
        cols = st.columns(len(popular))
        for i, ticker in enumerate(popular):
            with cols[i]:
                if st.button(ticker, key=f"pop_{ticker}", use_container_width=True):
                    st.session_state["watchlist"].append(ticker)
                    st.rerun()


def render_settings_page():
    """Render the settings page."""
    st.markdown("# ⚙️ 설정")

    tab1, tab2, tab3 = st.tabs(["🔑 API 설정", "🎛️ 분석 설정", "🎨 화면 설정"])

    with tab1:
        st.markdown("### API 키 설정")
        st.info("""
        **Streamlit Cloud 배포 시:**
        1. [share.streamlit.io](https://share.streamlit.io) 접속
        2. 앱 설정 > Secrets 메뉴
        3. `.streamlit/secrets.toml.example` 참고하여 설정
        """)

        st.text_input(
            "Anthropic API Key",
            type="password",
            key="anthropic_key",
            help="Claude AI 사용을 위한 API 키"
        )
        st.text_input(
            "OpenDART API Key",
            type="password",
            key="opendart_key",
            help="한국 주식 공시정보 조회용"
        )
        st.text_input(
            "FRED API Key",
            type="password",
            key="fred_key",
            help="미국 거시경제 데이터 조회용"
        )

    with tab2:
        st.markdown("### AI 분석 설정")

        st.slider(
            "토론 라운드 수",
            min_value=1,
            max_value=5,
            value=3,
            key="debate_rounds",
            help="AI 에이전트 간 토론 횟수"
        )

        st.checkbox(
            "악마의 변호인 포함",
            value=True,
            key="include_devils",
            help="비판적 관점 에이전트 포함 여부"
        )

        st.selectbox(
            "분석 깊이",
            options=["빠른 분석", "표준 분석", "심층 분석"],
            index=1,
            key="analysis_depth",
        )

    with tab3:
        st.markdown("### 화면 설정")

        st.selectbox(
            "언어",
            options=["한국어", "English"],
            key="language",
        )

        st.selectbox(
            "테마",
            options=["다크 모드", "라이트 모드", "시스템 설정"],
            key="theme",
        )

        st.checkbox(
            "애니메이션 효과",
            value=True,
            key="animations",
        )

    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("💾 설정 저장", type="primary", use_container_width=True):
            st.success("✅ 설정이 저장되었습니다!")
    with col2:
        if st.button("🔄 기본값 복원", use_container_width=True):
            st.info("기본 설정으로 복원되었습니다.")


def render_welcome_banner():
    """Render welcome banner for first-time users."""
    if "welcome_dismissed" not in st.session_state:
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 2rem;
            border-radius: 1rem;
            margin-bottom: 2rem;
            color: white;
        ">
            <h2 style="margin: 0;">🏛️ AI 투자위원회에 오신 것을 환영합니다!</h2>
            <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">
                6명의 AI 애널리스트가 토론을 통해 종목을 분석합니다.
                AI와 대결하고, 유튜브 콘텐츠도 만들어보세요!
            </p>
        </div>
        """, unsafe_allow_html=True)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("""
            <div style="text-align: center; padding: 1rem;">
                <h1>🔍</h1>
                <h4>종목 분석</h4>
                <p style="font-size: 0.9rem; color: #888;">
                    AI 위원회의 심층 분석
                </p>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown("""
            <div style="text-align: center; padding: 1rem;">
                <h1>⚔️</h1>
                <h4>AI vs Human</h4>
                <p style="font-size: 0.9rem; color: #888;">
                    당신의 분석 실력 테스트
                </p>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown("""
            <div style="text-align: center; padding: 1rem;">
                <h1>🎬</h1>
                <h4>콘텐츠 스튜디오</h4>
                <p style="font-size: 0.9rem; color: #888;">
                    유튜브 영상 자동 생성
                </p>
            </div>
            """, unsafe_allow_html=True)

        if st.button("시작하기 →", type="primary"):
            st.session_state["welcome_dismissed"] = True
            st.rerun()

        st.markdown("---")


def main():
    """Main application entry point."""
    # Render sidebar and get selected page
    page = render_sidebar()

    # Check API configuration
    if not check_api_keys() and page not in ["⚙️ 설정", "📊 대시보드"]:
        st.warning("⚠️ API 키가 설정되지 않았습니다. 설정 페이지에서 API 키를 입력하세요.")

    # Route to selected page
    if page == "📊 대시보드":
        render_welcome_banner()
        render_dashboard()
    elif page == "🔍 종목 분석":
        render_analysis_page()
    elif page == "⚔️ AI vs Human 대결":
        render_battle_arena_main()
    elif page == "🎬 콘텐츠 스튜디오":
        render_youtube_studio_main()
    elif page == "📋 관심종목":
        render_watchlist_page()
    elif page == "⚙️ 설정":
        render_settings_page()


if __name__ == "__main__":
    main()
