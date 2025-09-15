import os
import json
import uuid
from datetime import datetime, timedelta
from typing import Union, List

import google.generativeai as genai
from bson import ObjectId
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, Body
from pymongo import MongoClient

# Pydantic 모델 import
from schemas import ItineraryRequest, ItineraryResponse, FrontendItineraryResponse, FrontendDay, FrontendPlace, CourseSaveRequest, CourseItinerary, CourseDay, CoursePlace

# MongoDB 핸들러 함수 import (새로 추가)
from services.db_handler import get_random_places, tourism_collection, starting_point_collection
from services.data_converter import data_converter

# MongoDB 클라이언트 설정 (코스 저장용)
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
client = MongoClient(MONGO_URI)
db = client["wherewego"]
courses_collection = db["courses"]

# .env 파일에서 환경 변수 로드
load_dotenv()

# 라우터 객체 생성
router = APIRouter()

# --- Gemini API 설정 ---
# (이전과 동일)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY 환경변수를 설정해주세요.")
genai.configure(api_key=GEMINI_API_KEY)
gemini_model = genai.GenerativeModel('gemini-1.5-flash')

# --- MongoDB 설정은 db_handler.py로 이동했으므로 여기서는 tourism_collection만 사용 ---

def build_gemini_prompt(request_data: ItineraryRequest, places_info: list, start_place_name: str = None) -> str:
    """
    Gemini API에 전송할 프롬프트를 생성하는 함수
    """

    # 장소 목록 문자열 구성 (ID 포함)
    place_list_str = "\n".join([
        f"- ID: {str(place['_id'])}\n"
        f"  이름: {place['name']}\n"
        f"  주소: {place['address']}\n"
        f"  위치: {place['location']['coordinates']}\n"
        f"  설명: {place.get('description', '관광 명소')}"
        for place in places_info
    ])

    # JSON 형식 예시 (실제 ObjectId 스타일)
    json_format_example = """
    {
        "dailySchedule": [
        {
            "day": 1,
            "date": "YYYY-MM-DD",
            "places": [
                {
                    "_id": "681891fa77e67d6ebadae3dd",  // 장소 ID (문자열)
                    "estimated_duration": 2,
                    "travel_time_from_previous": 0
                }
            ]
        }
        ],
        "travelTips": "부산 여행을 위한 종합적인 팁입니다..."
    }
    """

    # 시작점 정보
    start_point_info = ""
    if start_place_name:
        start_point_info = f"- 부산 내 여행 시작점: {start_place_name}"

    # 전체 프롬프트
    prompt = f"""
    당신은 최고의 여행 코스 플래너입니다. 아래 주어진 정보를 바탕으로 최적의 여행 코스를 JSON 형식으로 짜주세요.

    # 여행 기본 정보:
    - 총 여행 기간: {request_data.travelDuration}일
    - 여행 시작일: {request_data.travelStartDate}
    {start_point_info}

    # 방문해야 할 장소 목록 (총 {len(places_info)}곳):
    {place_list_str}

    # 요구사항:
    1. 위 목록에 있는 장소들을 포함하여 {request_data.travelDuration}일 동안의 일정을 구성해주세요. 필요시 추가 장소를 추천할 수 있습니다.
    2. {f"첫째 날 첫 일정은 '{start_place_name}'에서 시작" if start_place_name else "효율적인 동선을 고려하여 시작점을 선택"}해주세요.
    3. 이동 시간과 각 장소에서의 추천 체류 시간을 고려하여 가장 효율적인 동선으로 일정을 구성해주세요.
    4. 각 날짜(date)는 'YYYY-MM-DD' 형식으로 정확하게 계산해서 넣어주세요.
    5. 각 장소별 예상 체류 시간(estimated_duration)은 시간 단위의 정수(예: 2)로, 이전 장소로부터의 이동 시간(travel_time_from_previous)은 분 단위의 정수(예: 30)로 표시해주세요. 첫 장소의 이동 시간은 0입니다.
    6. 마지막으로 부산 여행을 위한 유용한 종합 팁(travelTips)을 2-3문장으로 작성해주세요.
    7. 반드시 아래의 JSON 형식과 키 이름을 정확히 지켜서 응답해주세요. 반드시 장소 ID에는 위에 제공된 ID를 그대로 사용해주세요. 이름이 아닙니다. 
    8. 반드시 JSON만 응답해주세요. 그 외 문장, 주석, 설명은 포함하지 마세요.

    # 출력 JSON 형식 예시:
    {json_format_example}
    """

    return prompt.strip()

def convert_to_frontend_format(itinerary_response: ItineraryResponse) -> FrontendItineraryResponse:
    """
    백엔드 응답을 프론트엔드가 원하는 형태로 변환하는 함수
    """
    frontend_days = []
    
    for day_schedule in itinerary_response.dailySchedule:
        # 날짜 형식 변환: "2026-08-21" -> "2026. 8. 21."
        date_parts = day_schedule.date.split("-")
        formatted_date = f"{date_parts[0]}. {int(date_parts[1])}. {int(date_parts[2])}."
        
        # Day 이름 생성
        day_name = f"Day {day_schedule.day}"
        
        # 장소 정보 변환
        frontend_places = []
        for i, place in enumerate(day_schedule.places):
            # 시간 계산 (첫 장소는 14:00부터 시작, 이후 장소는 이전 장소 + 체류시간 + 이동시간)
            if i == 0:
                start_hour = 14
                start_minute = 0
            else:
                # 이전 장소의 체류시간과 이동시간을 고려하여 시간 계산
                prev_place = day_schedule.places[i-1]
                travel_time_minutes = prev_place.travel_time_from_previous
                duration_hours = prev_place.estimated_duration
                
                # 간단한 시간 계산 (실제로는 더 정교한 로직 필요)
                total_minutes = travel_time_minutes + (duration_hours * 60)
                start_hour = 14 + (total_minutes // 60)
                start_minute = total_minutes % 60
            
            time_str = f"{start_hour:02d}:{start_minute:02d}"
            
            # 아이콘 타입 결정 (카테고리 기반)
            icon_type = "MuseumIcon"  # 기본값
            if hasattr(place, 'category'):
                if '해수욕장' in place.name or '해변' in place.name:
                    icon_type = "BeachAccessIcon"
                elif '시장' in place.name or '상가' in place.name:
                    icon_type = "ShoppingCartIcon"
                elif '식당' in place.name or '맛집' in place.name:
                    icon_type = "RestaurantIcon"
                elif '케이블카' in place.name or '공원' in place.name:
                    icon_type = "FlightTakeoffIcon"
            
            frontend_place = FrontendPlace(
                id=str(i + 1),  # 프론트엔드에서 사용하는 순서 ID
                name=place.name,
                placeId=place.id,
                time=time_str,
                icon=icon_type
            )
            frontend_places.append(frontend_place)
        
        frontend_day = FrontendDay(
            date=formatted_date,
            dayName=day_name,
            places=frontend_places
        )
        frontend_days.append(frontend_day)
    
    return FrontendItineraryResponse(
        itinerary=frontend_days
    )

def convert_frontend_to_save_format(frontend_response: FrontendItineraryResponse, user_id: str, course_name: str) -> CourseSaveRequest:
    """
    프론트엔드 형태를 DB 저장 형태로 변환하는 함수
    """
    course_days = []
    
    for day_data in frontend_response.itinerary:
        day_number = int(day_data.dayName.split(" ")[1])  # "Day 1" -> 1
        
        # 날짜 형식 변환: "2026. 8. 21." -> "2026-08-21"
        date_parts = day_data.date.replace(".", "").split()
        formatted_date = f"{date_parts[0]}-{date_parts[1].zfill(2)}-{date_parts[2].zfill(2)}"
        
        day_places = []
        for place in day_data.places:
            course_place = CoursePlace(
                place_id=place.placeId or place.id,
                name=place.name,
                time=place.time
            )
            day_places.append(course_place)
        
        course_day = CourseDay(
            day=day_number,
            date=formatted_date,
            places=day_places
        )
        course_days.append(course_day)
    
    # 실제 여행 코스 데이터 구성
    itinerary = CourseItinerary(
        days=course_days
    )
    
    return CourseSaveRequest(
        user_id=user_id,
        course_name=course_name,
        itinerary=itinerary
    )



@router.post("/generate", response_model=FrontendItineraryResponse)
async def generate_itinerary(request: ItineraryRequest = Body(...)):
    """
    사용자 설문조사 결과를 바탕으로 Gemini API를 호출하여 여행 코스를 생성합니다.
    """
    try:
        # 1. 사용자가 선택한 장소 ID 리스트를 사용합니다.
        selected_place_ids = [ObjectId(pid) for pid in request.selected_places]
        
        if not selected_place_ids:
            raise HTTPException(status_code=400, detail="선택된 장소가 없습니다. 최소 1개 이상의 장소를 선택해주세요.")
        
        # 2. MongoDB에서 선택된 장소들의 상세 정보를 조회합니다.
        places_cursor = tourism_collection.find({"_id": {"$in": selected_place_ids}})
        places_details = {str(p['_id']): p async for p in places_cursor}

        if not places_details:
            raise HTTPException(status_code=404, detail="선택된 장소 정보를 찾을 수 없습니다.")
        
        # 시작점 설정 (사용자가 선택한 경우 또는 첫 번째 장소)
        start_place_info = None
        start_place_name = None
        
        if request.starting_point:
            # 사용자가 시작점을 선택한 경우
            start_place_id = ObjectId(request.starting_point)
            if str(start_place_id) in places_details:
                start_place_info = places_details[str(start_place_id)]
                start_place_name = start_place_info['name']
            else:
                # 시작점이 선택된 장소에 없는 경우, 별도로 조회
                start_place_cursor = tourism_collection.find_one({"_id": start_place_id})
                if start_place_cursor:
                    start_place_info = start_place_cursor
                    start_place_name = start_place_info['name']
                else:
                    raise HTTPException(status_code=404, detail="선택한 시작점 장소를 찾을 수 없습니다.")
        else:
            # 시작점을 선택하지 않은 경우, 첫 번째 장소를 시작점으로 설정
            first_place_id = list(places_details.keys())[0]
            start_place_info = places_details[first_place_id]
            start_place_name = start_place_info['name']
        
        if len(places_details) < len(selected_place_ids):
            # 일부 ID가 DB에 없는 경우를 대비
            found_ids = set(places_details.keys())
            missing_ids = [str(oid) for oid in selected_place_ids if str(oid) not in found_ids]
            print(f"DB에서 찾지 못한 ID: {missing_ids}")
            raise HTTPException(status_code=404, detail=f"일부 장소 정보를 DB에서 찾을 수 없습니다: {missing_ids}")

        # 선택된 장소들을 모두 코스에 포함시킵니다 (시작점 제외하지 않음)
        selected_places_info = list(places_details.values())

        # 3. Gemini API에 보낼 프롬프트를 생성합니다.
        prompt = build_gemini_prompt(request, selected_places_info, start_place_name)

        # 4. Gemini API 호출
        response = gemini_model.generate_content(prompt)
        cleaned_response_text = response.text.strip().replace("```json", "").replace("```", "").strip()
        
        print("==== Gemini 응답 원문 ====")
        print(response.text)

        # 5. Gemini 응답(JSON)을 파싱합니다.
        try:
            gemini_result = json.loads(cleaned_response_text)
        except json.JSONDecodeError:
            raise HTTPException(status_code=500, detail="Gemini API로부터 유효한 JSON 응답을 받지 못했습니다.")

        # 6. 파싱된 결과를 프론트엔드 응답 형식(ItineraryResponse)에 맞게 가공합니다.
        final_schedule = []
        start_date = datetime.strptime(request.travelStartDate, "%Y-%m-%d")

        for daily_plan in gemini_result.get("dailySchedule", []):
            day_number = daily_plan.get("day")
            if not day_number: continue
            
            current_date = start_date + timedelta(days=day_number - 1)
            
            day_places = []
            for place_info in daily_plan.get("places", []):
                place_id_str = place_info.get("_id")
                if place_id_str in places_details:
                    db_place_detail = places_details[place_id_str].copy()
                    db_place_detail['_id'] = str(db_place_detail['_id'])
                    
                    place_data = {
                        **db_place_detail,
                        "estimated_duration": place_info.get("estimated_duration", 2),
                        "travel_time_from_previous": place_info.get("travel_time_from_previous", 20),
                    }
                    day_places.append(place_data)

            final_schedule.append({
                "day": day_number,
                "date": current_date.strftime("%Y-%m-%d"), # 프론트와 형식을 맞춤
                "places": day_places,
            })
        
        # 백엔드 형태로 응답 생성
        backend_response = ItineraryResponse(
            dailySchedule=final_schedule,
            travelTips=gemini_result.get("travelTips", "즐거운 부산 여행 되세요!")
        )
        
        # 프론트엔드 형태로 변환하여 반환
        return convert_to_frontend_format(backend_response)

    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail=f"서버 내부 오류가 발생했습니다: {e}")

@router.post("/save")
async def save_course(request_data: Union[List[dict], dict] = Body(...)):
    """
    생성된 여행 코스를 DB에 저장합니다.
    프론트엔드 형식과 백엔드 형식을 모두 자동으로 지원합니다.
    """
    try:
        # 데이터 변환 서비스 사용
        from services.data_converter import data_converter
        
        normalized_data = data_converter.normalize_course_data(request_data)
        
        # 고유한 코스 ID 생성
        course_id = str(uuid.uuid4())
        
        # 현재 시간
        now = datetime.now()
        
        # DB에 저장할 문서 구성
        course_document = {
            "course_id": course_id,
            "user_id": normalized_data["user_id"],
            "course_name": normalized_data["course_name"],
            "itinerary": normalized_data["itinerary"],
            "created_at": now,
            "updated_at": now
        }
        
        # MongoDB에 저장
        result = courses_collection.insert_one(course_document)
        
        if result.inserted_id:
            return {
                "success": True,
                "course_id": course_id,
                "message": "코스가 성공적으로 저장되었습니다."
            }
        else:
            raise HTTPException(status_code=500, detail="코스 저장에 실패했습니다.")
            
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"코스 저장 중 오류 발생: {e}")
        raise HTTPException(status_code=500, detail=f"서버 내부 오류가 발생했습니다: {e}")

@router.get("/user/{user_id}")
async def get_user_courses(user_id: str):
    """
    특정 사용자의 저장된 코스 목록을 조회합니다.
    """
    try:
        # 사용자의 코스 목록 조회
        courses = list(courses_collection.find(
            {"user_id": user_id},
            {"course_id": 1, "course_name": 1, "created_at": 1, "updated_at": 1}
        ).sort("created_at", -1))
        
        # ObjectId를 문자열로 변환
        for course in courses:
            course["_id"] = str(course["_id"])
            course["created_at"] = course["created_at"].isoformat()
            course["updated_at"] = course["updated_at"].isoformat()
        
        return {
            "success": True,
            "courses": courses
        }
        
    except Exception as e:
        print(f"코스 조회 중 오류 발생: {e}")
        raise HTTPException(status_code=500, detail=f"서버 내부 오류가 발생했습니다: {e}")

@router.get("/course/{course_id}")
async def get_course_detail(course_id: str, format: str = "backend"):
    """
    특정 코스의 상세 정보를 조회합니다.
    
    Args:
        course_id: 코스 ID
        format: 응답 형식 ("backend" 또는 "frontend")
    """
    try:
        # 코스 상세 정보 조회
        course = courses_collection.find_one({"course_id": course_id})
        
        if not course:
            raise HTTPException(status_code=404, detail="코스를 찾을 수 없습니다.")
        
        # ObjectId를 문자열로 변환
        course["_id"] = str(course["_id"])
        course["created_at"] = course["created_at"].isoformat()
        course["updated_at"] = course["updated_at"].isoformat()
        
        if format == "frontend":
            # 프론트엔드 형식으로 변환
            frontend_data = data_converter.convert_backend_to_frontend(course)
            return {
                "success": True,
                "course": course,  # 원본 데이터
                "itinerary": frontend_data  # 프론트엔드 형식 데이터
            }
        else:
            # 기존 백엔드 형식
            return {
                "success": True,
                "course": course
            }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"코스 상세 조회 중 오류 발생: {e}")
        raise HTTPException(status_code=500, detail=f"서버 내부 오류가 발생했습니다: {e}")

@router.get("/course/{course_id}/frontend")
async def get_course_for_frontend(course_id: str):
    """
    프론트엔드 TravelPlanSamplePage에서 바로 사용할 수 있는 형식으로 코스를 반환합니다.
    """
    try:
        # 코스 상세 정보 조회
        course = courses_collection.find_one({"course_id": course_id})
        
        if not course:
            raise HTTPException(status_code=404, detail="코스를 찾을 수 없습니다.")
        
        # 프론트엔드 형식으로 변환
        frontend_data = data_converter.convert_backend_to_frontend(course)
        
        return frontend_data  # 배열 형태로 직접 반환
        
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"프론트엔드용 코스 조회 중 오류 발생: {e}")
        raise HTTPException(status_code=500, detail=f"서버 내부 오류가 발생했습니다: {e}")