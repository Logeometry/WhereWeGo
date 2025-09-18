from pathlib import Path
import sys
import os

import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# 라우터 imports
from settings import Settings
from routeres.category_router import router as category_router
from routeres.auth_router import router as auth_router
from routeres.google_login_router import router as google_login_router
from routeres.kakao_login_router import router as kakao_login_router
from routeres.refresh_token_router import router as refresh_token_router
from routeres.nearby_place_router import router as nearby_place_router
from routeres.location_datail_router import router as location_detail_router
from routeres.weather_router import router as weather_router
from routeres.festival_router import router as festival_router
from routeres.survey_router import router as survey_router
from routeres.recommeded_cors_router import router as recommended_course_router
from routeres.course_management_router import router as course_management_router
from routeres.wish_router import router as wish_router
from routeres.wishList_router import router as wishlist_router
from routeres.crowding_router import router as crowding_router
from routeres.tmap_crowding_router import router as tmap_crowding_router

from dotenv import load_dotenv
import os
import asyncio

load_dotenv()

# 환경변수 기본값 설정
os.environ.setdefault("SECRET_KEY", "y314adfas...23414afdafasf524515411")
os.environ.setdefault("FRONTEND_URL", "http://localhost:3000")
os.environ.setdefault("MONGO_ATLAS_URI", "mongodb://localhost:27017")
os.environ.setdefault("ENVIRONMENT", "dev")

SECRET_KEY = os.getenv("SECRET_KEY")
FRONTEND_URL = os.getenv("FRONTEND_URL")
settings = Settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup - ML 모델 초기화
    print("🚀 서버 시작 - ML 모델 초기화 중...")
    try:
        from routeres.survey_router import initialize_survey_model
        model_init_success = initialize_survey_model()
        if model_init_success:
            print("✅ ML 모델 초기화 완료 - 추론 전용 모드로 서버 시작")
        else:
            print("⚠️ ML 모델 초기화 실패 - 룰 기반 fallback 모드로 시작")
    except Exception as e:
        print(f"⚠️ 모델 초기화 중 오류 발생: {e}")
        print("🔄 룰 기반 fallback 모드로 서버 시작")

    yield
    # Shutdown
    pass


app = FastAPI(lifespan=lifespan, redirect_slashes=False)

origins = [
    "http://localhost:8000",
    "http://localhost:3000",
    "http://127.0.0.1:8000",
    "http://127.0.0.1:3000",
    FRONTEND_URL
]

# CORS 설정 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# API 라우터 등록
app.include_router(category_router, prefix="/api", tags=["카테고리"])
app.include_router(survey_router, prefix="/api/v1/survey", tags=["설문조사"], include_in_schema=False)
app.include_router(google_login_router, prefix="/api/v1", tags=["인증"])
app.include_router(kakao_login_router, prefix="/api/v1", tags=["인증"])
app.include_router(refresh_token_router, prefix="/api/v1", tags=["인증"])
app.include_router(nearby_place_router, prefix="/api/v1", tags=["주변장소"])
app.include_router(location_detail_router, prefix="/api/v1", tags=["장소상세"])
app.include_router(weather_router, prefix="/api/v1", tags=["날씨"])
app.include_router(festival_router, prefix="/api/v1", tags=["축제"])
app.include_router(recommended_course_router, prefix="/api/v1", tags=["추천코스"])
app.include_router(course_management_router, prefix="/api/v1", tags=["코스관리"])
app.include_router(wish_router, prefix="/api/v1", tags=["찜기능"])
app.include_router(wishlist_router, prefix="/api/v1", tags=["찜목록"])
app.include_router(crowding_router, prefix="/api/v1", tags=["혼잡도"])
app.include_router(tmap_crowding_router, prefix="/api/v1", tags=["티맵 혼잡도"])
app.include_router(auth_router, prefix="/api/v1", tags=["인증"])

app.mount("/test", StaticFiles(directory="test"), name="test")
# app.mount("/static", StaticFiles(directory="."), name="static")  # 보안상 제거 - templates 직접 접근 방지

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def get_safe_file_path(filename):
    """파일 경로를 안전하게 찾아서 반환"""
    current_path = os.path.join(BASE_DIR, "test", filename)
    if os.path.exists(current_path):
        return current_path

    parent_path = os.path.join(os.path.dirname(BASE_DIR), "WhereWeGo-backend", "test", filename)
    if os.path.exists(parent_path):
        return parent_path

    cwd_path = os.path.join(os.getcwd(), "WhereWeGo-backend", "test", filename)
    if os.path.exists(cwd_path):
        return cwd_path

    return current_path


test_dir = os.path.join(os.path.dirname(__file__), "test")
app.mount(
    "/test",
    StaticFiles(directory=test_dir, html=True),
    name="test_static"
)


@app.get("/favicon.ico")
async def favicon():
    return Response(status_code=204)


@app.get("/")
async def root():
    """루트 경로에서 Google 로그인으로 리다이렉트"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="http://localhost:8000/api/v1/auth/google/login", status_code=302)


@app.get("/attractions")
async def show_attractions():
    file_path = os.path.join(BASE_DIR, "google_maps_tourist.html")
    if os.path.exists(file_path):
        return FileResponse(file_path)
    return {"error": "File not found"}


@app.get("/login")
def serve_test_page():
    file_path = get_safe_file_path("login_test.html")
    return FileResponse(file_path)


@app.get("/course-builder")
def serve_course_builder():
    file_path = get_safe_file_path("integrated_course_builder.html")
    return FileResponse(file_path)


@app.get("/survey")
def serve_survey_template():
    file_path = get_safe_file_path("survey_original_template.html")
    return FileResponse(file_path)


@app.get("/survey-complete")
def serve_complete_survey():
    file_path = get_safe_file_path("complete_survey_test.html")
    return FileResponse(file_path)


# survey_router가 이제 모든 설문조사 관련 엔드포인트를 처리합니다.
# /api/v1/survey/ 경로로 등록되어 있으므로 다음과 같이 접근할 수 있습니다:
# - /api/v1/survey/ (메인 페이지)
# - /api/v1/survey/select
# - /api/v1/survey/data
# - /api/v1/survey/recommendations
# - /api/v1/survey/ml-recommendations
# - /api/v1/survey/vote
# - /api/v1/survey/health
# - /api/v1/survey/debug
# - /api/v1/survey/model-status
# - /api/v1/survey/load-model
# - /api/v1/survey/reset
# - /api/v1/survey/reset-all

# 기존 클라이언트 호환성을 위해 루트 경로도 지원 (제거됨 - 로그인 우선 실행을 위해)
# app.include_router(survey_router, prefix="", tags=["설문조사-루트"])

if __name__ == "__main__":
    # 상대 import 문제 해결을 위한 패키지 경로 설정
    import sys
    from pathlib import Path
    import os

    # 현재 디렉토리를 sys.path에 추가 (상대 import를 위해)
    current_dir = Path(__file__).parent
    if str(current_dir) not in sys.path:
        sys.path.insert(0, str(current_dir))

    # 작업 디렉토리를 WhereWeGo-backend로 변경
    os.chdir(current_dir)

    # reload=False로 변경하여 서버 중복 실행 방지
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=False)