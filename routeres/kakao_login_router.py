## 카카오 로그인 라우터
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
KAKAO_REST_API_KEY = os.getenv("KAKAKO_REST_API_KEY")  # REST API 키로 통일
KAKAO_REDIRECT_URI = "http://localhost:8000/api/v1/auth/kakao/callback"
KAKAO_AUTH_BASE = "https://kauth.kakao.com/oauth/authorize"

# 디버깅: 환경변수 확인
print(f"KAKAO_REST_API_KEY: {KAKAO_REST_API_KEY}")
print(f"FRONTEND_URL: {FRONTEND_URL}")
print(f"SECRET_KEY: {SECRET_KEY}")

# 카카오 로그인 페이지 연결 라우터
@router.get("/auth/kakao/login")
def login_with_kakao():
    params = {
        "client_id": KAKAO_REST_API_KEY,
        "redirect_uri": KAKAO_REDIRECT_URI,
        "response_type": "code"
    }
    url = KAKAO_AUTH_BASE + "?" + urllib.parse.urlencode(params)
    
    # 디버깅: 생성된 URL 출력
    print(f"[DEBUG] Generated Kakao login URL: {url}")
    print(f"[DEBUG] REST API Key: {KAKAO_REST_API_KEY}")
    print(f"[DEBUG] Redirect URI: {KAKAO_REDIRECT_URI}")
    
    return RedirectResponse(url)

# 로그인 콜백 라우터
@router.get("/auth/kakao/callback")
def kakao_callback(request: Request):
    code = request.query_params.get("code")
    error = request.query_params.get("error")
    error_description = request.query_params.get("error_description")
    
    # 오류가 있는 경우 상세 정보 출력
    if error:
        print(f"[KAKAO ERROR] Error: {error}")
        print(f"[KAKAO ERROR] Description: {error_description}")
        raise HTTPException(status_code=400, detail=f"Kakao OAuth error: {error} - {error_description}")
    
    if not code:
        raise HTTPException(status_code=400)
    
    # 카카오에 access_token 요청하기
    token_resp = requests.post("https://kauth.kakao.com/oauth/token", data={
        "grant_type": "authorization_code",
        "client_id": KAKAO_REST_API_KEY,
        "redirect_uri": KAKAO_REDIRECT_URI,
        "code": code
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
        "https://kapi.kakao.com/v2/user/me",
        headers={"Authorization": f"Bearer {access_token}"}
    )

    if user_info_resp.status_code != 200:
        raise HTTPException(status_code=500)

    user_info = user_info_resp.json()
    oauth, oauth_id = "kakao", str(user_info["id"])

    user = find_user_by_oauth(oauth, oauth_id)
    if not user:
        # 카카오 응답 구조에 맞게 사용자 정보 추출
        kakao_account = user_info.get("kakao_account", {})
        properties = user_info.get("properties", {})
        email = kakao_account.get("email")
        
        # 같은 이메일로 다른 OAuth 제공자로 가입한 사용자가 있는지 확인
        existing_user = find_user_by_email(email) if email else None
        
        if existing_user:
            # 기존 사용자의 OAuth 정보를 카카오로 변경하고 리프레시 토큰 갱신
            print(f"[DEBUG] Found existing user with same email, updating OAuth provider to Kakao")
            update_user_refresh_token_expiry(existing_user["user_id"], refresh_token)
            user = existing_user
            user["oauth"] = "kakao"
            user["oauth_id"] = oauth_id
            user["picture"] = properties.get("profile_image")
        else:
            # 새 사용자 생성
            refresh_token_expiry = datetime.utcnow() + timedelta(days=1)
            user = {
                "user_id": str(uuid.uuid4()),
                "oauth": "kakao",
                "email": email,
                "name": properties.get("nickname"),
                "oauth_id": str(user_info["id"]),
                "picture": properties.get("profile_image"),
                "refresh_token": refresh_token,
                "refresh_token_expiry": refresh_token_expiry.isoformat()
            }
            user["created_at"] = datetime.utcnow().isoformat()
            add_user(user)
    else:
        # 기존 사용자의 리프레시 토큰 업데이트
        if refresh_token:
            update_user_refresh_token(user["user_id"], refresh_token)

    # 리프레시 토큰 만료 시간을 1일로 설정 (JWT 토큰은 2시간 유지)
    refresh_token_expiry = datetime.utcnow() + timedelta(days=1)
    
    token = jwt.encode(
        {"sub": user["user_id"], "exp": datetime.utcnow() + timedelta(minutes=120)},
        SECRET_KEY,
        algorithm="HS256"
    )
    
    # 디버깅: 토큰 생성 확인
    print(f"[DEBUG] Generated JWT token: {token[:50]}...")
    print(f"[DEBUG] User ID: {user['user_id']}")
    print(f"[DEBUG] User data: {user}")
    
    # 테스트 페이지로 리디렉션 (개발 중)
    homepage_url = "http://localhost:8000/test/survey_system_test.html"

    # 로그인 후 홈페이지로 리디렉션
    response = RedirectResponse(url=homepage_url)
    
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        max_age=7200,
        samesite="lax",
        secure=False,  # HTTPS 배포 시 True로 바꿔야함
        path="/"
    )
    
    # 디버깅: 쿠키 설정 확인
    print(f"[DEBUG] Cookie set: access_token={token[:20]}...")
    print(f"[DEBUG] Redirecting to: {homepage_url}")
    
    return response
