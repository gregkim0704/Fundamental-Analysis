"""AI vs Human 대결 심판 서비스.

대결 결과를 공정하게 심판하고 점수를 부여하는 서비스입니다.
"""
import json
import logging
from datetime import datetime
from typing import Any, Optional

from langchain_anthropic import ChatAnthropic

from models.battle_game import (
    InvestmentBattle,
    BattleResult,
    BattleRound,
    BattleCategory,
    BattleStatus,
    HumanAnalysis,
    AIAnalysisSummary,
    BADGES,
    calculate_target_accuracy,
    determine_direction,
)

logger = logging.getLogger(__name__)


class BattleJudge:
    """대결 심판 서비스."""

    def __init__(self, model_name: str = "claude-opus-4-5-20251101"):
        """Initialize battle judge."""
        self.llm = ChatAnthropic(
            model_name=model_name,
            temperature=0.2,  # 일관된 심판을 위해 낮은 온도
        )

    async def judge_battle(
        self,
        battle: InvestmentBattle,
        current_price: Optional[float] = None,
    ) -> BattleResult:
        """대결 심판.

        Args:
            battle: 대결 정보
            current_price: 현재 주가 (사후 검증용)

        Returns:
            대결 결과
        """
        human = battle.human_analysis
        ai = battle.ai_analysis

        if not human or not ai:
            raise ValueError("대결 데이터가 완전하지 않습니다.")

        # 각 카테고리별 심판
        rounds = []

        # 1. 목표가 대결
        target_round = await self._judge_target_price(human, ai, battle.start_price, current_price)
        rounds.append(target_round)

        # 2. 방향성 대결
        direction_round = await self._judge_direction(human, ai, battle.start_price, current_price)
        rounds.append(direction_round)

        # 3. 리스크 식별 대결
        risk_round = await self._judge_risk_identification(human, ai)
        rounds.append(risk_round)

        # 4. 논리성 대결
        logic_round = await self._judge_logic_quality(human, ai, battle.ticker)
        rounds.append(logic_round)

        # 5. 종합 대결
        overall_round = await self._judge_overall(human, ai, battle.ticker)
        rounds.append(overall_round)

        # 총점 계산
        human_total = sum(r.human_score or 0 for r in rounds)
        ai_total = sum(r.ai_score or 0 for r in rounds)

        # 승자 결정
        if human_total > ai_total + 10:  # 10점 이상 차이
            final_winner = "human"
        elif ai_total > human_total + 10:
            final_winner = "ai"
        else:
            final_winner = "draw"

        # 배지 계산
        badges = self._calculate_badges(human, ai, rounds, final_winner, current_price, battle.start_price)

        # 학습 포인트 생성
        lessons = await self._generate_lessons(human, ai, rounds, battle.ticker)

        return BattleResult(
            final_winner=final_winner,
            human_total_score=human_total,
            ai_total_score=ai_total,
            round_results=rounds,
            badges_earned=badges,
            lessons_learned=lessons,
        )

    async def _judge_target_price(
        self,
        human: HumanAnalysis,
        ai: AIAnalysisSummary,
        start_price: float,
        current_price: Optional[float],
    ) -> BattleRound:
        """목표가 대결 심판."""
        human_position = f"목표가 ₩{human.target_price:,.0f} (확신도 {human.confidence_score}/10)"
        ai_position = f"목표가 ₩{ai.target_price:,.0f} (확신도 {ai.confidence_score:.1f}/10)"

        # 실제 가격이 있으면 정확도 기반 심판
        if current_price:
            human_acc = calculate_target_accuracy(human.target_price, current_price)
            ai_acc = calculate_target_accuracy(ai.target_price, current_price)

            human_score = int(human_acc)
            ai_score = int(ai_acc)

            if human_acc > ai_acc + 5:
                winner = "human"
                comment = f"인간 목표가가 더 정확! (인간 {human_acc:.1f}% vs AI {ai_acc:.1f}%)"
            elif ai_acc > human_acc + 5:
                winner = "ai"
                comment = f"AI 목표가가 더 정확! (AI {ai_acc:.1f}% vs 인간 {human_acc:.1f}%)"
            else:
                winner = "draw"
                comment = f"비슷한 정확도 (인간 {human_acc:.1f}% vs AI {ai_acc:.1f}%)"
        else:
            # 실제 가격 없으면 논리성으로 심판
            prompt = f"""두 분석가의 목표가 설정을 비교 평가하세요.

현재가: ₩{start_price:,.0f}

인간 분석가:
- 목표가: ₩{human.target_price:,.0f} (현재가 대비 {(human.target_price/start_price-1)*100:.1f}%)
- 확신도: {human.confidence_score}/10
- 근거: {json.dumps(human.bull_thesis[:3], ensure_ascii=False)}

AI 위원회:
- 목표가: ₩{ai.target_price:,.0f} (현재가 대비 {(ai.target_price/start_price-1)*100:.1f}%)
- 확신도: {ai.confidence_score:.1f}/10
- 근거: {json.dumps(ai.bull_thesis[:3], ensure_ascii=False)}

다음 JSON으로 응답:
{{"human_score": 0-100, "ai_score": 0-100, "winner": "human"/"ai"/"draw", "comment": "심판 코멘트"}}"""

            result = await self._invoke_judge(prompt)
            human_score = result.get("human_score", 50)
            ai_score = result.get("ai_score", 50)
            winner = result.get("winner", "draw")
            comment = result.get("comment", "")

        return BattleRound(
            category=BattleCategory.TARGET_PRICE,
            category_name_kr="목표가 대결",
            human_position=human_position,
            ai_position=ai_position,
            human_score=human_score,
            ai_score=ai_score,
            winner=winner,
            judge_comment=comment,
        )

    async def _judge_direction(
        self,
        human: HumanAnalysis,
        ai: AIAnalysisSummary,
        start_price: float,
        current_price: Optional[float],
    ) -> BattleRound:
        """방향성 대결 심판."""
        human_direction = "상승" if human.target_price > start_price else "하락" if human.target_price < start_price else "횡보"
        ai_direction = "상승" if ai.target_price > start_price else "하락" if ai.target_price < start_price else "횡보"

        human_position = f"{human.recommendation} ({human_direction} 전망)"
        ai_position = f"{ai.recommendation} ({ai_direction} 전망)"

        if current_price:
            actual_direction = determine_direction(start_price, current_price)
            actual_text = {"up": "상승", "down": "하락", "flat": "횡보"}.get(actual_direction, "횡보")

            human_correct = (
                (human_direction == "상승" and actual_direction == "up") or
                (human_direction == "하락" and actual_direction == "down") or
                (human_direction == "횡보" and actual_direction == "flat")
            )
            ai_correct = (
                (ai_direction == "상승" and actual_direction == "up") or
                (ai_direction == "하락" and actual_direction == "down") or
                (ai_direction == "횡보" and actual_direction == "flat")
            )

            human_score = 80 if human_correct else 20
            ai_score = 80 if ai_correct else 20

            if human_correct and not ai_correct:
                winner = "human"
                comment = f"실제 {actual_text}! 인간 승리"
            elif ai_correct and not human_correct:
                winner = "ai"
                comment = f"실제 {actual_text}! AI 승리"
            elif human_correct and ai_correct:
                winner = "draw"
                comment = f"둘 다 {actual_text} 정확히 예측!"
            else:
                winner = "draw"
                comment = f"둘 다 예측 실패 (실제: {actual_text})"
        else:
            # 논리성 기반 심판
            prompt = f"""두 분석가의 방향성 예측을 비교 평가하세요.

인간: {human_position}
AI: {ai_position}

다음 JSON으로 응답:
{{"human_score": 0-100, "ai_score": 0-100, "winner": "human"/"ai"/"draw", "comment": "심판 코멘트"}}"""

            result = await self._invoke_judge(prompt)
            human_score = result.get("human_score", 50)
            ai_score = result.get("ai_score", 50)
            winner = result.get("winner", "draw")
            comment = result.get("comment", "")

        return BattleRound(
            category=BattleCategory.DIRECTION,
            category_name_kr="방향성 대결",
            human_position=human_position,
            ai_position=ai_position,
            human_score=human_score,
            ai_score=ai_score,
            winner=winner,
            judge_comment=comment,
        )

    async def _judge_risk_identification(
        self,
        human: HumanAnalysis,
        ai: AIAnalysisSummary,
    ) -> BattleRound:
        """리스크 식별 대결 심판."""
        human_risks = human.key_risks + human.bear_thesis
        ai_risks = ai.key_risks + ai.bear_thesis

        human_position = f"식별 리스크 {len(human_risks)}개"
        ai_position = f"식별 리스크 {len(ai_risks)}개"

        prompt = f"""두 분석가의 리스크 식별 능력을 비교 평가하세요.

인간이 식별한 리스크:
{json.dumps(human_risks, ensure_ascii=False, indent=2)}

AI가 식별한 리스크:
{json.dumps(ai_risks, ensure_ascii=False, indent=2)}

평가 기준:
1. 리스크의 중요도와 심각성
2. 리스크 식별의 포괄성
3. 리스크 설명의 구체성
4. 누락된 중요 리스크 여부

다음 JSON으로 응답:
{{"human_score": 0-100, "ai_score": 0-100, "winner": "human"/"ai"/"draw", "comment": "심판 코멘트", "missed_risks": ["누락된 중요 리스크들"]}}"""

        result = await self._invoke_judge(prompt)

        return BattleRound(
            category=BattleCategory.RISK_IDENTIFICATION,
            category_name_kr="리스크 식별",
            human_position=human_position,
            ai_position=ai_position,
            human_score=result.get("human_score", 50),
            ai_score=result.get("ai_score", 50),
            winner=result.get("winner", "draw"),
            judge_comment=result.get("comment", ""),
        )

    async def _judge_logic_quality(
        self,
        human: HumanAnalysis,
        ai: AIAnalysisSummary,
        ticker: str,
    ) -> BattleRound:
        """분석 논리성 대결 심판."""
        prompt = f"""두 분석가의 분석 논리성을 비교 평가하세요. (종목: {ticker})

## 인간 분석가

투자의견: {human.recommendation}
확신도: {human.confidence_score}/10

매수 근거:
{json.dumps(human.bull_thesis, ensure_ascii=False, indent=2)}

리스크 인식:
{json.dumps(human.bear_thesis, ensure_ascii=False, indent=2)}

분석 요약:
{human.analysis_summary}

## AI 위원회

투자의견: {ai.recommendation}
확신도: {ai.confidence_score}/10
합의 수준: {ai.consensus_level}

매수 근거:
{json.dumps(ai.bull_thesis, ensure_ascii=False, indent=2)}

리스크 인식:
{json.dumps(ai.bear_thesis, ensure_ascii=False, indent=2)}

분석 요약:
{ai.analysis_summary}

---

평가 기준:
1. 논리의 일관성: 주장과 근거가 일치하는가?
2. 근거의 구체성: 데이터와 사실에 기반한 분석인가?
3. 균형성: 강점과 약점을 균형있게 분석했는가?
4. 결론의 타당성: 분석 내용과 결론이 부합하는가?
5. 독창성: 새로운 통찰이 있는가?

다음 JSON으로 응답:
{{
    "human_score": 0-100,
    "ai_score": 0-100,
    "winner": "human"/"ai"/"draw",
    "comment": "심판 코멘트",
    "human_strengths": ["인간 분석의 강점"],
    "ai_strengths": ["AI 분석의 강점"],
    "human_weaknesses": ["인간 분석의 약점"],
    "ai_weaknesses": ["AI 분석의 약점"]
}}"""

        result = await self._invoke_judge(prompt)

        human_position = f"논리성 점수: {result.get('human_score', 50)}/100"
        ai_position = f"논리성 점수: {result.get('ai_score', 50)}/100"

        return BattleRound(
            category=BattleCategory.TIMING,  # 논리성 카테고리로 사용
            category_name_kr="분석 논리성",
            human_position=human_position,
            ai_position=ai_position,
            human_score=result.get("human_score", 50),
            ai_score=result.get("ai_score", 50),
            winner=result.get("winner", "draw"),
            judge_comment=result.get("comment", ""),
        )

    async def _judge_overall(
        self,
        human: HumanAnalysis,
        ai: AIAnalysisSummary,
        ticker: str,
    ) -> BattleRound:
        """종합 대결 심판."""
        prompt = f"""두 분석가의 종합 분석 품질을 평가하세요. (종목: {ticker})

## 인간 분석가 ({human.analyst_experience})
- 투자의견: {human.recommendation}
- 목표가: ₩{human.target_price:,.0f}
- 확신도: {human.confidence_score}/10
- 투자기간: {human.time_horizon}
- 분석 요약: {human.analysis_summary[:300]}

## AI 위원회
- 투자의견: {ai.recommendation}
- 목표가: ₩{ai.target_price:,.0f}
- 확신도: {ai.confidence_score}/10
- 합의 수준: {ai.consensus_level}
- 참여 에이전트: {len(ai.agents_involved)}명
- 분석 요약: {ai.analysis_summary[:300]}

---

종합 평가 기준:
1. 분석의 깊이와 포괄성
2. 실행 가능한 인사이트 제공 여부
3. 투자자에게 실질적 도움이 되는 정도
4. 분석의 차별화 요소

다음 JSON으로 응답:
{{
    "human_score": 0-100,
    "ai_score": 0-100,
    "winner": "human"/"ai"/"draw",
    "comment": "종합 심판 코멘트",
    "standout_analysis": "가장 돋보인 분석 포인트"
}}"""

        result = await self._invoke_judge(prompt)

        return BattleRound(
            category=BattleCategory.OVERALL,
            category_name_kr="종합 평가",
            human_position=f"종합 점수: {result.get('human_score', 50)}/100",
            ai_position=f"종합 점수: {result.get('ai_score', 50)}/100",
            human_score=result.get("human_score", 50),
            ai_score=result.get("ai_score", 50),
            winner=result.get("winner", "draw"),
            judge_comment=result.get("comment", ""),
        )

    def _calculate_badges(
        self,
        human: HumanAnalysis,
        ai: AIAnalysisSummary,
        rounds: list[BattleRound],
        final_winner: str,
        current_price: Optional[float],
        start_price: float,
    ) -> list[str]:
        """획득 배지 계산."""
        badges = []

        # 승리 배지
        if final_winner == "human":
            badges.append("first_blood")  # 첫 승리 (실제로는 이력 확인 필요)

            # 역발상 승리 (AI와 반대 방향 예측으로 승리)
            human_direction = human.target_price > start_price
            ai_direction = ai.target_price > start_price
            if human_direction != ai_direction:
                badges.append("contrarian")

        # 정확도 배지 (사후 검증 시)
        if current_price:
            human_acc = calculate_target_accuracy(human.target_price, current_price)
            if human_acc >= 95:
                badges.append("sniper")

        # 리스크 식별 배지
        risk_round = next((r for r in rounds if r.category == BattleCategory.RISK_IDENTIFICATION), None)
        if risk_round and risk_round.winner == "human" and (risk_round.human_score or 0) >= 80:
            badges.append("eagle_eye")

        # 논리성 배지
        logic_round = next((r for r in rounds if r.category_name_kr == "분석 논리성"), None)
        if logic_round and logic_round.winner == "human" and (logic_round.human_score or 0) >= 85:
            badges.append("deep_thinker")

        return badges

    async def _generate_lessons(
        self,
        human: HumanAnalysis,
        ai: AIAnalysisSummary,
        rounds: list[BattleRound],
        ticker: str,
    ) -> list[str]:
        """학습 포인트 생성."""
        prompt = f"""이번 AI vs Human 투자 분석 대결 결과를 바탕으로 학습 포인트 3-5개를 생성하세요. (종목: {ticker})

## 대결 결과 요약

인간 분석:
- 투자의견: {human.recommendation}, 목표가: ₩{human.target_price:,.0f}
- 강점: {human.bull_thesis[:2]}
- 약점 인식: {human.bear_thesis[:2]}

AI 분석:
- 투자의견: {ai.recommendation}, 목표가: ₩{ai.target_price:,.0f}
- 강점: {ai.bull_thesis[:2]}
- 약점 인식: {ai.bear_thesis[:2]}

카테고리별 결과:
{json.dumps([{"category": r.category_name_kr, "winner": r.winner, "comment": r.judge_comment} for r in rounds], ensure_ascii=False, indent=2)}

---

투자자가 배울 수 있는 실질적인 포인트를 JSON 배열로 응답:
["학습포인트1", "학습포인트2", ...]"""

        try:
            response = await self.llm.ainvoke(prompt)
            return json.loads(response.content)
        except Exception as e:
            logger.error(f"Error generating lessons: {e}")
            return [
                "AI와 인간 분석의 관점 차이를 이해하면 더 나은 투자 결정을 할 수 있습니다.",
                "다양한 시각에서 리스크를 검토하는 것이 중요합니다.",
                "확신도와 실제 분석 깊이가 일치하는지 점검해보세요."
            ]

    async def _invoke_judge(self, prompt: str) -> dict:
        """심판 LLM 호출."""
        try:
            response = await self.llm.ainvoke(prompt)
            content = response.content

            # JSON 파싱
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            return json.loads(content)
        except Exception as e:
            logger.error(f"Error invoking judge: {e}")
            return {"human_score": 50, "ai_score": 50, "winner": "draw", "comment": "심판 오류"}


async def run_battle(
    ticker: str,
    company_name: str,
    start_price: float,
    human_analysis: HumanAnalysis,
    ai_analysis_result: dict,  # 기존 분석 시스템 결과
) -> InvestmentBattle:
    """대결 실행.

    Args:
        ticker: 종목 코드
        company_name: 회사명
        start_price: 시작 가격
        human_analysis: 인간 분석
        ai_analysis_result: AI 분석 결과

    Returns:
        완료된 대결
    """
    # AI 분석 요약 생성
    decision = ai_analysis_result.get("committee_decision", {})
    agent_analyses = ai_analysis_result.get("agent_analyses", [])

    ai_summary = AIAnalysisSummary(
        recommendation=decision.get("final_recommendation", "Hold"),
        target_price=decision.get("target_price", start_price),
        confidence_score=decision.get("confidence_score", 5.0),
        bull_thesis=decision.get("key_reasons", []),
        bear_thesis=decision.get("key_risks", []),
        key_catalysts=[],
        key_risks=decision.get("key_risks", []),
        analysis_summary=ai_analysis_result.get("executive_summary", {}).get("one_liner", ""),
        agents_involved=[a.get("agent_name", "") for a in agent_analyses],
        debate_rounds=ai_analysis_result.get("debate_results", {}).get("total_rounds", 3),
        consensus_level=decision.get("confidence_level", "중간"),
    )

    # 대결 생성
    battle = InvestmentBattle(
        ticker=ticker,
        company_name=company_name,
        start_price=start_price,
        human_analysis=human_analysis,
        ai_analysis=ai_summary,
        status=BattleStatus.IN_PROGRESS,
    )

    # 심판 실행
    judge = BattleJudge()
    result = await judge.judge_battle(battle)

    battle.result = result
    battle.status = BattleStatus.COMPLETED

    return battle
