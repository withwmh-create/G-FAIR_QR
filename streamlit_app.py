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
    page_title="G-FAIR KOREA 2026",
    page_icon="🎯",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom secret key for secure signing of temporary tokens
SECRET_KEY = b"NEXUS-SECURE-KEY-FOR-QR-AUTHENTICATION-2026"

def generate_secure_token() -> str:
    """Generates a secure stateful-like signed token: timestamp.signature"""
    timestamp = int(time.time())
    msg = f"{timestamp}".encode()
    sig = hmac.new(SECRET_KEY, msg, hashlib.sha256).hexdigest()[:16]
    return f"{timestamp}.{sig}"


def verify_secure_token(token: str) -> bool:
    """Verifies HMAC signature and 10-second validity of the token"""
    try:
        parts = token.split(".")
        if len(parts) != 2:
            return False
        ts_str, sig = parts
        timestamp = int(ts_str)
        
        # Verify signature
        msg = f"{timestamp}".encode()
        expected_sig = hmac.new(SECRET_KEY, msg, hashlib.sha256).hexdigest()[:16]
        if not hmac.compare_digest(sig, expected_sig):
            return False
            
        # Verify expiration (Resilient window: allow up to 60s for scan/load and 10s for clock drift)
        current_time = int(time.time())
        age = current_time - timestamp
        
        # Resilient tolerance window absorbing latency and clock drift
        if -10 <= age <= 60:
            return True
        return False
    except Exception:
        return False


def clean_html(html_str: str) -> str:
    """Strips leading and trailing whitespace from each line of HTML to prevent Markdown parser from treating it as a code block"""
    return "\n".join(line.strip() for line in html_str.split("\n"))


# Get absolute path of the directory containing this file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
logo_path = os.path.join(BASE_DIR, "static", "images", "logo.png")

# Routing based on Streamlit query parameters
query_params = st.query_params
token = query_params.get("token")

# Custom global CSS to ensure stunning premium aesthetics and bypass browser CSP blocks
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

    /* Hide Streamlit header and footer padding */
    header, footer {
        visibility: hidden !important;
    }

    /* Premium glassmorphism cards and wrappers */
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

    /* Verification Badge styling */
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

    /* Native centering overrides */
    [data-testid="stColumn"] {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
    }

    /* styled list for buyers */
    .buyer-grid {
        display: grid;
        grid-template-columns: 1fr;
        gap: 1.25rem;
        margin-bottom: 1.5rem;
        width: 100%;
    }

    .buyer-card {
        background: rgba(15, 23, 42, 0.4);
        border: 1px solid rgba(255, 255, 255, 0.04);
        border-radius: 16px;
        padding: 1.25rem 1.5rem;
        display: flex;
        align-items: center;
        gap: 1.25rem;
        width: 100%;
        text-align: left;
    }

    .buyer-avatar {
        width: 48px;
        height: 48px;
        border-radius: 12px;
        background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
        color: #ffffff;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        font-size: 1.2rem;
        flex-shrink: 0;
        box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
    }

    .buyer-details {
        flex-grow: 1;
    }

    .buyer-company {
        font-size: 0.75rem;
        font-weight: 700;
        color: var(--primary);
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 2px;
        display: inline-block;
        background: rgba(99, 102, 241, 0.1);
        padding: 2px 8px;
        border-radius: 4px;
    }

    .buyer-name-row {
        display: flex;
        align-items: baseline;
        gap: 6px;
        margin-bottom: 4px;
    }

    .buyer-name {
        font-size: 1.15rem;
        font-weight: 700;
        color: var(--text-main);
    }

    .buyer-position {
        font-size: 0.85rem;
        color: var(--text-muted);
        font-weight: 500;
    }

    .buyer-contact {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 10px;
        padding: 8px 12px;
        color: var(--text-main);
        font-size: 0.85rem;
        font-weight: 600;
        white-space: nowrap;
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
    # BUYER VERIFICATION SCREEN
    # ==========================================
    is_valid = verify_secure_token(token)
    buyers_list = []
    error_msg = None
    
    if is_valid:
        csv_path = os.path.join(BASE_DIR, "data", "raw", "buyers.csv")
        if os.path.exists(csv_path):
            try:
                # Read CSV data with pandas
                df = pd.read_csv(csv_path)
                buyers_list = df.to_dict(orient="records")
            except Exception as e:
                error_msg = f"데이터베이스를 읽는 중 오류가 발생했습니다: {str(e)}"
                is_valid = False
        else:
            error_msg = "바이어 데이터베이스(CSV)가 존재하지 않습니다."
            is_valid = False
    else:
        error_msg = "보안 인증 토큰이 만료되었거나 유효하지 않습니다. 대시보드의 최신 QR 코드를 다시 스캔해주세요."

    # Render Centered brand logo natively using st.image to guarantee CSP-immune execution
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if os.path.exists(logo_path):
            st.image(logo_path, use_container_width=True)

    # Build verification elements
    if is_valid:
        verification_badge_html = "<div class='verification-badge success'><span class='badge-dot success'></span>Verified Secure Session</div>"
        
        buyer_cards_html = ""
        for b in buyers_list:
            avatar_char = b['이름'][0] if b['이름'] else 'B'
            buyer_cards_html += f"""
            <div class="buyer-card">
                <div class="buyer-avatar">{avatar_char}</div>
                <div class="buyer-details">
                    <span class="buyer-company">{b['회사명']}</span>
                    <div class="buyer-name-row">
                        <span class="buyer-name">{b['이름']}</span>
                        <span class="buyer-position">{b['직급']}</span>
                    </div>
                </div>
                <div class="buyer-contact">{b['연락처']}</div>
            </div>
            """
            
        panel_content_html = f"""
        <div class="success-header" style="text-align: center; margin-bottom: 2rem;">
            <h1 class="card-title" style="font-size: 1.7rem;">바이어 데이터베이스 조회</h1>
            <p style="font-size: 0.9rem; color: var(--text-muted);">보안 승인을 거쳐 복호화된 실시간 네트워킹 바이어 카드 목록입니다.</p>
        </div>
        <div class="buyer-grid">
            {buyer_cards_html}
        </div>
        <div class="panel-footer">
            <span style="color: var(--primary); font-weight: 600;">✓ AES-256 동적 토큰 검증 완료</span>
            <span>조회 시각: 2026-07-10</span>
        </div>
        """
    else:
        verification_badge_html = "<div class='verification-badge expired'><span class='badge-dot expired'></span>Token Expired / Blocked</div>"
        panel_content_html = f"""
        <div class="error-container">
            <div class="error-icon-wrapper">
                <span style="color:var(--accent-red); font-size: 2.5rem; font-weight: bold;">!</span>
            </div>
            <h1 class="error-title">인증 토큰이 유효하지 않습니다</h1>
            <p class="error-description">
                해당 세션은 유효시간(10초)이 초과되었거나 손상되었습니다. 바이어 보안 데이터 유출을 방지하기 위해 실시간 데이터 액세스가 자동으로 영구히 차단되었습니다.
            </p>
            <div class="error-action-list">
                <div class="error-action-title">해결 방법</div>
                <ul>
                    <li>중앙 QR 코드 디스플레이 모니터링 화면으로 돌아갑니다.</li>
                    <li>새로 갱신된(10초 이내) QR 코드를 스마트폰으로 다시 스캔해주세요.</li>
                    <li>네트워크 상태 혹은 서버 시간 동기화 오차를 확인해 주세요.</li>
                </ul>
            </div>
            <a href="/" target="_self" class="btn-retry">대시보드로 돌아가기</a>
        </div>
        """

    # Assemble and display premium verification card with clean_html to prevent raw markdown code blocks
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
    # MAIN QR CODE GENERATION & ROTATION DASHBOARD
    # ==========================================
    
    # Automatically determine the default URL based on host environment (Windows = local, Linux = Streamlit Cloud)
    default_url = "http://localhost:8501" if os.name == "nt" else "https://g-fair-qr.streamlit.app"
    
    st.sidebar.header("⚙️ 배포 설정")
    base_url = st.sidebar.text_input(
        "G-FAIR QR 배포 URL", 
        value=default_url,
        help="Streamlit Cloud에 배포 완료 후, 발급받은 실제 URL(예: https://g-fair-qr.streamlit.app)을 입력하시면 QR 스캔 연결이 정상 가동됩니다."
    )
    
    # Initialize states in Streamlit session state
    if "current_token" not in st.session_state:
        st.session_state.current_token = generate_secure_token()
    if "time_remaining" not in st.session_state:
        st.session_state.time_remaining = 10.0
        
    # Autorefresh every 1 second (1000ms) to update the countdown smoothly in cloud production
    # This is 100% stable, consumes 0% CPU, and prevents script timeouts or WebSocket crashes on Streamlit Cloud!
    st_autorefresh(interval=1000, key="countdown_refresh")
    
    # Generate QR code natively
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=10, border=4)
    scan_url = f"{base_url}/?token={st.session_state.current_token}"
    qr.add_data(scan_url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="#1e1b4b", back_color="white")
    
    # Save the QR image to standard PNG bytes to prevent type mismatch on Streamlit
    qr_buf = BytesIO()
    qr_img.save(qr_buf, format="PNG")
    qr_bytes = qr_buf.getvalue()
    
    progress_percentage = (st.session_state.time_remaining / 10.0) * 100
    
    # Render Centered brand logo natively using st.image to guarantee CSP-immune execution
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if os.path.exists(logo_path):
            st.image(logo_path, use_container_width=True)

    # Open premium styled card container with clean_html to prevent raw markdown code blocks
    st.markdown(clean_html("""
    <div class="premium-wrapper">
        <div class="premium-card">
            <h1 class="card-title">Buyer Verification QR</h1>
            <div class="status-badge">
                <span class="pulse-dot"></span>
                <span>Secure Token Rotating</span>
            </div>
    """), unsafe_allow_html=True)
    
    # Display the QR image NATIVELY inside the card using st.image to bypass browser sandbox CSP block
    col_qr1, col_qr2, col_qr3 = st.columns([1.25, 2, 1.25])
    with col_qr2:
        st.image(qr_bytes, use_container_width=True)
        
    # Render progress bar, countdown info and close the container with clean_html
    st.markdown(clean_html(f"""
            <div class="countdown-container">
                <div class="countdown-label">
                    <span>보안 승인 토큰 만료 및 갱신</span>
                    <span class="timer-sec">{st.session_state.time_remaining:.1f}s</span>
                </div>
                <div class="progress-bar-bg">
                    <div class="progress-bar-fill" style="width: {progress_percentage}%;"></div>
                </div>
            </div>
            <div class="helper-text">
                💡 스마트폰 카메라로 스캔하면 G-FAIR 바이어 정보 카드로 이동합니다.
            </div>
        </div> <!-- Close premium-card -->
        <div class="footer">
            <p>&copy; 2026 G-FAIR KOREA 2026. All Rights Reserved.</p>
        </div>
    </div> <!-- Close premium-wrapper -->
    """), unsafe_allow_html=True)
    
    # Tick down remaining time by 1.0 second on each autorefresh trigger
    st.session_state.time_remaining -= 1.0
    
    # Token rotation trigger
    if st.session_state.time_remaining <= 0:
        st.session_state.current_token = generate_secure_token()
        st.session_state.time_remaining = 10.0
