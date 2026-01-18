"""썸네일 및 시각 콘텐츠 생성 서비스.

유튜브 썸네일, 인포그래픽, 차트 등 시각 자료를 생성합니다.
"""
import logging
from io import BytesIO
from typing import Optional
import json

from models.youtube_content import ThumbnailSpec, VisualAsset

logger = logging.getLogger(__name__)


# =============================================================================
# 썸네일 HTML 템플릿 (Streamlit에서 렌더링용)
# =============================================================================

THUMBNAIL_TEMPLATES = {
    "dramatic": """
    <div style="
        width: 1280px;
        height: 720px;
        background: linear-gradient(135deg, {bg_color1} 0%, {bg_color2} 100%);
        position: relative;
        font-family: 'Noto Sans KR', sans-serif;
        overflow: hidden;
    ">
        <!-- 배경 효과 -->
        <div style="
            position: absolute;
            top: -50%;
            right: -25%;
            width: 100%;
            height: 200%;
            background: radial-gradient(circle, {accent_color}22 0%, transparent 70%);
        "></div>

        <!-- 메인 텍스트 -->
        <div style="
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            text-align: center;
            z-index: 10;
        ">
            <div style="
                font-size: 48px;
                color: #ffffff88;
                margin-bottom: 10px;
            ">{sub_headline}</div>
            <div style="
                font-size: 96px;
                font-weight: 900;
                color: #ffffff;
                text-shadow: 0 4px 20px {accent_color}88;
                -webkit-text-stroke: 2px {accent_color};
            ">{headline}</div>
            <div style="
                font-size: 56px;
                color: {accent_color};
                margin-top: 20px;
                font-weight: 700;
            ">{bottom_text}</div>
        </div>

        <!-- 코너 장식 -->
        <div style="
            position: absolute;
            bottom: 20px;
            right: 30px;
            font-size: 32px;
            color: #ffffff66;
        ">AI 투자위원회</div>
    </div>
    """,

    "versus": """
    <div style="
        width: 1280px;
        height: 720px;
        background: linear-gradient(90deg, #1e3a5f 0%, #1a1a2e 50%, #5f1e3a 100%);
        position: relative;
        font-family: 'Noto Sans KR', sans-serif;
    ">
        <!-- 왼쪽 (인간) -->
        <div style="
            position: absolute;
            left: 80px;
            top: 50%;
            transform: translateY(-50%);
            text-align: center;
        ">
            <div style="font-size: 120px;">🧠</div>
            <div style="
                font-size: 64px;
                font-weight: 900;
                color: #4fc3f7;
            ">인간</div>
            <div style="
                font-size: 36px;
                color: #ffffff88;
            ">{human_info}</div>
        </div>

        <!-- 중앙 VS -->
        <div style="
            position: absolute;
            left: 50%;
            top: 50%;
            transform: translate(-50%, -50%);
            text-align: center;
        ">
            <div style="
                font-size: 160px;
                font-weight: 900;
                color: #ffd700;
                text-shadow: 0 0 40px #ffd70088;
            ">VS</div>
            <div style="
                font-size: 32px;
                color: #ffffff;
                margin-top: 10px;
            ">{ticker}</div>
        </div>

        <!-- 오른쪽 (AI) -->
        <div style="
            position: absolute;
            right: 80px;
            top: 50%;
            transform: translateY(-50%);
            text-align: center;
        ">
            <div style="font-size: 120px;">🤖</div>
            <div style="
                font-size: 64px;
                font-weight: 900;
                color: #e91e63;
            ">AI</div>
            <div style="
                font-size: 36px;
                color: #ffffff88;
            ">{ai_info}</div>
        </div>

        <!-- 하단 텍스트 -->
        <div style="
            position: absolute;
            bottom: 40px;
            left: 50%;
            transform: translateX(-50%);
            font-size: 48px;
            font-weight: 700;
            color: #ffffff;
        ">{headline}</div>
    </div>
    """,

    "question": """
    <div style="
        width: 1280px;
        height: 720px;
        background: linear-gradient(135deg, #ff6b35 0%, #1a1a2e 100%);
        position: relative;
        font-family: 'Noto Sans KR', sans-serif;
    ">
        <!-- 메인 질문 마크 -->
        <div style="
            position: absolute;
            right: 100px;
            top: 50%;
            transform: translateY(-50%);
            font-size: 400px;
            color: #ffffff22;
            font-weight: 900;
        ">?</div>

        <!-- 텍스트 영역 -->
        <div style="
            position: absolute;
            left: 80px;
            top: 50%;
            transform: translateY(-50%);
        ">
            <div style="
                font-size: 72px;
                font-weight: 900;
                color: #ffffff;
                margin-bottom: 20px;
            ">{headline}</div>
            <div style="
                font-size: 56px;
                color: #ffd700;
                font-weight: 700;
            ">{sub_headline}</div>
            <div style="
                font-size: 40px;
                color: #ffffff88;
                margin-top: 30px;
            ">AI가 분석한 결과는?</div>
        </div>
    </div>
    """,

    "news": """
    <div style="
        width: 1280px;
        height: 720px;
        background: #0a0a15;
        position: relative;
        font-family: 'Noto Sans KR', sans-serif;
    ">
        <!-- 뉴스 배너 -->
        <div style="
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 80px;
            background: #e63946;
            display: flex;
            align-items: center;
            padding: 0 40px;
        ">
            <div style="
                font-size: 36px;
                font-weight: 900;
                color: #ffffff;
            ">🔴 BREAKING</div>
            <div style="
                font-size: 28px;
                color: #ffffff;
                margin-left: 40px;
            ">AI 투자위원회 속보</div>
        </div>

        <!-- 메인 콘텐츠 -->
        <div style="
            position: absolute;
            top: 120px;
            left: 60px;
            right: 60px;
        ">
            <div style="
                font-size: 80px;
                font-weight: 900;
                color: #ffffff;
                line-height: 1.2;
            ">{headline}</div>
            <div style="
                font-size: 48px;
                color: #4fc3f7;
                margin-top: 30px;
            ">{sub_headline}</div>
        </div>

        <!-- 하단 정보 -->
        <div style="
            position: absolute;
            bottom: 40px;
            left: 60px;
            right: 60px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        ">
            <div style="
                font-size: 32px;
                color: #ffffff88;
            ">{ticker}</div>
            <div style="
                font-size: 32px;
                color: {price_color};
                font-weight: 700;
            ">{price_info}</div>
        </div>
    </div>
    """,

    "clean": """
    <div style="
        width: 1280px;
        height: 720px;
        background: #ffffff;
        position: relative;
        font-family: 'Noto Sans KR', sans-serif;
    ">
        <!-- 컬러 액센트 -->
        <div style="
            position: absolute;
            top: 0;
            left: 0;
            width: 20px;
            height: 100%;
            background: {accent_color};
        "></div>

        <!-- 메인 콘텐츠 -->
        <div style="
            position: absolute;
            top: 50%;
            left: 100px;
            transform: translateY(-50%);
        ">
            <div style="
                font-size: 40px;
                color: #666666;
                margin-bottom: 20px;
            ">AI 투자 분석</div>
            <div style="
                font-size: 96px;
                font-weight: 900;
                color: #1a1a2e;
            ">{headline}</div>
            <div style="
                font-size: 48px;
                color: {accent_color};
                margin-top: 20px;
                font-weight: 700;
            ">{sub_headline}</div>
        </div>

        <!-- 우측 정보 -->
        <div style="
            position: absolute;
            right: 80px;
            top: 50%;
            transform: translateY(-50%);
            text-align: right;
        ">
            <div style="
                font-size: 64px;
                color: {price_color};
                font-weight: 900;
            ">{target_price}</div>
            <div style="
                font-size: 32px;
                color: #999999;
            ">목표가</div>
        </div>
    </div>
    """,
}


# =============================================================================
# 색상 테마
# =============================================================================

COLOR_SCHEMES = {
    "red_black": {
        "bg_color1": "#1a1a2e",
        "bg_color2": "#16213e",
        "accent_color": "#e94560",
        "price_color": "#e94560",
    },
    "blue_white": {
        "bg_color1": "#1e3a5f",
        "bg_color2": "#0a192f",
        "accent_color": "#4fc3f7",
        "price_color": "#4fc3f7",
    },
    "green_gold": {
        "bg_color1": "#1a472a",
        "bg_color2": "#0d2818",
        "accent_color": "#4caf50",
        "price_color": "#ffd700",
    },
    "purple_pink": {
        "bg_color1": "#2d1b4e",
        "bg_color2": "#1a1a2e",
        "accent_color": "#e040fb",
        "price_color": "#ff4081",
    },
    "orange_dark": {
        "bg_color1": "#3d2914",
        "bg_color2": "#1a1a2e",
        "accent_color": "#ff9800",
        "price_color": "#ff5722",
    },
}


class ThumbnailGenerator:
    """썸네일 생성기."""

    def generate_thumbnail_html(
        self,
        spec: ThumbnailSpec,
        additional_data: Optional[dict] = None,
    ) -> str:
        """썸네일 HTML 생성.

        Args:
            spec: 썸네일 사양
            additional_data: 추가 데이터 (목표가, 티커 등)

        Returns:
            렌더링 가능한 HTML
        """
        template = THUMBNAIL_TEMPLATES.get(spec.style, THUMBNAIL_TEMPLATES["dramatic"])
        colors = COLOR_SCHEMES.get(spec.color_scheme, COLOR_SCHEMES["red_black"])

        # 데이터 준비
        data = {
            **colors,
            "headline": spec.headline,
            "sub_headline": spec.sub_headline or "",
            "bottom_text": "",
        }

        if additional_data:
            data.update(additional_data)

        # 텍스트 요소 처리
        for text_elem in spec.text_elements:
            position = text_elem.get("position", "")
            if position == "bottom":
                data["bottom_text"] = text_elem.get("text", "")
            elif position == "top":
                data["sub_headline"] = text_elem.get("text", "")

        return template.format(**data)

    def generate_comparison_html(
        self,
        human_data: dict,
        ai_data: dict,
        winner: Optional[str] = None,
    ) -> str:
        """비교 테이블 HTML 생성."""
        winner_badge_human = "🏆" if winner == "human" else ""
        winner_badge_ai = "🏆" if winner == "ai" else ""

        return f"""
        <div style="
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            padding: 40px;
            border-radius: 20px;
            font-family: 'Noto Sans KR', sans-serif;
        ">
            <h2 style="text-align: center; color: #ffffff; margin-bottom: 30px;">
                ⚔️ AI vs 인간 분석 비교 ⚔️
            </h2>

            <table style="width: 100%; border-collapse: collapse; color: #ffffff;">
                <thead>
                    <tr style="background: #ffffff11;">
                        <th style="padding: 15px; text-align: left; width: 30%;">항목</th>
                        <th style="padding: 15px; text-align: center; width: 35%;">🧠 인간 {winner_badge_human}</th>
                        <th style="padding: 15px; text-align: center; width: 35%;">🤖 AI {winner_badge_ai}</th>
                    </tr>
                </thead>
                <tbody>
                    <tr style="border-bottom: 1px solid #ffffff22;">
                        <td style="padding: 15px;">투자의견</td>
                        <td style="padding: 15px; text-align: center; font-weight: bold; color: #4fc3f7;">
                            {human_data.get('recommendation', '-')}
                        </td>
                        <td style="padding: 15px; text-align: center; font-weight: bold; color: #e91e63;">
                            {ai_data.get('recommendation', '-')}
                        </td>
                    </tr>
                    <tr style="border-bottom: 1px solid #ffffff22;">
                        <td style="padding: 15px;">목표가</td>
                        <td style="padding: 15px; text-align: center; font-size: 1.2em;">
                            ₩{human_data.get('target_price', 0):,.0f}
                        </td>
                        <td style="padding: 15px; text-align: center; font-size: 1.2em;">
                            ₩{ai_data.get('target_price', 0):,.0f}
                        </td>
                    </tr>
                    <tr style="border-bottom: 1px solid #ffffff22;">
                        <td style="padding: 15px;">확신도</td>
                        <td style="padding: 15px; text-align: center;">
                            {human_data.get('confidence', 0)}/10
                        </td>
                        <td style="padding: 15px; text-align: center;">
                            {ai_data.get('confidence', 0):.1f}/10
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>
        """

    def generate_scorecard_html(
        self,
        data: dict,
    ) -> str:
        """스코어카드 HTML 생성."""
        recommendation = data.get("recommendation", "")
        target_price = data.get("target_price", 0)
        confidence = data.get("confidence", 0)
        vote_result = data.get("vote_result", {})

        # 색상 결정
        if "매수" in recommendation or "Buy" in recommendation:
            rec_color = "#4caf50"
        elif "매도" in recommendation or "Sell" in recommendation:
            rec_color = "#e94560"
        else:
            rec_color = "#ffc107"

        bullish_count = len(vote_result.get("bullish", []))
        neutral_count = len(vote_result.get("neutral", []))
        bearish_count = len(vote_result.get("bearish", []))

        return f"""
        <div style="
            background: linear-gradient(135deg, #1a1a2e 0%, #0f3460 100%);
            padding: 40px;
            border-radius: 20px;
            font-family: 'Noto Sans KR', sans-serif;
            text-align: center;
        ">
            <h2 style="color: #ffffff; margin-bottom: 30px;">
                🏛️ AI 투자위원회 결정
            </h2>

            <!-- 투자의견 -->
            <div style="
                font-size: 64px;
                font-weight: 900;
                color: {rec_color};
                margin-bottom: 20px;
            ">{recommendation}</div>

            <!-- 목표가 -->
            <div style="
                font-size: 48px;
                color: #ffffff;
                margin-bottom: 10px;
            ">목표가: ₩{target_price:,.0f}</div>

            <!-- 확신도 -->
            <div style="
                font-size: 32px;
                color: #ffffff88;
                margin-bottom: 30px;
            ">확신도: {confidence}/10</div>

            <!-- 투표 결과 -->
            <div style="
                display: flex;
                justify-content: center;
                gap: 40px;
            ">
                <div>
                    <div style="font-size: 40px;">🟢</div>
                    <div style="color: #4caf50; font-size: 24px;">매수 {bullish_count}</div>
                </div>
                <div>
                    <div style="font-size: 40px;">🟡</div>
                    <div style="color: #ffc107; font-size: 24px;">중립 {neutral_count}</div>
                </div>
                <div>
                    <div style="font-size: 40px;">🔴</div>
                    <div style="color: #e94560; font-size: 24px;">매도 {bearish_count}</div>
                </div>
            </div>
        </div>
        """

    def generate_risk_infographic_html(
        self,
        risks: list[str],
    ) -> str:
        """리스크 인포그래픽 HTML 생성."""
        risk_items = ""
        for i, risk in enumerate(risks[:5], 1):
            risk_items += f"""
            <div style="
                display: flex;
                align-items: center;
                padding: 15px 20px;
                background: #ffffff11;
                border-radius: 10px;
                margin-bottom: 15px;
                border-left: 4px solid #e94560;
            ">
                <div style="
                    font-size: 24px;
                    margin-right: 15px;
                    color: #e94560;
                ">⚠️</div>
                <div style="
                    color: #ffffff;
                    font-size: 18px;
                ">{risk}</div>
            </div>
            """

        return f"""
        <div style="
            background: linear-gradient(135deg, #1a1a2e 0%, #2d1b1b 100%);
            padding: 40px;
            border-radius: 20px;
            font-family: 'Noto Sans KR', sans-serif;
        ">
            <h2 style="color: #e94560; margin-bottom: 30px; text-align: center;">
                ⚠️ 주요 리스크 요인
            </h2>
            {risk_items}
        </div>
        """

    def generate_key_points_html(
        self,
        points: list[str],
        title: str = "핵심 투자 포인트",
    ) -> str:
        """핵심 포인트 HTML 생성."""
        point_items = ""
        icons = ["💡", "📈", "🎯", "✨", "🔥"]

        for i, point in enumerate(points[:5]):
            icon = icons[i % len(icons)]
            point_items += f"""
            <div style="
                display: flex;
                align-items: center;
                padding: 15px 20px;
                background: #ffffff11;
                border-radius: 10px;
                margin-bottom: 15px;
                border-left: 4px solid #4caf50;
            ">
                <div style="
                    font-size: 24px;
                    margin-right: 15px;
                ">{icon}</div>
                <div style="
                    color: #ffffff;
                    font-size: 18px;
                ">{point}</div>
            </div>
            """

        return f"""
        <div style="
            background: linear-gradient(135deg, #1a1a2e 0%, #1b2d1b 100%);
            padding: 40px;
            border-radius: 20px;
            font-family: 'Noto Sans KR', sans-serif;
        ">
            <h2 style="color: #4caf50; margin-bottom: 30px; text-align: center;">
                {title}
            </h2>
            {point_items}
        </div>
        """

    def generate_debate_timeline_html(
        self,
        rounds: list[dict],
    ) -> str:
        """토론 타임라인 HTML 생성."""
        timeline_items = ""

        for i, round_data in enumerate(rounds, 1):
            timeline_items += f"""
            <div style="
                display: flex;
                align-items: center;
                margin-bottom: 20px;
            ">
                <div style="
                    width: 50px;
                    height: 50px;
                    background: linear-gradient(135deg, #e94560 0%, #0f3460 100%);
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: #ffffff;
                    font-weight: bold;
                    font-size: 20px;
                    margin-right: 20px;
                ">{i}</div>
                <div style="
                    flex: 1;
                    background: #ffffff11;
                    padding: 15px 20px;
                    border-radius: 10px;
                ">
                    <div style="color: #4fc3f7; font-weight: bold; margin-bottom: 5px;">
                        라운드 {round_data.get('round', i)}
                    </div>
                    <div style="color: #ffffff;">
                        {round_data.get('theme', '')}
                    </div>
                </div>
            </div>
            """

        return f"""
        <div style="
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            padding: 40px;
            border-radius: 20px;
            font-family: 'Noto Sans KR', sans-serif;
        ">
            <h2 style="color: #ffffff; margin-bottom: 30px; text-align: center;">
                🎯 AI 토론 과정
            </h2>
            {timeline_items}
        </div>
        """


def generate_visual_asset_html(asset: VisualAsset) -> str:
    """VisualAsset을 HTML로 변환."""
    generator = ThumbnailGenerator()

    if asset.asset_type == "scorecard":
        return generator.generate_scorecard_html(asset.data)
    elif asset.asset_type == "comparison":
        return generator.generate_comparison_html(
            asset.data.get("human", {}),
            asset.data.get("ai", {}),
            asset.data.get("winner"),
        )
    elif asset.asset_type == "infographic":
        return generator.generate_risk_infographic_html(asset.data.get("risks", []))
    elif asset.asset_type == "stat_highlight":
        return generator.generate_key_points_html(
            asset.data.get("points", []),
            asset.title,
        )
    elif asset.asset_type == "timeline":
        return generator.generate_debate_timeline_html(asset.data.get("rounds", []))
    else:
        return f"<div>Unknown asset type: {asset.asset_type}</div>"
