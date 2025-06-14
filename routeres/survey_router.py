# routeres/survey_router.py

## 설문조사를 위한 장소 추천 라우터
## DB에서 상위 50개 중 랜덤으로 5개를 불러온다 

from bson import ObjectId
from fastapi import APIRouter, HTTPException
from typing import List
from sklearn.metrics.pairwise import cosine_similarity

import numpy as np
from schemas import Tourism, CategoryScore, SurveyResponse
from db import places_col
import random
import traceback
from services.survey_service import recommend_similar_places_from_survey

router = APIRouter()

@router.post("/survey/recommend-similar")
async def recommend_similar_places(survey: List[SurveyResponse]):
    try:
        return await recommend_similar_places_from_survey(survey)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"추천 실패: {str(e)}")
