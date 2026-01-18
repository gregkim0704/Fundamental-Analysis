"""Debate visualization components for Streamlit UI."""
import streamlit as st
from typing import Any, Optional


def render_debate_transcript(debate_rounds: list, agent_opinions: dict) -> None:
    """Render the full debate transcript with visual formatting.

    Args:
        debate_rounds: List of DebateRound objects
        agent_opinions: Dictionary of agent opinions
    """
    if not debate_rounds:
        st.info("토론 기록이 없습니다.")
        return

    st.markdown("## 🎭 AI 투자위원회 토론 기록")
    st.markdown("---")

    for round_data in debate_rounds:
        round_num = round_data.round_number if hasattr(round_data, 'round_number') else round_data.get('round_number', 0)

        with st.expander(f"📢 라운드 {round_num}", expanded=(round_num == 1)):
            render_debate_round(round_data)

    # Summary
    st.markdown("---")
    render_debate_summary(debate_rounds, agent_opinions)


def render_debate_round(round_data) -> None:
    """Render a single debate round.

    Args:
        round_data: DebateRound object or dict
    """
    # Get counter arguments
    counter_args = (
        round_data.counter_arguments
        if hasattr(round_data, 'counter_arguments')
        else round_data.get('counter_arguments', [])
    )

    # Get responses
    responses = (
        round_data.responses
        if hasattr(round_data, 'responses')
        else round_data.get('responses', [])
    )

    # Render each challenge-response pair
    for i, counter_arg in enumerate(counter_args):
        target = (
            counter_arg.target_agent.value
            if hasattr(counter_arg, 'target_agent')
            else counter_arg.get('target_agent', 'unknown')
        )

        challenge_text = (
            counter_arg.counter_argument
            if hasattr(counter_arg, 'counter_argument')
            else counter_arg.get('counter_argument', '')
        )

        severity = (
            counter_arg.severity.value
            if hasattr(counter_arg, 'severity')
            else counter_arg.get('severity', 'medium')
        )

        evidence = (
            counter_arg.evidence
            if hasattr(counter_arg, 'evidence')
            else counter_arg.get('evidence', [])
        )

        # Challenge card
        severity_color = {
            "low": "🟢",
            "medium": "🟡",
            "high": "🟠",
            "critical": "🔴",
        }.get(severity, "🟡")

        st.markdown(f"""
        <div style="background-color: #1a1a2e; padding: 15px; border-radius: 10px; margin: 10px 0; border-left: 4px solid #e94560;">
            <div style="color: #e94560; font-weight: bold; margin-bottom: 10px;">
                😈 Devil's Advocate → {target.upper()} {severity_color}
            </div>
            <div style="color: #eee;">
                {challenge_text}
            </div>
        </div>
        """, unsafe_allow_html=True)

        if evidence:
            with st.container():
                st.markdown("**📋 근거:**")
                for ev in evidence[:3]:
                    st.markdown(f"  - {ev}")

        # Find matching response
        matching_response = None
        for resp in responses:
            resp_agent = (
                resp.agent_type.value
                if hasattr(resp, 'agent_type')
                else resp.get('agent_type', '')
            )
            if resp_agent == target:
                matching_response = resp
                break

        if matching_response:
            response_text = (
                matching_response.response
                if hasattr(matching_response, 'response')
                else matching_response.get('response', '')
            )

            adjusted_score = (
                matching_response.adjusted_score
                if hasattr(matching_response, 'adjusted_score')
                else matching_response.get('adjusted_score')
            )

            acknowledged = (
                matching_response.acknowledged_risks
                if hasattr(matching_response, 'acknowledged_risks')
                else matching_response.get('acknowledged_risks', [])
            )

            # Response card
            score_badge = ""
            if adjusted_score:
                if adjusted_score >= 7:
                    score_badge = f"<span style='background-color: #28a745; padding: 2px 8px; border-radius: 4px;'>점수 유지: {adjusted_score}/10</span>"
                elif adjusted_score >= 5:
                    score_badge = f"<span style='background-color: #ffc107; padding: 2px 8px; border-radius: 4px;'>점수 조정: {adjusted_score}/10</span>"
                else:
                    score_badge = f"<span style='background-color: #dc3545; padding: 2px 8px; border-radius: 4px;'>점수 하락: {adjusted_score}/10</span>"

            agent_emoji = {
                "macro": "🌍",
                "quant": "📊",
                "valuation": "💰",
                "qualitative": "🎯",
                "industry": "🏭",
            }.get(target, "🤖")

            st.markdown(f"""
            <div style="background-color: #16213e; padding: 15px; border-radius: 10px; margin: 10px 0 20px 30px; border-left: 4px solid #0f4c75;">
                <div style="color: #0f4c75; font-weight: bold; margin-bottom: 10px;">
                    {agent_emoji} {target.upper()} 방어 {score_badge}
                </div>
                <div style="color: #eee;">
                    {response_text[:500]}{'...' if len(response_text) > 500 else ''}
                </div>
            </div>
            """, unsafe_allow_html=True)

            if acknowledged:
                st.markdown("**⚠️ 인정한 리스크:**")
                for risk in acknowledged:
                    st.markdown(f"  - {risk}")

        st.markdown("<hr style='border: 0.5px solid #333;'>", unsafe_allow_html=True)

    # Round summary
    resolved = (
        round_data.resolved_issues
        if hasattr(round_data, 'resolved_issues')
        else round_data.get('resolved_issues', [])
    )

    remaining = (
        round_data.remaining_concerns
        if hasattr(round_data, 'remaining_concerns')
        else round_data.get('remaining_concerns', [])
    )

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**✅ 해결된 이슈**")
        if resolved:
            for issue in resolved:
                st.success(issue)
        else:
            st.text("없음")

    with col2:
        st.markdown("**❌ 남은 우려**")
        if remaining:
            for concern in remaining:
                st.warning(concern)
        else:
            st.text("없음")


def render_debate_summary(debate_rounds: list, agent_opinions: dict) -> None:
    """Render debate summary with score changes.

    Args:
        debate_rounds: List of debate rounds
        agent_opinions: Final agent opinions
    """
    st.markdown("### 📊 토론 결과 요약")

    # Calculate score changes
    initial_scores = {}
    final_scores = {}

    for agent_key, opinion in agent_opinions.items():
        if agent_key == "devils_advocate":
            continue

        score = (
            opinion.get("score", 5)
            if isinstance(opinion, dict)
            else getattr(opinion, "score", 5)
        )
        final_scores[agent_key] = score

        # Try to find initial score from first round
        if debate_rounds:
            first_round = debate_rounds[0]
            counter_args = (
                first_round.counter_arguments
                if hasattr(first_round, 'counter_arguments')
                else first_round.get('counter_arguments', [])
            )
            for ca in counter_args:
                ca_target = (
                    ca.target_agent.value
                    if hasattr(ca, 'target_agent')
                    else ca.get('target_agent', '')
                )
                if ca_target == agent_key:
                    # Assume original score was higher if adjusted down
                    initial_scores[agent_key] = score + 0.5  # Approximate
                    break

    # Render score comparison
    cols = st.columns(len(final_scores))
    for i, (agent, score) in enumerate(final_scores.items()):
        with cols[i]:
            initial = initial_scores.get(agent, score)
            change = score - initial

            emoji = {
                "macro": "🌍",
                "quant": "📊",
                "valuation": "💰",
            }.get(agent, "🤖")

            if change < -0.5:
                st.metric(
                    f"{emoji} {agent.upper()}",
                    f"{score:.1f}/10",
                    f"{change:+.1f}",
                    delta_color="inverse"
                )
            elif change > 0.5:
                st.metric(
                    f"{emoji} {agent.upper()}",
                    f"{score:.1f}/10",
                    f"{change:+.1f}"
                )
            else:
                st.metric(
                    f"{emoji} {agent.upper()}",
                    f"{score:.1f}/10",
                    "유지"
                )

    # Key takeaways
    st.markdown("### 🔑 핵심 논쟁 포인트")

    all_concerns = []
    for round_data in debate_rounds:
        remaining = (
            round_data.remaining_concerns
            if hasattr(round_data, 'remaining_concerns')
            else round_data.get('remaining_concerns', [])
        )
        all_concerns.extend(remaining)

    if all_concerns:
        for concern in set(all_concerns)[:5]:
            st.markdown(f"- ⚠️ {concern}")
    else:
        st.success("모든 주요 우려사항이 토론을 통해 해소되었습니다.")


def render_debate_chat_view(debate_rounds: list) -> None:
    """Render debate as a chat-like interface.

    Args:
        debate_rounds: List of debate rounds
    """
    st.markdown("## 💬 토론 채팅 뷰")

    for round_data in debate_rounds:
        round_num = (
            round_data.round_number
            if hasattr(round_data, 'round_number')
            else round_data.get('round_number', 0)
        )

        st.markdown(f"### 라운드 {round_num}")

        counter_args = (
            round_data.counter_arguments
            if hasattr(round_data, 'counter_arguments')
            else round_data.get('counter_arguments', [])
        )

        responses = (
            round_data.responses
            if hasattr(round_data, 'responses')
            else round_data.get('responses', [])
        )

        # Interleave challenges and responses
        for counter_arg in counter_args:
            target = (
                counter_arg.target_agent.value
                if hasattr(counter_arg, 'target_agent')
                else counter_arg.get('target_agent', 'unknown')
            )

            challenge = (
                counter_arg.counter_argument
                if hasattr(counter_arg, 'counter_argument')
                else counter_arg.get('counter_argument', '')
            )

            # Devil's Advocate message (left aligned)
            with st.chat_message("assistant", avatar="😈"):
                st.markdown(f"**[→ {target.upper()}]** {challenge}")

            # Find and show response
            for resp in responses:
                resp_agent = (
                    resp.agent_type.value
                    if hasattr(resp, 'agent_type')
                    else resp.get('agent_type', '')
                )

                if resp_agent == target:
                    response_text = (
                        resp.response
                        if hasattr(resp, 'response')
                        else resp.get('response', '')
                    )

                    adjusted = (
                        resp.adjusted_score
                        if hasattr(resp, 'adjusted_score')
                        else resp.get('adjusted_score')
                    )

                    avatar = {
                        "macro": "🌍",
                        "quant": "📊",
                        "valuation": "💰",
                    }.get(target, "🤖")

                    with st.chat_message("user", avatar=avatar):
                        score_note = f" [점수 조정: {adjusted}]" if adjusted else ""
                        st.markdown(f"**{target.upper()}**{score_note}: {response_text}")
                    break
