import os
import hmac
import hashlib
import time
import base64
import pandas as pd
import qrcode
from io import BytesIO
import streamlit as st
from streamlit_autorefresh import st_autorefresh

# Set Streamlit page config
st.set_page_config(
    page_title="G-FAIR KOREA 2026 - Secure Badge Portal",
    page_icon="🛡️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom secret key for secure signing of temporary tokens
SECRET_KEY = b"NEXUS-SECURE-KEY-FOR-QR-AUTHENTICATION-2026"

def generate_secure_token(buyer_id: str) -> str:
    """Generates a secure stateful-like signed token containing the buyer ID: timestamp.buyer_id.signature"""
    timestamp = int(time.time())
    msg = f"{timestamp}.{buyer_id}".encode()
    sig = hmac.new(SECRET_KEY, msg, hashlib.sha256).hexdigest()[:16]
    return f"{timestamp}.{buyer_id}.{sig}"


def verify_secure_token(token: str) -> tuple[bool, str]:
    """Verifies HMAC signature, 60s validity window, and returns (is_valid, buyer_id)"""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return False, ""
        ts_str, buyer_id, sig = parts
        timestamp = int(ts_str)
        
        # Verify signature
        msg = f"{timestamp}.{buyer_id}".encode()
        expected_sig = hmac.new(SECRET_KEY, msg, hashlib.sha256).hexdigest()[:16]
        if not hmac.compare_digest(sig, expected_sig):
            return False, ""
            
        # Verify expiration (Resilient window: allow up to 60s for scan/load and 10s for clock drift)
        current_time = int(time.time())
        age = current_time - timestamp
        
        # Resilient tolerance window absorbing latency and clock drift
        if -10 <= age <= 60:
            return True, buyer_id
        return False, ""
    except Exception:
        return False, ""


def clean_html(html_str: str) -> str:
    """Strips leading and trailing whitespace from each line of HTML to prevent Markdown parser from treating it as a code block"""
    return "\n".join(line.strip() for line in html_str.split("\n"))


# Get absolute path of the directory and CSV file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
logo_path = os.path.join(BASE_DIR, "static", "images", "logo.png")
csv_path = os.path.join(BASE_DIR, "data", "raw", "buyers.csv")

def get_buyers_db() -> list[dict]:
    """Reads the CSV file securely and returns buyer dictionary list"""
    if os.path.exists(csv_path):
        try:
            df = pd.read_csv(csv_path)
            return df.to_dict(orient="records")
        except Exception:
            return []
    return []


# Routing based on Streamlit query parameters
query_params = st.query_params
token = query_params.get("token")

# Inject Custom global CSS for breathtaking premium aesthetics
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800&family=Noto+Sans+KR:wght@400;500;700;900&display=swap');

    :root {
        --bg-gradient: linear-gradient(135deg, #0f172a 0%, #1e1e38 50%, #090d16 100%);
        --card-bg: rgba(30, 41, 59, 0.45);
        --card-border: rgba(255, 255, 255, 0.08);
        --primary: #6366f1;
        --primary-glow: rgba(99, 102, 241, 0.35);
        --secondary: #a855f7;
        --accent-green: #10b981;
        --accent-red: #ef4444;
        --text-main: #f8fafc;
        --text-muted: #94a3b8;
    }

    /* Override Streamlit's default background */
    .stApp {
        background: var(--bg-gradient) !important;
        font-family: 'Outfit', 'Noto Sans KR', sans-serif !important;
        color: var(--text-main) !important;
    }

    /* Hide Streamlit default components for a clean look */
    header, footer {
        visibility: hidden !important;
    }

    /* Premium card layout structures */
    .premium-wrapper {
        width: 100%;
        max-width: 520px;
        margin: 0 auto;
        padding: 0 1rem;
    }

    .premium-card {
        background: var(--card-bg);
        border: 1px solid var(--card-border);
        border-radius: 24px;
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        padding: 2.5rem 2rem;
        box-shadow: 0 30px 60px -15px rgba(0, 0, 0, 0.6), 
                    0 0 50px rgba(99, 102, 241, 0.08);
        position: relative;
        overflow: hidden;
        text-align: center;
        margin-top: 1rem;
    }

    .premium-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, var(--primary), var(--secondary));
        border-top-left-radius: 24px;
        border-top-right-radius: 24px;
    }

    .card-title {
        font-size: 1.55rem;
        font-weight: 800;
        letter-spacing: -0.025em;
        background: linear-gradient(135deg, #ffffff 0%, #cbd5e1 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }

    .card-subtitle {
        font-size: 0.875rem;
        color: var(--text-muted);
        margin-bottom: 1.5rem;
    }

    /* Custom form styling overrides for premium look and high-contrast readability */
    .stTextInput>div>div>input {
        background-color: rgba(15, 23, 42, 0.5) !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        color: var(--text-main) !important;
        border-radius: 12px !important;
        padding: 10px 14px !important;
        font-size: 0.95rem !important;
        transition: all 0.3s ease !important;
    }

    .stTextInput>div>div>input:focus {
        border-color: var(--primary) !important;
        box-shadow: 0 0 10px var(--primary-glow) !important;
    }

    /* Force input labels to be bright, bold, and highly readable */
    .stTextInput label, [data-testid="stWidgetLabel"] p {
        color: #e2e8f0 !important; /* Premium Slate-White color for excellent visibility */
        font-weight: 700 !important; /* Extra bold weighting */
        font-size: 0.95rem !important;
        letter-spacing: -0.01em !important;
        margin-bottom: 8px !important;
        display: block;
        text-align: left !important;
    }

    /* High-contrast placeholder text */
    .stTextInput input::placeholder {
        color: rgba(255, 255, 255, 0.45) !important; /* Perfect balance: highly visible but distinct */
        font-weight: 500 !important;
    }

    /* Badges */
    .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(16, 185, 129, 0.1);
        border: 1px solid rgba(16, 185, 129, 0.2);
        padding: 5px 14px;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 700;
        color: var(--accent-green);
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 1.5rem;
    }

    .pulse-dot {
        width: 6px;
        height: 6px;
        background-color: var(--accent-green);
        border-radius: 50%;
        box-shadow: 0 0 10px var(--accent-green);
        animation: pulse-animation 1.5s infinite;
    }

    @keyframes pulse-animation {
        0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
        70% { transform: scale(1); box-shadow: 0 0 0 8px rgba(16, 185, 129, 0); }
        100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
    }

    .verification-badge {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 8px 18px;
        border-radius: 9999px;
        font-size: 0.875rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin: 1.5rem auto;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.2);
    }

    .verification-badge.success {
        background: rgba(16, 185, 129, 0.15);
        border: 1px solid rgba(16, 185, 129, 0.3);
        color: var(--accent-green);
    }

    .verification-badge.expired {
        background: rgba(239, 68, 68, 0.15);
        border: 1px solid rgba(239, 68, 68, 0.3);
        color: var(--accent-red);
    }

    .badge-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        display: inline-block;
    }

    .badge-dot.success { background-color: var(--accent-green); box-shadow: 0 0 10px var(--accent-green); }
    .badge-dot.expired { background-color: var(--accent-red); box-shadow: 0 0 10px var(--accent-red); }

    /* Single Buyer Card styling (verified) */
    .buyer-card-verified {
        background: rgba(15, 23, 42, 0.55);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 20px;
        padding: 1.75rem;
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 1.25rem;
        width: 100%;
        text-align: center;
        margin-top: 1rem;
        box-shadow: inset 0 0 20px rgba(99, 102, 241, 0.05);
    }

    .buyer-avatar-verified {
        width: 72px;
        height: 72px;
        border-radius: 50%;
        background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
        color: #ffffff;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 800;
        font-size: 1.8rem;
        box-shadow: 0 8px 24px rgba(99, 102, 241, 0.4);
    }

    .buyer-company-verified {
        font-size: 0.8rem;
        font-weight: 800;
        color: var(--primary);
        text-transform: uppercase;
        letter-spacing: 0.08em;
        background: rgba(99, 102, 241, 0.12);
        padding: 4px 12px;
        border-radius: 6px;
        margin-bottom: 0.5rem;
        display: inline-block;
    }

    .buyer-name-verified {
        font-size: 1.45rem;
        font-weight: 800;
        color: var(--text-main);
        margin-bottom: 2px;
    }

    .buyer-position-verified {
        font-size: 0.95rem;
        color: var(--text-muted);
        font-weight: 500;
        margin-bottom: 1.25rem;
    }

    .buyer-contact-verified {
        background: rgba(255, 255, 255, 0.04);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 12px;
        padding: 10px 20px;
        color: var(--text-main);
        font-size: 0.95rem;
        font-weight: 700;
        width: 100%;
        max-width: 280px;
        letter-spacing: 0.02em;
    }

    /* Welcome Profile Banner on Dashboard */
    .profile-banner {
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.04);
        border-radius: 16px;
        padding: 1rem;
        margin-bottom: 1.5rem;
        display: flex;
        align-items: center;
        gap: 12px;
        text-align: left;
    }

    .profile-avatar {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
        color: #ffffff;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        font-size: 1.1rem;
    }

    .profile-text {
        display: flex;
        flex-direction: column;
    }

    .profile-greet { font-size: 0.85rem; color: var(--text-muted); }
    .profile-name { font-size: 0.95rem; font-weight: 700; color: var(--text-main); }

    /* Centering layout helper */
    [data-testid="stColumn"] {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
    }

    /* Premium interactive button overrides for perfect contrast and visibility */
    .stButton button {
        background-color: rgba(99, 102, 241, 0.18) !important;
        color: #ffffff !important;
        border: 1px solid rgba(99, 102, 241, 0.45) !important;
        font-weight: 700 !important;
        font-size: 0.95rem !important;
        font-family: 'Outfit', 'Noto Sans KR', sans-serif !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.15) !important;
        border-radius: 12px !important;
        padding: 10px 16px !important;
    }

    .stButton button:hover {
        background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%) !important;
        border-color: transparent !important;
        color: #ffffff !important;
        box-shadow: 0 10px 25px -5px rgba(99, 102, 241, 0.45) !important;
        transform: translateY(-2px) !important;
    }

    .stButton button:active {
        transform: translateY(0) !important;
    }

    /* Countdown bar */
    .countdown-container {
        width: 100%;
        margin: 1.5rem 0;
        text-align: left;
    }

    .countdown-label {
        font-size: 0.85rem;
        color: var(--text-muted);
        margin-bottom: 0.6rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-weight: 500;
    }

    .timer-sec {
        color: var(--text-main);
        font-weight: 700;
        font-size: 0.9rem;
        background: rgba(255, 255, 255, 0.08);
        padding: 2px 8px;
        border-radius: 6px;
    }

    .progress-bar-bg {
        width: 100%;
        height: 6px;
        background: rgba(255, 255, 255, 0.06);
        border-radius: 9999px;
        overflow: hidden;
    }

    .progress-bar-fill {
        height: 100%;
        background: linear-gradient(90deg, var(--primary), var(--secondary));
        box-shadow: 0 0 10px var(--primary-glow);
        border-radius: 9999px;
        transition: width 1s linear;
    }

    .helper-text {
        font-size: 0.75rem;
        color: var(--text-muted);
        line-height: 1.5;
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.04);
        padding: 10px 16px;
        border-radius: 12px;
        width: 100%;
    }

    /* Error styles */
    .error-container {
        text-align: center;
        padding: 1rem 0;
        display: flex;
        flex-direction: column;
        align-items: center;
        width: 100%;
    }

    .error-icon-wrapper {
        width: 80px;
        height: 80px;
        background: rgba(239, 68, 68, 0.1);
        border: 1px solid rgba(239, 68, 68, 0.2);
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-bottom: 1.5rem;
    }

    .error-title {
        font-size: 1.45rem;
        font-weight: 800;
        color: var(--text-main);
        margin-bottom: 0.75rem;
    }

    .error-description {
        font-size: 0.9rem;
        color: var(--text-muted);
        line-height: 1.6;
        margin-bottom: 1.75rem;
    }

    .error-action-list {
        text-align: left;
        background: rgba(0, 0, 0, 0.25);
        border: 1px solid rgba(255, 255, 255, 0.03);
        border-radius: 14px;
        padding: 1.25rem;
        margin-bottom: 1.75rem;
        width: 100%;
    }

    .error-action-title {
        font-size: 0.85rem;
        font-weight: 700;
        color: var(--accent-red);
        margin-bottom: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    .error-action-list ul {
        list-style: none;
        display: flex;
        flex-direction: column;
        gap: 8px;
        padding: 0;
        margin: 0;
    }

    .error-action-list li {
        font-size: 0.85rem;
        color: var(--text-muted);
        padding-left: 12px;
        position: relative;
    }

    .error-action-list li::before {
        content: "•";
        color: var(--accent-red);
        position: absolute;
        left: 0;
        font-weight: bold;
    }

    .btn-retry {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
        border: none;
        color: #ffffff;
        font-size: 0.9rem;
        font-weight: 700;
        padding: 12px 28px;
        border-radius: 12px;
        cursor: pointer;
        box-shadow: 0 10px 20px -5px rgba(99, 102, 241, 0.3);
        text-decoration: none !important;
        margin-top: 1rem;
    }

    .panel-footer {
        margin-top: 2rem;
        border-top: 1px solid rgba(255, 255, 255, 0.05);
        padding-top: 1.25rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 0.75rem;
        color: var(--text-muted);
        width: 100%;
    }

    .footer {
        margin-top: 2rem;
        font-size: 0.75rem;
        color: rgba(148, 163, 184, 0.3);
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)


if token:
    # ==========================================
    # SPECIFIC BUYER VERIFICATION SCREEN (SCAN OUTCOME)
    # ==========================================
    is_valid, matched_buyer_id = verify_secure_token(token)
    matched_buyer = None
    
    if is_valid:
        buyers = get_buyers_db()
        for b in buyers:
            if b.get("아이디") == matched_buyer_id:
                matched_buyer = b
                break
        if not matched_buyer:
            is_valid = False
            error_msg = "존재하지 않거나 삭제된 바이어 ID입니다."
    else:
        error_msg = "보안 승인 토큰이 만료되었거나 손상되었습니다. 바이어의 대시보드 화면에 있는 10초 최신 QR 코드를 다시 스캔해주세요."

    # Render Centered brand logo natively
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if os.path.exists(logo_path):
            st.image(logo_path, use_container_width=True)

    # Build verification elements dynamically
    if is_valid and matched_buyer:
        verification_badge_html = "<div class='verification-badge success'><span class='badge-dot success'></span>Verified Secure Session</div>"
        avatar_char = matched_buyer['이름'][0] if matched_buyer['이름'] else 'B'
        
        panel_content_html = f"""
        <div class="success-header" style="text-align: center; margin-bottom: 1.5rem;">
            <h1 class="card-title" style="font-size: 1.7rem;">Verified Buyer Pass</h1>
            <p style="font-size: 0.9rem; color: var(--text-muted);">블록체인 동적 서명 암호화를 거쳐 검증된 실시간 G-FAIR 바이어 카드입니다.</p>
        </div>
        
        <div class="buyer-card-verified">
            <div class="buyer-avatar-verified">{avatar_char}</div>
            <div class="buyer-details-verified">
                <span class="buyer-company-verified">{matched_buyer['회사명']}</span>
                <div class="buyer-name-verified">{matched_buyer['이름']}</div>
                <div class="buyer-position-verified">{matched_buyer['직급']}</div>
                <div class="buyer-contact-verified">📞 {matched_buyer['연락처']}</div>
            </div>
        </div>
        
        <div class="panel-footer">
            <span style="color: var(--accent-green); font-weight: 700;">✓ 신원 승인 매칭 완료</span>
            <span>검증시각: 2026-07-10 실시간</span>
        </div>
        """
    else:
        verification_badge_html = "<div class='verification-badge expired'><span class='badge-dot expired'></span>Token Expired / Blocked</div>"
        panel_content_html = f"""
        <div class="error-container">
            <div class="error-icon-wrapper">
                <span style="color:var(--accent-red); font-size: 2.5rem; font-weight: bold;">!</span>
            </div>
            <h1 class="error-title">유효하지 않은 인증 토큰</h1>
            <p class="error-description">
                보안을 강화하기 위해 QR 코드 인증 수명이 실시간 만료되었습니다. 바이어 데이터 유출 방지를 위해 이 다이렉트 액세스 세션은 즉시 자동 파기되었습니다.
            </p>
            <div class="error-action-list">
                <div class="error-action-title">해결 방법</div>
                <ul>
                    <li>바이어 전용 모바일 보안 패스 화면을 열어둡니다.</li>
                    <li>화면에 10초마다 자동 회전 갱신되는 새로운 QR 코드를 다시 스캔해 주세요.</li>
                    <li>모바일 기기의 Wi-Fi/네트워크 연결 상태를 확인해 주세요.</li>
                </ul>
            </div>
            <a href="/" target="_self" class="btn-retry">인증 홈으로 가기</a>
        </div>
        """

    # Assemble and display premium verification card
    st.markdown(clean_html(f"""
    <div class="premium-wrapper" style="max-width: 680px;">
        <div style="text-align: center;">
            {verification_badge_html}
        </div>
        <div class="premium-card">
            {panel_content_html}
        </div>
        <div class="footer">
            <p>&copy; 2026 G-FAIR KOREA 2026. All Rights Reserved.</p>
        </div>
    </div>
    """), unsafe_allow_html=True)

else:
    # ==========================================
    # LOGIN OR PERSONAL BADGE DASHBOARD SCREEN
    # ==========================================
    
    # Initialize session states
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "user_info" not in st.session_state:
        st.session_state.user_info = None

    # Render Centered brand logo natively
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if os.path.exists(logo_path):
            st.image(logo_path, use_container_width=True)

    if not st.session_state.logged_in:
        # ==========================================
        # 1. Sleek Glassmorphism Login Page
        # ==========================================
        st.markdown(clean_html("""
        <div class="premium-wrapper">
            <div class="premium-card">
                <h1 class="card-title">G-FAIR Buyer Pass</h1>
                <p class="card-subtitle">바이어 로그인 정보를 입력하여 모바일 디지털 보안 보안증을 가동하세요.</p>
        """), unsafe_allow_html=True)

        # Draw actual input fields using Streamlit but targets premium style classes
        login_id = st.text_input("아이디 (ID)", placeholder="예: buyer01")
        login_pw = st.text_input("비밀번호 (Password)", type="password", placeholder="••••••••")
        
        # Action columns
        col_btn1, col_btn2 = st.columns([1, 1])
        with col_btn1:
            login_submit = st.button("보안인증 로그인 🔑", use_container_width=True)
            
        with col_btn2:
            show_help = st.button("계정 안내 ℹ️", use_container_width=True)

        if show_help:
            st.info("💡 데모 로그인 계정 안내:\n- 아이디: buyer01 ~ buyer05\n- 비밀번호: pass01 ~ pass05 (예: buyer01 / pass01)")

        if login_submit:
            if not login_id or not login_pw:
                st.error("⚠️ 아이디와 비밀번호를 모두 입력해 주세요.")
            else:
                # Validate database matching
                buyers = get_buyers_db()
                matched = None
                for b in buyers:
                    if b.get("아이디") == login_id and b.get("비밀번호") == login_pw:
                        matched = b
                        break
                
                if matched:
                    st.session_state.logged_in = True
                    st.session_state.user_info = matched
                    st.session_state.current_token = generate_secure_token(matched["아이디"])
                    st.session_state.time_remaining = 10.0
                    st.success(f"🔐 {matched['이름']} 바이어님, 신원 인증에 성공했습니다!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("❌ 아이디 또는 비밀번호가 틀렸습니다. 다시 확인해 주세요.")

        st.markdown(clean_html("""
            </div> <!-- Close premium-card -->
            <div class="footer">
                <p>&copy; 2026 G-FAIR KOREA 2026. All Rights Reserved.</p>
            </div>
        </div> <!-- Close premium-wrapper -->
        """), unsafe_allow_html=True)

    else:
        # ==========================================
        # 2. Personalized Smart Secure Dashboard Screen
        # ==========================================
        buyer_data = st.session_state.user_info
        buyer_id = buyer_data["아이디"]
        
        # Automatically determine default server base URL
        default_url = "http://localhost:8501" if os.name == "nt" else "https://g-fair-qr.streamlit.app"
        
        # Display side panel configurations quietly
        st.sidebar.header("⚙️ 배포 설정")
        base_url = st.sidebar.text_input(
            "G-FAIR QR 배포 URL", 
            value=default_url,
            help="배포 환경의 실제 주소에 맞춰 자동으로 QR 스캔 연결 주소가 매핑됩니다."
        )
        
        # Sidebar configurations remain clean and focused

        # Autorefresh smoothly every 1 second (1000ms)
        st_autorefresh(interval=1000, key="countdown_refresh")
        
        # Initialize token variables inside state
        if "current_token" not in st.session_state:
            st.session_state.current_token = generate_secure_token(buyer_id)
        if "time_remaining" not in st.session_state:
            st.session_state.time_remaining = 10.0

        # Generate Secure Personal QR code
        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=10, border=4)
        scan_url = f"{base_url}/?token={st.session_state.current_token}"
        qr.add_data(scan_url)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="#1e1b4b", back_color="white")
        
        # Convert to bytes safely
        qr_buf = BytesIO()
        qr_img.save(qr_buf, format="PNG")
        qr_bytes = qr_buf.getvalue()
        
        progress_percentage = (st.session_state.time_remaining / 10.0) * 100
        avatar_char = buyer_data['이름'][0] if buyer_data['이름'] else 'B'

        # Render premium header greeting and credentials
        st.markdown(clean_html(f"""
        <div class="premium-wrapper">
            <div class="profile-banner">
                <div class="profile-avatar">{avatar_char}</div>
                <div class="profile-text">
                    <span class="profile-greet">신원 확인 상태: 정식 등록 바이어</span>
                    <span class="profile-name">{buyer_data['이름']} {buyer_data['직급']} / {buyer_data['회사명']}</span>
                </div>
            </div>
            
            <div class="premium-card" style="margin-top: 0.5rem;">
                <h1 class="card-title">My Mobile Secure Pass</h1>
                <div class="status-badge">
                    <span class="pulse-dot"></span>
                    <span>Dynamic Badge Active</span>
                </div>
        """), unsafe_allow_html=True)

        # Render Secure QR code image natively
        col_qr1, col_qr2, col_qr3 = st.columns([1.25, 2, 1.25])
        with col_qr2:
            st.image(qr_bytes, use_container_width=True)

        # Render dynamic progress and closing elements
        st.markdown(clean_html(f"""
                <div class="countdown-container">
                    <div class="countdown-label">
                        <span>인증 암호화 토큰 10초 교체 회전</span>
                        <span class="timer-sec">{st.session_state.time_remaining:.1f}s</span>
                    </div>
                    <div class="progress-bar-bg">
                        <div class="progress-bar-fill" style="width: {progress_percentage}%;"></div>
                    </div>
                </div>
                <div class="helper-text">
                    💡 게이트웨이 또는 파트너 데스크에 이 모바일 보안 바코드를 제시하세요. 상대방이 스캔하면 바이어님의 인증 정보 1개가 보관 해제되어 증명됩니다.
                </div>
            </div> <!-- Close premium-card -->
        </div> <!-- Close premium-wrapper -->
        """), unsafe_allow_html=True)
        
        # Center-aligned main body logout and return to home button
        st.write("")
        col_out1, col_out2, col_out3 = st.columns([1, 2, 1])
        with col_out2:
            if st.button("로그아웃 및 인증 홈으로 🔓", use_container_width=True):
                st.session_state.logged_in = False
                st.session_state.user_info = None
                st.rerun()

        # Render small session signature and footer underneath the button
        st.markdown(clean_html(f"""
        <div style="text-align: center; margin-top: 1rem;">
            <p style="font-size:0.75rem; color: rgba(255, 255, 255, 0.25);">사용자 세션: {buyer_data['아이디']}</p>
        </div>
        <div class="footer" style="margin-top: 1.5rem;">
            <p>&copy; 2026 G-FAIR KOREA 2026. All Rights Reserved.</p>
        </div>
        """), unsafe_allow_html=True)

        # Tick down remaining time by 1.0 second on each autorefresh trigger
        st.session_state.time_remaining -= 1.0
        
        # Token rotation trigger
        if st.session_state.time_remaining <= 0:
            st.session_state.current_token = generate_secure_token(buyer_id)
            st.session_state.time_remaining = 10.0
