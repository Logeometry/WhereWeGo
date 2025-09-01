from bson import ObjectId
from fastapi import APIRouter, HTTPException, Depends, Header
from typing import List, Optional
from sklearn.metrics.pairwise import cosine_similarity
import jwt
import os
import numpy as np
from schemas import Tourism, CategoryScore, SurveyResponse
from db import places_col
import random
import traceback
from services.survey_service import recommend_similar_places_from_survey
from services.ml_recommendation_service import ml_recommendation_service

router = APIRouter()

async def get_current_user_id(authorization: Optional[str] = Header(None)) -> Optional[str]:
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

@router.post("/survey/recommend-similar")
async def recommend_similar_places(survey: List[SurveyResponse]):
    try:
        return await recommend_similar_places_from_survey(survey)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"추천 실패: {str(e)}")

@router.post("/survey/ml-recommend")
async def get_ml_recommendations_from_survey(
    survey: List[SurveyResponse],
    user_id: Optional[str] = Depends(get_current_user_id)
):
    try:
        is_logged_in = user_id is not None
        
        if not user_id:
            import uuid
            user_id = f"anonymous_{uuid.uuid4().hex[:8]}"
        
        survey_dict = [
            {
                "content_id": pref.content_id,
                "responses": pref.responses,
                "name": pref.name
            }
            for pref in survey
        ]
        
        recommendations = await ml_recommendation_service.get_recommendations(
            user_id=user_id,
            count=10,
            survey_preferences=survey_dict,
            save_to_logs=is_logged_in
        )
        
        if not recommendations:
            try:
                return await recommend_similar_places_from_survey(survey)
            except Exception as survey_error:
                print(f"설문조사 기반 추천 실패: {survey_error}")
                # 기본 추천으로 폴백
                from services.db_handler import get_random_places
                random_places = await get_random_places(10)
                return {
                    "message": "ML 모델과 설문조사 기반 추천이 실패하여 기본 추천을 제공합니다.",
                    "user_id": user_id,
                    "recommendations": [{"place_id": str(pid), "score": 0.5, "model_score": 0.5} for pid in random_places]
                }
        
        return {
            "message": "ML 모델 기반 개인화 추천이 완료되었습니다.",
            "user_id": user_id,
            "recommendations": recommendations
        }
        
    except Exception as e:
        print(f"ML 추천 실패: {e}")
        try:
            return await recommend_similar_places_from_survey(survey)
        except Exception as fallback_error:
            print(f"설문조사 기반 추천도 실패: {fallback_error}")
            # 최종 폴백: 기본 추천
            from services.db_handler import get_random_places
            random_places = await get_random_places(10)
            return {
                "message": "모든 추천 시스템이 실패하여 기본 추천을 제공합니다.",
                "user_id": user_id,
                "recommendations": [{"place_id": str(pid), "score": 0.5, "model_score": 0.5} for pid in random_places]
            }
