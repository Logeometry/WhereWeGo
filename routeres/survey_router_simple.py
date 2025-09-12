# routeres/survey_router_simple.py
"""
단순화된 설문조사 라우터
4단계로 구성된 효율적인 설문조사 시스템
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from typing import List, Optional, Dict
from pydantic import BaseModel
import os
import sys
from datetime import datetime

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
    from db import user_log_col  # user_log 컬렉션 import
    # 5라운드 추천 로직 import
    from routeres.survey_router import (
        convert_to_schema_format,
        find_recommended_items,
        load_tourism_data,
        get_category_group_mapping,
        filter_items_by_preferences
    )
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

class SurveyStatusResponse(BaseModel):
    """설문조사 상태 응답"""
    user_id: str
    logged_in: bool
    has_survey_data: bool
    has_votes: bool
    status: str

class SurveySubmitResponse(BaseModel):
    """설문조사 제출 응답"""
    status: str
    message: str
    survey_id: str

class VoteData(BaseModel):
    """개별 투표 데이터"""
    round: int
    choice: str  # "primary" 또는 "alternative"
    item_name: str

class VoteSubmitRequest(BaseModel):
    """투표 제출 요청"""
    votes: List[VoteData]

class VoteSubmitResponse(BaseModel):
    """투표 제출 응답"""
    status: str
    message: str
    vote_id: str

class PlaceRecommendationResponse(BaseModel):
    """장소 추천 응답"""
    status: str
    recommendations: List[Dict]
    message: str

class MLRecommendationResponse(BaseModel):
    """ML 추천 응답"""
    status: str
    recommendations: List[Dict]
    total_count: int
    model_info: Dict
    message: str

# ============ 1. 로그인 인증 확인 ============

@router.get("/survey/status", response_model=SurveyStatusResponse)
async def get_survey_status(user_id=Depends(get_current_user)):
    """1. 로그인 인증 확인 및 설문조사 상태 조회"""
    try:
        # 설문조사 데이터 확인 (DB에서 확인)
        has_survey_data = await check_survey_data_exists(user_id)
        has_votes = await check_votes_exist(user_id)
        
        return SurveyStatusResponse(
            user_id=user_id,
            logged_in=True,
            has_survey_data=has_survey_data,
            has_votes=has_votes,
            status="success"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"상태 조회 실패: {str(e)}")

async def check_survey_data_exists(user_id: str) -> bool:
    """사용자의 설문조사 데이터 존재 여부 확인 (JWT 토큰 기반 보안)"""
    try:
        if not IMPORTS_AVAILABLE or user_log_col is None:
            return False
            
        # JWT 토큰으로 인증된 사용자만 접근 가능
        result = await user_log_col.find_one({
            "user_id": user_id, 
            "type": "survey",
            "status": "completed"
        })
        return result is not None
    except Exception as e:
        print(f"설문조사 데이터 존재 확인 오류: {e}")
        return False

async def check_votes_exist(user_id: str) -> bool:
    """사용자의 투표 데이터 존재 여부 확인 (JWT 토큰 기반 보안)"""
    try:
        if not IMPORTS_AVAILABLE or user_log_col is None:
            return False
            
        # JWT 토큰으로 인증된 사용자만 접근 가능
        result = await user_log_col.find_one({
            "user_id": user_id, 
            "type": "votes",
            "status": "completed"
        })
        return result is not None
    except Exception as e:
        print(f"투표 데이터 존재 확인 오류: {e}")
        return False

# ============ 2. 설문조사 데이터 저장 (기존 로직 활용) ============

@router.post("/survey/submit", response_model=SurveySubmitResponse)
async def submit_survey(request: Request, user_id=Depends(get_current_user)):
    """2. 설문조사 데이터를 user_log에 저장 (JWT 토큰 기반 보안)"""
    try:
        print(f"[DEBUG] ===== 설문조사 제출 함수 호출됨 =====")
        print(f"[DEBUG] user_id: {user_id}")
        
        # Request body 직접 읽기
        body = await request.body()
        print(f"[DEBUG] 원본 요청 본문 (바이트): {body}")
        print(f"[DEBUG] 원본 요청 본문 (문자열): {body.decode('utf-8')}")
        
        # JSON 파싱
        import json
        try:
            data = json.loads(body.decode('utf-8'))
            print(f"[DEBUG] 받은 데이터: {data}")
        except json.JSONDecodeError as e:
            print(f"[DEBUG] JSON 파싱 오류: {e}")
            raise HTTPException(status_code=400, detail=f"잘못된 JSON 형식: {str(e)}")
        
        # 설문조사 데이터 검증
        required_fields = ['activity', 'activity_level', 'time', 'season', 'preference']
        for field in required_fields:
            if not data.get(field):
                raise HTTPException(status_code=400, detail=f"{field} 필드가 필요합니다.")
        
        if not IMPORTS_AVAILABLE or user_log_col is None:
            raise HTTPException(status_code=500, detail="데이터베이스 연결을 사용할 수 없습니다.")
        
        # 기존 설문조사 데이터가 있는지 확인
        existing_survey = await user_log_col.find_one({
            "user_id": user_id,
            "type": "survey"
        })
        
        # 설문조사 데이터를 user_log에 저장
        survey_log = {
            "user_id": user_id,  # JWT 토큰에서 검증된 사용자 ID
            "type": "survey",
            "data": data,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "status": "completed"
        }
        
        if existing_survey:
            # 기존 데이터 업데이트
            result = await user_log_col.update_one(
                {"user_id": user_id, "type": "survey"},
                {"$set": survey_log}
            )
            survey_id = str(existing_survey.get("_id", ""))
        else:
            # 새 데이터 삽입
            result = await user_log_col.insert_one(survey_log)
            survey_id = str(result.inserted_id)
        
        if not result:
            raise HTTPException(status_code=500, detail="데이터베이스 저장에 실패했습니다.")
        
        return SurveySubmitResponse(
            status="success",
            message="설문조사 데이터가 성공적으로 저장되었습니다.",
            survey_id=survey_id
        )
    except Exception as e:
        print(f"설문조사 저장 오류: {e}")
        raise HTTPException(status_code=500, detail=f"설문조사 저장 실패: {str(e)}")

@router.post("/survey/votes", response_model=VoteSubmitResponse)
async def submit_votes(request: Request, user_id=Depends(get_current_user)):
    """투표 데이터를 user_log에 저장 (JWT 토큰 기반 보안)"""
    try:
        # Raw request body 확인
        try:
            body = await request.json()
            print(f"[DEBUG] Raw request body: {body}")
            print(f"[DEBUG] Body type: {type(body)}")
        except Exception as json_error:
            print(f"[DEBUG] JSON 파싱 에러: {json_error}")
            print(f"[DEBUG] Request content type: {request.headers.get('content-type')}")
            print(f"[DEBUG] Request body raw: {await request.body()}")
            raise HTTPException(status_code=400, detail=f"JSON 파싱 에러: {str(json_error)}")
        
        # 수동으로 데이터 파싱
        if "votes" not in body:
            raise HTTPException(status_code=400, detail="votes 필드가 없습니다.")
        
        votes_data = body["votes"]
        print(f"[DEBUG] Votes data: {votes_data}")
        print(f"[DEBUG] Votes type: {type(votes_data)}")
        
        # 투표 데이터 검증
        if not votes_data or len(votes_data) == 0:
            raise HTTPException(status_code=400, detail="투표 데이터를 입력해주세요.")
        
        if not IMPORTS_AVAILABLE or user_log_col is None:
            raise HTTPException(status_code=500, detail="데이터베이스 연결을 사용할 수 없습니다.")
        
        # 기존 투표 데이터가 있는지 확인
        existing_votes = await user_log_col.find_one({
            "user_id": user_id,
            "type": "votes"
        })
        
        # 투표 데이터를 user_log에 저장
        vote_log = {
            "user_id": user_id,  # JWT 토큰에서 검증된 사용자 ID
            "type": "votes",
            "data": votes_data,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "status": "completed",
            "total_votes": len(votes_data)
        }
        
        if existing_votes:
            # 기존 데이터 업데이트
            result = await user_log_col.update_one(
                {"user_id": user_id, "type": "votes"},
                {"$set": vote_log}
            )
            vote_id = str(existing_votes.get("_id", ""))
        else:
            # 새 데이터 삽입
            result = await user_log_col.insert_one(vote_log)
            vote_id = str(result.inserted_id)
        
        if not result:
            raise HTTPException(status_code=500, detail="데이터베이스 저장에 실패했습니다.")
        
        return VoteSubmitResponse(
            status="success",
            message="투표 데이터가 성공적으로 저장되었습니다.",
            vote_id=vote_id
        )
    except Exception as e:
        print(f"투표 저장 오류: {e}")
        raise HTTPException(status_code=500, detail=f"투표 저장 실패: {str(e)}")

# ============ 3. 설문조사 장소 추천 ============

@router.get("/survey/place-recommendations", response_model=PlaceRecommendationResponse)
async def get_survey_place_recommendations(user_id=Depends(get_current_user)):
    """3. 설문조사를 위한 장소 추천"""
    try:
        # 사용자의 설문조사 데이터 조회
        survey_data = await get_user_survey_data(user_id)
        if not survey_data:
            raise HTTPException(status_code=404, detail="설문조사 데이터를 찾을 수 없습니다.")
        
        # 기존 recommend_location.py의 로직 활용
        # TODO: recommend_location.py의 get_place_recommendations 함수 호출
        recommendations = await generate_survey_place_recommendations(survey_data)
        
        return PlaceRecommendationResponse(
            status="success",
            recommendations=recommendations,
            message="설문조사용 장소 추천이 완료되었습니다."
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"장소 추천 실패: {str(e)}")

async def get_user_survey_data(user_id: str) -> dict:
    """사용자의 설문조사 데이터 조회 (JWT 토큰 기반 보안)"""
    try:
        if not IMPORTS_AVAILABLE or user_log_col is None:
            print("DB 연결을 사용할 수 없습니다.")
            return {}
        
        # JWT 토큰으로 인증된 사용자만 자신의 데이터에 접근 가능
        result = await user_log_col.find_one({
            "user_id": user_id, 
            "type": "survey",
            "status": "completed"
        })
        
        if result and "data" in result:
            return result["data"]
        else:
            print(f"사용자 {user_id}의 설문조사 데이터를 찾을 수 없습니다.")
            return {}
            
    except Exception as e:
        print(f"설문조사 데이터 조회 오류: {e}")
        return {}

async def generate_survey_place_recommendations(survey_data: dict) -> list:
    """설문조사 기반 장소 추천 생성 (5라운드 추천 로직 활용)"""
    try:
        print(f"[DEBUG] 설문조사 데이터: {survey_data}")
        
        # 설문조사 데이터를 스키마 형식으로 변환
        user_schema = convert_to_schema_format(survey_data, "temp_user_id")
        print(f"[DEBUG] 변환된 스키마: {user_schema}")
        
        # 5라운드 추천 아이템 찾기
        recommendations_result = find_recommended_items(user_schema)
        
        if "error" in recommendations_result:
            print(f"추천 생성 오류: {recommendations_result['error']}")
            return []
        
        # 5라운드 추천 데이터를 프론트엔드 호환 형식으로 변환
        rounds = recommendations_result.get("rounds", [])
        recommendations = []
        
        for round_data in rounds:
            # 주 카테고리 아이템
            primary_item = round_data.get("primary", {}).get("item", {})
            # 대안 카테고리 아이템
            alternative_item = round_data.get("alternative", {}).get("item", {})
            
            if primary_item and alternative_item:
                recommendations.append({
                    "primary": {
                        "name": primary_item.get("name", ""),
                        "address": primary_item.get("address", "주소 정보 없음"),
                        "category": primary_item.get("category", ""),
                        "score": primary_item.get("final_score", 0.0),
                        "reason": round_data.get("primary", {}).get("reason", "")
                    },
                    "alternative": {
                        "name": alternative_item.get("name", ""),
                        "address": alternative_item.get("address", "주소 정보 없음"),
                        "category": alternative_item.get("category", ""),
                        "score": alternative_item.get("final_score", 0.0),
                        "reason": round_data.get("alternative", {}).get("reason", "")
                    },
                    "round_number": round_data.get("round_number", 0)
                })
        
        return recommendations
    except Exception as e:
        print(f"장소 추천 생성 오류: {e}")
        return []

# ============ 4. ML 모델 기반 추천 (20곳 추천) ============

@router.get("/survey/ml-recommendations", response_model=MLRecommendationResponse)
async def get_ml_recommendations(user_id=Depends(get_current_user)):
    """4. ML 모델에 설문조사 결과를 input으로 받아서 장소 추천 (20곳)"""
    try:
        # 사용자의 설문조사 데이터 조회
        survey_data = await get_user_survey_data(user_id)
        if not survey_data:
            raise HTTPException(status_code=404, detail="설문조사 데이터를 찾을 수 없습니다.")
        
        # 사용자의 투표 데이터 조회
        vote_data = await get_user_vote_data(user_id)
        
        # ML 모델을 사용한 추천 (20곳)
        if IMPORTS_AVAILABLE and ml_recommendation_service:
            # 설문조사 데이터와 투표 데이터를 ML 모델 형식으로 변환
            survey_preferences = convert_survey_to_ml_format(survey_data, vote_data)
            
            recommendations = await ml_recommendation_service.get_recommendations(
                user_id=user_id,
                count=20,  # 20곳 추천
                survey_preferences=survey_preferences,
                save_to_logs=True
            )
            
            return MLRecommendationResponse(
                status="success",
                recommendations=recommendations or [],
                total_count=len(recommendations) if recommendations else 0,
                model_info={
                    "model_type": "SymmetricResidualCategoryNCF",
                    "input_type": "survey_data",
                    "recommendation_count": 20
                },
                message="ML 모델 기반 추천이 완료되었습니다."
            )
        else:
            # ML 서비스가 없으면 기본 추천
            basic_recommendations = await generate_basic_recommendations(20)
            return MLRecommendationResponse(
                status="success",
                recommendations=basic_recommendations,
                total_count=len(basic_recommendations),
                model_info={
                    "model_type": "Basic Recommendation",
                    "input_type": "survey_data",
                    "recommendation_count": 20
                },
                message="기본 추천이 완료되었습니다."
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ML 추천 실패: {str(e)}")

async def get_user_vote_data(user_id: str) -> list:
    """사용자의 투표 데이터 조회 (JWT 토큰 기반 보안)"""
    try:
        if not IMPORTS_AVAILABLE or user_log_col is None:
            print("DB 연결을 사용할 수 없습니다.")
            return []
        
        # JWT 토큰으로 인증된 사용자만 자신의 데이터에 접근 가능
        result = await user_log_col.find_one({
            "user_id": user_id, 
            "type": "votes",
            "status": "completed"
        })
        
        if result and "data" in result:
            return result["data"]
        else:
            print(f"사용자 {user_id}의 투표 데이터를 찾을 수 없습니다.")
            return []
            
    except Exception as e:
        print(f"투표 데이터 조회 오류: {e}")
        return []

def convert_survey_to_ml_format(survey_data: dict, vote_data: list = None) -> list:
    """설문조사 데이터와 투표 데이터를 ML 모델 형식으로 변환"""
    try:
        # 설문조사 데이터를 ML 모델이 이해할 수 있는 형식으로 변환
        # TODO: 실제 변환 로직 구현 (기존 convert_to_schema_format 활용)
        user_schema = convert_to_schema_format(survey_data, "temp_user")
        
        # 투표 데이터가 있으면 추가 변환
        if vote_data and len(vote_data) >= 5:
            # TODO: 투표 데이터를 ML 모델 형식으로 변환
            return [{
                "user_id": user_schema[0],
                "category_group": user_schema[1],
                "activity_level_idx": user_schema[2],
                "time_period": user_schema[3],
                "season": user_schema[4],
                "preference": user_schema[5],
                "pos_item_index": 1,      # TODO: 투표 데이터에서 추출
                "neg_item_index": 2       # TODO: 투표 데이터에서 추출
            }]
        else:
            # 투표 데이터가 없으면 기본 설문조사 데이터만 사용
            return [{
                "user_id": user_schema[0],
                "category_group": user_schema[1],
                "activity_level_idx": user_schema[2],
                "time_period": user_schema[3],
                "season": user_schema[4],
                "preference": user_schema[5],
                "pos_item_index": 1,
                "neg_item_index": 2
            }]
    except Exception as e:
        print(f"ML 형식 변환 오류: {e}")
        return []

async def generate_basic_recommendations(count: int) -> list:
    """기본 추천 생성 (ML 모델이 없을 때)"""
    try:
        # 기본 추천 로직
        recommendations = []
        for i in range(count):
            recommendations.append({
                "place_id": str(i + 1),
                "name": f"추천 장소 {i + 1}",
                "score": 0.9 - (i * 0.01),
                "reason": f"기본 추천 장소 {i + 1}"
            })
        return recommendations
    except Exception as e:
        print(f"기본 추천 생성 오류: {e}")
        return []

# ============ 추가 유틸리티 라우터들 ============

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

@router.delete("/survey/reset")
async def reset_survey_data(user_id=Depends(get_current_user)):
    """설문조사 데이터 초기화 (JWT 토큰 기반 보안)"""
    try:
        if not IMPORTS_AVAILABLE or user_log_col is None:
            raise HTTPException(status_code=500, detail="데이터베이스 연결을 사용할 수 없습니다.")
        
        # JWT 토큰으로 인증된 사용자만 자신의 데이터를 삭제할 수 있음
        result = await user_log_col.delete_many({
            "user_id": user_id,
            "type": {"$in": ["survey", "votes"]}
        })
        
        return {
            "status": "success", 
            "message": f"설문조사 데이터가 초기화되었습니다. (삭제된 문서: {result.deleted_count}개)",
            "deleted_count": result.deleted_count
        }
    except Exception as e:
        print(f"데이터 초기화 오류: {e}")
        raise HTTPException(status_code=500, detail=f"데이터 초기화 실패: {str(e)}")

# ============ 파일 끝 ============
