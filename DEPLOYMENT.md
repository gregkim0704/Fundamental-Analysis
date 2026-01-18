# 🚀 Streamlit Cloud 배포 가이드

## 빠른 시작 (5분 내 배포)

### 1단계: GitHub 저장소 준비

```bash
# 프로젝트 디렉토리로 이동
cd Fundamental-Analysis

# Git 초기화 (아직 안했다면)
git init

# 모든 파일 추가
git add .

# 커밋
git commit -m "Initial commit: AI 투자위원회 앱"

# GitHub 저장소 생성 후 연결
git remote add origin https://github.com/YOUR_USERNAME/fundamental-analysis.git
git push -u origin main
```

### 2단계: Streamlit Cloud 배포

1. **[share.streamlit.io](https://share.streamlit.io)** 접속
2. **Sign in with GitHub** 클릭
3. **New app** 클릭
4. 저장소 정보 입력:
   - **Repository**: `YOUR_USERNAME/fundamental-analysis`
   - **Branch**: `main`
   - **Main file path**: `app/main.py`
5. **Deploy!** 클릭

### 3단계: Secrets 설정 (API 키)

1. 배포된 앱 우측 상단 **⋮** 메뉴 클릭
2. **Settings** 선택
3. **Secrets** 탭 클릭
4. 아래 내용 입력:

```toml
# 필수
ANTHROPIC_API_KEY = "sk-ant-api03-your-key-here"

# 선택 (한국 주식 분석 시 필요)
OPENDART_API_KEY = "your-opendart-key"

# 선택 (거시경제 데이터)
FRED_API_KEY = "your-fred-key"
```

5. **Save** 클릭

---

## 파일 구조

```
Fundamental-Analysis/
├── app/
│   ├── main.py              # 메인 엔트리포인트 ⭐
│   ├── pages/
│   │   ├── dashboard.py
│   │   └── analysis.py
│   └── components/
│       ├── battle_arena.py
│       ├── youtube_studio.py
│       └── ...
├── .streamlit/
│   ├── config.toml          # Streamlit 설정
│   └── secrets.toml.example # Secrets 템플릿
├── requirements.txt         # 의존성
└── DEPLOYMENT.md           # 이 파일
```

---

## API 키 발급 방법

### Anthropic API (필수)
1. [console.anthropic.com](https://console.anthropic.com) 접속
2. 회원가입 후 API Keys 메뉴
3. Create Key 클릭
4. 생성된 키 복사 (`sk-ant-api03-...`)

### OpenDART API (한국 주식)
1. [opendart.fss.or.kr](https://opendart.fss.or.kr) 접속
2. 회원가입
3. 인증키 신청
4. 발급된 40자리 키 복사

### FRED API (거시경제)
1. [fred.stlouisfed.org](https://fred.stlouisfed.org) 접속
2. My Account → API Keys
3. Request API Key
4. 발급된 32자리 키 복사

---

## 트러블슈팅

### ❌ ModuleNotFoundError
```
requirements.txt에 해당 패키지가 있는지 확인
```

### ❌ API 키 오류
```
Settings > Secrets에서 키가 올바르게 입력되었는지 확인
따옴표 포함, 공백 없이 입력
```

### ❌ 메모리 부족
```
Streamlit Cloud 무료 플랜은 1GB 메모리 제한
대용량 데이터 분석 시 유료 플랜 고려
```

### ❌ 앱이 느림
```
캐싱 활용: @st.cache_data 데코레이터 사용
불필요한 API 호출 줄이기
```

---

## 커스텀 도메인 (선택)

1. Streamlit Cloud 앱 Settings
2. Custom domain 섹션
3. 도메인 입력 (예: `ai-committee.yourdomain.com`)
4. DNS 설정에 CNAME 레코드 추가:
   - Host: `ai-committee`
   - Value: `your-app.streamlit.app`

---

## 앱 URL

배포 완료 후 URL 형식:
```
https://YOUR_USERNAME-fundamental-analysis-app-main-XXXXX.streamlit.app
```

또는 커스텀 도메인:
```
https://ai-committee.yourdomain.com
```

---

## 로컬 테스트

배포 전 로컬에서 테스트:

```bash
# 가상환경 생성
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 로컬 실행
streamlit run app/main.py
```

브라우저에서 `http://localhost:8501` 접속

---

## 업데이트 방법

코드 수정 후:

```bash
git add .
git commit -m "Update: 기능 설명"
git push
```

Streamlit Cloud가 자동으로 재배포합니다 (약 1-2분 소요).

---

## 문의

- GitHub Issues: [저장소 URL]/issues
- Streamlit 문서: [docs.streamlit.io](https://docs.streamlit.io)
