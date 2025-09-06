## 공통 인증 라우터
## 로그인 확인 오류 코드 정리
## 401 : 로그인이 안되어있는 상태
## 404 : 로그인이 되었으나 인증 실패 - 쿠키 저장X, 잘못된 토큰 등

from fastapi import APIRouter, Depends, Request, HTTPException, Response
from services.user_store import find_user_by_id, is_token_blacklisted, add_to_blacklist, is_refresh_token_expired
from jose import jwt, JWTError
from dotenv import load_dotenv
import os

router = APIRouter()
load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")

# 로그인 확인
def get_current_user(request: Request) -> str:
    print(f"[DEBUG] get_current_user called - URL: {request.url}")
    token = request.cookies.get("access_token")
    print(f"[DEBUG] Cookie token: {token[:20] if token else 'None'}...")
    
    if not token:
        # 1-1) HTTP 401: 쿠키가 없거나, fetch의 credentials: "include" 누락
        print("[DEBUG] No access_token cookie found")
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        print(f"[DEBUG] JWT payload: {payload}")
    except JWTError as e:
        # 2-1) HTTP 401: 잘못된 토큰(서명 실패, 만료, 알고리즘 불일치 등)
        print(f"[DEBUG] JWT decode error: {e}")
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")

    # 블랙리스트 확인
    if is_token_blacklisted(token):
        print("[DEBUG] Token is blacklisted")
        raise HTTPException(status_code=401, detail="Token is blacklisted")

    user_id = payload.get("sub")
    print(f"[DEBUG] Extracted user_id: {user_id}")
    
    if not user_id:
        # 3-1) HTTP 401: payload에 sub가 없어서 user_id를 꺼낼 수 없음
        print("[DEBUG] No user_id in payload")
        raise HTTPException(status_code=401, detail="Invalid token payload")
    
    # 리프레시 토큰 만료 확인
    if is_refresh_token_expired(user_id):
        print(f"[DEBUG] Refresh token expired for user: {user_id}, adding JWT to blacklist")
        # 리프레시 토큰이 만료된 경우 현재 JWT 토큰을 블랙리스트에 추가
        add_to_blacklist(token, user_id, "refresh_token_expired")
        raise HTTPException(status_code=401, detail="Refresh token expired, please login again")

    return user_id

@router.get("/me")
def read_me(user_id=Depends(get_current_user)):
    print(f"[DEBUG] /me endpoint called with user_id: {user_id}")
    user = find_user_by_id(user_id)
    if not user:
        print(f"[DEBUG] User not found in database for user_id: {user_id}")
        raise HTTPException(status_code=404)
    print(f"[DEBUG] User found: {user}")
    return {
        "user_id": user["user_id"],   # 내부 식별자
        "oauth":   user["oauth"],     # 로그인 방식 (google, kakao 등)
        "email":   user["email"],
        "name":    user["name"],
        "picture": user["picture"],
    }

# 로그아웃
@router.post("/logout")
def logout(request: Request, response: Response):
    token = request.cookies.get("access_token")
    
    if token:
        try:
            # JWT 토큰에서 user_id 추출
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            user_id = payload.get("sub")
            
            if user_id:
                # 토큰을 블랙리스트에 추가
                add_to_blacklist(token, user_id, "logout")
                print(f"[DEBUG] Token blacklisted for user: {user_id}")
        except JWTError:
            # 토큰이 이미 만료되었거나 잘못된 경우 무시
            print("[DEBUG] Invalid token during logout, skipping blacklist")
    
    # 쿠키에서 토큰 삭제
    response.delete_cookie("access_token")
    return {"message": "로그아웃"}

# 강제 로그아웃 (개발용)
@router.get("/force-logout")
def force_logout(response: Response):
    response.delete_cookie("access_token", path="/")
    return {"message": "강제 로그아웃 완료"}
