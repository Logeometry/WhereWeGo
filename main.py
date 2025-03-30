from fastapi import FastAPI, WebSocket, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os
import json
from knn import get_tourist_spots, get_restaurants, get_nearby_restaurants

app = FastAPI()

# CORS 미들웨어 설정 수정
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

current_dir = os.path.dirname(os.path.abspath(__file__))

app.mount("/static", StaticFiles(directory=current_dir), name="static")


@app.get("/favicon.ico")
async def favicon():
    return Response(status_code=204)


@app.get("/")
async def root():
    return {"message": "Welcome to the API"}


@app.get("/attractions")
async def show_attractions():
    file_path = os.path.join(current_dir, "google_maps_tourist.html")
    print(f"찾고 있는 파일 경로: {file_path}")  # 디버깅용

    if os.path.exists(file_path):
        print(f"파일을 찾았습니다!")  # 디버깅용
        return FileResponse(file_path)
    else:
        print(f"파일을 찾을 수 없습니다.")  # 디버깅용
        print(f"현재 디렉토리의 파일 목록:")
        for file in os.listdir(current_dir):
            print(f"- {file}")
        return {"error": "File not found"}



@app.get("/api/nearby-restaurants/{tourist_name}")
async def get_nearby_restaurants_api(tourist_name: str):
    try:
        nearby_restaurants = get_nearby_restaurants(tourist_name)
        return nearby_restaurants
    except Exception as e:
        return {"error": str(e)}
