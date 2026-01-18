"""Research input components for Streamlit UI - 사용자 자료 입력 및 검토 결과 표시."""
import streamlit as st
from datetime import datetime
from typing import Optional

from models.user_research import (
    ResearchDocument,
    SourceType,
    UserResearchInput,
    BiasType,
)


def render_research_input_form(ticker: str) -> Optional[UserResearchInput]:
    """사용자 자료 입력 폼 렌더링.

    Args:
        ticker: 분석 대상 종목

    Returns:
        입력된 UserResearchInput 또는 None
    """
    st.markdown("## 📚 참고 자료 입력")
    st.markdown("분석에 참고할 자료들을 입력해주세요. 자료의 신뢰성과 편향을 AI가 검토합니다.")

    # 세션 상태 초기화
    if "research_documents" not in st.session_state:
        st.session_state.research_documents = []

    # 자료 추가 폼
    with st.expander("📄 새 자료 추가", expanded=len(st.session_state.research_documents) == 0):
        col1, col2 = st.columns(2)

        with col1:
            doc_title = st.text_input("자료 제목", key="doc_title")
            source_type = st.selectbox(
                "자료 유형",
                options=[
                    ("company_ir", "회사 IR 자료"),
                    ("analyst_report", "증권사 리포트"),
                    ("news_article", "뉴스 기사"),
                    ("financial_statement", "재무제표"),
                    ("industry_report", "산업 보고서"),
                    ("earnings_call", "실적 발표 콜"),
                    ("regulatory_filing", "공시 자료"),
                    ("social_media", "SNS/커뮤니티"),
                    ("expert_opinion", "전문가 의견"),
                    ("user_analysis", "내 분석"),
                    ("other", "기타"),
                ],
                format_func=lambda x: x[1],
                key="source_type",
            )
            source_name = st.text_input("출처명 (예: 삼성증권, Bloomberg)", key="source_name")

        with col2:
            publish_date = st.date_input("발행일", value=datetime.now(), key="publish_date")
            author = st.text_input("저자/애널리스트", key="author")
            user_trust = st.slider("신뢰도 (내 판단)", 1, 10, 5, key="user_trust")

        doc_content = st.text_area(
            "자료 내용 또는 요약",
            height=150,
            key="doc_content",
            placeholder="자료의 주요 내용을 입력하세요...",
        )

        # 핵심 주장 입력
        key_claims_text = st.text_area(
            "핵심 주장 (줄바꿈으로 구분)",
            height=80,
            key="key_claims",
            placeholder="이 자료의 핵심 주장들을 한 줄에 하나씩 입력하세요.",
        )

        col3, col4 = st.columns(2)
        with col3:
            target_price = st.number_input("목표가 (있는 경우)", min_value=0.0, value=0.0, key="target_price")
        with col4:
            recommendation = st.selectbox(
                "투자의견",
                options=["없음", "Strong Buy", "Buy", "Hold", "Sell", "Strong Sell"],
                key="recommendation",
            )

        url = st.text_input("원본 링크 (선택)", key="doc_url")
        user_notes = st.text_area("내 메모", height=60, key="user_notes")

        if st.button("자료 추가", type="primary"):
            if doc_title and doc_content:
                key_claims = [c.strip() for c in key_claims_text.split("\n") if c.strip()]

                new_doc = ResearchDocument(
                    title=doc_title,
                    source_type=SourceType(source_type[0]),
                    source_name=source_name or "Unknown",
                    content=doc_content,
                    publish_date=datetime.combine(publish_date, datetime.min.time()),
                    author=author if author else None,
                    url=url if url else None,
                    key_claims=key_claims,
                    data_points=[],
                    target_price=target_price if target_price > 0 else None,
                    recommendation=recommendation if recommendation != "없음" else None,
                    user_notes=user_notes if user_notes else None,
                    user_trust_level=user_trust,
                )

                st.session_state.research_documents.append(new_doc)
                st.success(f"'{doc_title}' 추가됨!")
                st.rerun()
            else:
                st.error("제목과 내용은 필수입니다.")

    # 추가된 자료 목록 표시
    if st.session_state.research_documents:
        st.markdown("### 📋 추가된 자료 목록")

        for i, doc in enumerate(st.session_state.research_documents):
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])

                with col1:
                    type_emoji = {
                        "company_ir": "🏢",
                        "analyst_report": "📊",
                        "news_article": "📰",
                        "financial_statement": "📑",
                        "industry_report": "🏭",
                        "earnings_call": "📞",
                        "regulatory_filing": "📝",
                        "social_media": "💬",
                        "expert_opinion": "👨‍💼",
                        "user_analysis": "🔍",
                        "other": "📄",
                    }.get(doc.source_type.value, "📄")

                    st.markdown(f"**{type_emoji} {doc.title}**")
                    st.caption(f"{doc.source_name} | 신뢰도: {doc.user_trust_level}/10")

                with col2:
                    if doc.target_price:
                        st.metric("목표가", f"${doc.target_price:,.0f}")

                with col3:
                    if st.button("삭제", key=f"del_{i}"):
                        st.session_state.research_documents.pop(i)
                        st.rerun()

                st.divider()

    # 사용자 가설 및 질문
    st.markdown("### 💡 투자 가설 및 질문")

    user_hypothesis = st.text_area(
        "투자 가설 (왜 이 종목에 관심이 있는가?)",
        height=80,
        key="user_hypothesis",
        placeholder="예: AI 인프라 투자 확대로 데이터센터 수요가 증가하면 이 회사가 수혜를 받을 것이다.",
    )

    user_concerns_text = st.text_area(
        "우려사항 (줄바꿈으로 구분)",
        height=60,
        key="user_concerns",
        placeholder="예:\n밸류에이션이 너무 높다\n경쟁 심화 우려",
    )

    user_questions_text = st.text_area(
        "알고 싶은 점 (줄바꿈으로 구분)",
        height=60,
        key="user_questions",
        placeholder="예:\n지금 가격이 적정한가?\n경쟁사 대비 경쟁력은?",
    )

    # 투자 컨텍스트
    st.markdown("### ⚙️ 투자 컨텍스트")
    col1, col2 = st.columns(2)

    with col1:
        investment_horizon = st.selectbox(
            "투자 기간",
            options=["단기 (1년 이내)", "중기 (1-3년)", "장기 (3년 이상)"],
            key="investment_horizon",
        )

    with col2:
        risk_tolerance = st.selectbox(
            "위험 허용도",
            options=["보수적", "중립", "공격적"],
            key="risk_tolerance",
        )

    position_context = st.text_input(
        "현재 포지션 상황 (선택)",
        key="position_context",
        placeholder="예: 이미 5% 보유 중, 추가 매수 검토",
    )

    # UserResearchInput 생성 및 반환
    if st.session_state.research_documents or user_hypothesis:
        user_concerns = [c.strip() for c in user_concerns_text.split("\n") if c.strip()]
        user_questions = [q.strip() for q in user_questions_text.split("\n") if q.strip()]

        return UserResearchInput(
            ticker=ticker,
            documents=st.session_state.research_documents,
            user_hypothesis=user_hypothesis if user_hypothesis else None,
            user_concerns=user_concerns,
            user_questions=user_questions,
            investment_horizon=investment_horizon,
            risk_tolerance=risk_tolerance,
            position_context=position_context if position_context else None,
        )

    return None


def render_validation_results(validation_result: dict) -> None:
    """자료 검토 결과 표시.

    Args:
        validation_result: DataValidatorAgent의 분석 결과
    """
    if not validation_result:
        return

    st.markdown("## 🔍 자료 검토 결과")

    # 전체 신뢰도
    overall = validation_result.get("overall_reliability", {})
    col1, col2, col3 = st.columns(3)

    with col1:
        score = overall.get("score", 5)
        color = "green" if score >= 7 else "orange" if score >= 5 else "red"
        st.markdown(f"""
        <div style="text-align: center; padding: 10px; background-color: #1a1a2e; border-radius: 10px;">
            <h3 style="color: {color};">{score}/10</h3>
            <p>전체 신뢰도</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        level = overall.get("level", "unknown")
        level_text = {"high": "높음 ✅", "medium": "보통 ⚠️", "low": "낮음 ❌"}.get(level, "알 수 없음")
        st.markdown(f"""
        <div style="text-align: center; padding: 10px; background-color: #1a1a2e; border-radius: 10px;">
            <h3>{level_text}</h3>
            <p>신뢰도 수준</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        high_bias = overall.get("high_bias_documents", 0)
        st.markdown(f"""
        <div style="text-align: center; padding: 10px; background-color: #1a1a2e; border-radius: 10px;">
            <h3 style="color: {'red' if high_bias > 0 else 'green'};">{high_bias}개</h3>
            <p>높은 편향 자료</p>
        </div>
        """, unsafe_allow_html=True)

    # 개별 자료 검토 결과
    bias_results = validation_result.get("bias_results", [])
    if bias_results:
        st.markdown("### 📄 개별 자료 검토")

        for result in bias_results:
            severity = result.get("bias_severity", "low")
            severity_color = {"low": "#28a745", "medium": "#ffc107", "high": "#dc3545"}.get(severity, "#6c757d")

            with st.expander(f"{result.get('document_title', 'Unknown')} - 신뢰도: {result.get('reliability_score', 'N/A')}/10"):
                # 편향 표시
                biases = result.get("detected_biases", [])
                if biases:
                    st.markdown("**발견된 편향:**")
                    bias_labels = {
                        "bullish_bias": "🟢 낙관적 편향",
                        "bearish_bias": "🔴 비관적 편향",
                        "recency_bias": "⏰ 최근성 편향",
                        "confirmation_bias": "🔄 확증 편향",
                        "survivorship_bias": "💀 생존 편향",
                        "selection_bias": "📊 선택 편향",
                        "conflict_of_interest": "⚠️ 이해충돌",
                        "outdated": "📅 오래된 정보",
                        "incomplete": "❓ 불완전",
                        "unverified": "❔ 미검증",
                    }
                    for bias in biases:
                        label = bias_labels.get(bias, bias)
                        st.markdown(f"  - {label}")

                # 편향 설명
                if result.get("bias_explanation"):
                    st.markdown(f"**분석:** {result['bias_explanation']}")

                # 오래된 정보
                outdated = result.get("outdated_info", [])
                if outdated:
                    st.warning("**오래된 정보:**")
                    for info in outdated:
                        st.markdown(f"  - {info}")

                # 검증 불가 주장
                unverifiable = result.get("unverifiable_claims", [])
                if unverifiable:
                    st.warning("**검증 불가 주장:**")
                    for claim in unverifiable:
                        st.markdown(f"  - {claim}")

                # 활용 권장사항
                if result.get("usage_recommendation"):
                    st.info(f"**활용 권장:** {result['usage_recommendation']}")

                # 주의사항
                caveats = result.get("caveats", [])
                if caveats:
                    st.markdown("**주의사항:**")
                    for caveat in caveats:
                        st.markdown(f"  - ⚠️ {caveat}")


def render_research_synthesis(synthesis: dict) -> None:
    """자료 종합 분석 결과 표시.

    Args:
        synthesis: 종합 분석 결과
    """
    if not synthesis:
        return

    st.markdown("## 📊 자료 종합 분석")

    # 합의점과 의견차
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### ✅ 자료들이 동의하는 점")
        consensus = synthesis.get("consensus_points", [])
        if consensus:
            for point in consensus:
                st.success(point)
        else:
            st.info("합의점 없음")

    with col2:
        st.markdown("### ⚔️ 자료 간 의견 차이")
        divergent = synthesis.get("divergent_points", [])
        if divergent:
            for point in divergent:
                st.warning(point)
        else:
            st.info("의견 차이 없음")

    # 검증된 사실 vs 논쟁 주장
    col3, col4 = st.columns(2)

    with col3:
        st.markdown("### 📌 검증된 사실")
        verified = synthesis.get("verified_facts", [])
        if verified:
            for fact in verified:
                st.markdown(f"✓ {fact}")
        else:
            st.info("검증된 사실 없음")

    with col4:
        st.markdown("### ❓ 논쟁이 있는 주장")
        disputed = synthesis.get("disputed_claims", [])
        if disputed:
            for claim in disputed:
                st.markdown(f"? {claim}")
        else:
            st.info("논쟁 주장 없음")

    # 정보 격차
    gaps = synthesis.get("information_gaps", [])
    if gaps:
        st.markdown("### 🔍 추가 조사 필요 영역")
        for gap in gaps:
            st.error(f"📍 {gap}")

    # 핵심 시사점
    takeaways = synthesis.get("key_takeaways", [])
    if takeaways:
        st.markdown("### 💡 핵심 시사점")
        for takeaway in takeaways:
            st.info(takeaway)

    # 에이전트 집중 영역
    focus_areas = synthesis.get("recommended_focus_areas", [])
    if focus_areas:
        st.markdown("### 🎯 에이전트들이 집중할 영역")
        for area in focus_areas:
            st.markdown(f"➡️ {area}")
