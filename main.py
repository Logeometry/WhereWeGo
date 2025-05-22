from fastapi import FastAPI, Request, Response
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from routeres.search_router import router as search_router
from routeres.category_router import router as category_router
from routeres.google_login_router import router as google_login_router
from fastapi.security import OAuth2PasswordBearer
from routeres.nearby_place_router import router as nearby_place_router
from routeres.user_log_ranking_router import router as get_ranking
from routeres.location_datail_router import router as simple_location_detail
from routeres.weather_router import router as weather_router
from routeres.festival_router import router as festival_router
from routeres.itinerary_router import router as itinerary_router

## from routeres.survey_router import router as survey_router
## from routeres.logging_router import router as logging_router
from schemas import SurveyRequest
import os

SECRET_KEY = os.getenv("SECRET_KEY")
app = FastAPI()

# CORS 설정 추가
# app.add_middleware(
#    CORSMiddleware,
#    allow_origins=["http://localhost:3000"],  # 리액트 개발 서버 주소
#    allow_credentials=True,
#    allow_methods=["*"],  # 모든 HTTP 메서드 허용
#    allow_headers=["*"],  # 모든 헤더 허용
#)

app.include_router(search_router, prefix="/api/v1") 
app.include_router(category_router, prefix="/api/v1")
## app.include_router(survey_router, prefix="/api/v1")
## app.include_router(logging_router, prefix="/api/v1")
app.include_router(google_login_router, prefix="/api/v1")
app.include_router(nearby_place_router, prefix="/api/v1")
app.include_router(get_ranking, prefix="/api/v1")
app.include_router(simple_location_detail, prefix="/api/v1")
app.include_router(weather_router, prefix="/api/v1")
app.include_router(festival_router, prefix="/api/v1")
app.include_router(itinerary_router)

app.mount("/test", StaticFiles(directory="test"), name="test")

origins = [
    "http://localhost",
    "http://localhost:8080",
    "http://127.0.0.1",
    "http://127.0.0.1:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app.mount("/static", StaticFiles(directory=BASE_DIR), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "test"))


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

# test용 코드 
@app.get("/search_test", response_class=HTMLResponse)
async def test_page(request: Request):
    return templates.TemplateResponse("search_test.html", {"request": request})

@app.get("/category_test", response_class=HTMLResponse)
async def category_test_page(request: Request):
    return templates.TemplateResponse("category_test.html", {"request": request})

## @app.get("/survey_test", response_class=HTMLResponse)
## async def survey_test_page(request: Request):
##     return templates.TemplateResponse("survey_test.html", {"request": request})

# 로그인 테스트
@app.get("/login")
def serve_test_page():
    return FileResponse("test/login_test.html")
