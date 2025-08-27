# routeres/recommend_location.py
"""
장소 추천 및 코스 생성 라우터
1. 우선순위 기반 10개 장소 추천 (추천점수 포함)
2. 선택된 장소들로 여행 코스 생성
"""

from fastapi import APIRouter, HTTPException, Query, Body
from typing import List, Optional, Dict
from pydantic import BaseModel
from datetime import datetime, timedelta
import random
from bson import ObjectId

from services.db_handler import tourism_collection, starting_point_collection
from services.survey_service import recommend_similar_places_from_survey
from services.ml_recommendation_service import ml_recommendation_service
from schemas import SurveyResponse, ItineraryRequest, ItineraryResponse

router = APIRouter()

# Pydantic 모델 정의 (ML 모델과의 일관성을 위해 ID 중심으로 단순화)
class RecommendedPlace(BaseModel):
    place_id: str
    name: str
    category: str
    recommendation_score: float  # 0.0 ~ 1.0

class RecommendationRequest(BaseModel):
    user_id: Optional[str] = None  # ML 추천을 위한 사용자 ID
    user_preferences: Optional[List[SurveyResponse]] = None
    exclude_places: Optional[List[str]] = None  # 이미 선택된 장소들 제외
    category_filter: Optional[str] = None
    location_filter: Optional[str] = None
    use_ml: bool = False  # ML 모델 사용 여부

class RecommendationResponse(BaseModel):
    places: List[RecommendedPlace]
    total_count: int
    message: str

# 코스 생성은 recommeded_cors_router.py에서 처리하므로 제거

@router.post("/recommendations", response_model=RecommendationResponse)
async def get_place_recommendations(request: RecommendationRequest = Body(...)):
    """
    우선순위 기반 10개 장소 추천 (추천점수 포함)
    
    Args:
        request: 추천 요청 정보 (사용자 선호도, 제외할 장소, 필터 등)
    
    Returns:
        10개의 추천 장소 리스트 (추천점수 순)
    """
    try:
        # 1. 기본 쿼리 구성
        query = {}
        
        # 이미 선택된 장소 제외
        if request.exclude_places:
            query["_id"] = {"$nin": [ObjectId(pid) for pid in request.exclude_places]}
        
        # 카테고리 필터
        if request.category_filter:
            query["category"] = request.category_filter
        
        # 지역 필터
        if request.location_filter:
            query["location"] = {"$regex": request.location_filter, "$options": "i"}
        
        # 2. 추천 방식 결정 및 실행
        if request.use_ml and request.user_id:
            # ML 모델 기반 추천
            recommendations = await get_ml_recommendations(
                request.user_id,
                request.exclude_places,
                query
            )
        elif request.user_preferences:
            # 사용자 선호도 기반 추천
            recommendations = await get_personalized_recommendations(
                request.user_preferences, 
                query
            )
        else:
            # 인기도 기반 추천
            recommendations = await get_popularity_recommendations(query)
        
        # 3. 상위 10개만 반환
        top_10_recommendations = recommendations[:10]
        
        return RecommendationResponse(
            places=top_10_recommendations,
            total_count=len(top_10_recommendations),
            message="추천 장소를 성공적으로 가져왔습니다."
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"추천 생성 실패: {str(e)}"
        )

async def get_personalized_recommendations(
    user_preferences: List[SurveyResponse],
    base_query: Dict
) -> List[RecommendedPlace]:
    """사용자 선호도 기반 개인화 추천 (임시 하드코딩)"""
    
    try:
        # 임시로 설문 결과를 하드코딩 (실제로는 설문 라우터에서 받아와야 함)
        # 설문이 없으므로 인기도 기반으로 폴백
        print("설문 기반 추천이 아직 구현되지 않았습니다. 인기도 기반으로 폴백합니다.")
        return await get_popularity_recommendations(base_query)
        
    except Exception as e:
        print(f"개인화 추천 오류: {e}")
        # 오류 시 인기도 기반으로 폴백
        return await get_popularity_recommendations(base_query)

async def get_ml_recommendations(
    user_id: str,
    exclude_places: List[str],
    base_query: Dict
) -> List[RecommendedPlace]:
    """ML 모델 기반 추천"""
    
    try:
        # ML 서비스에서 추천 받기
        ml_recommendations = await ml_recommendation_service.get_recommendations(
            user_id=user_id,
            count=20,
            exclude_places=exclude_places
        )
        
        if not ml_recommendations:
            print("ML 추천 결과가 없습니다. 인기도 기반으로 폴백합니다.")
            return await get_popularity_recommendations(base_query)
        
        # DB에서 장소 상세 정보 조회
        place_ids = [ObjectId(rec["place_id"]) for rec in ml_recommendations]
        places_cursor = tourism_collection.find({"_id": {"$in": place_ids}})
        places_details = {str(p['_id']): p async for p in places_cursor}
        
        # 응답 형식 변환
        recommendations = []
        for rec in ml_recommendations:
            place_id = rec["place_id"]
            if place_id in places_details:
                place = places_details[place_id]
                recommendations.append(RecommendedPlace(
                    place_id=place_id,
                    name=place.get("name", ""),
                    category=place.get("category", ""),
                    recommendation_score=min(max(rec["score"], 0.0), 1.0)  # 0.0~1.0 범위로 정규화
                ))
        
        return recommendations
        
    except Exception as e:
        print(f"ML 추천 오류: {e}")
        # 오류 시 인기도 기반으로 폴백
        return await get_popularity_recommendations(base_query)

async def get_popularity_recommendations(base_query: Dict) -> List[RecommendedPlace]:
    """인기도 기반 추천 (기본값)"""
    
    try:
        # 인기도 점수 계산 (더 다양한 점수 분포를 위해 수정)
        pipeline = [
            {"$match": base_query},
            {"$addFields": {
                "base_score": {
                    "$add": [
                        {"$multiply": [{"$ifNull": ["$rating", 0]}, 0.3]},
                        {"$multiply": [{"$ifNull": ["$visit_count", 0]}, 0.2]},
                        {"$multiply": [{"$ifNull": ["$review_count", 0]}, 0.1]}
                    ]
                }
            }},
            {"$addFields": {
                "popularity_score": {
                    "$add": [
                        "$base_score",
                        {"$multiply": [{"$rand": {}}, 0.4]}  # 랜덤 요소 비중 증가
                    ]
                }
            }},
            {"$sort": {"popularity_score": -1}},
            {"$limit": 20}  # 더 많은 후보에서 선택
        ]
        
        places_cursor = tourism_collection.aggregate(pipeline)
        places = await places_cursor.to_list(length=20)
        
        # 응답 형식 변환 (ID 중심으로 단순화)
        recommendations = []
        for place in places:
            recommendations.append(RecommendedPlace(
                place_id=str(place["_id"]),
                name=place.get("name", ""),
                category=place.get("category", ""),
                recommendation_score=min(place.get("popularity_score", 0.0), 1.0)  # 1.0 이하로 제한
            ))
        
        return recommendations
        
    except Exception as e:
        print(f"인기도 추천 오류: {e}")
        # 최후의 수단: 랜덤 추천
        return await get_random_recommendations(base_query)

async def get_random_recommendations(base_query: Dict) -> List[RecommendedPlace]:
    """랜덤 추천 (폴백)"""
    
    try:
        # 랜덤 샘플링
        pipeline = [
            {"$match": base_query},
            {"$sample": {"size": 20}},
            {"$limit": 20}
        ]
        
        places_cursor = tourism_collection.aggregate(pipeline)
        places = await places_cursor.to_list(length=20)
        
        # 응답 형식 변환 (ID 중심으로 단순화)
        recommendations = []
        for place in places:
            recommendations.append(RecommendedPlace(
                place_id=str(place["_id"]),
                name=place.get("name", ""),
                category=place.get("category", ""),
                recommendation_score=round(random.uniform(0.2, 0.9), 2)  # 더 다양한 랜덤 점수
            ))
        
        return recommendations
        
    except Exception as e:
        print(f"랜덤 추천 오류: {e}")
        return []

# 코스 생성은 recommeded_cors_router.py에서 처리하므로 제거

@router.get("/categories")
async def get_categories():
    """사용 가능한 카테고리 목록 반환"""
    try:
        pipeline = [
            {"$group": {"_id": "$category", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        
        categories_cursor = tourism_collection.aggregate(pipeline)
        categories = await categories_cursor.to_list(length=None)
        
        return {
            "categories": [
                {"name": cat["_id"], "count": cat["count"]} 
                for cat in categories if cat["_id"]
            ]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"카테고리 조회 실패: {str(e)}"
        )

@router.get("/locations")
async def get_locations():
    """사용 가능한 지역 목록 반환"""
    try:
        pipeline = [
            {"$group": {"_id": "$location", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        
        locations_cursor = tourism_collection.aggregate(pipeline)
        locations = await locations_cursor.to_list(length=None)
        
        return {
            "locations": [
                {"name": loc["_id"], "count": loc["count"]} 
                for loc in locations if loc["_id"]
            ]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"지역 조회 실패: {str(e)}"
        )
