# G-FAIR KOREA 2026 - Secure QR Buyer Verification System 🚀

> **실시간 10초 보안 토큰 회전 기반의 QR 바이어 정보 조회 풀스택 웹 애플리케이션**

본 프로젝트는 보안이 극도로 중요한 비즈니스 네트워킹 현장(예: G-FAIR KOREA 전시회 등)에서 스마트폰 QR 스캔을 통해 바이어 정보를 조회하는 안전하고 현대적인 시스템입니다. 

---

## ✨ 핵심 기능 (Key Features)

1. **실시간 10초 보안 토큰 회전 (Dynamic 10s Token Rotation)**
   - 백엔드에서 `HMAC-SHA256` 서명 방식을 사용하여 10초간만 유효한 임시 암호화 토큰(`timestamp.signature`)을 생성합니다.
   - 데이터 위변조를 원천 차단하며 데이터베이스 없이 완벽히 Stateless하게 동작합니다.

2. **부드러운 카운트다운 게이지 & QR 자동 갱신 (Smooth UX Countdown)**
   - 대시보드 화면에서 실시간 100ms 간격으로 디크리먼트(Decrement)되는 프로그레스 바가 흐르며, `0.0s` 도달 시 AJAX 호출을 통해 새로운 보안 QR 코드로 자동 갱신됩니다.

3. **고해상도 맞춤형 브랜드 로고 내장 (Brand Customization)**
   - Python `Pillow` 벡터 드로잉을 통해 제작된 고화질 전용 로고(`logo.png`)가 상단 헤더에 탑재되어 전시회 브랜딩의 일관성을 높입니다.

4. **보안 지향형 바이어 카드 정보 조회 (Secure Directory Decryption)**
   - **유효 시간(10초) 내 스캔 시**: Pandas를 통해 바이어 정보 DB(`buyers.csv`)를 안전하게 로드한 뒤, 원클릭 연락처 복사 기능이 내장된 프리미엄 글래스모피즘(Glassmorphism) 카드 UI를 렌더링합니다.
   - **유효 시간 초과 시**: 바이어 정보 접근을 완전 봉쇄하고 강렬한 경고 아이콘과 함께 대시보드 복귀 안내 카드를 표시합니다.

---

## 🛠️ 기술 스택 (Tech Stack)

- **Backend**: FastAPI, Uvicorn, Jinja2 (HTML Template Engine)
- **Data Science / File I/O**: Pandas (CSV 파싱 및 관리)
- **QR & Image processing**: qrcode, Pillow (디지털 로고 생성 및 QR 이미지 동적 생성)
- **Frontend**: HTML5, Vanilla CSS3 (Neon-Dark Theme & Glassmorphic CSS), Vanilla JS (Fetch API, 100ms Smooth Ticker)

---

## 📂 폴더 구조 (Directory Tree)

```text
.
├── app/
│   ├── main.py                 # FastAPI 핵심 백엔드 애플리케이션 및 토큰 유효성 검증 로직
│   ├── generate_logo.py        # PIL 기반 고해상도 G-FAIR KOREA 로고 프로그램 생성기
│   ├── verify_endpoints.py     # 통합 시스템 E2E 자동 검증 스크립트
│   └── templates/
│       ├── qr.html             # [PC/전시장용] 실시간 QR 코드 회전 대시보드
│       └── buyer.html          # [모바일 스캔용] 바이어 정보 해독 프로필 카드 / 차단 화면
├── data/
│   └── raw/
│       └── buyers.csv          # 바이어 엑셀(CSV) 데이터 원본 (회사명, 이름, 직급, 연락처)
├── static/
│   └── images/
│       └── logo.png            # 생성된 고품질 전용 브랜드 로고
├── requirements.txt            # 파이썬 의존성 패키지 규격
└── .gitignore                  # Git 커밋 제외 대상 관리 파일
```

---

## ⚙️ 설치 및 실행 방법 (Installation & Usage)

### 1. 의존성 패키지 설치
로컬 터미널을 열고 필요한 패키지들을 한 번에 설치합니다.
```bash
pip install -r requirements.txt
```

### 2. 브랜드 로고 생성 (선택 사항)
새롭게 브랜드 로고를 다시 드로잉하고 배치하려는 경우 실행합니다.
```bash
python app/generate_logo.py
```

### 3. 웹 서버 구동
Uvicorn 서버를 실행합니다.
```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
실행이 완료되면 브라우저에서 [http://127.0.0.1:8000](http://127.0.0.1:8000)으로 접속합니다.

### 4. 통합 검증 스크립트 실행
서버의 통신 상태 및 10초 만료 로직이 설계대로 작동하는지 자동으로 E2E 검증을 처리합니다.
```bash
python app/verify_endpoints.py
```

---

## 🔒 보안 정책 (Security Policy)

전시장 내 유출 위협을 차단하기 위해, 일회성으로 생성된 일련의 QR 코드는 **스캔 직후 모바일 기기의 브라우저 로드 시점 기준 10초 이내에 승인**을 완료해야만 데이터베이스를 디코딩합니다. 10초를 초과한 상태에서 접속을 시도하면 세션은 자동으로 만료되며, 대시보드에 표시되는 최신 QR 코드를 실시간으로 다시 인식해야만 바이어 조회가 복구됩니다.
