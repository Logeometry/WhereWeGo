## 구글 로그인 라우터
## 로그인 확인 오류 코드 정리
## 401 : 로그인이 안되어있는 상태
## 404 : 로그인이 되었으나 인증 실패 - 쿠키 저장X, 잘못된 토큰 등

import uuid
from fastapi import APIRouter, Depends, Request, HTTPException, Response
from fastapi.responses import RedirectResponse, JSONResponse
from services.user_store import find_user_by_oauth, find_user_by_id, add_user
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
        user = {
            "user_id": str(uuid.uuid4()), 
            "oauth": "google", 
            "email":     user_info.get("email"),
            "name": user_info.get("name"),
            "oauth_id": user_info.get("sub"),
            "picture": user_info.get("picture")
        }
        user["created_at"] = datetime.utcnow().isoformat()
        add_user(user)

    token = jwt.encode(
        {"sub": user["user_id"], "exp": datetime.utcnow() + timedelta(minutes=120)},
        SECRET_KEY,
        algorithm="HS256"
    )
     # 현재는 테스틑를 위해 /login 페이지, 홈페이지로 바꿀 예정 => 변경 완료
    homepage_url = f"{FRONTEND_URL.rstrip('/')}/"

    # 로그인 후 홈페이지로 리디렉션
    response = RedirectResponse(url=homepage_url)
    
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        max_age=7200, 
        samesite="lax",
        secure=False, # HTTPS 배포 시 True로 바꿔야함
        path="/"
    )
    return response
