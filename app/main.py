import os
import hmac
import hashlib
import time
import pandas as pd
import qrcode
from io import BytesIO

from fastapi import FastAPI, Request, Query
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI(title="G-FAIR KOREA 2026 Secure QR System")

# Secret key for signing the temporary tokens
SECRET_KEY = b"NEXUS-SECURE-KEY-FOR-QR-AUTHENTICATION-2026"

# Create static directories and mount static files
os.makedirs("static/images", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates setup
os.makedirs("app/templates", exist_ok=True)
templates = Jinja2Templates(directory="app/templates")


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
            
        # Verify expiration (must be within 10 seconds)
        current_time = int(time.time())
        age = current_time - timestamp
        
        # Checking age within 0 to 10 seconds
        if 0 <= age <= 10:
            return True
        return False
    except Exception:
        return False


@app.get("/")
@app.get("/qr-display")
def qr_display_page(request: Request):
    """Renders the main display page which refreshes QR code every 10s"""
    return templates.TemplateResponse(request=request, name="qr.html")


@app.get("/api/get-token")
def get_token():
    """Returns a newly generated secure token"""
    token = generate_secure_token()
    return JSONResponse({
        "token": token,
        "expires_in": 10
    })


@app.get("/generate-qr")
def generate_qr(token: str = Query(...), request: Request = None):
    """Dynamically generates a custom QR code pointing to /buyer?token=<token>"""
    base_url = str(request.base_url).rstrip("/")
    buyer_url = f"{base_url}/buyer?token={token}"
    
    # Generate high-quality QR Code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(buyer_url)
    qr.make(fit=True)
    
    # Create customized visual styling: Dark indigo modules on clean background
    img = qr.make_image(fill_color="#1e1b4b", back_color="white")
    
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    
    return StreamingResponse(buf, media_type="image/png")


@app.get("/buyer")
def buyer_info(token: str = Query(...), request: Request = None):
    """Validates secure token, reads CSV with Pandas, and displays buyer cards"""
    is_valid = verify_secure_token(token)
    
    buyers_list = []
    error_msg = None
    
    if is_valid:
        csv_path = "data/raw/buyers.csv"
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
        error_msg = "보안 인증 토큰이 만료되었거나 유효하지 않습니다. QR 코드를 새로 스캔해주세요."
        
    return templates.TemplateResponse(
        request=request,
        name="buyer.html",
        context={
            "is_valid": is_valid,
            "buyers": buyers_list,
            "error_msg": error_msg,
            "token": token
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
