# 설문 응답 수신을 위한 라우터
#from fastapi import APIRouter, HTTPException
#from schemas import SurveyRequest
#from services.survey_saver import save_survey
#
#router = APIRouter()
#
#@router.post("/survey")
#def submit_survey(survey: SurveyRequest):
#    try:
#        save_survey(survey)
#        return {"message": "설문이 성공적으로 저장되었습니다."}
#    except Exception as e:
#        raise HTTPException(status_code=500, detail=str(e))


# 설문 응답 저장을 위한 라투어
from fastapi import APIRouter, HTTPException
from typing import List
from pathlib import Path
from schemas import LocationData, CategoryScore, SurveyResponse
from services.data_loader import load_location_data_from_json
from services.survey_compute_service import compute_category_scores

router = APIRouter()

@router.get("/items")
async def read_survey_items():
    try:
        return load_location_data_from_json(str(DATA_PATH))
    except Exception:
        raise HTTPException(500, "설문지 항목을 불러오는 데 실패했습니다.")

@router.post(
    "/recommend-by-score",
    response_model=List[Course],
    summary="프론트에서 집계된 카테고리 점수로 코스 추천"
)
async def recommend_by_score(category_scores: List[CategoryScore]):
    """
    1) 프론트에서 계산해온 [{category, score}, …] 를 받고
    2) recommend_courses(service) 에 넘겨서
    3) Course 리스트를 반환
    """
    if not category_scores:
        raise HTTPException(400, "카테고리 점수 정보가 없습니다.")
    try:
        return await recommend_courses(category_scores)
    except Exception:
        raise HTTPException(500, "코스 추천 중 오류가 발생했습니다.")