# 📊 Fundamental Analysis Pro

AI 투자위원회(Investment Committee) 기반 Multi-Agent 주식 펀더멘털 분석 플랫폼

## 🎯 프로젝트 개요

이 앱은 **AI 투자위원회** 개념을 구현합니다. 각 전문 영역을 담당하는 에이전트들이 독립적으로 분석한 후, 서로의 견해를 검증하고 토론하여 최종 투자 의사결정을 도출합니다.

### 왜 Multi-Agent인가?

- ✅ 단일 모델의 편향 방지 → 다양한 관점의 교차 검증
- ✅ 역할 분리로 분석 깊이 증가
- ✅ 실제 투자위원회/애널리스트 팀 구조 모방
- ✅ 의사결정 과정의 투명성 확보

## 🤖 AI 투자위원회 구성

| 에이전트 | 역할 | 분석 영역 |
|----------|------|-----------|
| 🎩 **Chairman** | 의장 | 전체 조율, 최종 결정 |
| 🌍 **Macro** | 거시경제 전문가 | 금리, 유동성, 경기 사이클 |
| 💰 **Quant** | 재무분석 전문가 | ROIC, 이익의 질, FCF |
| 🎯 **Qualitative** | 정성분석 전문가 | Moat, 경영진, 거버넌스 |
| 🏭 **Industry** | 산업 전문가 | 경쟁구도, 시장구조 |
| 📈 **Valuation** | 밸류에이션 전문가 | DCF, 상대가치 |
| ⚠️ **Risk** | 리스크 관리자 | 사업/재무/시장 리스크 |
| 😈 **Devil's Advocate** | 반대 논거 전문가 | 맹점 발견, Pre-mortem |

## 📋 주요 기능

### 1. 거시 환경 분석
- 금리 사이클 추적
- 유동성 지표 모니터링
- 섹터 로테이션 분석
- 정책 영향 평가

### 2. 재무제표 심층 분석
- ROIC vs WACC 스프레드
- 이익의 질 분석 (Accrual Ratio)
- 현금흐름 품질 평가
- 가치 창출 분석 (EVA)

### 3. 정성적 분석
- 경쟁우위(Moat) 평가
- 경영진 품질 분석
- Porter's 5 Forces
- ESG 고려사항

### 4. 밸류에이션
- DCF 모델
- 상대가치 분석
- 시나리오 분석 (Bear/Base/Bull)
- 목표 주가 범위 산출

### 5. 역발상 검증
- Pre-mortem 분석
- 반대 논거 탐색
- 맹점 발견

## 🛠️ 기술 스택

| 카테고리 | 기술 |
|----------|------|
| Agent Framework | LangGraph + LangChain |
| LLM | Claude Opus 4.5 |
| Frontend | Streamlit |
| Data | yfinance, FRED, OpenDART |
| Visualization | Plotly |

## 📁 프로젝트 구조

```
Fundamental-Analysis/
├── app/                    # Streamlit 애플리케이션
│   ├── main.py
│   ├── pages/
│   └── components/
├── agents/                 # Multi-Agent Core
│   ├── base_agent.py
│   ├── chairman.py
│   ├── macro_agent.py
│   ├── quant_agent.py
│   ├── valuation_agent.py
│   └── devils_advocate.py
├── graph/                  # LangGraph Workflows
│   ├── state.py
│   └── workflow.py
├── tools/                  # Agent Tools
│   ├── stock_price.py
│   ├── financial_data.py
│   ├── macro_data.py
│   └── valuation_calc.py
├── core/                   # Business Logic
│   ├── financial_analysis.py
│   ├── valuation_models.py
│   ├── quality_metrics.py
│   └── roic_wacc.py
├── models/                 # Data Models
├── prompts/                # Agent Prompts
├── config/                 # Configuration
├── tests/                  # Tests
└── requirements.txt
```

## 🚀 시작하기

### 1. 환경 설정

```bash
# 저장소 클론
git clone https://github.com/your-repo/fundamental-analysis.git
cd fundamental-analysis

# 가상환경 생성
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
```

### 2. API 키 설정

`.env.example`을 `.env`로 복사하고 API 키 입력:

```bash
cp .env.example .env
```

```env
ANTHROPIC_API_KEY=your_anthropic_api_key
OPENDART_API_KEY=your_opendart_api_key  # 한국 시장용
FRED_API_KEY=your_fred_api_key  # 거시경제 데이터용
```

### 3. 앱 실행

```bash
streamlit run app/main.py
```

브라우저에서 `http://localhost:8501` 접속

## 📊 사용 예시

### 기본 분석

```python
from graph.workflow import analyze_stock

# 종목 분석 실행
result = await analyze_stock("AAPL")

# 결과 확인
print(result["committee_decision"]["recommendation"])
print(result["committee_decision"]["target_price_mid"])
```

### 커스텀 분석

```python
from graph.state import AnalysisRequest, WorkflowConfig
from graph.workflow import AnalysisWorkflow

# 설정 커스터마이즈
config = WorkflowConfig(
    max_debate_rounds=3,
    include_devils_advocate=True,
)

# 워크플로우 실행
workflow = AnalysisWorkflow(config)
request = AnalysisRequest(
    ticker="005930.KS",
    focus_areas=["valuation", "risk"],
)
result = await workflow.run(request)
```

## 🔄 분석 프로세스

```
Phase 1: 독립 분석
┌─────────────────────────────────────────────────────────────┐
│  Macro Agent ─────┐                                         │
│  Quant Agent ─────┼──────> Valuation Agent                  │
│  Qualitative Agent┘        Risk Agent                       │
│  Industry Agent ───────────────────────────────────────────>│
└─────────────────────────────────────────────────────────────┘
                              ↓
Phase 2: 교차 검증 & 토론
┌─────────────────────────────────────────────────────────────┐
│  Devil's Advocate: 반박 제기                                 │
│  각 Agent: 반박 응답                                         │
│  Chairman: 중재 및 조정                                      │
│  (3라운드 반복)                                              │
└─────────────────────────────────────────────────────────────┘
                              ↓
Phase 3: 최종 의사결정
┌─────────────────────────────────────────────────────────────┐
│  가중 평균 점수 산출                                         │
│  합의 수준 평가                                              │
│  최종 투자 의견 도출                                         │
│  보고서 생성                                                 │
└─────────────────────────────────────────────────────────────┘
```

## 📈 출력 예시

```json
{
  "ticker": "AAPL",
  "recommendation": "Buy",
  "weighted_score": 7.2,
  "consensus_level": 78,
  "target_price": {
    "low": 165,
    "mid": 195,
    "high": 225
  },
  "key_strengths": [
    "강력한 FCF 창출력",
    "Wide Moat (생태계 락인)",
    "우수한 자본 배분 이력"
  ],
  "key_risks": [
    "중국 시장 의존도",
    "성장률 둔화 우려",
    "규제 리스크"
  ]
}
```

## 🧪 테스트

```bash
# 전체 테스트 실행
pytest

# 특정 모듈 테스트
pytest tests/test_tools/
pytest tests/test_agents/

# 커버리지 리포트
pytest --cov=. --cov-report=html
```

## 📝 라이선스

MIT License

## 🤝 기여

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📧 문의

Issues 또는 Discussions를 통해 문의해주세요.

---

**Powered by Claude Opus 4.5 & LangGraph**
