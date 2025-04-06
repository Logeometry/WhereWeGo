# 설문 응답 수신을 위한 라우터
from fastapi import APIRouter, HTTPException
from schemas import SurveyRequest
from services.survey_saver import save_survey

router = APIRouter()

@router.post("/survey")
def submit_survey(survey: SurveyRequest):
    try:
        save_survey(survey)
        return {"message": "설문이 성공적으로 저장되었습니다."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
