"""Stock analysis page for Fundamental Analysis app."""
import asyncio
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from tools.stock_price import get_stock_info, get_price_history
from tools.financial_data import get_financial_metrics
from core.financial_analysis import FinancialAnalyzer
from core.valuation_models import get_comprehensive_valuation


def render_analysis_page():
    """Render the stock analysis page."""
    st.title("🔍 Stock Analysis")

    # Get ticker from session state or input
    default_ticker = st.session_state.get("analysis_ticker", "")

    col1, col2 = st.columns([3, 1])
    with col1:
        ticker = st.text_input(
            "Enter Stock Ticker",
            value=default_ticker,
            placeholder="e.g., AAPL, NVDA, 005930.KS",
        )
    with col2:
        st.write("")  # Spacing
        st.write("")
        analyze_button = st.button("🚀 Run Analysis", type="primary", use_container_width=True)

    if ticker and analyze_button:
        run_analysis(ticker)
    elif ticker:
        # Show basic stock info without full analysis
        show_stock_overview(ticker)


def show_stock_overview(ticker: str):
    """Show basic stock overview."""
    with st.spinner(f"Loading {ticker} data..."):
        try:
            stock_info = get_stock_info.invoke({"ticker": ticker})

            if "error" in stock_info:
                st.error(f"Error: {stock_info['error']}")
                return

            # Basic info display
            info = stock_info.get("info", {})

            st.markdown(f"## {info.get('name', ticker)} ({ticker})")

            # Price metrics
            col1, col2, col3, col4 = st.columns(4)

            current_price = stock_info.get("current_price")
            prev_close = stock_info.get("prev_close")
            change = ((current_price - prev_close) / prev_close * 100) if current_price and prev_close else 0

            with col1:
                st.metric(
                    "Current Price",
                    f"${current_price:,.2f}" if current_price else "N/A",
                    f"{change:+.2f}%" if change else None,
                )

            with col2:
                st.metric(
                    "Market Cap",
                    f"${stock_info.get('market_cap', 0)/1e9:.1f}B" if stock_info.get('market_cap') else "N/A",
                )

            with col3:
                st.metric(
                    "P/E Ratio",
                    f"{stock_info.get('pe_ratio', 0):.1f}" if stock_info.get('pe_ratio') else "N/A",
                )

            with col4:
                st.metric(
                    "52W Range",
                    f"${stock_info.get('price_52w_low', 0):.0f} - ${stock_info.get('price_52w_high', 0):.0f}",
                )

            st.info("Click 'Run Analysis' for comprehensive AI-powered analysis")

        except Exception as e:
            st.error(f"Error loading stock data: {e}")


def run_analysis(ticker: str):
    """Run comprehensive analysis."""
    st.markdown(f"## 📊 Comprehensive Analysis: {ticker}")

    # Create tabs for different analyses
    tabs = st.tabs([
        "📈 Overview",
        "💰 Financials",
        "📊 Valuation",
        "🤖 AI Committee",
    ])

    # Overview Tab
    with tabs[0]:
        render_overview_tab(ticker)

    # Financials Tab
    with tabs[1]:
        render_financials_tab(ticker)

    # Valuation Tab
    with tabs[2]:
        render_valuation_tab(ticker)

    # AI Committee Tab
    with tabs[3]:
        render_ai_committee_tab(ticker)


def render_overview_tab(ticker: str):
    """Render overview tab."""
    with st.spinner("Loading overview..."):
        try:
            stock_info = get_stock_info.invoke({"ticker": ticker})
            price_history = get_price_history.invoke({
                "ticker": ticker,
                "period": "1y",
                "interval": "1d"
            })

            if "error" in stock_info:
                st.error(f"Error: {stock_info['error']}")
                return

            info = stock_info.get("info", {})

            # Company Info
            st.markdown("### Company Overview")
            col1, col2 = st.columns([2, 1])

            with col1:
                st.markdown(f"""
                **Name:** {info.get('name', ticker)}
                **Sector:** {info.get('sector', 'N/A')}
                **Industry:** {info.get('industry', 'N/A')}
                **Country:** {info.get('country', 'N/A')}
                """)

            with col2:
                current_price = stock_info.get("current_price")
                market_cap = stock_info.get("market_cap", 0)

                st.markdown(f"""
                **Price:** ${current_price:,.2f} {info.get('currency', 'USD')}
                **Market Cap:** ${market_cap/1e9:.1f}B
                **Volume:** {stock_info.get('volume', 0):,}
                """)

            # Price Chart
            st.markdown("### Price Chart (1 Year)")
            if "data" in price_history and price_history["data"]:
                chart_data = price_history["data"]
                dates = [d["date"] for d in chart_data]
                prices = [d["close"] for d in chart_data]

                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=dates,
                    y=prices,
                    mode='lines',
                    name='Close Price',
                    line=dict(color='#667eea', width=2),
                ))

                fig.update_layout(
                    xaxis_title="Date",
                    yaxis_title="Price",
                    hovermode='x unified',
                    height=400,
                )

                st.plotly_chart(fig, use_container_width=True)

            # Key Statistics
            st.markdown("### Key Statistics")
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.markdown("**Valuation**")
                st.write(f"P/E: {stock_info.get('pe_ratio', 'N/A')}")
                st.write(f"P/B: {stock_info.get('pb_ratio', 'N/A')}")
                st.write(f"P/S: {stock_info.get('ps_ratio', 'N/A')}")
                st.write(f"EV/EBITDA: {stock_info.get('ev_ebitda', 'N/A')}")

            with col2:
                st.markdown("**Profitability**")
                st.write(f"ROE: {stock_info.get('roe', 'N/A')}%")
                st.write(f"ROA: {stock_info.get('roa', 'N/A')}%")
                st.write(f"Profit Margin: {stock_info.get('profit_margin', 'N/A')}%")
                st.write(f"Operating Margin: {stock_info.get('operating_margin', 'N/A')}%")

            with col3:
                st.markdown("**Growth**")
                st.write(f"Revenue Growth: {stock_info.get('revenue_growth', 'N/A')}%")
                st.write(f"Earnings Growth: {stock_info.get('earnings_growth', 'N/A')}%")

            with col4:
                st.markdown("**Financial Health**")
                st.write(f"Current Ratio: {stock_info.get('current_ratio', 'N/A')}")
                st.write(f"D/E Ratio: {stock_info.get('debt_to_equity', 'N/A')}")
                st.write(f"Dividend Yield: {stock_info.get('dividend_yield', 'N/A')}%")

        except Exception as e:
            st.error(f"Error in overview: {e}")


def render_financials_tab(ticker: str):
    """Render financials tab."""
    with st.spinner("Analyzing financials..."):
        try:
            analyzer = FinancialAnalyzer(ticker)
            analysis = analyzer.get_comprehensive_analysis()

            if "error" in analysis:
                st.error(f"Error: {analysis['error']}")
                return

            # Overall Score
            st.markdown("### Financial Health Score")
            score = analysis.get("overall_score", 5)
            score_color = "#28a745" if score >= 7 else "#ffc107" if score >= 5 else "#dc3545"

            col1, col2 = st.columns([1, 3])
            with col1:
                st.markdown(f"""
                <div style='text-align: center; padding: 2rem; background: linear-gradient(135deg, {score_color}, {score_color}99); border-radius: 1rem; color: white;'>
                    <h1 style='margin: 0; font-size: 3rem;'>{score:.1f}</h1>
                    <p style='margin: 0;'>/ 10</p>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                if analysis.get("key_insights"):
                    st.markdown("**Key Insights:**")
                    for insight in analysis["key_insights"][:5]:
                        st.markdown(f"✅ {insight}")

                if analysis.get("key_concerns"):
                    st.markdown("**Concerns:**")
                    for concern in analysis["key_concerns"][:5]:
                        st.markdown(f"⚠️ {concern}")

            # Value Creation
            st.markdown("### Value Creation Analysis")
            value_creation = analysis.get("value_creation", {})

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                roic = value_creation.get("roic", 0)
                st.metric("ROIC", f"{roic:.1f}%" if roic else "N/A")
            with col2:
                wacc = value_creation.get("wacc", 0)
                st.metric("WACC", f"{wacc:.1f}%" if wacc else "N/A")
            with col3:
                spread = value_creation.get("spread", 0)
                st.metric("ROIC-WACC Spread", f"{spread:.1f}%" if spread else "N/A",
                         delta="Value Creating" if spread and spread > 0 else "Value Destroying")
            with col4:
                eva = value_creation.get("eva", 0)
                st.metric("EVA", f"${eva/1e6:.0f}M" if eva else "N/A")

            # Profitability Trends
            st.markdown("### Profitability Trends")
            profitability = analysis.get("profitability", {})
            history = profitability.get("history", [])

            if history:
                years = [h["year"] for h in history]
                gross_margins = [h.get("gross_margin") for h in history]
                op_margins = [h.get("operating_margin") for h in history]
                net_margins = [h.get("net_margin") for h in history]

                fig = go.Figure()
                fig.add_trace(go.Bar(name="Gross Margin", x=years, y=gross_margins))
                fig.add_trace(go.Bar(name="Operating Margin", x=years, y=op_margins))
                fig.add_trace(go.Bar(name="Net Margin", x=years, y=net_margins))

                fig.update_layout(
                    barmode='group',
                    xaxis_title="Year",
                    yaxis_title="Margin (%)",
                    height=350,
                )
                st.plotly_chart(fig, use_container_width=True)

        except Exception as e:
            st.error(f"Error in financial analysis: {e}")


def render_valuation_tab(ticker: str):
    """Render valuation tab."""
    with st.spinner("Running valuation analysis..."):
        try:
            valuation = get_comprehensive_valuation(ticker)

            if "error" in valuation:
                st.error(f"Error: {valuation['error']}")
                return

            current_price = valuation.get("current_price", 0)
            target_range = valuation.get("target_price_range", {})

            # Target Price Range
            st.markdown("### Target Price Range")

            col1, col2, col3 = st.columns(3)
            with col1:
                low = target_range.get("low", 0)
                upside_low = valuation.get("upside_potential", {}).get("to_low", 0)
                st.metric("Bear Case", f"${low:.2f}" if low else "N/A",
                         f"{upside_low:+.1f}%" if upside_low else None)
            with col2:
                mid = target_range.get("mid", 0)
                upside_mid = valuation.get("upside_potential", {}).get("to_mid", 0)
                st.metric("Base Case", f"${mid:.2f}" if mid else "N/A",
                         f"{upside_mid:+.1f}%" if upside_mid else None)
            with col3:
                high = target_range.get("high", 0)
                upside_high = valuation.get("upside_potential", {}).get("to_high", 0)
                st.metric("Bull Case", f"${high:.2f}" if high else "N/A",
                         f"{upside_high:+.1f}%" if upside_high else None)

            # Price Position Chart
            if all([low, mid, high, current_price]):
                st.markdown("### Price Position")
                fig = go.Figure()

                # Add range bar
                fig.add_trace(go.Bar(
                    x=[high - low],
                    y=["Target Range"],
                    orientation='h',
                    base=low,
                    marker_color='lightblue',
                    name='Target Range',
                ))

                # Add current price marker
                fig.add_vline(x=current_price, line_dash="dash", line_color="red")
                fig.add_annotation(x=current_price, y="Target Range",
                                  text=f"Current: ${current_price:.2f}",
                                  showarrow=True, arrowhead=2)

                fig.update_layout(height=200, showlegend=False)
                st.plotly_chart(fig, use_container_width=True)

            # DCF Details
            st.markdown("### DCF Valuation Details")
            dcf = valuation.get("dcf_valuation", {}).get("base_case", {})

            if dcf.get("assumptions"):
                st.markdown("**Key Assumptions:**")
                assumptions = dcf.get("assumptions", {})
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.write(f"Growth Rate: {assumptions.get('high_growth_rate', 'N/A')}")
                with col2:
                    st.write(f"Terminal Growth: {assumptions.get('terminal_growth_rate', 'N/A')}")
                with col3:
                    st.write(f"WACC: {assumptions.get('wacc', 'N/A')}")

            # Relative Valuation
            st.markdown("### Relative Valuation")
            relative = valuation.get("relative_valuation", {})
            multiples = relative.get("current_multiples", {})

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("P/E", f"{multiples.get('pe_ratio', 'N/A'):.1f}" if multiples.get('pe_ratio') else "N/A")
            with col2:
                st.metric("P/B", f"{multiples.get('pb_ratio', 'N/A'):.2f}" if multiples.get('pb_ratio') else "N/A")
            with col3:
                st.metric("P/S", f"{multiples.get('ps_ratio', 'N/A'):.2f}" if multiples.get('ps_ratio') else "N/A")
            with col4:
                st.metric("EV/EBITDA", f"{multiples.get('ev_ebitda', 'N/A'):.1f}" if multiples.get('ev_ebitda') else "N/A")

        except Exception as e:
            st.error(f"Error in valuation analysis: {e}")


def render_ai_committee_tab(ticker: str):
    """Render AI Committee analysis tab."""
    st.markdown("### 🤖 AI Investment Committee Analysis")

    st.info("""
    **Note:** Full AI Committee analysis requires API key configuration.
    Configure your Anthropic API key in Settings to enable this feature.
    """)

    # Show what the analysis would include
    st.markdown("""
    The AI Investment Committee analysis includes:

    #### Phase 1: Independent Analysis
    - 🌍 **Macro Agent**: Macro environment impact assessment
    - 💰 **Quant Agent**: Financial statement deep dive
    - 🎯 **Qualitative Agent**: Moat and management analysis
    - 🏭 **Industry Agent**: Industry structure analysis
    - 📈 **Valuation Agent**: Multi-method valuation
    - ⚠️ **Risk Agent**: Risk identification and quantification

    #### Phase 2: Cross-Verification & Debate
    - 😈 **Devil's Advocate**: Challenges all bullish assumptions
    - 🔄 **3-Round Debate**: Counter-arguments and responses
    - ⚖️ **Resolution**: Chairman mediates disagreements

    #### Phase 3: Final Decision
    - 📊 **Weighted Voting**: Confidence-weighted scores
    - 📋 **Committee Report**: Executive summary
    - 🎯 **Recommendation**: Buy/Hold/Sell with target prices
    """)

    # Mock committee result display
    st.markdown("---")
    st.markdown("### Sample Committee Output Structure")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        **Agent Votes:**
        | Agent | Score | Confidence |
        |-------|-------|------------|
        | Macro | 7.5 | 80% |
        | Quant | 8.0 | 85% |
        | Qualitative | 6.5 | 70% |
        | Industry | 7.0 | 75% |
        | Valuation | 7.5 | 80% |
        | Risk | 6.0 | 85% |
        """)

    with col2:
        st.markdown("""
        **Committee Decision:**
        - **Weighted Score:** 7.2 / 10
        - **Consensus Level:** 78%
        - **Recommendation:** BUY
        - **Conviction:** Medium-High
        - **Risk Level:** Medium
        """)

    # Enable analysis button (requires API key)
    if st.button("🚀 Run Full AI Committee Analysis", type="primary", use_container_width=True):
        st.warning("Please configure your Anthropic API key in Settings to run the full analysis.")
