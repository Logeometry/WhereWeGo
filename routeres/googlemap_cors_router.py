# googlemap_cors_router.py
# Google Maps로 코스를 보여주는 라우터

import os
from typing import List, Dict, Optional, Tuple
import aiohttp
from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel, Field

from services.db_handler import tourism_collection
from bson import ObjectId

router = APIRouter()

# 환경변수에서 API 키 가져오기
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")


# ─────────────────────────────────────────────────────────────
# 📋 Request/Response 스키마
# ─────────────────────────────────────────────────────────────

class GoogleMapRouteRequest(BaseModel):
    """
    프론트엔드에서 받을 코스 데이터
    """
    places: List[str] = Field(..., description="장소 ID 리스트 (순서대로)")
    travel_mode: Optional[str] = Field("TRANSIT", description="이동 수단: DRIVING, WALKING, BICYCLING, TRANSIT")
    

class GooglePolylineSegment(BaseModel):
    """단일 경로 구간 (A -> B)"""
    from_place: str = Field(..., description="출발지 장소명")
    to_place: str = Field(..., description="도착지 장소명")
    from_coords: Dict[str, float] = Field(..., description="출발지 좌표 {'lat': ..., 'lng': ...}")
    to_coords: Dict[str, float] = Field(..., description="도착지 좌표 {'lat': ..., 'lng': ...}")
    distance_km: float = Field(..., description="거리 (km)")
    duration_minutes: float = Field(..., description="소요 시간 (분)")
    travel_mode: str = Field(..., description="이동 수단")
    encoded_polyline: Optional[str] = Field(None, description="Google 인코딩된 polyline")


class GoogleMapDataResponse(BaseModel):
    """프론트엔드로 반환할 Google Map 데이터"""
    segments: List[GooglePolylineSegment] = Field(..., description="각 구간별 경로")
    markers: List[Dict] = Field(..., description="마커 정보")
    center: Dict[str, float] = Field(..., description="지도 중심 좌표")
    zoom: int = Field(default=12, description="지도 줌 레벨")


# ─────────────────────────────────────────────────────────────
# 🛣️ Google Directions API 서비스
# ─────────────────────────────────────────────────────────────

class GoogleDirectionsService:
    """
    Google Directions API를 사용해 경로 데이터를 가져옵니다.
    프론트엔드에서 DirectionsService를 사용할 수 있도록 데이터를 반환합니다.
    """
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://maps.googleapis.com/maps/api/directions/json"
    
    async def get_route_data(
        self, 
        origin: Tuple[float, float],  # (lat, lng)
        destination: Tuple[float, float],
        mode: str = "transit"
    ) -> Dict:
        """
        두 지점 간 경로 데이터를 가져옵니다.
        
        Returns:
            {
                'encoded_polyline': str,  # Google의 인코딩된 polyline
                'distance_km': float,
                'duration_minutes': float,
                'steps': List[Dict]  # 상세 경로
            }
        """
        if not self.api_key:
            raise ValueError("Google Maps API 키가 설정되지 않았습니다.")
        
        # mode를 소문자로 변환
        mode_lower = mode.lower()
        
        params = {
            "origin": f"{origin[0]},{origin[1]}",
            "destination": f"{destination[0]},{destination[1]}",
            "mode": mode_lower,  # transit, driving, walking, bicycling
            "region": "KR",
            "language": "ko",
            "key": self.api_key
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(self.base_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if data.get("status") != "OK":
                            print(f"⚠️ Directions API 오류: {data.get('status')}")
                            # fallback: 직선 데이터 반환
                            return self._create_straight_line_data(origin, destination)
                        
                        # 경로 데이터 파싱
                        route = data["routes"][0]
                        leg = route["legs"][0]
                        
                        return {
                            "encoded_polyline": route["overview_polyline"]["points"],
                            "distance_km": leg["distance"]["value"] / 1000,
                            "duration_minutes": leg["duration"]["value"] / 60,
                            "distance_text": leg["distance"]["text"],
                            "duration_text": leg["duration"]["text"],
                            "steps": self._parse_steps(leg.get("steps", []))
                        }
                    else:
                        print(f"❌ Directions API HTTP 오류: {response.status}")
                        return self._create_straight_line_data(origin, destination)
                        
            except Exception as e:
                print(f"❌ Directions API 호출 오류: {e}")
                return self._create_straight_line_data(origin, destination)
    
    def _parse_steps(self, steps: List[Dict]) -> List[Dict]:
        """경로 단계 파싱"""
        parsed_steps = []
        for step in steps:
            parsed_steps.append({
                "distance": step["distance"]["text"],
                "duration": step["duration"]["text"],
                "instruction": step.get("html_instructions", ""),
                "travel_mode": step.get("travel_mode", "")
            })
        return parsed_steps
    
    def _create_straight_line_data(
        self, 
        origin: Tuple[float, float], 
        destination: Tuple[float, float]
    ) -> Dict:
        """API 실패 시 직선 데이터를 반환합니다."""
        from math import radians, sin, cos, sqrt, atan2
        
        # Haversine 거리 계산
        lat1, lng1 = map(radians, origin)
        lat2, lng2 = map(radians, destination)
        dlat = lat2 - lat1
        dlng = lng2 - lng1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlng/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        distance_km = 6371 * c  # 지구 반지름
        
        return {
            "encoded_polyline": None,  # 직선이므로 인코딩 불필요
            "distance_km": distance_km,
            "duration_minutes": distance_km * 2,
            "distance_text": f"{distance_km:.1f} km",
            "duration_text": f"{int(distance_km * 2)} 분",
            "steps": []
        }


# ─────────────────────────────────────────────────────────────
# 🗺️ API 엔드포인트
# ─────────────────────────────────────────────────────────────

@router.post("/course-route", response_model=GoogleMapDataResponse)
async def get_google_map_route_data(request: GoogleMapRouteRequest = Body(...)):
    """
    🎯 Google Maps용 코스 경로 데이터를 생성합니다.
    
    **프론트엔드는 이 API를 호출하고 Google Maps DirectionsService로 렌더링합니다!**
    
    - 장소 ID 리스트를 받아서
    - 각 구간별 경로 데이터 계산
    - Google Maps에서 사용할 수 있는 형식으로 변환
    - JSON으로 반환
    
    **참고:** 한국에서는 DRIVING 모드가 제한적일 수 있습니다.
    TRANSIT, WALKING, BICYCLING 모드를 권장합니다.
    """
    
    if not GOOGLE_MAPS_API_KEY:
        raise HTTPException(
            status_code=503, 
            detail="Google Maps API 키가 설정되지 않았습니다."
        )
    
    if not request.places or len(request.places) < 2:
        raise HTTPException(
            status_code=400,
            detail="최소 2개 이상의 장소가 필요합니다."
        )
    
    # 이동 수단 검증
    valid_modes = ["DRIVING", "WALKING", "BICYCLING", "TRANSIT"]
    travel_mode = request.travel_mode.upper()
    if travel_mode not in valid_modes:
        raise HTTPException(
            status_code=400,
            detail=f"올바른 이동 수단을 선택해주세요: {', '.join(valid_modes)}"
        )
    
    try:
        print(f"🗺️ Google Maps 경로 데이터 생성 시작: {len(request.places)}개 장소")
        print(f"   🚗 이동 수단: {travel_mode}")
        
        # 1. MongoDB에서 장소 정보 조회
        place_ids = [ObjectId(pid) for pid in request.places]
        places_cursor = tourism_collection.find({"_id": {"$in": place_ids}})
        places_data = [place async for place in places_cursor]
        
        if len(places_data) != len(request.places):
            raise HTTPException(
                status_code=404,
                detail="일부 장소를 찾을 수 없습니다."
            )
        
        # 순서 유지
        places_dict = {str(place["_id"]): place for place in places_data}
        ordered_places = [places_dict[pid] for pid in request.places]
        
        # 2. 각 구간별 경로 계산
        directions_service = GoogleDirectionsService(GOOGLE_MAPS_API_KEY)
        segments = []
        markers = []
        
        for i in range(len(ordered_places)):
            place = ordered_places[i]
            
            # 좌표 추출
            if 'location' in place and 'coordinates' in place['location']:
                lng, lat = place['location']['coordinates']
            elif 'map_x' in place and 'map_y' in place:
                lng, lat = place['map_x'], place['map_y']
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"장소 '{place.get('name')}'의 좌표 정보가 없습니다."
                )
            
            # 마커 정보 추가
            markers.append({
                "name": place.get("name", "Unknown"),
                "lat": lat,
                "lng": lng,
                "order": i + 1,
                "address": place.get("address", ""),
                "place_id": str(place["_id"])
            })
            
            # 다음 장소로 가는 경로 계산
            if i < len(ordered_places) - 1:
                next_place = ordered_places[i + 1]
                
                # 다음 장소 좌표
                if 'location' in next_place and 'coordinates' in next_place['location']:
                    next_lng, next_lat = next_place['location']['coordinates']
                else:
                    next_lng, next_lat = next_place['map_x'], next_place['map_y']
                
                # 경로 조회
                print(f"   🛣️ 경로 계산: {place.get('name')} → {next_place.get('name')}")
                route_data = await directions_service.get_route_data(
                    origin=(lat, lng),
                    destination=(next_lat, next_lng),
                    mode=travel_mode
                )
                
                segments.append(GooglePolylineSegment(
                    from_place=place.get("name", "Unknown"),
                    to_place=next_place.get("name", "Unknown"),
                    from_coords={"lat": lat, "lng": lng},
                    to_coords={"lat": next_lat, "lng": next_lng},
                    distance_km=round(route_data["distance_km"], 2),
                    duration_minutes=round(route_data["duration_minutes"], 1),
                    travel_mode=travel_mode,
                    encoded_polyline=route_data.get("encoded_polyline")
                ))
        
        # 3. 지도 중심 좌표 계산
        avg_lat = sum(m["lat"] for m in markers) / len(markers)
        avg_lng = sum(m["lng"] for m in markers) / len(markers)
        
        response = GoogleMapDataResponse(
            segments=segments,
            markers=markers,
            center={"lat": avg_lat, "lng": avg_lng},
            zoom=12
        )
        
        print(f"✅ Google Maps 경로 데이터 생성 완료: {len(segments)}개 구간")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 경로 데이터 생성 오류: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"경로 데이터 생성 중 오류가 발생했습니다: {str(e)}"
        )

