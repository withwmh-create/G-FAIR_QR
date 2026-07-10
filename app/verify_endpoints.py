import urllib.request
import urllib.parse
import json
import time

def verify():
    base_url = "http://127.0.0.1:8000"
    print("=== STARTING PROGRAMMATIC VERIFICATION ===")
    
    # 1. Test / (QR Display Page)
    print("Testing GET / ...")
    try:
        response = urllib.request.urlopen(f"{base_url}/")
        html = response.read().decode('utf-8')
        assert "Buyer Verification QR" in html, "QR page title/header missing!"
        print(" [OK] / (QR Display Page) loaded and contains correct elements.")
    except Exception as e:
        print(f" [FAIL] / endpoint failed: {e}")
        return False
        
    # 2. Test /api/get-token
    print("Testing GET /api/get-token ...")
    try:
        response = urllib.request.urlopen(f"{base_url}/api/get-token")
        data = json.loads(response.read().decode('utf-8'))
        token = data.get("token")
        expires_in = data.get("expires_in")
        assert token is not None, "Token field is missing!"
        assert expires_in == 10, f"Expected expires_in=10, got {expires_in}"
        print(f" [OK] /api/get-token returned a valid token: {token}")
    except Exception as e:
        print(f" [FAIL] /api/get-token endpoint failed: {e}")
        return False
        
    # 3. Test /generate-qr?token=...
    print("Testing GET /generate-qr ...")
    try:
        url = f"{base_url}/generate-qr?token={urllib.parse.quote(token)}"
        response = urllib.request.urlopen(url)
        content_type = response.headers.get("Content-Type")
        content = response.read()
        assert "image/png" in content_type, f"Expected image/png, got {content_type}"
        assert content.startswith(b"\x89PNG\r\n\x1a\n"), "Not a valid PNG image!"
        print(" [OK] /generate-qr returned a valid QR PNG image stream.")
    except Exception as e:
        print(f" [FAIL] /generate-qr endpoint failed: {e}")
        return False
        
    # 4. Test /buyer?token=... (VALID Token)
    print("Testing GET /buyer with VALID token ...")
    try:
        url = f"{base_url}/buyer?token={urllib.parse.quote(token)}"
        response = urllib.request.urlopen(url)
        html = response.read().decode('utf-8')
        assert "바이어 데이터베이스 조회" in html, "Success state text missing!"
        assert "네오 테크놀로지" in html, "Sample buyer company name missing!"
        assert "김민준" in html, "Sample buyer name missing!"
        print(" [OK] /buyer validated token successfully and decrypted the buyer card database.")
    except Exception as e:
        print(f" [FAIL] /buyer with valid token failed: {e}")
        return False
        
    # 5. Test /buyer?token=... (EXPIRED Token)
    print("Waiting 11 seconds to let token expire...")
    time.sleep(11)
    print("Testing GET /buyer with EXPIRED token ...")
    try:
        url = f"{base_url}/buyer?token={urllib.parse.quote(token)}"
        response = urllib.request.urlopen(url)
        html = response.read().decode('utf-8')
        assert "인증 토큰이 유효하지 않습니다" in html, "Expired state warning text missing!"
        assert "네오 테크놀로지" not in html, "Buyer data should NOT be shown for expired tokens!"
        print(" [OK] /buyer successfully blocked expired token and rendered secure blocked screen.")
    except Exception as e:
        print(f" [FAIL] /buyer with expired token failed: {e}")
        return False
        
    print("\n=== VERIFICATION COMPLETED: ALL TESTS PASSED SUCCESSFULLY! ===")
    return True

if __name__ == "__main__":
    verify()
