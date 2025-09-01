# routeres/recommend_location.py
"""
장소 추천 라우터
우선순위 기반 장소 추천 (추천점수 포함)
- ML 모델 기반 추천
- 인기도 기반 추천  
- 사용자 선호도 기반 추천
"""

from fastapi import APIRouter, HTTPException, Query, Body, Depends, Header
from typing import List, Optional, Dict
from pydantic import BaseModel
from datetime import datetime, timedelta
import random
import os
import jwt
from bson import ObjectId
from services.db_handler import tourism_collection
from services.ml_recommendation_service import MLRecommendationService
from schemas import SurveyResponse

router = APIRouter()

# JWT 토큰에서 유저 ID 추출하는 의존성 함수
async def get_current_user_id(authorization: Optional[str] = Header(None)) -> Optional[str]:
    """JWT 토큰에서 유저 ID 추출"""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    
    try:
        token = authorization.split(" ")[1]
        SECRET_KEY = os.getenv("SECRET_KEY", "y314adfas...23414afdafasf524515411")
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload.get("sub")
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

class RecommendedPlace(BaseModel):
    place_id: str
    name: str
    category: str
    recommendation_score: float

class RecommendationRequest(BaseModel):
    user_id: Optional[str] = None
    user_preferences: Optional[List[SurveyResponse]] = None
    exclude_places: Optional[List[str]] = None
    category_filter: Optional[str] = None
    location_filter: Optional[str] = None
    use_ml: bool = False

class RecommendationResponse(BaseModel):
    places: List[RecommendedPlace]
    total_count: int
    message: str

@router.post("/recommendations", response_model=RecommendationResponse)
async def get_place_recommendations(
    request: RecommendationRequest = Body(...),
    user_id: Optional[str] = Depends(get_current_user_id)
):
    try:
        query = {}
        
        if request.exclude_places:
            query["_id"] = {"$nin": [ObjectId(pid) for pid in request.exclude_places]}
        
        if request.category_filter:
            query["category"] = request.category_filter
        
        if request.location_filter:
            query["location"] = {"$regex": request.location_filter, "$options": "i"}
        
        if not user_id and not request.user_id:
            import uuid
            actual_user_id = f"anonymous_{uuid.uuid4().hex[:8]}"
        else:
            actual_user_id = user_id or request.user_id or "anonymous_user"
        
        is_logged_in = user_id is not None
        
        if request.user_preferences:
            exclude_places = request.exclude_places or []
            recommendations = await get_ml_recommendations(
                actual_user_id,
                exclude_places,
                query,
                request.user_preferences,
                is_logged_in
            )
        elif request.use_ml:
            recommendations = await get_ml_recommendations(
                actual_user_id,
                request.exclude_places,
                query,
                None,
                is_logged_in
            )
        else:
            recommendations = await get_popularity_recommendations(query)
        
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


async def get_ml_recommendations(
    user_id: str,
    exclude_places: List[str],
    base_query: Dict,
    survey_preferences: List[SurveyResponse] = None,
    is_logged_in: bool = True
) -> List[RecommendedPlace]:
    """ML 모델 기반 추천"""
    
    try:
        if not hasattr(get_ml_recommendations, 'ml_service'):
            get_ml_recommendations.ml_service = MLRecommendationService()
            
            model_path = os.path.join(os.path.dirname(__file__), '..', 'model', 'model_epoch_5.pth')
            mapping_path = os.path.join(os.path.dirname(__file__), '..', 'model', 'model_epoch_5_mappings.json')
            
            if os.path.exists(model_path):
                await get_ml_recommendations.ml_service.load_model(model_path, mapping_path)
            else:
                return await get_popularity_recommendations(base_query)
        
        survey_dict = None
        if survey_preferences:
            survey_dict = [
                {
                    "content_id": pref.content_id,
                    "responses": pref.responses,
                    "name": pref.name
                }
                for pref in survey_preferences
            ]
        
        ml_recommendations = await get_ml_recommendations.ml_service.get_recommendations(
            user_id=user_id,
            count=20,
            exclude_places=exclude_places,
            survey_preferences=survey_dict,
            save_to_logs=is_logged_in
        )
        
        if not ml_recommendations:
            return await get_popularity_recommendations(base_query)
        
        place_ids = [ObjectId(rec["place_id"]) for rec in ml_recommendations]
        places_cursor = tourism_collection.find({"_id": {"$in": place_ids}})
        places_details = {str(p['_id']): p async for p in places_cursor}
        
        recommendations = []
        for rec in ml_recommendations:
            place_id = rec["place_id"]
            if place_id in places_details:
                place = places_details[place_id]
                recommendations.append(RecommendedPlace(
                    place_id=place_id,
                    name=place.get("name", ""),
                    category=place.get("category", ""),
                    recommendation_score=min(max(rec["score"], 0.0), 1.0)
                ))
        
        return recommendations
        
    except Exception as e:
        return await get_popularity_recommendations(base_query)

async def get_popularity_recommendations(base_query: Dict) -> List[RecommendedPlace]:
    """인기도 기반 추천 (기본값)"""
    
    try:
        # 인기도 점수 계산 (실제 DB 필드명에 맞게 수정)
        pipeline = [
            {"$match": base_query},
            {"$addFields": {
                "base_score": {
                    "$add": [
                        {"$multiply": [{"$ifNull": ["$rating", 0]}, 0.4]},        # 평점 40%
                        {"$multiply": [{"$ifNull": ["$visitors_count", 0]}, 0.3]}, # 방문자수 30%
                        {"$multiply": [{"$ifNull": ["$review_count", 0]}, 0.2]}    # 리뷰수 20%
                    ]
                }
            }},
            {"$addFields": {
                "popularity_score": {
                    "$add": [
                        "$base_score",
                        {"$multiply": [{"$rand": {}}, 0.1]}  # 랜덤 요소 10%로 감소
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
