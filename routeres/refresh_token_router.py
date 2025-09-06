## 리프레시 토큰 라우터
## JWT 토큰 갱신을 위한 엔드포인트

import requests
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from services.user_store import get_user_refresh_token, find_user_by_id
from jose import jwt, JWTError
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

router = APIRouter()
load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
KAKAO_REST_API_KEY = os.getenv("KAKAKO_REST_API_KEY")


def verify_jwt_token(token: str) -> dict:
    """JWT 토큰을 검증하고 페이로드를 반환"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


@router.post("/auth/refresh")
async def refresh_access_token(request: Request):
    """리프레시 토큰을 사용하여 새로운 액세스 토큰 발급"""
    
    # 쿠키에서 현재 토큰 가져오기
    current_token = request.cookies.get("access_token")
    if not current_token:
        raise HTTPException(status_code=401, detail="No access token found")
    
    try:
        # 현재 토큰 검증 (만료되어도 페이로드는 읽을 수 있음)
        payload = verify_jwt_token(current_token)
        user_id = payload.get("sub")
        
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        
        # 사용자 정보 조회
        user = find_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # 사용자의 리프레시 토큰 조회
        refresh_token = get_user_refresh_token(user_id)
        if not refresh_token:
            raise HTTPException(status_code=401, detail="No refresh token found")
        
        # OAuth 제공자에 따라 다른 처리
        oauth_provider = user.get("oauth")
        
        if oauth_provider == "google":
            new_access_token = refresh_google_token(refresh_token)
        elif oauth_provider == "kakao":
            new_access_token = refresh_kakao_token(refresh_token)
        else:
            raise HTTPException(status_code=400, detail="Unsupported OAuth provider")
        
        # 새로운 JWT 토큰 생성
        new_jwt_token = jwt.encode(
            {"sub": user_id, "exp": datetime.utcnow() + timedelta(minutes=120)},
            SECRET_KEY,
            algorithm="HS256"
        )
        
        # 응답 생성
        response = JSONResponse({
            "message": "Token refreshed successfully",
            "access_token": new_jwt_token
        })
        
        # 새로운 토큰을 쿠키에 설정
        response.set_cookie(
            key="access_token",
            value=new_jwt_token,
            httponly=True,
            max_age=7200,
            samesite="lax",
            secure=False,  # HTTPS 배포 시 True로 변경
            path="/"
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Token refresh failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Token refresh failed")


def refresh_google_token(refresh_token: str) -> str:
    """구글 리프레시 토큰으로 새로운 액세스 토큰 발급"""
    token_resp = requests.post("https://oauth2.googleapis.com/token", data={
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token"
    })
    
    if token_resp.status_code != 200:
        print(f"[ERROR] Google token refresh failed: {token_resp.status_code}")
        print(f"[RESPONSE] {token_resp.text}")
        raise HTTPException(status_code=500, detail="Failed to refresh Google token")
    
    token_data = token_resp.json()
    return token_data.get("access_token")


def refresh_kakao_token(refresh_token: str) -> str:
    """카카오 리프레시 토큰으로 새로운 액세스 토큰 발급"""
    token_resp = requests.post("https://kauth.kakao.com/oauth/token", data={
        "grant_type": "refresh_token",
        "client_id": KAKAO_REST_API_KEY,
        "refresh_token": refresh_token
    })
    
    if token_resp.status_code != 200:
        print(f"[ERROR] Kakao token refresh failed: {token_resp.status_code}")
        print(f"[RESPONSE] {token_resp.text}")
        raise HTTPException(status_code=500, detail="Failed to refresh Kakao token")
    
    token_data = token_resp.json()
    return token_data.get("access_token")
