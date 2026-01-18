"""Chart components for the Streamlit app."""
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st
from typing import Any, Optional


def render_header():
    """Render the application header."""
    st.markdown("""
    <div style='text-align: center; padding: 1rem;'>
        <h1 style='color: #667eea;'>📊 Fundamental Analysis Pro</h1>
        <p style='color: #666;'>AI 투자위원회 기반 체계적인 주식 분석 플랫폼</p>
    </div>
    """, unsafe_allow_html=True)


def render_score_gauge(score: float, title: str = "Score") -> go.Figure:
    """Render a gauge chart for scores.

    Args:
        score: Score value (1-10)
        title: Chart title

    Returns:
        Plotly figure
    """
    color = "#28a745" if score >= 7 else "#ffc107" if score >= 5 else "#dc3545"

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': title},
        gauge={
            'axis': {'range': [1, 10]},
            'bar': {'color': color},
            'steps': [
                {'range': [1, 4], 'color': "#ffcccc"},
                {'range': [4, 7], 'color': "#ffffcc"},
                {'range': [7, 10], 'color': "#ccffcc"},
            ],
            'threshold': {
                'line': {'color': "black", 'width': 4},
                'thickness': 0.75,
                'value': score
            }
        }
    ))

    fig.update_layout(height=250, margin=dict(l=20, r=20, t=40, b=20))
    return fig


def render_agent_scores_radar(scores: dict[str, float]) -> go.Figure:
    """Render a radar chart for agent scores.

    Args:
        scores: Dictionary of agent names to scores

    Returns:
        Plotly figure
    """
    categories = list(scores.keys())
    values = list(scores.values())

    # Close the radar chart
    categories.append(categories[0])
    values.append(values[0])

    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself',
        name='Agent Scores',
        line_color='#667eea',
        fillcolor='rgba(102, 126, 234, 0.3)',
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 10]
            )
        ),
        showlegend=False,
        height=400,
    )

    return fig


def render_price_target_chart(
    current_price: float,
    target_low: float,
    target_mid: float,
    target_high: float,
) -> go.Figure:
    """Render a price target visualization.

    Args:
        current_price: Current stock price
        target_low: Bear case target
        target_mid: Base case target
        target_high: Bull case target

    Returns:
        Plotly figure
    """
    fig = go.Figure()

    # Add target range bar
    fig.add_trace(go.Bar(
        x=['Target Range'],
        y=[target_high - target_low],
        base=target_low,
        name='Target Range',
        marker_color='lightblue',
        width=0.5,
    ))

    # Add markers for key prices
    fig.add_trace(go.Scatter(
        x=['Target Range'],
        y=[current_price],
        mode='markers',
        marker=dict(size=15, color='red', symbol='diamond'),
        name='Current Price',
    ))

    fig.add_trace(go.Scatter(
        x=['Target Range'],
        y=[target_mid],
        mode='markers',
        marker=dict(size=12, color='green', symbol='star'),
        name='Base Target',
    ))

    fig.update_layout(
        title='Price Target Analysis',
        yaxis_title='Price',
        height=400,
        showlegend=True,
    )

    return fig


def render_margin_trends(data: list[dict]) -> go.Figure:
    """Render margin trends chart.

    Args:
        data: List of dicts with year, gross_margin, operating_margin, net_margin

    Returns:
        Plotly figure
    """
    if not data:
        return go.Figure()

    years = [d.get('year') for d in data]
    gross = [d.get('gross_margin') for d in data]
    operating = [d.get('operating_margin') for d in data]
    net = [d.get('net_margin') for d in data]

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=years, y=gross,
        mode='lines+markers',
        name='Gross Margin',
        line=dict(color='#28a745'),
    ))

    fig.add_trace(go.Scatter(
        x=years, y=operating,
        mode='lines+markers',
        name='Operating Margin',
        line=dict(color='#667eea'),
    ))

    fig.add_trace(go.Scatter(
        x=years, y=net,
        mode='lines+markers',
        name='Net Margin',
        line=dict(color='#dc3545'),
    ))

    fig.update_layout(
        title='Margin Trends',
        xaxis_title='Year',
        yaxis_title='Margin (%)',
        height=350,
        hovermode='x unified',
    )

    return fig


def render_risk_matrix(risks: list[dict]) -> go.Figure:
    """Render a risk matrix visualization.

    Args:
        risks: List of risk dicts with severity and probability

    Returns:
        Plotly figure
    """
    severity_map = {'low': 1, 'medium': 2, 'high': 3, 'critical': 4}
    prob_map = {'low': 1, 'medium': 2, 'high': 3}

    x_vals = []
    y_vals = []
    texts = []
    colors = []

    for risk in risks:
        sev = severity_map.get(risk.get('severity', 'medium').lower(), 2)
        prob = prob_map.get(risk.get('probability', 'medium').lower(), 2)
        x_vals.append(prob)
        y_vals.append(sev)
        texts.append(risk.get('description', '')[:30])
        colors.append(sev * prob)

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=x_vals,
        y=y_vals,
        mode='markers+text',
        marker=dict(
            size=30,
            color=colors,
            colorscale='RdYlGn_r',
            showscale=True,
        ),
        text=texts,
        textposition='top center',
    ))

    fig.update_layout(
        title='Risk Matrix',
        xaxis=dict(
            title='Probability',
            tickvals=[1, 2, 3],
            ticktext=['Low', 'Medium', 'High'],
            range=[0.5, 3.5],
        ),
        yaxis=dict(
            title='Severity',
            tickvals=[1, 2, 3, 4],
            ticktext=['Low', 'Medium', 'High', 'Critical'],
            range=[0.5, 4.5],
        ),
        height=400,
    )

    return fig


def render_committee_vote_chart(votes: list[dict]) -> go.Figure:
    """Render committee voting visualization.

    Args:
        votes: List of vote dicts with agent_type, score, confidence

    Returns:
        Plotly figure
    """
    if not votes:
        return go.Figure()

    agents = [v.get('agent_type', '') for v in votes]
    scores = [v.get('score', 5) for v in votes]
    confidences = [v.get('confidence', 50) for v in votes]

    fig = go.Figure()

    # Add score bars
    fig.add_trace(go.Bar(
        name='Score',
        x=agents,
        y=scores,
        marker_color=['#28a745' if s >= 7 else '#ffc107' if s >= 5 else '#dc3545' for s in scores],
    ))

    # Add confidence line
    fig.add_trace(go.Scatter(
        name='Confidence',
        x=agents,
        y=[c/10 for c in confidences],  # Scale to same axis
        mode='lines+markers',
        yaxis='y2',
        line=dict(color='#667eea', dash='dash'),
    ))

    fig.update_layout(
        title='Committee Votes',
        xaxis_title='Agent',
        yaxis=dict(title='Score', range=[0, 10]),
        yaxis2=dict(
            title='Confidence (%)',
            overlaying='y',
            side='right',
            range=[0, 100],
        ),
        height=400,
        barmode='group',
    )

    return fig
