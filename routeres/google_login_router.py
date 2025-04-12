## 구글 로그인 라우터
from fastapi import APIRouter, Depends, Request, HTTPException, Response
from fastapi.responses import RedirectResponse, JSONResponse
from services.user_store import find_user_by_email, add_user
import urllib.parse
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
from jose import jwt, JWTError
import os

router = APIRouter()
load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
REDIRECT_URI = "http://127.0.0.1:8000/api/v1/auth/google/callback"
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
        return JSONResponse({"error": "액세스 토큰을 가져오는 데 실패했습니다"}, status_code=400)
    
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
        return JSONResponse({"error": "액세스 토큰을 가져오는 데 실패했습니다"}, status_code=500)

    token_data = token_resp.json()
    access_token = token_data.get("access_token")

    # access_token으로 사용자 정보 요청
    user_info_resp = requests.get(
        "https://www.googleapis.com/oauth2/v3/userinfo",
        headers={"Authorization": f"Bearer {access_token}"}
    )

    if user_info_resp.status_code != 200:
        return JSONResponse({"error": "사용자 정보를 가져오는 데 실패했습니다"}, status_code=500)

    user_info = user_info_resp.json()
    email = user_info.get("email")

    user = find_user_by_email(email)
    if not user:
        user = {
            "email": email,
            "name": user_info.get("name"),
            "google_id": user_info.get("sub"),
            "picture": user_info.get("picture"),
            "created_at": datetime.utcnow().isoformat()
        }
        add_user(user)

    token = jwt.encode(
        {
            "sub": email,
            "exp": datetime.utcnow() + timedelta(minutes=120) # 유지 시간
        },
            SECRET_KEY,
            algorithm="HS256"
    )
     # 현재는 테스틑를 위해 /login 페이지, 홈페이지로 바꿀 예정
    homepage_url = "http://127.0.0.1:8000/login"

    # 로그인 후 홈페이지로 리디렉션
    response = RedirectResponse(url=homepage_url)
    
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        max_age=7200, 
        samesite="Lax",
        secure=False    # HTTPS 배포 시 True로 바꿔야함
    )
    return response

# 로그인 확인
def get_current_user(request: Request):
    token = request.cookies.get("access_token") 
    if not token:
        raise HTTPException(status_code=401, detail="인증되지 않았습니다")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload.get("sub")  # emali(유저확인 용도)
    except JWTError:
        raise HTTPException(status_code=401, detail="유효하지 않은 토큰")

@router.get("/me")
def read_me(user_email=Depends(get_current_user)):
    user = find_user_by_email(user_email)
    if not user:
        raise HTTPException(status_code=404, detail="유저를 찾을 없습니다")
    return {
        "email": user.email,
        "name": user.name,  # 닉네임
        "picture": user.picture  # 프로필 이미지
    }


# 로그아웃
@router.post("/logout")
def logout(response: Response):
    response.delete_cookie("access_token")
    return {"message": "로그아웃"}