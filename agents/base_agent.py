"""Base agent class for all specialized agents."""
import json
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Optional

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from config.settings import settings
from models.agent_opinion import AgentOpinion, AgentType, Sentiment

logger = logging.getLogger(__name__)


class AgentConfig(BaseModel):
    """Configuration for an agent."""
    agent_type: AgentType = Field(..., description="Type of agent")
    model_name: str = Field(
        default=settings.default_model,
        description="LLM model name"
    )
    temperature: float = Field(default=settings.temperature, description="LLM temperature")
    max_tokens: int = Field(default=4096, description="Max tokens for response")
    prompt_file: Optional[str] = Field(None, description="Path to prompt file")


class BaseAgent(ABC):
    """Base class for all analysis agents."""

    def __init__(
        self,
        config: AgentConfig,
        tools: Optional[list[BaseTool]] = None,
    ):
        """Initialize the agent.

        Args:
            config: Agent configuration
            tools: Optional list of tools available to the agent
        """
        self.config = config
        self.tools = tools or []
        self._llm: Optional[ChatAnthropic] = None
        self._system_prompt: Optional[str] = None

    @property
    def agent_type(self) -> AgentType:
        """Get agent type."""
        return self.config.agent_type

    @property
    def llm(self) -> ChatAnthropic:
        """Get or create LLM instance."""
        if self._llm is None:
            self._llm = ChatAnthropic(
                model=self.config.model_name,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                api_key=settings.anthropic_api_key,
            )
            if self.tools:
                self._llm = self._llm.bind_tools(self.tools)
        return self._llm

    @property
    def system_prompt(self) -> str:
        """Get system prompt for the agent."""
        if self._system_prompt is None:
            self._system_prompt = self._load_system_prompt()
        return self._system_prompt

    def _load_system_prompt(self) -> str:
        """Load system prompt from file or return default."""
        if self.config.prompt_file:
            prompt_path = Path(self.config.prompt_file)
            if prompt_path.exists():
                return prompt_path.read_text(encoding="utf-8")

        # Try loading from prompts directory
        prompt_file = Path("prompts") / f"{self.config.agent_type.value}.md"
        if prompt_file.exists():
            return prompt_file.read_text(encoding="utf-8")

        # Return default prompt
        return self._get_default_prompt()

    @abstractmethod
    def _get_default_prompt(self) -> str:
        """Get default system prompt for this agent type."""
        pass

    @abstractmethod
    async def analyze(self, context: dict[str, Any]) -> dict[str, Any]:
        """Perform analysis.

        Args:
            context: Analysis context including stock data and other agent results

        Returns:
            Analysis result dictionary
        """
        pass

    async def invoke(
        self,
        user_message: str,
        context: Optional[dict[str, Any]] = None,
    ) -> str:
        """Invoke the LLM with a message.

        Args:
            user_message: User message/query
            context: Optional additional context

        Returns:
            LLM response text
        """
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=self._build_user_message(user_message, context)),
        ]

        try:
            response = await self.llm.ainvoke(messages)
            return response.content
        except Exception as e:
            logger.error(f"Error invoking LLM for {self.agent_type}: {e}")
            raise

    def _build_user_message(
        self,
        message: str,
        context: Optional[dict[str, Any]] = None,
    ) -> str:
        """Build user message with context.

        Args:
            message: Base message
            context: Optional context to include

        Returns:
            Formatted message string
        """
        if not context:
            return message

        context_str = json.dumps(context, indent=2, default=str, ensure_ascii=False)
        return f"""Context:
```json
{context_str}
```

{message}"""

    def create_opinion(
        self,
        ticker: str,
        score: float,
        confidence: float,
        summary: str,
        key_points: list[str],
        concerns: list[str],
        detailed_analysis: Optional[dict] = None,
    ) -> AgentOpinion:
        """Create an agent opinion.

        Args:
            ticker: Stock ticker
            score: Score from 1-10
            confidence: Confidence level 0-100
            summary: Brief summary
            key_points: Key analysis points
            concerns: Concerns identified
            detailed_analysis: Optional detailed analysis data

        Returns:
            AgentOpinion instance
        """
        # Determine sentiment from score
        if score >= 8:
            sentiment = Sentiment.VERY_BULLISH
        elif score >= 6.5:
            sentiment = Sentiment.BULLISH
        elif score >= 4.5:
            sentiment = Sentiment.NEUTRAL
        elif score >= 3:
            sentiment = Sentiment.BEARISH
        else:
            sentiment = Sentiment.VERY_BEARISH

        return AgentOpinion(
            agent_type=self.agent_type,
            ticker=ticker,
            score=score,
            confidence=confidence,
            sentiment=sentiment,
            summary=summary,
            key_points=key_points,
            concerns=concerns,
            detailed_analysis=detailed_analysis,
        )

    async def respond_to_counter_argument(
        self,
        counter_argument: str,
        original_analysis: dict[str, Any],
    ) -> dict[str, Any]:
        """Respond to a counter argument from Devil's Advocate.

        Args:
            counter_argument: The counter argument to respond to
            original_analysis: The original analysis being challenged

        Returns:
            Response with potential score adjustment
        """
        prompt = f"""You are responding to a counter-argument raised against your analysis.

Original Analysis Summary:
{json.dumps(original_analysis, indent=2, default=str, ensure_ascii=False)}

Counter-Argument:
{counter_argument}

Please provide:
1. Your response to this counter-argument
2. Whether you acknowledge any valid points
3. If the counter-argument changes your assessment, provide an adjusted score (1-10)
4. Any risks you now acknowledge that weren't in your original analysis

Respond in JSON format:
{{
    "response": "your detailed response",
    "valid_points_acknowledged": ["list of valid points you acknowledge"],
    "adjusted_score": null or number,
    "newly_acknowledged_risks": ["list of risks"]
}}"""

        response = await self.invoke(prompt)
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {
                "response": response,
                "valid_points_acknowledged": [],
                "adjusted_score": None,
                "newly_acknowledged_risks": [],
            }

    async def rebut(self, context: dict[str, Any]) -> dict[str, Any]:
        """Rebut a challenge from Devil's Advocate.

        이 메서드는 토론 과정에서 Devil's Advocate의 도전에 대응할 때 사용됩니다.
        에이전트는 자신의 분석을 방어하거나, 타당한 지적을 인정하고 점수를 조정할 수 있습니다.

        Args:
            context: 도전 컨텍스트
                - original_opinion: 원래 의견
                - challenge: 도전 내용
                - challenge_evidence: 도전 근거
                - severity: 심각도
                - stock_info: 주식 정보

        Returns:
            방어 응답:
                - defense: 방어 논리
                - adjusted_score: 조정된 점수 (변경 시)
                - acknowledged_risks: 인정한 리스크
                - counter_evidence: 반박 증거
        """
        original = context.get("original_opinion", {})
        challenge = context.get("challenge", "")
        evidence = context.get("challenge_evidence", [])
        severity = context.get("severity", "medium")

        prompt = f"""당신은 투자위원회에서 자신의 분석을 방어해야 합니다.

## 당신의 원래 분석
- 점수: {original.get('score', 'N/A')}/10
- 요약: {original.get('summary', 'N/A')}
- 핵심 포인트: {original.get('key_points', [])}

## Devil's Advocate의 도전
{challenge}

### 도전 근거
{json.dumps(evidence, ensure_ascii=False) if evidence else "없음"}

### 심각도: {severity}

---

당신은 30년 경력의 전문 애널리스트입니다.
이 도전에 대해 논리적으로 반박하거나, 타당한 지적이라면 솔직히 인정하세요.

다음 JSON 형식으로 응답하세요:
{{
    "defense": "당신의 방어 논리 (구체적이고 데이터 기반으로)",
    "adjusted_score": null 또는 1-10 사이의 숫자 (도전이 타당하다면 조정),
    "acknowledged_risks": ["인정하는 리스크 목록"],
    "counter_evidence": ["당신의 입장을 지지하는 증거"],
    "confidence_after_debate": 0-100 사이의 숫자,
    "final_stance": "maintain" 또는 "partially_concede" 또는 "fully_concede"
}}"""

        response = await self.invoke(prompt)
        try:
            # JSON 블록 추출
            if "```json" in response:
                json_start = response.find("```json") + 7
                json_end = response.find("```", json_start)
                response = response[json_start:json_end].strip()
            elif "```" in response:
                json_start = response.find("```") + 3
                json_end = response.find("```", json_start)
                response = response[json_start:json_end].strip()

            result = json.loads(response)
            return {
                "defense": result.get("defense", ""),
                "adjusted_score": result.get("adjusted_score"),
                "acknowledged_risks": result.get("acknowledged_risks", []),
                "counter_evidence": result.get("counter_evidence", []),
                "confidence": result.get("confidence_after_debate", 70),
                "stance": result.get("final_stance", "maintain"),
            }
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse rebut response: {response[:100]}...")
            return {
                "defense": response,
                "adjusted_score": None,
                "acknowledged_risks": [],
                "counter_evidence": [],
                "confidence": 50,
                "stance": "maintain",
            }
