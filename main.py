from pathlib import Path
import sys
from fastapi import FastAPI, Request, Response
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
# from fastapi.templating import Jinja2Templates  # 임시 비활성화

# 라우터 imports
from settings import Settings
from routeres.search_router import router as search_router
from routeres.category_router import router as category_router
from routeres.auth_router import router as auth_router
from routeres.google_login_router import router as google_login_router
from routeres.kakao_login_router import router as kakao_login_router
from routeres.nearby_place_router import router as nearby_place_router
from routeres.location_datail_router import router as location_detail_router
from routeres.weather_router import router as weather_router
from routeres.festival_router import router as festival_router
from routeres.survey_router import router as survey_router
from routeres.recommeded_cors_router import router as recommended_course_router
from routeres.course_management_router import router as course_management_router
from routeres.wish_router import router as wish_router
from routeres.crowding_router import router as crowding_router
from routeres.tmap_crowding_router import router as tmap_crowding_router
# from routeres.photo_gallery_router import router as photo_gallery_router
from routeres.recommend_location import router as recommend_location_router
# from routeres.map_spot import router as map_spot_router  # 임시 비활성화

from dotenv import load_dotenv
import os
import asyncio

load_dotenv()

# 환경변수 기본값 설정
os.environ.setdefault("SECRET_KEY", "y314adfas...23414afdafasf524515411")
os.environ.setdefault("FRONTEND_URL", "http://localhost:3000")
os.environ.setdefault("MONGO_ATLAS_URI", "mongodb://localhost:27017")
os.environ.setdefault("ENVIRONMENT", "dev")

# ML 모델 초기화
async def initialize_ml_model():
    """ML 모델 초기화"""
    try:
        from services.ml_recommendation_service import ml_recommendation_service
        ckpt_path = os.path.join(os.path.dirname(__file__), "model", "model_epoch_5.pth")
        await ml_recommendation_service.load_model(ckpt_path)
    except Exception as e:
        print(f"ML 모델 초기화 실패: {e}")

SECRET_KEY = os.getenv("SECRET_KEY")
FRONTEND_URL = os.getenv("FRONTEND_URL")
settings = Settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await initialize_ml_model()
    yield
    # Shutdown
    pass

app = FastAPI(lifespan=lifespan)

origins = [
    "http://localhost:8000",
    "http://localhost:3000",
    FRONTEND_URL
]

# CORS 설정 추가
app.add_middleware(
   CORSMiddleware,
   allow_origins=origins,  # 리스트 형태, 추후 배포 서버만 가능하게 수정할 예정
   allow_credentials=True,
   allow_methods=["*"],  # 모든 HTTP 메서드 허용
   allow_headers=["*"],  # 모든 헤더 허용
)

# API 라우터 등록
app.include_router(search_router, prefix="/api/v1", tags=["검색"])
app.include_router(category_router, prefix="/api", tags=["카테고리"])
app.include_router(survey_router, prefix="/api/v1", tags=["설문조사"])
app.include_router(google_login_router, prefix="/api/v1", tags=["인증"])
app.include_router(kakao_login_router, prefix="/api/v1", tags=["인증"])
app.include_router(nearby_place_router, prefix="/api/v1", tags=["주변장소"])
app.include_router(location_detail_router, prefix="/api/v1", tags=["장소상세"])
app.include_router(weather_router, prefix="/api/v1", tags=["날씨"])
app.include_router(festival_router, prefix="/api/v1", tags=["축제"])
app.include_router(recommended_course_router, prefix="/api/v1", tags=["추천코스"])
app.include_router(course_management_router, prefix="/api/v1", tags=["코스관리"])
app.include_router(wish_router, prefix="/api/v1", tags=["찜기능"])
app.include_router(crowding_router, prefix="/api/v1", tags=["혼잡도"])
app.include_router(tmap_crowding_router, prefix="/api/v1", tags=["티맵 혼잡도"])
# app.include_router(photo_gallery_router, prefix="/api/v1", tags=["관광사진갤러리"])
app.include_router(recommend_location_router, prefix="/api/v1", tags=["장소추천"])
app.include_router(auth_router, prefix="/api/v1", tags=["인증"])  # 공통 인증 라우터를 마지막에 등록
# app.include_router(map_spot_router, prefix="/api/v1", tags=["지도"])  # 임시 비활성화

app.mount("/test", StaticFiles(directory="test"), name="test")
app.mount("/static", StaticFiles(directory="."), name="static")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# templates 설정 (임시 비활성화)
# templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "test"))

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
    return {"message": "Welcome to the API"}




@app.get("/attractions")
async def show_attractions():
    file_path = os.path.join(BASE_DIR, "google_maps_tourist.html")
    if os.path.exists(file_path):
        return FileResponse(file_path)
    return {"error": "File not found"}

# test용 코드 (임시 비활성화)
## @app.get("/search_test", response_class=HTMLResponse)
## async def test_page(request: Request):
##    return templates.TemplateResponse("search_test.html", {"request": request})

# @app.get("/category_test", response_class=HTMLResponse)
# async def category_test_page(request: Request):
#     return templates.TemplateResponse("category_test.html", {"request": request})

## @app.get("/survey_test", response_class=HTMLResponse)
## async def survey_test_page(request: Request):
##     return templates.TemplateResponse("survey_test.html", {"request": request})

# 로그인 테스트
@app.get("/login")
def serve_test_page():
    return FileResponse("test/login_test.html")

# 통합 코스 빌더
@app.get("/course-builder")
def serve_course_builder():
    return FileResponse("test/integrated_course_builder.html")
