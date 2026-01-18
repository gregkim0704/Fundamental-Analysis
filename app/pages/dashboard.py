"""Dashboard page for Fundamental Analysis app."""
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def render_dashboard():
    """Render the main dashboard."""
    st.title("📊 Fundamental Analysis Dashboard")
    st.markdown("AI 투자위원회 기반 체계적인 주식 분석 플랫폼")

    # Quick stats row
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="🌍 Macro Environment",
            value="Neutral",
            delta="금리 인하 기대",
        )

    with col2:
        st.metric(
            label="📈 Market Trend",
            value="Bullish",
            delta="+2.3% MTD",
        )

    with col3:
        st.metric(
            label="⚠️ Risk Level",
            value="Medium",
            delta="VIX 18.5",
        )

    with col4:
        st.metric(
            label="📋 Analyses Today",
            value="0",
            delta="Start analyzing!",
        )

    st.markdown("---")

    # Main content area
    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("### 🤖 AI 투자위원회 구조")
        st.markdown("""
        이 앱은 **Multi-Agent 시스템**으로 다양한 전문 에이전트가 협력하여 투자 의사결정을 내립니다:

        | 에이전트 | 역할 | 분석 영역 |
        |----------|------|-----------|
        | 🎩 **Chairman** | 의장 | 전체 조율, 최종 결정 |
        | 🌍 **Macro** | 거시경제 | 금리, 유동성, 경기 사이클 |
        | 💰 **Quant** | 재무분석 | ROIC, 이익의 질, FCF |
        | 🎯 **Qualitative** | 정성분석 | Moat, 경영진, 거버넌스 |
        | 🏭 **Industry** | 산업분석 | 경쟁구도, 시장구조 |
        | 📈 **Valuation** | 밸류에이션 | DCF, 상대가치 |
        | ⚠️ **Risk** | 리스크 | 사업/재무/시장 리스크 |
        | 😈 **Devil's Advocate** | 반대논거 | 맹점 발견, Pre-mortem |
        """)

    with col2:
        st.markdown("### 📌 Quick Start")
        st.info("""
        1. 사이드바에서 티커 입력
        2. "Analyze" 버튼 클릭
        3. AI 위원회 분석 대기
        4. 종합 보고서 확인
        """)

        st.markdown("### 🔥 Popular Tickers")
        popular = ["AAPL", "NVDA", "MSFT", "005930.KS", "GOOGL"]
        for ticker in popular:
            if st.button(ticker, key=f"popular_{ticker}", use_container_width=True):
                st.session_state["analysis_ticker"] = ticker
                st.session_state["page"] = "🔍 Stock Analysis"
                st.rerun()

    st.markdown("---")

    # Analysis workflow visualization
    st.markdown("### 🔄 분석 프로세스")

    # Create workflow diagram using Plotly
    fig = go.Figure()

    # Nodes
    nodes = [
        ("사용자 요청", 0, 2),
        ("Chairman", 1, 2),
        ("Macro Agent", 2, 3),
        ("Quant Agent", 2, 2.5),
        ("Qualitative Agent", 2, 2),
        ("Industry Agent", 2, 1.5),
        ("Valuation Agent", 3, 2.5),
        ("Risk Agent", 3, 1.5),
        ("Devil's Advocate", 4, 2),
        ("토론 & 검증", 5, 2),
        ("최종 의사결정", 6, 2),
    ]

    # Add nodes
    for name, x, y in nodes:
        fig.add_trace(go.Scatter(
            x=[x], y=[y],
            mode='markers+text',
            marker=dict(size=40, color='#667eea'),
            text=[name],
            textposition='bottom center',
            hoverinfo='text',
        ))

    # Add edges
    edges = [
        (0, 1), (1, 2), (1, 3), (1, 4), (1, 5),
        (2, 6), (3, 6), (4, 6), (5, 7),
        (6, 8), (7, 8), (8, 9), (9, 10),
    ]

    for start, end in edges:
        x0, y0 = nodes[start][1], nodes[start][2]
        x1, y1 = nodes[end][1], nodes[end][2]
        fig.add_trace(go.Scatter(
            x=[x0, x1], y=[y0, y1],
            mode='lines',
            line=dict(color='#ccc', width=2),
            hoverinfo='none',
        ))

    fig.update_layout(
        showlegend=False,
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        height=300,
        margin=dict(l=20, r=20, t=20, b=20),
    )

    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Features overview
    st.markdown("### ✨ 주요 기능")

    feat_col1, feat_col2, feat_col3 = st.columns(3)

    with feat_col1:
        st.markdown("""
        #### 📊 거시 환경 분석
        - 금리 사이클 추적
        - 유동성 지표 모니터링
        - 섹터 로테이션 분석
        - 정책 영향 평가
        """)

    with feat_col2:
        st.markdown("""
        #### 💰 재무 심층 분석
        - ROIC vs WACC 스프레드
        - 이익의 질 분석
        - 현금흐름 품질 평가
        - 가치 창출 분석
        """)

    with feat_col3:
        st.markdown("""
        #### 🎯 정성적 분석
        - 경쟁우위(Moat) 평가
        - 경영진 품질 분석
        - Porter's 5 Forces
        - ESG 고려사항
        """)

    st.markdown("---")

    # Footer
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 2rem;'>
        <p>Powered by Claude Opus 4.5 & LangGraph</p>
        <p>© 2024 Fundamental Analysis Pro</p>
    </div>
    """, unsafe_allow_html=True)
