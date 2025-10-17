## 구글 로그인 라우터
## 로그인 확인 오류 코드 정리
## 401 : 로그인이 안되어있는 상태
## 404 : 로그인이 되었으나 인증 실패 - 쿠키 저장X, 잘못된 토큰 등

import uuid
from fastapi import APIRouter, Depends, Request, HTTPException, Response
from fastapi.responses import RedirectResponse, JSONResponse
from services.user_store import find_user_by_oauth, find_user_by_id, add_user, update_user_refresh_token, find_user_by_email, update_user_refresh_token_expiry
import urllib.parse
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
from jose import jwt, JWTError
import os

router = APIRouter()
load_dotenv()

FRONTEND_URL = os.getenv("FRONTEND_URL")
SECRET_KEY = os.getenv("SECRET_KEY")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")

# Google OAuth 설정 확인
if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
    print("⚠️ Google OAuth 환경변수가 설정되지 않았습니다.")
    print("⚠️ Google 로그인 기능이 제한됩니다.")
    GOOGLE_OAUTH_AVAILABLE = False
else:
    GOOGLE_OAUTH_AVAILABLE = True
    print("✅ Google OAuth 설정 완료")
REDIRECT_URI = "http://localhost:8000/api/v1/auth/google/callback"
SCOPE = "openid email profile"  # 기본 ID, email, profile 정보 요청
GOOGLE_AUTH_BASE = "https://accounts.google.com/o/oauth2/v2/auth"


# 구글 로그인 페이지 연결 라우터
@router.get("/auth/google/login")
def login_with_google():
    parms = {
        "client_id" : GOOGLE_CLIENT_ID,
        "redirect_uri" : REDIRECT_URI, 
        "response_type" : "code",   # 요청하는 data
        "scope" : SCOPE,         # 권한
        "access_type" : "offline",  # refresh_token
        "prompt" : "consent",   # 사용자 동의창은 매번!
    }
    url = GOOGLE_AUTH_BASE + "?" + urllib.parse.urlencode(parms)

    return RedirectResponse(url)

# 로그인 콜백 라우터
@router.get("/auth/google/callback")
def google_callback(request: Request):
    code = request.query_params.get("code")
    if not code :
        raise HTTPException(status_code=400)
    
    # google에 access_token 요청하기
    token_resp = requests.post("https://oauth2.googleapis.com/token", data={
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code"
    })
    if token_resp.status_code != 200:
        print("[ERROR]", token_resp.status_code)
        print("[RESPONSE]", token_resp.text) 
        raise HTTPException(status_code=500)

    token_data = token_resp.json()
    access_token = token_data.get("access_token")
    refresh_token = token_data.get("refresh_token")

    # access_token으로 사용자 정보 요청
    user_info_resp = requests.get(
        "https://www.googleapis.com/oauth2/v3/userinfo",
        headers={"Authorization": f"Bearer {access_token}"}
    )

    if user_info_resp.status_code != 200:
        raise HTTPException(status_code=500)

    user_info = user_info_resp.json()
    oauth, oauth_id = "google", user_info["sub"]

    user = find_user_by_oauth(oauth, oauth_id)
    if not user:
        # 같은 이메일로 다른 OAuth 제공자로 가입한 사용자가 있는지 확인
        existing_user = find_user_by_email(user_info.get("email"))
        
        if existing_user:
            # 기존 사용자의 OAuth 정보를 구글로 변경하고 리프레시 토큰 갱신
            print(f"[DEBUG] Found existing user with same email, updating OAuth provider to Google")
            update_user_refresh_token_expiry(existing_user["user_id"], refresh_token)
            user = existing_user
            user["oauth"] = "google"
            user["oauth_id"] = oauth_id
            user["picture"] = user_info.get("picture")
        else:
            # 새 사용자 생성
            refresh_token_expiry = datetime.utcnow() + timedelta(days=1)
            user = {
                "user_id": str(uuid.uuid4()), 
                "oauth": "google", 
                "email":     user_info.get("email"),
                "name": user_info.get("name"),
                "oauth_id": user_info.get("sub"),
                "picture": user_info.get("picture"),
                "refresh_token": refresh_token,
                "refresh_token_expiry": refresh_token_expiry.isoformat()
            }
            user["created_at"] = datetime.utcnow().isoformat()
            add_user(user)
    else:
        # 기존 사용자의 마지막 로그인 시간 업데이트 및 리프레시 토큰 갱신
        current_time = datetime.utcnow().isoformat()
        user["last_login"] = current_time
        if refresh_token:
            update_user_refresh_token(user["user_id"], refresh_token)

    # 리프레시 토큰 만료 시간을 1일로 설정 (JWT 토큰은 2시간 유지)
    refresh_token_expiry = datetime.utcnow() + timedelta(days=1)
    
    token = jwt.encode(
        {"sub": user["user_id"], "exp": datetime.utcnow() + timedelta(minutes=120)},
        SECRET_KEY,
        algorithm="HS256"
    )

     # 현재는 테스틑를 위해 /login 페이지, 홈페이지로 바꿀 예정 => 변경 완료
    homepage_url = FRONTEND_URL

    # 로그인 후 홈페이지로 리디렉션 (토큰을 URL 파라미터로 전달)
    # 보안상 더 안전한 방법: 프론트엔드에서 토큰을 받아서 localStorage에 저장
    # homepage_url_with_token = f"{FRONTEND_URL.rstrip('/')}/?token={token}"
    
    response = RedirectResponse(url=homepage_url)
    
    # 백업용으로 쿠키도 설정 (프론트엔드에서 토큰 추출 실패 시)
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        max_age=7200, 
        samesite="none",  # 크로스 도메인 허용
        secure=True,      # HTTPS 필수
        path="/",
        domain=None       # 쿠키를 현재 도메인에만 설정
    )
    return response
