from fastapi import APIRouter, HTTPException, Query
import httpx
import os
from dotenv import load_dotenv
from typing import Dict, Optional
from datetime import datetime

load_dotenv()

router = APIRouter()

# 티맵 API 키
TMAP_API_KEY = os.getenv("TMAP_API_KEY")

async def get_tmap_crowding_data(poi_id: str, lat: Optional[float] = None, lng: Optional[float] = None) -> Dict:
    """티맵 실시간 혼잡도 데이터 조회"""
    try:
        if not TMAP_API_KEY:
            raise HTTPException(status_code=500, detail="TMAP API 키가 설정되지 않았습니다.")
        
        url = f"https://apis.openapi.sk.com/tmap/puzzle/pois/{poi_id}"
        
        params = {
            "appKey": TMAP_API_KEY
        }
        
        # 위경도가 제공된 경우에만 추가
        if lat is not None and lng is not None:
            params["lat"] = lat
            params["lng"] = lng
        
        headers = {
            "Accept": "application/json"
        }
        
        print(f"[DEBUG] 티맵 혼잡도 API 호출: {url}")
        print(f"[DEBUG] 파라미터: {params}")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            
        data = response.json()
        return data
        
    except httpx.HTTPStatusError as e:
        print(f"[ERROR] HTTP 오류: {e.response.status_code} - {e.response.text}")
        raise HTTPException(status_code=e.response.status_code, detail=f"티맵 API 호출 오류: {e.response.text}")
    except Exception as e:
        print(f"[ERROR] 일반 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"티맵 혼잡도 조회 오류: {str(e)}")

@router.get("/tmap-crowding/poi/{poi_id}", 
    summary="티맵 실시간 장소 혼잡도 조회",
    description="티맵 API를 통해 특정 POI의 실시간 혼잡도 정보를 조회합니다.",
    response_description="실시간 혼잡도 데이터",
    tags=["티맵 혼잡도"])
async def get_poi_crowding(
    poi_id: str,
    lat: Optional[float] = Query(None, description="주변 혼잡도를 구할 중심 위도값 (WGS84)"),
    lng: Optional[float] = Query(None, description="주변 혼잡도를 구할 중심 경도값 (WGS84)")
):
    """티맵 실시간 장소 혼잡도 조회
    
    티맵 API를 통해 특정 POI의 실시간 혼잡도 정보를 조회합니다.
    
    Args:
        poi_id (str): POI ID 또는 POI 식별자
        lat (float, optional): 주변 혼잡도를 구할 중심 위도값 (WGS84)
        lng (float, optional): 주변 혼잡도를 구할 중심 경도값 (WGS84)
    
    Returns:
        dict: 성공 여부와 혼잡도 데이터를 포함한 응답
        
    Raises:
        HTTPException: API 호출 실패 시 에러
    """
    try:
        data = await get_tmap_crowding_data(poi_id, lat, lng)
        
        # 응답 데이터 구조화
        result = {
            "success": True,
            "message": "티맵 실시간 혼잡도 조회 성공",
            "data": data
        }
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"티맵 혼잡도 조회 중 오류 발생: {str(e)}")

@router.get("/tmap-crowding/area", 
    summary="티맵 실시간 주변 혼잡도 조회",
    description="티맵 API를 통해 특정 위경도 기준 주변의 실시간 혼잡도 정보를 조회합니다.",
    response_description="주변 실시간 혼잡도 데이터",
    tags=["티맵 혼잡도"])
async def get_area_crowding(
    lat: float = Query(..., description="주변 혼잡도를 구할 중심 위도값 (WGS84)"),
    lng: float = Query(..., description="주변 혼잡도를 구할 중심 경도값 (WGS84)"),
    poi_id: Optional[str] = Query(None, description="POI ID (선택사항)")
):
    """티맵 실시간 주변 혼잡도 조회
    
    티맵 API를 통해 특정 위경도 기준 주변의 실시간 혼잡도 정보를 조회합니다.
    
    Args:
        lat (float): 주변 혼잡도를 구할 중심 위도값 (WGS84)
        lng (float): 주변 혼잡도를 구할 중심 경도값 (WGS84)
        poi_id (str, optional): POI ID (선택사항)
    
    Returns:
        dict: 성공 여부와 주변 혼잡도 데이터를 포함한 응답
        
    Raises:
        HTTPException: API 호출 실패 시 에러
    """
    try:
        # POI ID가 제공되지 않은 경우 더미 값 사용 (API에서 주변 혼잡도만 조회)
        if not poi_id:
            poi_id = "dummy"
        
        data = await get_tmap_crowding_data(poi_id, lat, lng)
        
        # 응답 데이터 구조화
        result = {
            "success": True,
            "message": "티맵 주변 혼잡도 조회 성공",
            "data": data,
            "request_info": {
                "latitude": lat,
                "longitude": lng,
                "poi_id": poi_id
            }
        }
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"티맵 주변 혼잡도 조회 중 오류 발생: {str(e)}")

@router.get("/tmap-crowding/level-info", 
    summary="티맵 혼잡도 레벨 정보",
    description="티맵 혼잡도 레벨별 상세 정보를 제공합니다.",
    response_description="혼잡도 레벨 정보",
    tags=["티맵 혼잡도"])
async def get_crowding_level_info():
    """티맵 혼잡도 레벨 정보
    
    티맵 혼잡도 레벨별 상세 정보를 제공합니다.
    
    Returns:
        dict: 혼잡도 레벨별 상세 정보
    """
    level_info = {
        "success": True,
        "message": "혼잡도 레벨 정보",
        "data": {
            "levels": [
                {
                    "level": 1,
                    "name": "여유",
                    "range": "0.025명 미만/㎡",
                    "description": "전방 시야가 트인 상태",
                    "color": "green"
                },
                {
                    "level": 2,
                    "name": "보통",
                    "range": "0.025명 이상~0.05명 미만/㎡",
                    "description": "전방 시야가 다소 막히는 상태",
                    "color": "yellow"
                },
                {
                    "level": 3,
                    "name": "혼잡",
                    "range": "0.05명 이상~0.3명 미만/㎡",
                    "description": "지나가는 사람과 서로 부딪힐 수 있는 다소 혼잡한 상태",
                    "color": "orange"
                },
                {
                    "level": 4,
                    "name": "매우 혼잡",
                    "range": "0.3명 이상/㎡",
                    "description": "매우 혼잡하여 불쾌할 수 있는 상태",
                    "color": "red"
                }
            ],
            "unit": "명/㎡ (단위 면적당 추정 방문자 수)",
            "coordinate_system": "WGS84 경위도 좌표계"
        }
    }
    
    return level_info
