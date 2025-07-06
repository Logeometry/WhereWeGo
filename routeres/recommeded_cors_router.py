import os
import json
from datetime import datetime, timedelta

import google.generativeai as genai
from bson import ObjectId
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, Body
from pymongo import MongoClient

# Pydantic 모델 import
from schemas import ItineraryRequest, ItineraryResponse

# MongoDB 핸들러 함수 import (새로 추가)
from services.db_handler import get_random_places, tourism_collection

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

def build_gemini_prompt(request_data: ItineraryRequest, places_info: list, start_place_name: str) -> str:
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

    # 전체 프롬프트
    prompt = f"""
    당신은 최고의 여행 코스 플래너입니다. 아래 주어진 정보를 바탕으로 최적의 여행 코스를 JSON 형식으로 짜주세요.

    # 여행 기본 정보:
    - 총 여행 기간: {request_data.travelDuration}일
    - 여행 시작일: {request_data.travelStartDate}
    - 출발 도시: {request_data.otherCity or request_data.departureCity}
    - 부산 내 여행 시작점: {start_place_name}

    # 방문해야 할 장소 목록 (총 {len(places_info)}곳):
    {place_list_str}

    # 요구사항:
    1. 위 목록에 있는 장소들만 {request_data.travelDuration}일 동안의 일정에 포함시켜 주세요.
    2. 첫째 날 첫 일정은 반드시 '{start_place_name}'에서 시작하는 것을 기준으로 다음 장소를 추천해주세요.
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



@router.post("/generate", response_model=ItineraryResponse)
async def generate_itinerary(request: ItineraryRequest = Body(...)):
    """
    사용자 설문조사 결과를 바탕으로 Gemini API를 호출하여 여행 코스를 생성합니다.
    """
    try:
        # 1. (변경점) 딥러닝 모델 대신 MongoDB에서 랜덤으로 추천 장소 ID 리스트를 가져옵니다.
        # 딥러닝 모델이 구현되면 이 부분을 교체하면 됩니다.
        place_ids = get_random_places(count=10)
        
        if not place_ids or len(place_ids) < 10:
            raise HTTPException(status_code=503, detail="추천 장소를 충분히 가져오지 못했습니다. DB를 확인해주세요.")

        # 2. MongoDB에서 추천된 장소 10곳과 시작 장소의 상세 정보를 조회합니다.
        start_place_id = ObjectId(request.startingPoint)
        all_required_ids = place_ids + [start_place_id]
        
        # ... 이하 로직은 이전과 동일 ...
        places_cursor = tourism_collection.find({"_id": {"$in": all_required_ids}})
        places_details = {str(p['_id']): p for p in places_cursor}

        if len(places_details) < len(all_required_ids):
            # 일부 ID가 DB에 없는 경우를 대비
            found_ids = set(places_details.keys())
            missing_ids = [str(oid) for oid in all_required_ids if str(oid) not in found_ids]
            print(f"DB에서 찾지 못한 ID: {missing_ids}")
            raise HTTPException(status_code=404, detail=f"일부 장소 정보를 DB에서 찾을 수 없습니다: {missing_ids}")

        start_place_info = places_details.get(request.startingPoint)
        # 추천 장소 목록에서는 시작 장소를 제외합니다.
        recommended_places_info = [details for pid, details in places_details.items() if pid != request.startingPoint]
        
        if not start_place_info:
            raise HTTPException(status_code=404, detail="시작 장소 정보를 찾을 수 없습니다.")

        # 3. Gemini API에 보낼 프롬프트를 생성합니다.
        prompt = build_gemini_prompt(request, recommended_places_info, start_place_info['name'])

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
        
        return ItineraryResponse(
            dailySchedule=final_schedule,
            travelTips=gemini_result.get("travelTips", "즐거운 부산 여행 되세요!")
        )

    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail=f"서버 내부 오류가 발생했습니다: {e}")