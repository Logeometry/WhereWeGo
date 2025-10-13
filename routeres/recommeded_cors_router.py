import os
import json
import uuid
import asyncio
import aiohttp
from datetime import datetime, timedelta, date, time
from typing import Union, List, Dict, Tuple, Optional, Any

import google.generativeai as genai
from bson import ObjectId
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, Body
from pymongo import MongoClient

# Pydantic 모델 import
from schemas import ItineraryRequest, ItineraryResponse, FrontendItineraryResponse, FrontendDay, FrontendPlace, CourseSaveRequest, CourseItinerary, CourseDay, CoursePlace

# MongoDB 핸들러 함수 import
from services.db_handler import get_random_places, tourism_collection, starting_point_collection
from services.data_converter import data_converter

# MongoDB 클라이언트 설정 (코스 저장용) - 안전하게 처리
MONGO_URI = os.getenv("MONGO_URI") or os.getenv("MONGO_ATLAS_URI", "mongodb://localhost:27017/")

try:
    client = MongoClient(MONGO_URI)
    db = client["wherewego"]
    courses_collection = db["courses"]
    print("✅ 코스 저장용 MongoDB 연결 성공")
except Exception as e:
    print(f"❌ 코스 저장용 MongoDB 연결 실패: {e}")
    client = None
    db = None
    courses_collection = None

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

# Google Distance Matrix API 키
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
if not GOOGLE_MAPS_API_KEY:
    print("⚠️ GOOGLE_MAPS_API_KEY 환경변수가 설정되지 않았습니다. Distance Matrix 기능이 제한됩니다.")
else:
    print("✅ Google Maps API 키가 설정되었습니다.")

# --- MongoDB 설정은 db_handler.py로 이동했으므로 여기서는 tourism_collection만 사용 ---

class OptimizedDistanceMatrixService:
    """
    🚀 최적화된 Google Distance Matrix API 서비스
    - 좌표 리스트 기반 일괄 처리
    - Transit 모드 전용 (한국 최적화)
    - 효율적인 매트릭스 데이터 처리
    """
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://maps.googleapis.com/maps/api/distancematrix/json"
        self.max_elements = 100  # Google API 제한
    
    async def get_distance_matrix_for_places(
        self, 
        place_coords: List[Tuple[float, float]],
        departure_time: Optional[int] = None
    ) -> Dict:
        """
        장소들의 좌표로부터 모든 쌍의 거리/시간 매트릭스를 가져옵니다.
        
        Args:
            place_coords: [(위도, 경도)] 형식의 좌표 리스트
            departure_time: 출발 시간 (Unix timestamp, 선택사항)
        
        Returns:
            Distance Matrix API 응답 데이터
        """
        if not self.api_key:
            raise ValueError("Google Maps API 키가 설정되지 않았습니다.")
        
        if len(place_coords) == 0:
            raise ValueError("좌표 리스트가 비어있습니다.")
        
        # 좌표를 "lat,lng" 형식의 문자열로 변환
        coord_strings = [f"{lat},{lng}" for lat, lng in place_coords]
        
        # API 요청 파라미터 구성
        params = {
            "origins": "|".join(coord_strings),
            "destinations": "|".join(coord_strings),  # 모든 장소를 origin과 destination으로 사용
            "mode": "transit",  # 한국에서는 transit만 정확함
            "units": "metric",
            "region": "KR",
            "key": self.api_key
        }
        
        # # # 출발 시간이 지정된 경우 추가 (현재 시간 기본값)
        # # if departure_time:
        # #     params["departure_time"] = departure_time
        # # else:
        # #     params["departure_time"] = int(datetime.now().timestamp())
        
        print(f"🚗 Distance Matrix API 호출: {len(place_coords)}개 장소 매트릭스 조회")
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(self.base_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"📡 Distance Matrix API 응답 status: {data.get('status')}")
                        if data.get("status") == "OK":
                            return data
                        else:
                            error_msg = f"Distance Matrix API 오류: {data.get('status', 'Unknown error')}"
                            if 'error_message' in data:
                                error_msg += f" - {data['error_message']}"
                            print(f"❌ {error_msg}")
                            print(f"📋 전체 응답: {data}")
                            raise HTTPException(status_code=400, detail=error_msg)
                    else:
                        raise HTTPException(
                            status_code=response.status,
                            detail=f"API 요청 실패: HTTP {response.status}"
                        )
            except aiohttp.ClientError as e:
                raise HTTPException(status_code=500, detail=f"네트워크 오류: {str(e)}")
    
    def parse_matrix_to_dict(self, matrix_data: Dict, place_ids: List[str]) -> Dict[str, Dict[str, Dict]]:
        """
        매트릭스 데이터를 딕셔너리 형태로 파싱합니다.
        
        Returns:
            {origin_id: {dest_id: {distance_km, duration_minutes, status}}}
        """
        result = {}
        
        for i, origin_id in enumerate(place_ids):
            result[origin_id] = {}
            
            for j, dest_id in enumerate(place_ids):
                if i == j:
                    # 같은 장소는 거리 0
                    result[origin_id][dest_id] = {
                        "distance_km": 0,
                        "duration_minutes": 0,
                        "status": "OK"
                    }
                else:
                    try:
                        element = matrix_data["rows"][i]["elements"][j]
                        
                        if element["status"] == "OK":
                            duration_seconds = element["duration"]["value"]
                            distance_meters = element["distance"]["value"]
                            
                            result[origin_id][dest_id] = {
                                # 🔢 계산용 숫자 데이터
                                "distance_km": distance_meters / 1000,
                                "duration_minutes": duration_seconds / 60,
                                "duration_seconds": duration_seconds,
                                
                                # 📝 한국어 표시용 텍스트 (Google API 제공)
                                "distance_text": element["distance"]["text"],    # "136 km"
                                "duration_text": element["duration"]["text"],    # "1시간 38분" 또는 "1 hour 38 mins"
                                
                                # ✅ 실제 사용 가능한 정보만 저장
                                
                                "status": "OK"
                            }
                        else:
                            result[origin_id][dest_id] = {
                                "distance_km": float('inf'),  # 갈 수 없는 경우
                                "duration_minutes": float('inf'),
                                "status": element["status"]
                            }
                    except (KeyError, IndexError):
                        result[origin_id][dest_id] = {
                            "distance_km": float('inf'),
                            "duration_minutes": float('inf'),
                            "status": "ERROR"
                        }
        
        return result
    

class SmartCourseGenerator:
    """
    🧠 스마트 여행 코스 생성기
    - Distance Matrix API 기반 정확한 이동 시간 계산
    - TSP 알고리즘 변형을 통한 최적 경로 탐색
    - 한국 관광지 특성을 반영한 추천 시스템
    """
    
    def __init__(self, distance_service: OptimizedDistanceMatrixService):
        self.distance_service = distance_service
    
    async def generate_course_db_format(
        self,
        places_data: List[Dict],
        start_place_id: str,
        travel_duration: int,
        request: ItineraryRequest
    ) -> Dict[str, Any]:
        """
        🎯 DB 저장 형태로 바로 여행 코스를 생성합니다.
        data_converter가 바로 처리할 수 있는 형태로 직접 생성합니다.
        """
        if not places_data:
            raise ValueError("장소 목록이 비어있습니다.")
        
        # 1. 좌표와 장소 정보 추출
        valid_places = []
        place_coords = []
        place_ids = []
        
        for place in places_data:
            coords = self._extract_coordinates(place)
            if coords:
                valid_places.append(place)
                place_coords.append(coords)
                place_ids.append(str(place['_id']))
        
        if len(valid_places) < 2:
            raise ValueError("좌표 정보가 있는 장소가 2개 미만입니다.")
        
        # 2. Distance Matrix API 호출
        matrix_data = await self.distance_service.get_distance_matrix_for_places(place_coords)
        distance_dict = self.distance_service.parse_matrix_to_dict(matrix_data, place_ids)
        
        # 3. 시작점 찾기
        start_idx = self._find_start_place_index(valid_places, start_place_id)
        
        # 4. DB 형태로 바로 일별 일정 생성
        return self._generate_db_format_schedules(
            valid_places,
            distance_dict,
            start_idx,
            travel_duration,
            request
        )
    
    def _extract_coordinates(self, place: Dict) -> Optional[Tuple[float, float]]:
        """장소 데이터에서 좌표를 추출합니다."""
        if 'location' in place and 'coordinates' in place['location']:
            # MongoDB GeoJSON 형식: [경도, 위도] -> (위도, 경도) 변환
            lon, lat = place['location']['coordinates']
            return (lat, lon)
        elif 'map_x' in place and 'map_y' in place:
            return (place['map_y'], place['map_x'])  # (위도, 경도)
        else:
            return None
    
    def _find_start_place_index(self, places: List[Dict], start_place_id: str) -> int:
        """시작 장소의 인덱스를 찾습니다."""
        for i, place in enumerate(places):
            if str(place['_id']) == start_place_id:
                return i
        return 0  # 찾지 못하면 첫 번째 장소

   # 프로트에서 ml 모델 점수 제공 받기기 
    def _get_place_score(self, place: Dict) -> float:
        """
        장소의 추천 점수를 가져옵니다.
        프론트엔드에서 ML 모델 점수를 전달받아 사용합니다.
        """
        # 🤖 ML 모델에서 계산된 추천 점수 사용
        ml_score = place.get('recommendation_score', place.get('score', 0.5))
        
        # 0-1 범위로 정규화
        return min(1.0, max(0.0, float(ml_score)))
    
    def _generate_db_format_schedules(
        self,
        places: List[Dict],
        distance_dict: Dict[str, Dict[str, Dict]],
        start_idx: int,
        travel_duration: int,
        request: ItineraryRequest
    ) -> Dict[str, Any]:
        """일별 최적화된 일정을 생성합니다."""
        itinerary = []
        place_ids = [str(place['_id']) for place in places]
        unvisited = set(range(len(places))) - {start_idx}
        
        # 각 장소의 ML 모델 추천 점수 가져오기
        place_scores = {i: self._get_place_score(places[i]) for i in range(len(places))}
        
        # 시작 날짜 계산 (오늘 날짜 사용)
        from datetime import datetime, timedelta
        start_date = datetime.now()
        
        for day in range(travel_duration):
            current_date = start_date + timedelta(days=day)
            day_schedule = {
                "day": day + 1,
                "date": current_date.strftime("%Y-%m-%d"),  # data_converter가 기대하는 형식
                "places": [],
                "total_distance": 0,
                "total_duration": 0
            }
            
            current_idx = start_idx if day == 0 else None
            places_visited_today = 0
            max_places_per_day = 3
            daily_time_budget = 8 * 60  # 8시간 (분 단위)
            
            # 첫째 날 첫 장소는 시작점
            if day == 0:
                place_data = places[current_idx]
                day_schedule["places"].append({
                    "place_id": str(place_data['_id']),
                    "name": place_data.get('name', 'Unknown Place'),
                    "time": "09:00"
                })
                places_visited_today += 1
                daily_time_budget -= 120  # 첫 장소 체류 시간 차감
            
            # 나머지 장소 선택
            while unvisited and places_visited_today < max_places_per_day and daily_time_budget > 60:
                best_next_idx = self._select_next_best_place(
                    current_idx,
                    unvisited,
                    place_ids,
                    distance_dict,
                    place_scores,
                    daily_time_budget,
                    places_visited_today == 0  # 첫 번째 선택인지
                )
                
                if best_next_idx is None:
                    break
                
                # 이동 정보 가져오기
                if current_idx is not None:
                    travel_info = distance_dict[place_ids[current_idx]][place_ids[best_next_idx]]
                    travel_time = travel_info.get("duration_minutes", 30)
                    distance = travel_info.get("distance_km", 0)
                else:
                    travel_time = 0
                    distance = 0
                
                # 시간 예산 확인
                required_time = travel_time + 120  # 이동시간 + 체류시간
                if required_time > daily_time_budget:
                    break
                
                # 도착 시간 계산
                base_hour = 9 + (places_visited_today * 3)
                arrival_time = f"{base_hour:02d}:00"
                
                # 이동 정보 상세화
                if current_idx is not None:
                    travel_info_detail = distance_dict[place_ids[current_idx]][place_ids[best_next_idx]]
                else:
                    travel_info_detail = {
                        "distance_km": 0,
                        "duration_minutes": 0,
                        "duration_seconds": 0,
                        "distance_text": "시작점",
                        "duration_text": "시작점",
                        "status": "OK"
                    }
                
                # 일정에 추가 (data_converter 호환 형식)
                place_data = places[best_next_idx]
                day_schedule["places"].append({
                    "place_id": str(place_data['_id']),
                    "name": place_data.get('name', 'Unknown Place'),
                    "time": arrival_time
                })
                
                # 상태 업데이트
                day_schedule["total_distance"] += distance
                day_schedule["total_duration"] += travel_time
                daily_time_budget -= required_time
                
                unvisited.remove(best_next_idx)
                current_idx = best_next_idx
                places_visited_today += 1
            
            itinerary.append(day_schedule)
        
        # data_converter가 기대하는 형식으로 반환
        return {
            "user_id": request.user_id if hasattr(request, 'user_id') and request.user_id else "guest_user",
            "course_name": "AI 추천 여행",
            "itinerary": {
                "days": itinerary
            }
        }
    
    async def generate_course_for_db(
        self,
        places_data: List[Dict],
        start_place_id: str,
        travel_duration: int,
        request: ItineraryRequest
    ) -> Dict[str, Any]:
        """
        🎯 코스를 생성합니다.
        data_converter가 처리할 수 있는 형태로 직접 생성합니다.
        """
        if not places_data:
            raise ValueError("장소 목록이 비어있습니다.")
        
        # 1. 좌표와 장소 정보 추출
        valid_places = []
        place_coords = []
        place_ids = []
        
        for place in places_data:
            coords = self._extract_coordinates(place)
            if coords:
                valid_places.append(place)
                place_coords.append(coords)
                place_ids.append(str(place['_id']))
        
        if len(valid_places) < 2:
            raise ValueError("좌표 정보가 있는 장소가 2개 미만입니다.")
        
        # 2. Distance Matrix API 호출
        matrix_data = await self.distance_service.get_distance_matrix_for_places(place_coords)
        distance_dict = self.distance_service.parse_matrix_to_dict(matrix_data, place_ids)
        
        # 3. 시작점 찾기
        start_idx = self._find_start_place_index(valid_places, start_place_id)
        
        # 4. 일별 일정 생성 (DB 형태로 바로)
        course_days = []
        start_date = datetime.now()
        unvisited = set(range(len(valid_places))) - {start_idx}
        
        # 각 장소의 ML 추천 점수 가져오기
        place_scores = {i: self._get_place_score(valid_places[i]) for i in range(len(valid_places))}
        
        for day in range(travel_duration):
            day_number = day + 1
            current_date = start_date + timedelta(days=day)
            
            current_idx = start_idx if day == 0 else None
            places_visited_today = 0
            max_places_per_day = 3
            daily_time_budget = 8 * 60  # 8시간 (분 단위)
            
            day_places = []
            
            # 첫째 날 첫 장소는 시작점
            if day == 0:
                place_detail = valid_places[current_idx]
                day_places.append({
                    "place_id": str(place_detail['_id']),
                    "_id": str(place_detail['_id']),
                    "name": place_detail['name'],
                    "description": place_detail.get('description', ''),
                    "address": place_detail.get('address', ''),
                    "location": place_detail.get('location', {"type": "Point", "coordinates": [0, 0]}),
                    "rating": place_detail.get('rating', 0),
                    "estimated_duration": 120,
                    "time": "09:00"
                })
                places_visited_today += 1
                daily_time_budget -= 120  # 첫 장소 체류시간 차감
            
            # 나머지 장소 선택
            while unvisited and places_visited_today < max_places_per_day and daily_time_budget > 60:
                best_next_idx = self._select_next_best_place(
                    current_idx,
                    unvisited,
                    place_ids,
                    distance_dict,
                    place_scores,
                    daily_time_budget,
                    places_visited_today == 0
                )
                
                if best_next_idx is None:
                    break
                
                # 이동 정보 계산
                if current_idx is not None:
                    travel_info = distance_dict[place_ids[current_idx]][place_ids[best_next_idx]]
                    travel_time = travel_info.get("duration_minutes", 30)
                else:
                    travel_time = 0
                
                # 시간 예산 확인
                required_time = travel_time + 120
                if required_time > daily_time_budget:
                    break
                
                # 도착 시간 계산
                base_hour = 9 + (places_visited_today * 3)
                arrival_time = f"{base_hour:02d}:00"
                
                # DB 형태로 장소 추가 (상세 정보 포함)
                place_detail = valid_places[best_next_idx]
                day_places.append({
                    "place_id": str(place_detail['_id']),
                    "_id": str(place_detail['_id']),
                    "name": place_detail['name'],
                    "description": place_detail.get('description', ''),
                    "address": place_detail.get('address', ''),
                    "location": place_detail.get('location', {"type": "Point", "coordinates": [0, 0]}),
                    "rating": place_detail.get('rating', 0),
                    "estimated_duration": 120,
                    "time": arrival_time
                })
                
                # 상태 업데이트
                daily_time_budget -= required_time
                unvisited.remove(best_next_idx)
                current_idx = best_next_idx
                places_visited_today += 1
            
            # DB 형태의 일일 일정 추가
            course_days.append({
                "day": day_number,
                "date": current_date.strftime("%Y-%m-%d"),
                "places": day_places
            })
        
        # 5. DB 저장 형태로 반환
        return {
            "user_id": request.user_id if hasattr(request, 'user_id') and request.user_id else "guest_user",
            "course_name": f"ML 추천 부산 여행 {travel_duration}일",
            "itinerary": {
                "days": course_days
            }
        }
    
    def _select_next_best_place(
        self,
        current_idx: Optional[int],
        unvisited: set,
        place_ids: List[str],
        distance_dict: Dict[str, Dict[str, Dict]],
        place_scores: Dict[int, float],
        time_budget: int,
        is_first_selection: bool
    ) -> Optional[int]:
        """다음 방문할 최적의 장소를 선택합니다."""
        best_idx = None
        best_score = -1
        
        for next_idx in unvisited:
            if current_idx is not None:
                travel_info = distance_dict[place_ids[current_idx]][place_ids[next_idx]]
                
                if travel_info["status"] != "OK":
                    continue
                
                travel_time = travel_info.get("duration_minutes", 30)
                distance_km = travel_info.get("distance_km", 0)
                
                # 시간 예산 확인
                if travel_time + 120 > time_budget:  # 이동시간 + 체류시간
                    continue
                
                # 거리 점수 (가까울수록 높음)
                distance_score = max(0, 1 - (distance_km / 50))
            else:
                distance_score = 1.0  # 첫 번째 선택시
            
            # 추천 점수
            recommendation_score = place_scores.get(next_idx, 0.5)
            
            # 가중치 적용
            if is_first_selection:
                # 첫 번째 선택: 추천점수 우선
                combined_score = (distance_score * 0.3) + (recommendation_score * 0.7)
            else:
                # 나머지 선택: 이동 효율성 우선
                combined_score = (distance_score * 0.6) + (recommendation_score * 0.4)
            
            if combined_score > best_score:
                best_score = combined_score
                best_idx = next_idx
        
        return best_idx


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
    🎯 여행 코스 생성 (통합 엔드포인트)
    
    ✨ 핵심 특징:
    - 장소 ID 또는 장소 이름으로 유연한 검색 지원
    - Google Distance Matrix API로 정확한 이동시간 계산
    - ML 추천점수 + 이동효율성 기반 최적 경로 생성
    
    🔄 처리 흐름:
    1. 장소 ID로 MongoDB 조회 시도
    2. 조회 실패 시 장소 이름으로 재검색
    3. Distance Matrix API로 실제 이동시간 계산
    4. 추천점수 + 이동효율성 기반 최적 경로 생성
    """
    # # 요청 데이터 로깅
    # print(f"📥 /generate 요청 받음:")
    # print(f"   - spots: {request.spots}")
    # print(f"   - user_id: {request.user_id}")
    # print(f"   - travelDuration: {request.travelDuration}")
    
    # 연결 상태 확인
    if tourism_collection is None:
        raise HTTPException(status_code=503, detail="데이터베이스 연결이 되어있지 않습니다.")
    
    if not GOOGLE_MAPS_API_KEY:
        raise HTTPException(status_code=503, detail="Google Maps API 키가 설정되지 않았습니다.")
    
    try:
        # 1. 입력 데이터 검증
        if not request.spots:
            raise HTTPException(status_code=400, detail="선택된 장소가 없습니다.")
        
        # travelDuration 자동 계산 (미입력 시)
        if request.travelDuration is None or request.travelDuration <= 0:
            # 장소 3개당 1일로 계산 (최소 1일)
            request.travelDuration = max(1, (len(request.spots) + 2) // 3)
            print(f"   📅 여행기간 자동 계산: {request.travelDuration}일 (장소 {len(request.spots)}개 기준)")
        
        print(f"🎯 여행 코스 생성 시작...")
        print(f"   📍 선택된 장소: {len(request.spots)}곳")
        print(f"   📅 여행기간: {request.travelDuration}일")
        
        # 2. 장소 ID를 ObjectId로 변환 시도
        selected_place_ids = []
        place_names = []
        
        for place_identifier in request.spots:
            try:
                # ObjectId로 변환 시도
                place_oid = ObjectId(place_identifier)
                selected_place_ids.append(place_oid)
            except Exception:
                # ObjectId 변환 실패 시 장소 이름으로 간주
                place_names.append(place_identifier)
                print(f"   📝 장소 이름으로 처리: {place_identifier}")
        
        print(f"   🔍 ObjectId로 조회할 장소: {len(selected_place_ids)}개")
        print(f"   📝 이름으로 조회할 장소: {len(place_names)}개")
        
        # 3. MongoDB에서 장소 정보 조회
        places_data = []
        
        # 3-1. ObjectId로 조회
        if selected_place_ids:
            places_cursor = tourism_collection.find({"_id": {"$in": selected_place_ids}})
            id_places = [place async for place in places_cursor]
            print(f"   ✅ ID로 조회된 장소: {len(id_places)}개")
            places_data.extend(id_places)
        
        # 3-2. 이름으로 조회
        if place_names:
            for place_name in place_names:
                name_result = await tourism_collection.find_one({
                    "name": {"$regex": f"^{place_name}$", "$options": "i"}
                })
                if name_result:
                    places_data.append(name_result)
                    print(f"   ✅ 이름으로 찾음: {place_name}")
                else:
                    print(f"   ❌ 이름으로도 찾을 수 없음: {place_name}")
        
        # 3-3. ID 조회 실패한 것들을 이름으로 재시도
        if len(places_data) < len(request.spots):
            print(f"   🔄 일부 장소 조회 실패, 이름으로 재검색 시도...")
            
            found_ids = {str(place['_id']) for place in places_data}
            missing_identifiers = [pid for pid in request.spots if pid not in found_ids]
            
            for missing_id in missing_identifiers:
                # 먼저 ObjectId인지 확인
                try:
                    ObjectId(missing_id)
                    # ObjectId인데 못 찾은 경우, 다른 방법으로 시도
                    print(f"   🔍 ObjectId {missing_id}로 재검색 시도...")
                    continue
                except:
                    # ObjectId가 아닌 경우 이름으로 검색
                    name_result = await tourism_collection.find_one({
                        "name": {"$regex": f"^{missing_id}$", "$options": "i"}
                    })
                    if name_result:
                        places_data.append(name_result)
                        print(f"   ✅ 재검색 성공: {missing_id}")

        if not places_data:
            raise HTTPException(status_code=404, detail="선택된 장소 정보를 찾을 수 없습니다.")
        
        print(f"   📊 최종 조회된 장소: {len(places_data)}개")
        
        # ObjectId를 문자열로 변환
        for place in places_data:
            place['_id'] = str(place['_id'])
        
        # 3. 시작점 설정
        start_place_id = request.starting_point or places_data[0]['_id']
        
        # 4. 스마트 코스 생성 서비스 초기화
        distance_service = OptimizedDistanceMatrixService(GOOGLE_MAPS_API_KEY)
        course_generator = SmartCourseGenerator(distance_service)
        
        # 5. DB 저장 형태로 바로 생성 (중간 변환 과정 제거)
        backend_course_data = await course_generator.generate_course_db_format(
            places_data=places_data,
            start_place_id=start_place_id,
            travel_duration=request.travelDuration,
            request=request
        )
        
        # 7. data_converter를 사용해 프론트엔드 형식으로 변환
        from services.data_converter import data_converter
        frontend_response_data = data_converter.convert_backend_to_frontend(backend_course_data)
        
        # 8. 최종 응답 형식으로 변환 (dailySchedule 형태)
        frontend_response = FrontendItineraryResponse(dailySchedule=[
            FrontendDay(
                day=day["day"],
                date=day["date"],
                places=[
                    FrontendPlace(
                        id=place["id"],
                        _id=place.get("_id"),
                        name=place["name"],
                        time=place.get("time", "09:00"),  # ✅ 필수 필드!
                        description=place.get("description"),
                        address=place.get("address"),
                        location=place.get("location"),
                        rating=place.get("rating"),
                        estimated_duration=place.get("estimated_duration")
                    ) for place in day["places"]
                ]
            ) for day in frontend_response_data
        ])
        
        # 9. 결과 로그
        total_places = sum(len(day.get('places', [])) for day in backend_course_data.get('itinerary', {}).get('days', []))
        print(f"✅ ML 추천점수 기반 코스 생성 완료!")
        print(f"   🏛️ 총 방문 장소: {total_places}곳")
        print(f"   🔄 data_converter 활용한 형식 변환 완료")
        print(f"   🤖 ML 추천점수 + Distance Matrix 조합")
        
        return frontend_response
        
    except HTTPException as e:
        print(f"❌ HTTP 예외 발생: {e.status_code} - {e.detail}")
        raise e
    except Exception as e:
        print(f"❌ 코스 생성 중 오류: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"서버 내부 오류가 발생했습니다: {e}")

@router.post("/save")
async def save_course(request_data: Union[List[dict], dict] = Body(...)):
    """
    생성된 여행 코스를 DB에 저장합니다.
    프론트엔드 형식과 백엔드 형식을 모두 자동으로 지원합니다.
    """
    # MongoDB 연결 상태 확인
    if courses_collection is None:
        raise HTTPException(status_code=503, detail="데이터베이스 연결이 되어있지 않습니다. 관리자에게 문의하세요.")
    
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

@router.delete("/course/{course_id}")
async def delete_course(course_id: str):
    """
    특정 코스를 삭제합니다.
    
    Args:
        course_id: 삭제할 코스 ID
    """
    # MongoDB 연결 상태 확인
    if courses_collection is None:
        raise HTTPException(status_code=503, detail="데이터베이스 연결이 되어있지 않습니다.")
    
    try:
        # 코스 존재 확인
        course = courses_collection.find_one({"course_id": course_id})
        if not course:
            raise HTTPException(status_code=404, detail="코스를 찾을 수 없습니다.")
        
        # 코스 삭제
        result = courses_collection.delete_one({"course_id": course_id})
        
        if result.deleted_count > 0:
            return {
                "success": True,
                "message": "코스가 성공적으로 삭제되었습니다.",
                "course_id": course_id
            }
        else:
            raise HTTPException(status_code=500, detail="코스 삭제에 실패했습니다.")
            
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"코스 삭제 중 오류 발생: {e}")
        raise HTTPException(status_code=500, detail=f"서버 내부 오류가 발생했습니다: {e}")





