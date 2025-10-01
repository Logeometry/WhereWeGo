# kakaomap_cors_router.py
# map에 코스를 보여주는 라우터

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

class MapRouteRequest(BaseModel):
    """
    프론트엔드에서 받을 코스 데이터
    사용자가 실시간으로 수정한 장소 리스트
    """
    places: List[str] = Field(..., description="장소 ID 리스트 (순서대로)")
    mode: Optional[str] = Field("transit", description="이동 수단 (transit, driving, walking)")
    

class TransitStep(BaseModel):
    """대중교통 상세 정보"""
    travel_mode: str = Field(..., description="이동 수단 (TRANSIT, WALKING 등)")
    instruction: str = Field(..., description="안내 텍스트 (HTML)")
    distance: str = Field(..., description="거리 텍스트")
    duration: str = Field(..., description="소요 시간 텍스트")
    transit_details: Optional[Dict] = Field(None, description="대중교통 상세 (버스/지하철 정보)")

class PolylineSegment(BaseModel):
    """단일 경로 구간 (A -> B)"""
    from_place: str = Field(..., description="출발지 장소명")
    to_place: str = Field(..., description="도착지 장소명")
    polyline: List[Dict[str, float]] = Field(..., description="경로 좌표 [{'lat': ..., 'lng': ...}]")
    distance_km: float = Field(..., description="거리 (km)")
    duration_minutes: float = Field(..., description="소요 시간 (분)")
    color: str = Field(..., description="선 색상 (hex)")
    steps: Optional[List[TransitStep]] = Field(None, description="상세 이동 경로 (버스, 도보 등)")


class MapDataResponse(BaseModel):
    """프론트엔드로 반환할 지도 데이터"""
    segments: List[PolylineSegment] = Field(..., description="각 구간별 경로")
    markers: List[Dict] = Field(..., description="마커 정보")
    center: Dict[str, float] = Field(..., description="지도 중심 좌표")
    zoom: int = Field(default=12, description="지도 줌 레벨")


# ─────────────────────────────────────────────────────────────
# 🎨 색상 팔레트 (각 구간마다 다른 색상)
# ─────────────────────────────────────────────────────────────

ROUTE_COLORS = [
    "#FF6B6B",  # 빨강
    "#4ECDC4",  # 청록
    "#45B7D1",  # 파랑
    "#FFA07A",  # 연어
    "#98D8C8",  # 민트
    "#F7DC6F",  # 노랑
    "#BB8FCE",  # 보라
    "#85C1E2",  # 하늘
    "#F8B739",  # 주황
    "#52B788",  # 초록
]


# ─────────────────────────────────────────────────────────────
# 🛣️ Google Directions API 서비스
# ─────────────────────────────────────────────────────────────

class GoogleDirectionsService:
    """
    Google Directions API를 사용해 상세 경로 좌표를 가져옵니다.
    Distance Matrix와 달리 실제 도로를 따라가는 polyline 좌표를 제공합니다.
    """
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://maps.googleapis.com/maps/api/directions/json"
    
    async def get_route_polyline(
        self, 
        origin: Tuple[float, float],  # (lat, lng)
        destination: Tuple[float, float],
        mode: str = "transit"
    ) -> Dict:
        """
        두 지점 간 상세 경로를 가져옵니다.
        
        Returns:
            {
                'polyline': [{'lat': ..., 'lng': ...}, ...],
                'distance_km': float,
                'duration_minutes': float
            }
        """
        if not self.api_key:
            raise ValueError("Google Maps API 키가 설정되지 않았습니다.")
        
        params = {
            "origin": f"{origin[0]},{origin[1]}",
            "destination": f"{destination[0]},{destination[1]}",
            "mode": mode,  # transit, driving, walking
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
                            # fallback: 직선 좌표 반환
                            return self._create_straight_line(origin, destination)
                        
                        # 경로 데이터 파싱
                        route = data["routes"][0]
                        leg = route["legs"][0]
                        
                        # polyline 디코딩
                        encoded_polyline = route["overview_polyline"]["points"]
                        decoded_coords = self._decode_polyline(encoded_polyline)
                        
                        # 상세 경로 단계 추출 (대중교통 정보 포함)
                        steps = []
                        for step in leg.get("steps", []):
                            step_info = {
                                "travel_mode": step.get("travel_mode", "UNKNOWN"),
                                "instruction": step.get("html_instructions", ""),
                                "distance": step.get("distance", {}).get("text", ""),
                                "duration": step.get("duration", {}).get("text", ""),
                                "transit_details": None
                            }
                            
                            # 대중교통 상세 정보 (버스, 지하철 등)
                            if step.get("travel_mode") == "TRANSIT" and "transit_details" in step:
                                transit = step["transit_details"]
                                step_info["transit_details"] = {
                                    "line_name": transit.get("line", {}).get("name", ""),
                                    "line_short_name": transit.get("line", {}).get("short_name", ""),
                                    "vehicle_type": transit.get("line", {}).get("vehicle", {}).get("type", ""),
                                    "vehicle_name": transit.get("line", {}).get("vehicle", {}).get("name", ""),
                                    "departure_stop": transit.get("departure_stop", {}).get("name", ""),
                                    "arrival_stop": transit.get("arrival_stop", {}).get("name", ""),
                                    "num_stops": transit.get("num_stops", 0),
                                    "headsign": transit.get("headsign", "")
                                }
                            
                            steps.append(step_info)
                        
                        return {
                            "polyline": decoded_coords,
                            "distance_km": leg["distance"]["value"] / 1000,
                            "duration_minutes": leg["duration"]["value"] / 60,
                            "steps": steps
                        }
                    else:
                        print(f"❌ Directions API HTTP 오류: {response.status}")
                        return self._create_straight_line(origin, destination)
                        
            except Exception as e:
                print(f"❌ Directions API 호출 오류: {e}")
                return self._create_straight_line(origin, destination)
    
    def _decode_polyline(self, encoded: str) -> List[Dict[str, float]]:
        """
        Google의 인코딩된 polyline을 좌표 리스트로 디코딩합니다.
        알고리즘: https://developers.google.com/maps/documentation/utilities/polylinealgorithm
        """
        coords = []
        index = 0
        lat = 0
        lng = 0
        
        while index < len(encoded):
            # Latitude 디코딩
            shift = 0
            result = 0
            while True:
                b = ord(encoded[index]) - 63
                index += 1
                result |= (b & 0x1f) << shift
                shift += 5
                if b < 0x20:
                    break
            dlat = ~(result >> 1) if (result & 1) else (result >> 1)
            lat += dlat
            
            # Longitude 디코딩
            shift = 0
            result = 0
            while True:
                b = ord(encoded[index]) - 63
                index += 1
                result |= (b & 0x1f) << shift
                shift += 5
                if b < 0x20:
                    break
            dlng = ~(result >> 1) if (result & 1) else (result >> 1)
            lng += dlng
            
            coords.append({
                "lat": lat / 1e5,
                "lng": lng / 1e5
            })
        
        return coords
    
    def _create_straight_line(
        self, 
        origin: Tuple[float, float], 
        destination: Tuple[float, float]
    ) -> Dict:
        """API 실패 시 직선 경로를 반환합니다."""
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
            "polyline": [
                {"lat": origin[0], "lng": origin[1]},
                {"lat": destination[0], "lng": destination[1]}
            ],
            "distance_km": distance_km,
            "duration_minutes": distance_km * 2,  # 대략적인 추정
            "steps": []  # 빈 배열 반환
        }


# ─────────────────────────────────────────────────────────────
# 🗺️ API 엔드포인트
# ─────────────────────────────────────────────────────────────

@router.post("/course-route", response_model=MapDataResponse)
async def get_course_route_data(request: MapRouteRequest = Body(...)):
    """
    🎯 코스 경로 데이터를 생성합니다.
    
    **프론트엔드는 이 API를 호출하고 결과를 카카오맵에 렌더링하기만 하면 됩니다!**
    
    복잡한 로직 (경로 계산, 좌표 변환, 색상 지정)은 모두 백엔드에서 처리합니다.
    
    - 장소 ID 리스트를 받아서
    - 각 구간별 상세 경로 계산
    - 카카오맵 Polyline 형식으로 변환
    - 구간별 다른 색상 지정
    - JSON으로 반환
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
    
    try:
        print(f"🗺️ 코스 경로 데이터 생성 시작: {len(request.places)}개 장소")
        
        # 1. MongoDB에서 장소 정보 조회
        place_ids = [ObjectId(pid) for pid in request.places]
        places_cursor = tourism_collection.find({"_id": {"$in": place_ids}})
        places_data = [place async for place in places_cursor]
        
        if len(places_data) != len(request.places):
            raise HTTPException(
                status_code=404,
                detail="일부 장소를 찾을 수 없습니다."
            )
        
        # 순서 유지 (요청한 순서대로 정렬)
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
                print(f"   🛣️ 경로 계산: {place.get('name')} → {next_place.get('name')} (mode: {request.mode})")
                route_data = await directions_service.get_route_polyline(
                    origin=(lat, lng),
                    destination=(next_lat, next_lng),
                    mode=request.mode or "transit"  # 요청한 이동 수단 사용
                )
                
                # 색상 선택 (순환)
                color = ROUTE_COLORS[i % len(ROUTE_COLORS)]
                
                segments.append(PolylineSegment(
                    from_place=place.get("name", "Unknown"),
                    to_place=next_place.get("name", "Unknown"),
                    polyline=route_data["polyline"],
                    distance_km=round(route_data["distance_km"], 2),
                    duration_minutes=round(route_data["duration_minutes"], 1),
                    color=color,
                    steps=route_data.get("steps", [])
                ))
        
        # 3. 지도 중심 좌표 계산 (모든 장소의 중간)
        avg_lat = sum(m["lat"] for m in markers) / len(markers)
        avg_lng = sum(m["lng"] for m in markers) / len(markers)
        
        response = MapDataResponse(
            segments=segments,
            markers=markers,
            center={"lat": avg_lat, "lng": avg_lng},
            zoom=12
        )
        
        print(f"✅ 경로 데이터 생성 완료: {len(segments)}개 구간")
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


