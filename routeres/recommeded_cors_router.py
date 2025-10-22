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

# 근처 장소 추천 서비스 import
from services.recommend_nearby_places_optimized import recommend_nearby_restaurants_optimized

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
        지역 기반 최적화 알고리즘을 사용합니다.
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
        
        # 4. ML 추천점수 기반 최적화 일정 생성
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
        base_score = min(1.0, max(0.0, float(ml_score)))
        
        return base_score
    
    async def _add_nearby_restaurants_to_course(self, daily_schedule: List[FrontendDay]) -> List[FrontendDay]:
        """
        코스의 각 장소 근처에서 음식점을 찾아 점심/저녁 시간에 추가합니다.
        """
        print("🍽️ 근처 음식점을 찾아 코스에 추가 중...")
        
        for day_schedule in daily_schedule:
            # 점심 시간(12:00)과 저녁 시간(18:00)에 음식점 추가
            meal_times = [12, 18]
            
            for meal_time in meal_times:
                # 해당 시간대에 이미 장소가 있는지 확인
                existing_place = None
                for place in day_schedule.places:
                    if place.time.startswith(f"{meal_time:02d}"):
                        existing_place = place
                        break
                
                if existing_place:
                    continue  # 이미 해당 시간에 장소가 있으면 건너뛰기
                
                # 가장 가까운 장소를 기준으로 음식점 찾기
                if day_schedule.places:
                    # 첫 번째 장소를 기준으로 근처 음식점 찾기
                    reference_place = day_schedule.places[0]
                    place_id = reference_place.id
                    
                    try:
                        # 근처 음식점 조회 (1km 반경)
                        nearby_restaurants = await recommend_nearby_restaurants_optimized(place_id, 1.0)
                        
                        if nearby_restaurants:
                            # 이미 추가된 음식점들 확인 (정확한 이름 비교)
                            added_restaurant_names = set()
                            for place in day_schedule.places:
                                if place.name:
                                    added_restaurant_names.add(place.name)
                            
                            # 중복되지 않는 음식점 찾기
                            selected_restaurant = None
                            for restaurant in nearby_restaurants:
                                restaurant_name = restaurant.get('name', '')
                                if restaurant_name not in added_restaurant_names:
                                    selected_restaurant = restaurant
                                    break
                            
                            if selected_restaurant:
                                # 음식점을 FrontendPlace로 변환
                                restaurant_place = FrontendPlace(
                                    id=str(selected_restaurant.get('_id', selected_restaurant.get('id', 'unknown'))),
                                    name=selected_restaurant.get('name', '근처 음식점'),
                                    time=f"{meal_time:02d}:00",
                                    address=selected_restaurant.get('address', ''),
                                    location=selected_restaurant.get('location', {}),
                                    rating=selected_restaurant.get('rating', 0.0),
                                    estimated_duration=120  # 2시간
                                )
                                
                                # 시간순으로 정렬하여 적절한 위치에 삽입
                                day_schedule.places.append(restaurant_place)
                                day_schedule.places.sort(key=lambda x: x.time)
                                
                                print(f"✅ {meal_time}시에 '{restaurant_place.name}' 추가됨")
                            else:
                                print(f"⚠️ {meal_time}시 중복되지 않는 음식점을 찾을 수 없습니다.")
                        else:
                            print(f"⚠️ {meal_time}시 근처에 음식점을 찾을 수 없습니다.")
                    
                    except Exception as e:
                        print(f"❌ 음식점 조회 중 오류: {e}")
                        continue
        
        return daily_schedule

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
        
        # 각 장소의 ML 모델 추천 점수 가져오기 (시간대별 먹거리 보너스 적용)
        place_scores = {}
        current_hour = 9  # 9시부터 시작
        for i in range(len(places)):
            current_time = f"{current_hour:02d}:00"
            place_scores[i] = self._get_place_score(places[i])
            current_hour += 2  # 다음 장소는 2시간 후
        
        # 시작 날짜 계산 (오늘 날짜 사용)
        from datetime import datetime, timedelta
        start_date = datetime.now()
        
        # 방문하지 않은 장소들 (시작점 제외)
        unvisited = set(range(len(places))) - {start_idx}
        
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
            daily_time_budget = 12 * 60  # 8시간 (분 단위)
            
            # 첫째 날 첫 장소는 시작점
            if day == 0:
                place_data = places[current_idx]
                day_schedule["places"].append({
                    "place_id": str(place_data['_id']),
                    "_id": str(place_data['_id']),
                    "name": place_data.get('name', 'Unknown Place'),
                    "description": place_data.get('description', ''),
                    "address": place_data.get('address', ''),
                    "location": place_data.get('location', {"type": "Point", "coordinates": [0, 0]}),
                    "rating": place_data.get('rating', 0),
                    "estimated_duration": 120,  # 기본 체류시간 2시간
                    "time": "09:00"
                })
                places_visited_today += 1
                daily_time_budget -= 120  # 첫 장소 체류 시간 차감
                unvisited.discard(current_idx)  # 방문한 장소를 unvisited에서 제거
            
            # 나머지 장소 선택 (하루 최대 3곳 엄격한 제한)
            while (unvisited and 
                   places_visited_today < max_places_per_day and 
                   daily_time_budget > 60):
                
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
                    print(f"   📍 Day {day + 1}: 더 이상 추가할 장소가 없습니다.")
                    break
                
                # 이동 정보 가져오기
                if current_idx is not None:
                    travel_info = distance_dict[place_ids[current_idx]][place_ids[best_next_idx]]
                    travel_time = travel_info.get("duration_minutes", 30)
                    distance = travel_info.get("distance_km", 0)
                else:
                    travel_time = 0
                    distance = 0
                
                # 시간 예산 확인 (이동시간 + 체류시간 2시간)
                required_time = travel_time + 120
                if required_time > daily_time_budget:
                    print(f"   ⏰ Day {day + 1}: 시간 예산 부족으로 장소 추가 중단")
                    break
                
                # 도착 시간 계산 (9시부터 시작, 각 장소당 3시간 간격)
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
                    "_id": str(place_data['_id']),
                    "name": place_data.get('name', 'Unknown Place'),
                    "description": place_data.get('description', ''),
                    "address": place_data.get('address', ''),
                    "location": place_data.get('location', {"type": "Point", "coordinates": [0, 0]}),
                    "rating": place_data.get('rating', 0),
                    "estimated_duration": 120,  # 기본 체류시간 2시간
                    "time": arrival_time
                })
                
                # 상태 업데이트
                day_schedule["total_distance"] += distance
                day_schedule["total_duration"] += travel_time
                daily_time_budget -= required_time
                
                unvisited.remove(best_next_idx)
                current_idx = best_next_idx
                places_visited_today += 1
                
                print(f"   ✅ Day {day + 1}: {place_data.get('name', 'Unknown')} 추가 ({places_visited_today}/{max_places_per_day})")
            
            # 하루 일정 완료 로그
            print(f"   📅 Day {day + 1} 완료: {places_visited_today}개 장소 방문")
            
            itinerary.append(day_schedule)
        
        # data_converter가 기대하는 형식으로 반환
        return {
            "user_id": request.user_id if hasattr(request, 'user_id') and request.user_id else "guest_user",
            "course_name": "AI 추천 여행",
            "itinerary": {
                "days": itinerary
            },
            "is_public": False,  # 기본적으로 비공개로 설정
            "description": getattr(request, 'description', "")  # 코스 설명
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
        
        # 각 장소의 ML 추천 점수 가져오기 (시간대별 먹거리 보너스 적용)
        place_scores = {}
        current_hour = 9  # 9시부터 시작
        for i in range(len(valid_places)):
            current_time = f"{current_hour:02d}:00"
            place_scores[i] = self._get_place_score(valid_places[i], current_time)
            current_hour += 2  # 다음 장소는 2시간 후
        
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
                unvisited.discard(current_idx)  # 방문한 장소를 unvisited에서 제거
            
            # 나머지 장소 선택 (하루 최대 3곳 엄격한 제한)
            while (unvisited and 
                   places_visited_today < max_places_per_day and 
                   daily_time_budget > 60):
                
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
                    print(f"   📍 Day {day_number}: 더 이상 추가할 장소가 없습니다.")
                    break
                
                # 이동 정보 계산
                if current_idx is not None:
                    travel_info = distance_dict[place_ids[current_idx]][place_ids[best_next_idx]]
                    travel_time = travel_info.get("duration_minutes", 30)
                else:
                    travel_time = 0
                
                # 시간 예산 확인 (이동시간 + 체류시간 2시간)
                required_time = travel_time + 120
                if required_time > daily_time_budget:
                    print(f"   ⏰ Day {day_number}: 시간 예산 부족으로 장소 추가 중단")
                    break
                
                # 도착 시간 계산 (9시부터 시작, 각 장소당 3시간 간격)
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
                
                print(f"   ✅ Day {day_number}: {place_detail.get('name', 'Unknown')} 추가 ({places_visited_today}/{max_places_per_day})")
            
            # 하루 일정 완료 로그
            print(f"   📅 Day {day_number} 완료: {places_visited_today}개 장소 방문")
            
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
            },
            "is_public": False,  # 기본적으로 비공개로 설정
            "description": getattr(request, 'description', "")  # 코스 설명
        }
    
    def _cluster_places_by_region(self, places_data: List[Dict]) -> Dict[str, List[Dict]]:
        """
        장소들을 지역별로 클러스터링합니다.
        기존 region 필드를 활용하여 그룹화합니다.
        """
        region_clusters = {}
        
        for place in places_data:
            region = place.get('region', '기타')
            if region not in region_clusters:
                region_clusters[region] = []
            region_clusters[region].append(place)
        
        print(f"🗺️ 지역별 클러스터링 완료: {len(region_clusters)}개 지역")
        for region, places in region_clusters.items():
            print(f"   📍 {region}: {len(places)}개 장소")
        
        return region_clusters
    
    def _calculate_region_distance(self, place1: Dict, place2: Dict) -> float:
        """두 장소 간의 거리를 계산합니다."""
        coords1 = self._extract_coordinates(place1)
        coords2 = self._extract_coordinates(place2)
        
        if not coords1 or not coords2:
            return float('inf')
        
        # 간단한 유클리드 거리 계산 (대략적인 거리)
        lat1, lon1 = coords1
        lat2, lon2 = coords2
        
        # 위도 1도 ≈ 111km, 경도 1도 ≈ 111km * cos(위도)
        lat_diff = (lat2 - lat1) * 111
        lon_diff = (lon2 - lon1) * 111 * abs(lat1) / 90  # 부산 위도 고려
        
        return (lat_diff ** 2 + lon_diff ** 2) ** 0.5
    
    def _is_same_region(self, place1: Dict, place2: Dict) -> bool:
        """두 장소가 같은 지역인지 확인합니다."""
        return place1.get('region', '기타') == place2.get('region', '기타')
    
    def _generate_region_optimized_schedule(
        self,
        places: List[Dict],
        distance_dict: Dict[str, Dict[str, Dict]],
        travel_duration: int,
        request: ItineraryRequest
    ) -> Dict[str, Any]:
        """
        지역 기반 최적화된 일정을 생성합니다.
        - 하루 2-3개 장소
        - 같은 지역 우선 배치
        - 지역 간 이동거리가 길면 다음날로 미루기
        """
        # 1. 지역별 클러스터링
        region_clusters = self._cluster_places_by_region(places)
        
        # 2. 각 지역 내에서 TSP로 최적 경로 생성
        region_routes = {}
        for region, region_places in region_clusters.items():
            if len(region_places) <= 1:
                region_routes[region] = region_places
            else:
                # 지역 내 TSP (간단한 Nearest Neighbor)
                region_routes[region] = self._solve_tsp_for_region(region_places, distance_dict)
        
        # 3. 일별 일정 생성
        itinerary = []
        start_date = datetime.now()
        place_ids = [str(place['_id']) for place in places]
        place_scores = {i: self._get_place_score(places[i]) for i in range(len(places))}
        
        # 모든 장소를 방문할 때까지 반복
        all_places = []
        for region_route in region_routes.values():
            all_places.extend(region_route)
        
        visited_places = set()
        
        for day in range(travel_duration):
            current_date = start_date + timedelta(days=day)
            day_schedule = {
                "day": day + 1,
                "date": current_date.strftime("%Y-%m-%d"),
                "places": [],
                "total_distance": 0,
                "total_duration": 0
            }
            
            places_visited_today = 0
            max_places_per_day = 3
            min_places_per_day = 2
            daily_time_budget = 8 * 60  # 8시간 (분 단위)
            current_region = None
            
            # 하루 일정 생성
            while places_visited_today < max_places_per_day and daily_time_budget > 60:
                best_next_place = self._select_next_place_region_optimized(
                    all_places,
                    visited_places,
                    current_region,
                    place_ids,
                    distance_dict,
                    place_scores,
                    daily_time_budget,
                    places_visited_today == 0
                )
                
                if best_next_place is None:
                    break
                
                # 지역 간 이동거리 체크
                if current_region is not None and not self._is_same_region(
                    best_next_place, 
                    all_places[list(visited_places)[-1]] if visited_places else best_next_place
                ):
                    # 다른 지역으로 이동하는 경우 거리 체크
                    if places_visited_today >= min_places_per_day:
                        # 이미 최소 장소 수를 채웠으면 다음날로 미루기
                        print(f"   📍 지역 변경으로 인한 다음날 연기: {best_next_place.get('name')}")
                        break
                
                # 시간 예산 확인
                travel_time = 0
                if visited_places:
                    last_place_idx = list(visited_places)[-1]
                    travel_info = distance_dict[place_ids[last_place_idx]][str(best_next_place['_id'])]
                    travel_time = travel_info.get("duration_minutes", 30)
                
                required_time = travel_time + 120  # 이동시간 + 체류시간
                if required_time > daily_time_budget:
                    break
                
                # 도착 시간 계산
                base_hour = 9 + (places_visited_today * 3)
                arrival_time = f"{base_hour:02d}:00"
                
                # 일정에 추가 (상세 정보 포함)
                day_schedule["places"].append({
                    "place_id": str(best_next_place['_id']),
                    "_id": str(best_next_place['_id']),
                    "name": best_next_place.get('name', 'Unknown Place'),
                    "description": best_next_place.get('description', ''),
                    "address": best_next_place.get('address', ''),
                    "location": best_next_place.get('location', {"type": "Point", "coordinates": [0, 0]}),
                    "rating": best_next_place.get('rating', 0),
                    "estimated_duration": 120,  # 기본 체류시간 2시간
                    "time": arrival_time
                })
                
                # 상태 업데이트
                day_schedule["total_distance"] += travel_time * 0.5  # 대략적인 거리
                day_schedule["total_duration"] += travel_time
                daily_time_budget -= required_time
                
                visited_places.add(all_places.index(best_next_place))
                current_region = best_next_place.get('region', '기타')
                places_visited_today += 1
            
            # 최소 장소 수 미달 시 경고
            if places_visited_today < min_places_per_day:
                print(f"   ⚠️ Day {day + 1}: 최소 장소 수 미달 ({places_visited_today}개)")
            
            itinerary.append(day_schedule)
        
        # data_converter가 기대하는 형식으로 반환
        return {
            "user_id": request.user_id if hasattr(request, 'user_id') and request.user_id else "guest_user",
            "course_name": "지역 최적화 여행",
            "itinerary": {
                "days": itinerary
            },
            "is_public": False,
            "description": getattr(request, 'description', "")
        }
    
    def _solve_tsp_for_region(self, region_places: List[Dict], distance_dict: Dict) -> List[Dict]:
        """지역 내에서 TSP로 최적 경로를 생성합니다."""
        if len(region_places) <= 1:
            return region_places
        
        # 간단한 Nearest Neighbor 알고리즘
        unvisited = set(range(len(region_places)))
        route = []
        current_idx = 0  # 첫 번째 장소부터 시작
        route.append(region_places[current_idx])
        unvisited.remove(current_idx)
        
        while unvisited:
            best_idx = None
            best_distance = float('inf')
            
            for next_idx in unvisited:
                place1_id = str(region_places[current_idx]['_id'])
                place2_id = str(region_places[next_idx]['_id'])
                
                if place1_id in distance_dict and place2_id in distance_dict[place1_id]:
                    distance = distance_dict[place1_id][place2_id].get("distance_km", float('inf'))
                else:
                    distance = self._calculate_region_distance(
                        region_places[current_idx], 
                        region_places[next_idx]
                    )
                
                if distance < best_distance:
                    best_distance = distance
                    best_idx = next_idx
            
            if best_idx is not None:
                route.append(region_places[best_idx])
                unvisited.remove(best_idx)
                current_idx = best_idx
            else:
                # 거리 정보가 없는 경우 남은 장소를 순서대로 추가
                route.extend([region_places[i] for i in unvisited])
                break
        
        return route
    
    def _select_next_place_region_optimized(
        self,
        all_places: List[Dict],
        visited_places: set,
        current_region: Optional[str],
        place_ids: List[str],
        distance_dict: Dict[str, Dict[str, Dict]],
        place_scores: Dict[int, float],
        time_budget: int,
        is_first_selection: bool
    ) -> Optional[Dict]:
        """지역 최적화된 다음 장소를 선택합니다."""
        best_place = None
        best_score = -1
        
        for i, place in enumerate(all_places):
            if i in visited_places:
                continue
            
            # 시간 예산 확인
            travel_time = 0
            if visited_places:
                last_place_idx = list(visited_places)[-1]
                travel_info = distance_dict[place_ids[last_place_idx]][str(place['_id'])]
                travel_time = travel_info.get("duration_minutes", 30)
            
            if travel_time + 120 > time_budget:
                continue
            
            # 지역 일관성 점수 (같은 지역이면 높은 점수)
            region_consistency = 1.0 if current_region == place.get('region', '기타') else 0.3
            
            # 거리 점수
            if visited_places:
                last_place_idx = list(visited_places)[-1]
                travel_info = distance_dict[place_ids[last_place_idx]][str(place['_id'])]
                distance_km = travel_info.get("distance_km", 0)
                distance_score = max(0, 1 - (distance_km / 50))
            else:
                distance_score = 1.0
            
            # ML 추천 점수
            recommendation_score = place_scores.get(i, 0.5)
            
            # 가중치 적용 (지역 일관성 강화)
            if is_first_selection:
                combined_score = (
                    region_consistency * 0.4 +
                    distance_score * 0.2 +
                    recommendation_score * 0.4
                )
            else:
                combined_score = (
                    region_consistency * 0.5 +  # 지역 일관성 강화
                    distance_score * 0.3 +
                    recommendation_score * 0.2
                )
            
            if combined_score > best_score:
                best_score = combined_score
                best_place = place
        
        return best_place
    
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
        """개선된 장소 선택 로직: 하루 최대 3곳 제한 + 거리+ML 점수 조합"""
        best_idx = None
        best_score = -1
        
        for next_idx in unvisited:
            # 1. 시간 예산 확인 (이동시간 + 체류시간 2시간)
            travel_time = 0
            if current_idx is not None:
                travel_info = distance_dict[place_ids[current_idx]][place_ids[next_idx]]
                travel_time = travel_info.get("duration_minutes", 30)
            
            required_time = travel_time + 120  # 이동시간 + 체류시간
            if required_time > time_budget:
                continue
            
            # 2. 거리 점수 계산 (가까울수록 높은 점수)
            if current_idx is not None:
                travel_info = distance_dict[place_ids[current_idx]][place_ids[next_idx]]
                distance_km = travel_info.get("distance_km", 0)
                distance_score = max(0, 1 - (distance_km / 50))  # 50km 기준 정규화
            else:
                distance_score = 1.0
            
            # 3. ML 추천 점수
            recommendation_score = place_scores.get(next_idx, 0.5)
            
            # 4. 가중치 적용 (거리 40% + ML 점수 60%)
            combined_score = (
                distance_score * 0.4 +        # 거리 점수 40%
                recommendation_score * 0.6    # ML 추천점수 60%
            )
            
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
        
        # 5개 이상일 때 배치 처리
        if len(request.spots) > 5:
            print(f"📊 {len(request.spots)}개 장소를 5개씩 묶어서 처리합니다.")
            return await generate_batch_optimized_course(request)
        
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
        
        # 9. 근처 음식점을 찾아서 코스에 추가
        try:
            # SmartCourseGenerator 인스턴스 생성 (distance_service 필요)
            generator = SmartCourseGenerator(distance_service)
            frontend_response.dailySchedule = await generator._add_nearby_restaurants_to_course(frontend_response.dailySchedule)
            print("🍽️ 근처 음식점 추가 완료")
        except Exception as e:
            print(f"⚠️ 음식점 추가 중 오류 발생: {e}")
            # 오류가 발생해도 기본 코스는 반환
        
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
            "is_public": False,  # 기본적으로 비공개로 설정
            "description": normalized_data.get("description", ""),  # 코스 설명
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

# TODO: 공개 코스 관련 기능들은 향후 구현 예정
# @router.get("/courses/public")
# async def get_public_courses(limit: int = 20, skip: int = 0):
#     """
#     공개된 코스 목록을 조회합니다.
#     
#     Args:
#         limit: 조회할 코스 수 (기본값: 20)
#         skip: 건너뛸 코스 수 (기본값: 0)
#     """
#     # MongoDB 연결 상태 확인
#     if courses_collection is None:
#         raise HTTPException(status_code=503, detail="데이터베이스 연결이 되어있지 않습니다.")
#     
#     try:
#         # 공개 코스만 조회 (최신순 정렬)
#         cursor = courses_collection.find(
#             {"is_public": True}
#         ).sort("created_at", -1).skip(skip).limit(limit)
#         
#         courses = []
#         for course in cursor:
#             # 민감한 정보 제외하고 반환
#             course_data = {
#                 "course_id": course["course_id"],
#                 "course_name": course["course_name"],
#                 "description": course.get("description", ""),
#                 "user_id": course["user_id"],
#                 "created_at": course["created_at"],
#                 "updated_at": course["updated_at"],
#                 "total_days": len(course["itinerary"]["days"]),
#                 "total_places": sum(len(day["places"]) for day in course["itinerary"]["days"])
#             }
#             courses.append(course_data)
#         
#         # 전체 공개 코스 수 조회
#         total_count = courses_collection.count_documents({"is_public": True})
#         
#         return {
#             "success": True,
#             "courses": courses,
#             "total_count": total_count,
#             "limit": limit,
#             "skip": skip
#         }
#         
#     except Exception as e:
#         print(f"공개 코스 조회 중 오류 발생: {e}")
#         raise HTTPException(status_code=500, detail=f"서버 내부 오류가 발생했습니다: {e}")

# @router.get("/courses/user/{user_id}")
# async def get_user_courses(user_id: str, include_private: bool = True):
#     """
#     특정 사용자의 코스 목록을 조회합니다.
#     
#     Args:
#         user_id: 사용자 ID
#         include_private: 비공개 코스 포함 여부 (기본값: True)
#     """
#     # MongoDB 연결 상태 확인
#     if courses_collection is None:
#         raise HTTPException(status_code=503, detail="데이터베이스 연결이 되어있지 않습니다.")
#     
#     try:
#         # 쿼리 조건 설정
#         query = {"user_id": user_id}
#         if not include_private:
#             query["is_public"] = True
#         
#         # 사용자 코스 조회 (최신순 정렬)
#         cursor = courses_collection.find(query).sort("created_at", -1)
#         
#         courses = []
#         for course in cursor:
#             course_data = {
#                 "course_id": course["course_id"],
#                 "course_name": course["course_name"],
#                 "description": course.get("description", ""),
#                 "is_public": course.get("is_public", False),
#                 "created_at": course["created_at"],
#                 "updated_at": course["updated_at"],
#                 "total_days": len(course["itinerary"]["days"]),
#                 "total_places": sum(len(day["places"]) for day in course["itinerary"]["days"])
#             }
#             courses.append(course_data)
#         
#         return {
#             "success": True,
#             "courses": courses,
#             "total_count": len(courses)
#         }
#         
#     except Exception as e:
#         print(f"사용자 코스 조회 중 오류 발생: {e}")
#         raise HTTPException(status_code=500, detail=f"서버 내부 오류가 발생했습니다: {e}")

# @router.get("/course/{course_id}")
# async def get_course_detail(course_id: str, user_id: Optional[str] = None):
#     """
#     특정 코스의 상세 정보를 조회합니다.
#     
#     Args:
#         course_id: 코스 ID
#         user_id: 요청한 사용자 ID (선택사항, 소유자 확인용)
#     """
#     # MongoDB 연결 상태 확인
#     if courses_collection is None:
#         raise HTTPException(status_code=503, detail="데이터베이스 연결이 되어있지 않습니다.")
#     
#     try:
#         # 코스 조회
#         course = courses_collection.find_one({"course_id": course_id})
#         if not course:
#             raise HTTPException(status_code=404, detail="코스를 찾을 수 없습니다.")
#         
#         # 공개 여부 및 소유자 확인
#         is_public = course.get("is_public", False)
#         is_owner = user_id and course["user_id"] == user_id
#         
#         if not is_public and not is_owner:
#             raise HTTPException(status_code=403, detail="비공개 코스입니다. 접근 권한이 없습니다.")
#         
#         # 코스 상세 정보 반환
#         return {
#             "success": True,
#             "course": {
#                 "course_id": course["course_id"],
#                 "course_name": course["course_name"],
#                 "description": course.get("description", ""),
#                 "is_public": is_public,
#                 "user_id": course["user_id"],
#                 "is_owner": is_owner,
#                 "itinerary": course["itinerary"],
#                 "created_at": course["created_at"],
#                 "updated_at": course["updated_at"]
#             }
#         }
#         
#     except HTTPException as e:
#         raise e
#     except Exception as e:
#         print(f"코스 상세 조회 중 오류 발생: {e}")
#         raise HTTPException(status_code=500, detail=f"서버 내부 오류가 발생했습니다: {e}")

# @router.put("/course/{course_id}/privacy")
# async def update_course_privacy(course_id: str, is_public: bool = Body(...), user_id: str = Body(...)):
#     """
#     코스의 공개/비공개 설정을 변경합니다.
#     
#     Args:
#         course_id: 코스 ID
#         is_public: 공개 여부
#         user_id: 요청한 사용자 ID (소유자 확인용)
#     """
#     # MongoDB 연결 상태 확인
#     if courses_collection is None:
#         raise HTTPException(status_code=503, detail="데이터베이스 연결이 되어있지 않습니다.")
#     
#     try:
#         # 코스 존재 및 소유자 확인
#         course = courses_collection.find_one({"course_id": course_id})
#         if not course:
#             raise HTTPException(status_code=404, detail="코스를 찾을 수 없습니다.")
#         
#         if course["user_id"] != user_id:
#             raise HTTPException(status_code=403, detail="코스 수정 권한이 없습니다.")
#         
#         # 공개/비공개 설정 업데이트
#         result = courses_collection.update_one(
#             {"course_id": course_id},
#             {
#                 "$set": {
#                     "is_public": is_public,
#                     "updated_at": datetime.now()
#                 }
#             }
#         )
#         
#         if result.modified_count > 0:
#             return {
#                 "success": True,
#                 "message": f"코스가 {'공개' if is_public else '비공개'}로 설정되었습니다.",
#                 "course_id": course_id,
#                 "is_public": is_public
#             }
#         else:
#             raise HTTPException(status_code=500, detail="코스 설정 변경에 실패했습니다.")
#             
#     except HTTPException as e:
#         raise e
#     except Exception as e:
#         print(f"코스 공개 설정 변경 중 오류 발생: {e}")
#         raise HTTPException(status_code=500, detail=f"서버 내부 오류가 발생했습니다: {e}")

@router.delete("/course/{course_id}")
async def delete_course(course_id: str, user_id: str = Body(...)):
    """
    특정 코스를 삭제합니다.
    
    Args:
        course_id: 삭제할 코스 ID
        user_id: 요청한 사용자 ID (소유자 확인용)
    """
    # MongoDB 연결 상태 확인
    if courses_collection is None:
        raise HTTPException(status_code=503, detail="데이터베이스 연결이 되어있지 않습니다.")
    
    try:
        # 코스 존재 및 소유자 확인
        course = courses_collection.find_one({"course_id": course_id})
        if not course:
            raise HTTPException(status_code=404, detail="코스를 찾을 수 없습니다.")
        
        if course["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="코스 삭제 권한이 없습니다.")
        
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


async def generate_batch_optimized_course(request: ItineraryRequest):
    """
    5개씩 묶어서 모든 경로를 계산하는 배치 최적화 함수
    12개 장소 → 144개 경로를 여러 번에 나누어 계산
    """
    print(f"🔄 배치 최적화 시작: {len(request.spots)}개 장소")
    
    # 1. 장소 ID를 ObjectId로 변환
    selected_place_ids = []
    place_names = []
    
    for place_identifier in request.spots:
        try:
            place_oid = ObjectId(place_identifier)
            selected_place_ids.append(place_oid)
        except Exception:
            place_names.append(place_identifier)
    
    # 2. MongoDB에서 장소 정보 조회
    all_places = []
    if selected_place_ids:
        places_cursor = tourism_collection.find({"_id": {"$in": selected_place_ids}})
        all_places.extend([place async for place in places_cursor])
    
    if place_names:
        places_cursor = tourism_collection.find({"name": {"$in": place_names}})
        all_places.extend([place async for place in places_cursor])
    
    if len(all_places) != len(request.spots):
        raise HTTPException(status_code=404, detail="일부 장소를 찾을 수 없습니다.")
    
    # 3. 5개씩 묶어서 배치 처리
    batch_size = 5
    batches = []
    for i in range(0, len(all_places), batch_size):
        batches.append(all_places[i:i + batch_size])
    
    print(f"📊 {len(all_places)}개 장소를 {len(batches)}개 그룹으로 분할")
    
    # 4. 모든 그룹 간의 거리 계산 (5×5씩 나누어 계산)
    distance_matrix = {}
    
    for i, batch1 in enumerate(batches):
        for j, batch2 in enumerate(batches):
            print(f"🔄 그룹 {i+1} → 그룹 {j+1} 거리 계산 중...")
            
            # 5×5씩 나누어 Google Distance Matrix API 호출
            batch_distances = await calculate_batch_distances(batch1, batch2, request.transport_mode)
            distance_matrix.update(batch_distances)
    
    print(f"✅ 총 {len(distance_matrix)}개 경로 계산 완료")
    
    # 5. 최적 경로 생성 (간단한 TSP 알고리즘 사용)
    optimized_course = await generate_simple_optimized_course(
        all_places=all_places,
        distance_matrix=distance_matrix,
        travel_duration=request.travelDuration,
        starting_point=request.starting_point
    )
    
    return optimized_course


async def calculate_batch_distances(batch1, batch2, transport_mode):
    """
    5×5 배치의 거리를 계산하는 함수
    """
    if not batch1 or not batch2:
        return {}
    
    # Google Distance Matrix API 호출
    origins = [f"{place['location']['coordinates'][1]},{place['location']['coordinates'][0]}" for place in batch1]
    destinations = [f"{place['location']['coordinates'][1]},{place['location']['coordinates'][0]}" for place in batch2]
    
    # 교통수단 매핑
    mode_map = {
        'TRANSIT': 'transit',
        'DRIVE': 'driving', 
        'WALK': 'walking'
    }
    
    google_mode = mode_map.get(transport_mode, 'transit')
    
    # Google Distance Matrix API 호출
    url = "https://maps.googleapis.com/maps/api/distancematrix/json"
    params = {
        'origins': '|'.join(origins),
        'destinations': '|'.join(destinations),
        'mode': google_mode,
        'key': GOOGLE_MAPS_API_KEY,
        'units': 'metric',
        'language': 'ko'
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                
                if data['status'] == 'OK':
                    # 거리 정보 파싱
                    distances = {}
                    for i, origin_place in enumerate(batch1):
                        for j, dest_place in enumerate(batch2):
                            if i < len(data['rows']) and j < len(data['rows'][i]['elements']):
                                element = data['rows'][i]['elements'][j]
                                if element['status'] == 'OK':
                                    distances[f"{origin_place['_id']}_{dest_place['_id']}"] = {
                                        'distance_km': element['distance']['value'] / 1000,
                                        'duration_minutes': element['duration']['value'] / 60
                                    }
                    return distances
                else:
                    print(f"⚠️ Google Distance Matrix API 오류: {data['status']}")
                    return {}
            else:
                print(f"❌ Google Distance Matrix API HTTP 오류: {response.status}")
                return {}
    
    return {}


async def generate_simple_optimized_course(all_places, distance_matrix, travel_duration, starting_point):
    """
    간단한 TSP 알고리즘을 사용한 최적 경로 생성
    """
    print(f"🎯 간단한 TSP 알고리즘으로 최적 경로 생성 중...")
    
    # 시작점 찾기
    start_place = None
    if starting_point:
        for place in all_places:
            if str(place['_id']) == starting_point:
                start_place = place
                break
    
    if not start_place:
        start_place = all_places[0]
    
    # 방문하지 않은 장소들
    unvisited = [place for place in all_places if place['_id'] != start_place['_id']]
    current_place = start_place
    route = [start_place]
    
    # 가장 가까운 장소를 찾아서 경로 생성
    while unvisited:
        nearest_place = None
        min_distance = float('inf')
        
        for place in unvisited:
            key = f"{current_place['_id']}_{place['_id']}"
            if key in distance_matrix:
                distance = distance_matrix[key]['distance_km']
                if distance < min_distance:
                    min_distance = distance
                    nearest_place = place
        
        if nearest_place:
            route.append(nearest_place)
            unvisited.remove(nearest_place)
            current_place = nearest_place
        else:
            # 거리 정보가 없는 경우 첫 번째 미방문 장소 선택
            route.append(unvisited[0])
            unvisited.remove(unvisited[0])
            current_place = route[-1]
    
    # 일정을 일수별로 나누기 (하루에 최대 3개 장소)
    max_places_per_day = 3
    daily_schedule = []
    
    # 장소를 균등하게 분배 (하루에 최대 3개)
    total_places = len(route)
    base_places_per_day = total_places // travel_duration
    extra_places = total_places % travel_duration
    
    place_index = 0
    for day in range(travel_duration):
        # 하루에 최대 3개 장소로 제한
        places_for_this_day = min(max_places_per_day, base_places_per_day + (1 if day < extra_places else 0))
        
        if place_index < len(route):
            end_index = min(place_index + places_for_this_day, len(route))
            day_places = route[place_index:end_index]
            place_index = end_index
            
            # FrontendPlace 형태로 변환 (점심/저녁 시간 비워두기)
            frontend_places = []
            current_hour = 9  # 9시부터 시작
            
            for i, place in enumerate(day_places):
                # 점심 시간(12:00-14:00)과 저녁 시간(18:00-20:00) 비워두기
                while current_hour in [12, 13, 18, 19]:
                    current_hour += 1
                
                time_str = f"{current_hour:02d}:00"
                
                frontend_place = FrontendPlace(
                    id=str(place['_id']),
                    name=place.get('name', 'Unknown'),
                    time=time_str,
                    address=place.get('address', ''),
                    location=place.get('location', {}),
                    rating=place.get('rating', 0.0),
                    estimated_duration=120  # 2시간
                )
                frontend_places.append(frontend_place)
                
                # 다음 장소는 2시간 후
                current_hour += 2
            
            daily_schedule.append(FrontendDay(
                day=day + 1,
                date=(datetime.now() + timedelta(days=day)).strftime('%Y-%m-%d'),
                places=frontend_places
            ))
    
    # 근처 음식점을 찾아서 코스에 추가
    try:
        # SmartCourseGenerator 인스턴스 생성 (distance_service 필요)
        distance_service = OptimizedDistanceMatrixService(GOOGLE_MAPS_API_KEY)
        generator = SmartCourseGenerator(distance_service)
        daily_schedule = await generator._add_nearby_restaurants_to_course(daily_schedule)
    except Exception as e:
        print(f"⚠️ 음식점 추가 중 오류 발생: {e}")
        # 오류가 발생해도 기본 코스는 반환
    
    return FrontendItineraryResponse(dailySchedule=daily_schedule)



