from fastapi import FastAPI, Request, Response
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from routeres.search_router import router as search_router
from routeres.category_router import router as category_router
from routeres.survey_router import router as survey_router
from routeres.logging_router import router as logging_router
from schemas import SurveyRequest
import os


app = FastAPI()

app.include_router(search_router, prefix="/api/v1") 
app.include_router(category_router, prefix="/api/v1")
app.include_router(survey_router, prefix="/api/v1")
app.include_router(logging_router)

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

@app.get("/survey_test", response_class=HTMLResponse)
async def survey_test_page(request: Request):
    return templates.TemplateResponse("survey_test.html", {"request": request})
