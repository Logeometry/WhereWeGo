# services/survey_service.py

from typing import List
from schemas import SurveyResponse
from db import places_col
from bson import ObjectId
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

async def recommend_similar_places_from_survey(survey: List[SurveyResponse]) -> List[dict]:
    """새로운 설문 구조에 기반한 장소 추천"""
    
    # 선호 카테고리 그룹 추출
    preferred_categories = [s.category_group for s in survey if s.pos_item_index > s.neg_item_index]
    
    # 활동성 레벨과 시간대 기반 필터링
    activity_preferences = {}
    time_preferences = {}
    
    for s in survey:
        if s.preference == 0:  # 활동성 선호
            activity_preferences[s.activity_level_idx] = activity_preferences.get(s.activity_level_idx, 0) + 1
        else:  # 시간대 선호
            time_preferences[s.time_period] = time_preferences.get(s.time_period, 0) + 1
    
    # MongoDB 쿼리 구성
    query_filter = {}
    if preferred_categories:
        query_filter["category_group"] = {"$in": preferred_categories}
    
    query_filter["vector_full"] = {"$exists": True, "$ne": None}
    
    candidates = await places_col.find(query_filter).to_list(length=2000)
    
    scored = []
    for place in candidates:
        vector = place.get("vector_full")
        if not vector:
            continue
        
        # 기본 점수 계산
        score = 1.0
        
        # 카테고리 매칭 보너스
        if place.get("category_group") in preferred_categories:
            score += 0.5
        
        # 계절성 고려 (향후 확장 가능)
        place["_id"] = str(place["_id"])
        place["recommendation_score"] = float(score)
        scored.append(place)
    
    scored.sort(key=lambda x: -x["recommendation_score"])
    return scored[:10]
