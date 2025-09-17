# routeres/survey_router_new.py
"""
단순화된 설문조사 라우터
4단계로 구성된 효율적인 설문조사 시스템
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional, Dict
from pydantic import BaseModel
import os
import sys

# 상위 디렉토리를 Python 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# 안전한 import
try:
    from schemas import SurveyData, VoteData, MLRecommendationResponse
    from routeres.auth_router import get_current_user
    from services.ml_recommendation_service import ml_recommendation_service
    from services.db_handler import tourism_collection
    IMPORTS_AVAILABLE = True
    print("✅ 모든 모듈 import 성공")
except ImportError as e:
    print(f"⚠️ 모듈 import 실패: {e}")
    IMPORTS_AVAILABLE = False

router = APIRouter()

# ============ 스키마 정의 ============

class SurveySubmitRequest(BaseModel):
    """설문조사 제출 요청"""
    activity: str
    activity_level: str
    time: str
    season: str
    preference: str

class SurveySaveRequest(BaseModel):
    """설문조사 결과 저장 요청"""
    survey_data: SurveySubmitRequest
    votes: List[VoteData]

class SurveyStatusResponse(BaseModel):
    """설문조사 상태 응답"""
    user_id: str
    logged_in: bool
    has_survey_data: bool
    has_votes: bool

class SurveySubmitResponse(BaseModel):
    """설문조사 제출 응답"""
    status: str
    recommendations: List[Dict]
    message: str

class SurveySaveResponse(BaseModel):
    """설문조사 저장 응답"""
    status: str
    message: str
    survey_id: str

class MLRecommendationResponse(BaseModel):
    """ML 추천 응답"""
    status: str
    recommendations: List[Dict]
    model_info: Dict

# ============ 1. 로그인 인증 확인 ============

@router.get("/survey/status", response_model=SurveyStatusResponse)
async def get_survey_status(user_id=Depends(get_current_user)):
    """1. 로그인 인증 확인 및 설문조사 상태 조회"""
    try:
        # 설문조사 데이터 확인 (임시로 메모리에서 확인)
        # 실제로는 DB에서 확인해야 함
        has_survey_data = False  # TODO: DB에서 확인
        has_votes = False        # TODO: DB에서 확인
        
        return SurveyStatusResponse(
            user_id=user_id,
            logged_in=True,
            has_survey_data=has_survey_data,
            has_votes=has_votes
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"상태 조회 실패: {str(e)}")

# ============ 2-1. 사용자 설문 + 2-2. 장소 추천 ============

@router.post("/survey/submit", response_model=SurveySubmitResponse)
async def submit_survey(request: SurveySubmitRequest, user_id=Depends(get_current_user)):
    """2-1. 사용자 설문 + 2-2. 설문조사를 위한 장소 추천"""
    try:
        # 설문조사 데이터 검증
        if not all([request.activity, request.activity_level, request.time, request.season, request.preference]):
            raise HTTPException(status_code=400, detail="모든 설문조사 항목을 입력해주세요.")
        
        # 설문조사 기반 장소 추천 생성
        recommendations = await generate_survey_recommendations(request)
        
        return SurveySubmitResponse(
            status="success",
            recommendations=recommendations,
            message="설문조사가 완료되었습니다. 추천 장소를 확인해주세요."
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"설문조사 제출 실패: {str(e)}")

async def generate_survey_recommendations(survey_data: SurveySubmitRequest) -> List[Dict]:
    """설문조사 기반 장소 추천 생성"""
    try:
        # 설문조사 데이터를 바탕으로 장소 추천 로직
        # 실제로는 recommend_location.py의 로직을 활용
        
        # 임시 추천 데이터 (실제로는 ML 모델이나 추천 알고리즘 사용)
        recommendations = [
            {
                "place_id": "1",
                "name": "해운대해수욕장",
                "category": "해수욕장,해변",
                "score": 0.95,
                "reason": f"{survey_data.activity} 카테고리의 고품질 관광지"
            },
            {
                "place_id": "2", 
                "name": "감천문화마을",
                "category": "테마거리",
                "score": 0.88,
                "reason": f"{survey_data.activity} 카테고리의 대안 관광지"
            }
            # ... 더 많은 추천
        ]
        
        return recommendations
    except Exception as e:
        print(f"추천 생성 오류: {e}")
        return []

# ============ 3. 설문조사 결과 DB 저장 ============

@router.post("/survey/save", response_model=SurveySaveResponse)
async def save_survey_results(request: SurveySaveRequest, user_id=Depends(get_current_user)):
    """3. 설문조사 결과를 DB에 저장 (추후 활용을 위하여)"""
    try:
        # 설문조사 데이터 검증
        if not request.survey_data or not request.votes:
            raise HTTPException(status_code=400, detail="설문조사 데이터와 투표 결과가 필요합니다.")
        
        # DB에 설문조사 결과 저장
        survey_id = await save_to_database(user_id, request.survey_data, request.votes)
        
        return SurveySaveResponse(
            status="success",
            message="설문조사 결과가 성공적으로 저장되었습니다.",
            survey_id=survey_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"설문조사 저장 실패: {str(e)}")

async def save_to_database(user_id: str, survey_data: SurveySubmitRequest, votes: List[VoteData]) -> str:
    """DB에 설문조사 결과 저장"""
    try:
        # 실제로는 MongoDB나 PostgreSQL에 저장
        # 임시로 메모리에 저장 (실제 구현 시 DB로 변경)
        
        survey_document = {
            "user_id": user_id,
            "survey_data": survey_data.dict(),
            "votes": [vote.dict() for vote in votes],
            "created_at": "2024-01-01T00:00:00Z",  # 실제로는 datetime.now()
            "status": "completed"
        }
        
        # TODO: 실제 DB 저장 로직
        # result = await tourism_collection.insert_one(survey_document)
        # return str(result.inserted_id)
        
        # 임시 ID 반환
        return f"survey_{user_id}_{len(votes)}"
    except Exception as e:
        print(f"DB 저장 오류: {e}")
        raise

# ============ 4. ML 모델 기반 추천 ============

@router.get("/survey/recommendations", response_model=MLRecommendationResponse)
async def get_ml_recommendations(user_id=Depends(get_current_user), k: int = 10):
    """4. 사용자 ID를 이용해서 ML 모델을 이용한 추천"""
    try:
        # 사용자의 설문조사 데이터 조회
        survey_data = await get_user_survey_data(user_id)
        if not survey_data:
            raise HTTPException(status_code=404, detail="설문조사 데이터를 찾을 수 없습니다.")
        
        # ML 모델을 사용한 추천
        if IMPORTS_AVAILABLE and ml_recommendation_service:
            recommendations = await ml_recommendation_service.get_recommendations(
                user_id=user_id,
                count=k,
                survey_preferences=survey_data.get('votes', []),
                save_to_logs=True
            )
            
            return MLRecommendationResponse(
                status="success",
                recommendations=recommendations or [],
                model_info={
                    "model_type": "SymmetricResidualCategoryNCF",
                    "total_items": len(recommendations) if recommendations else 0
                }
            )
        else:
            # ML 서비스가 없으면 기본 추천
            basic_recommendations = await generate_basic_recommendations(user_id)
            return MLRecommendationResponse(
                status="success",
                recommendations=basic_recommendations,
                model_info={
                    "model_type": "Basic Recommendation",
                    "total_items": len(basic_recommendations)
                }
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ML 추천 실패: {str(e)}")

async def get_user_survey_data(user_id: str) -> Optional[Dict]:
    """사용자의 설문조사 데이터 조회"""
    try:
        # 실제로는 DB에서 조회
        # survey_data = await tourism_collection.find_one({"user_id": user_id})
        # return survey_data
        
        # 임시 데이터 반환
        return {
            "user_id": user_id,
            "votes": [
                {"round": 1, "choice": "primary", "item_name": "해운대해수욕장"},
                {"round": 2, "choice": "alternative", "item_name": "감천문화마을"}
            ]
        }
    except Exception as e:
        print(f"설문조사 데이터 조회 오류: {e}")
        return None

async def generate_basic_recommendations(user_id: str) -> List[Dict]:
    """기본 추천 생성 (ML 모델이 없을 때)"""
    try:
        # 기본 추천 로직
        recommendations = [
            {
                "place_id": "1",
                "name": "해운대해수욕장",
                "score": 0.95,
                "reason": "인기 관광지"
            },
            {
                "place_id": "2",
                "name": "감천문화마을", 
                "score": 0.88,
                "reason": "문화 관광지"
            }
        ]
        return recommendations
    except Exception as e:
        print(f"기본 추천 생성 오류: {e}")
        return []

# ============ 추가 유틸리티 함수들 ============

@router.delete("/survey/reset")
async def reset_survey_data(user_id=Depends(get_current_user)):
    """설문조사 데이터 초기화"""
    try:
        # 실제로는 DB에서 삭제
        # await tourism_collection.delete_many({"user_id": user_id})
        
        return {"status": "success", "message": "설문조사 데이터가 초기화되었습니다."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"데이터 초기화 실패: {str(e)}")

@router.get("/survey/model-status")
async def get_model_status(user_id=Depends(get_current_user)):
    """ML 모델 상태 확인"""
    status = {
        "imports_available": IMPORTS_AVAILABLE,
        "ml_service_available": ml_recommendation_service is not None if IMPORTS_AVAILABLE else False,
        "current_user": user_id
    }
    
    if IMPORTS_AVAILABLE and ml_recommendation_service and ml_recommendation_service.is_loaded:
        status["model_loaded"] = True
        status["model_type"] = "SymmetricResidualCategoryNCF"
        status["device"] = str(ml_recommendation_service.device)
    else:
        status["model_loaded"] = False
    
    return status
