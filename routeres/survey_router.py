from bson import ObjectId
from fastapi import APIRouter, HTTPException, Depends, Header
from fastapi.responses import HTMLResponse
from typing import List, Optional, Dict
import jwt
import os
import sys
import numpy as np
import json
import random
import uuid
import traceback

# 상위 디렉토리를 Python 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# 안전한 import (실패해도 계속 동작)
try:
    from schemas import (Tourism, CategoryScore, SurveyResponse, SurveySelectionData, 
                        SurveyData, VoteData, LoginData, MLRecommendationResponse, Survey_log)
    from db import places_col
    from services.survey_service import recommend_similar_places_from_survey
    from services.ml_recommendation_service import ml_recommendation_service
    IMPORTS_AVAILABLE = True
    print("✅ 모든 모듈 import 성공")
except ImportError as e:
    print(f"⚠️ 모듈 import 실패: {e}")
    # 기본값으로 대체
    Tourism = None
    CategoryScore = None
    SurveyResponse = None
    SurveySelectionData = None
    SurveyData = None
    VoteData = None
    LoginData = None
    MLRecommendationResponse = None
    places_col = None
    recommend_similar_places_from_survey = None
    ml_recommendation_service = None
    IMPORTS_AVAILABLE = False

router = APIRouter()

# 사용자별 선택 데이터를 저장할 전역 변수 (1.localserver.py와 동일)
user_selections_dict = {}  # {user_id: {activity: ..., activity_level: ...}}
user_votes_dict = {}  # {user_id: [votes...]}
current_user_id = None  # 현재 로그인한 사용자 ID

# 1.localserver.py의 모든 함수들을 백엔드로 이식

def convert_to_schema_format(selections, user_id):
    """사용자 선택을 스키마 형식으로 변환 (1.localserver.py와 동일)"""
    user_id = str(user_id)  # 실제 사용자 ID 사용

    # 활동 카테고리 (문자열로 저장)
    activity = str(selections.get("activity", ""))

    # 활동성 변환: 높음=0, 중간=1, 낮음=2
    activity_level_map = {"높음": 0, "중간": 1, "낮음": 2}
    activity_level = int(activity_level_map.get(selections.get("activity_level"), -1))

    # 시간대 변환: 오전=0, 오후=1, 저녁=2
    time_map = {"오전": 0, "오후": 1, "저녁": 2}
    time = int(time_map.get(selections.get("time"), -1))

    # 계절 변환: 봄=0, 여름=1, 가을=2, 겨울=3
    season_map = {"봄": 0, "여름": 1, "가을": 2, "겨울": 3}
    season = int(season_map.get(selections.get("season"), -1))

    # 선호도 변환: 활동성=0, 시간대=1
    preference_map = {"활동성": 0, "시간대": 1}
    preference = int(preference_map.get(selections.get("preference"), -1))

    return [
        user_id,        # str - 실제 사용자 ID
        activity,       # str
        activity_level, # int (byte 범위)
        time,          # int (byte 범위)
        season,        # int (byte 범위)
        preference     # int (byte 범위)
    ]

def load_tourism_data():
    """관광지 데이터 로드 (1.localserver.py와 동일)"""
    try:
        file_paths = [
            'sort3Wpreference.json',
            os.path.join(parent_dir, 'model', 'sort3Wpreference.json'),
            'C:/Users/user/Desktop/새 폴더 (2)/.vscode/WhereWeGo-backend/model/sort3Wpreference.json'
        ]
        
        for file_path in file_paths:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except FileNotFoundError:
                continue
        
        print("관광지 데이터 파일을 찾을 수 없습니다.")
        return None
    except Exception as e:
        print(f"데이터 로드 오류: {e}")
        return None

def get_category_group_mapping():
    """사용자 선택 카테고리를 데이터 카테고리 그룹으로 매핑 (1.localserver.py와 동일)"""
    return {
        "자연풍경": "자연풍경",
        "자연산림": "자연산림",
        "관람및체험": "관람및체험",
        "휴양": "휴양",
        "테마거리": "테마거리",
        "예술감상": "예술 감상",
        "공연관람": "공연관람",
        "트레킹": "트레킹"
    }

def filter_items_by_preferences(items: List[Dict], user_schema: List) -> List[Dict]:
    """사용자 선호도에 맞는 아이템 필터링 (1.localserver.py와 동일)"""
    user_id, activity, activity_level, time_period, season, preference = user_schema
    
    # 활동성 레벨 매핑 (0: 높음, 1: 중간, 2: 낮음)
    activity_level_map = {0: "high", 1: "medium", 2: "low"}
    activity_level_str = activity_level_map.get(activity_level, "medium")
    
    # DataMaking.py의 카테고리 규칙과 동일한 로직 적용
    category_rules = {
        "자연풍경": {
            "activity_rules": {
                "high": ["해수욕장,해변", "섬", "워터테마파크"],
                "medium": ["전망대", "섬(내륙)"],
                "low": ["방조제", "아쿠아리움"]
            },
            "time_rules": {
                0: ["전망대", "해수욕장,해변", "섬"],  # 아침
                1: ["워터테마파크", "섬(내륙)", "아쿠아리움"],  # 오후
                2: ["전망대", "방조제"]  # 저녁
            },
            "season_rules": {
                0: ["전망대", "섬", "섬(내륙)"],  # 봄
                1: ["전망대", "섬", "해수욕장,해변", "섬(내륙)", "워터테마파크", "방조제", "아쿠아리움"],  # 여름
                2: ["전망대", "섬", "섬(내륙)"],  # 가을
                3: ["전망대", "아쿠아리움"]  # 겨울
            }
        },
        "테마거리": {
            "activity_rules": {
                "high": ["테마거리"],
                "medium": ["먹자골목"],
                "low": ["카페거리"]
            },
            "time_rules": {
                0: ["카페거리"],  # 아침
                1: ["테마거리", "먹자골목"],  # 오후
                2: ["카페거리", "먹자골목"]  # 저녁
            },
            "season_rules": {
                0: ["테마거리", "먹자골목", "카페거리"],  # 봄
                1: ["카페거리"],  # 여름
                2: ["테마거리", "먹자골목", "카페거리"],  # 가을
                3: ["먹자골목", "카페거리"]  # 겨울
            }
        }
    }
    
    # 카테고리 그룹에 맞는 규칙 가져오기
    if activity not in category_rules:
        return items
    
    rule = category_rules[activity]
    
    # 사용자 선호도에 맞는 카테고리들 찾기
    preferred_categories = set()
    
    # 활동성 기준 카테고리
    if activity_level_str in rule["activity_rules"]:
        preferred_categories.update(rule["activity_rules"][activity_level_str])
    
    # 시간대 기준 카테고리
    if time_period in rule["time_rules"]:
        preferred_categories.update(rule["time_rules"][time_period])
    
    # 계절 기준 카테고리
    if season in rule["season_rules"]:
        preferred_categories.update(rule["season_rules"][season])
    
    # 선호 카테고리에 맞는 아이템들 필터링
    filtered_items = []
    for item in items:
        if item.get('category') in preferred_categories:
            filtered_items.append(item)
    
    return filtered_items if filtered_items else items  # 필터링 결과가 없으면 전체 반환

def find_recommended_items(user_schema: List) -> Dict:
    """사용자 스키마를 바탕으로 5라운드 추천 아이템 찾기 (1.localserver.py와 동일)"""
    tourism_data = load_tourism_data()
    if not tourism_data:
        return {"error": "관광지 데이터를 불러올 수 없습니다."}
    
    user_id, activity, activity_level, time_period, season, preference = user_schema
    
    # 카테고리 매핑
    category_mapping = get_category_group_mapping()
    target_category_group = category_mapping.get(activity, activity)
    
    # 해당 카테고리 그룹의 아이템들 찾기
    target_items = []
    other_category_items = []
    
    for group in tourism_data.get('groups', []):
        if group.get('category_group') == target_category_group:
            target_items.extend(group.get('items', []))
        else:
            other_category_items.extend(group.get('items', []))
    
    # 사용자 선호도에 맞는 아이템 필터링
    filtered_target_items = filter_items_by_preferences(target_items, user_schema)
    
    if not filtered_target_items:
        return {"error": f"{activity} 카테고리에서 선호도에 맞는 관광지를 찾을 수 없습니다."}
    
    # final_score 기준으로 정렬
    filtered_target_items.sort(key=lambda x: x.get('final_score', 0), reverse=True)
    other_category_items.sort(key=lambda x: x.get('final_score', 0), reverse=True)
    
    # 사용된 관광지 인덱스 추적
    used_indices = set()
    rounds = []
    
    # 5라운드 생성
    for round_num in range(5):
        # 주 카테고리에서 아이템 선택
        primary_item = None
        for item in filtered_target_items:
            if item['index'] not in used_indices:
                primary_item = item
                used_indices.add(item['index'])
                break
        
        if not primary_item:
            return {"error": f"라운드 {round_num + 1}에서 충분한 주 카테고리 관광지를 찾을 수 없습니다."}
        
        # 비슷한 점수의 다른 카테고리 아이템 찾기
        target_score = primary_item.get('final_score', 0)
        score_tolerance = 0.8
        
        alternative_item = None
        
        # 1단계: 비슷한 점수의 다른 카테고리 아이템 찾기
        similar_items = []
        for item in other_category_items:
            if item['index'] not in used_indices:
                item_score = item.get('final_score', 0)
                if abs(item_score - target_score) <= score_tolerance:
                    similar_items.append(item)
        
        if similar_items:
            # 점수 차이가 가장 적은 아이템 선택
            similar_items.sort(key=lambda x: abs(x.get('final_score', 0) - target_score))
            alternative_item = similar_items[0]
            used_indices.add(alternative_item['index'])
        else:
            # 2단계: 비슷한 점수가 없으면 사용되지 않은 고품질 아이템 선택
            for item in other_category_items:
                if item['index'] not in used_indices:
                    alternative_item = item
                    used_indices.add(item['index'])
                    break
        
        if not alternative_item:
            return {"error": f"라운드 {round_num + 1}에서 충분한 대안 관광지를 찾을 수 없습니다."}
        
        rounds.append({
            "round_number": round_num + 1,
            "primary": {
                "item": primary_item,
                "reason": f"{activity} 카테고리의 고품질 관광지"
            },
            "alternative": {
                "item": alternative_item,
                "reason": f"{alternative_item.get('category_group', '다른')} 카테고리의 유사 만족도 관광지"
            }
        })
    
    return {
        "rounds": rounds,
        "total_rounds": 5,
        "total_places": 10,
        "user_preferences": {
            "activity": activity,
            "activity_level": ["높음", "중간", "낮음"][activity_level],
            "time_period": ["오전", "오후", "저녁"][time_period],
            "season": ["봄", "여름", "가을", "겨울"][season],
            "preference": ["활동성", "시간대"][preference]
        }
    }

def create_vote_schemas(user_id: str):
    """투표 기록을 스키마 형식으로 변환 (1.localserver.py와 동일)"""
    user_votes = user_votes_dict.get(user_id, [])
    user_selections = user_selections_dict.get(user_id, {})
    
    if not user_votes or len(user_votes) < 5:
        return None

    # 기본 사용자 스키마 정보
    base_schema = convert_to_schema_format(user_selections, user_id)
    user_id_val, category_group, activity_level_idx, time_period, season, preference = base_schema
    
    # 추천 데이터에서 선택된 아이템들 찾기
    tourism_data = load_tourism_data()
    if not tourism_data:
        return None

    # 모든 아이템을 인덱스로 매핑 및 전체 아이템 인덱스 수집
    all_items = {}
    all_item_indices = []
    for group in tourism_data.get('groups', []):
        for item in group.get('items', []):
            all_items[item['index']] = item
            all_item_indices.append(item['index'])
    
    vote_schemas = []
    used_negative_items = set()
    
    # 각 투표에 대해 스키마 생성
    for vote in user_votes:
        round_num = vote['round']
        choice = vote['choice']
        
        # 해당 라운드의 추천 데이터에서 positive/negative 아이템 찾기
        recommendations = find_recommended_items(base_schema)
        if "error" in recommendations:
            continue
            
        round_data = recommendations['rounds'][round_num - 1]
        
        if choice == 'primary':
            pos_item = round_data['primary']['item']
            neg_item = round_data['alternative']['item']
        else:
            pos_item = round_data['alternative']['item']
            neg_item = round_data['primary']['item']
        
        pos_item_index = int(pos_item['index'])
        original_neg_item_index = int(neg_item['index'])
        
        # 원본 스키마 생성
        original_schema = [
            str(user_id_val),
            str(category_group),
            int(activity_level_idx),
            int(time_period),
            int(season),
            int(preference),
            pos_item_index,
            original_neg_item_index
        ]
        vote_schemas.append(original_schema)
        
        # 사용된 아이템들을 추적
        used_negative_items.add(pos_item_index)
        used_negative_items.add(original_neg_item_index)
        
        # 추가 랜덤 부정 아이템 2개 생성
        available_negative_items = [idx for idx in all_item_indices 
                                  if idx not in used_negative_items and idx != pos_item_index]
        
        if len(available_negative_items) >= 2:
            random_neg_items = random.sample(available_negative_items, 2)
            
            for random_neg_index in random_neg_items:
                random_schema = [
                    str(user_id_val),
                    str(category_group),
                    int(activity_level_idx),
                    int(time_period),
                    int(season),
                    int(preference),
                    pos_item_index,
                    int(random_neg_index)
                ]
                vote_schemas.append(random_schema)
                used_negative_items.add(random_neg_index)
    
    return vote_schemas

# JWT 토큰에서 사용자 ID 추출하는 함수
def get_current_user_id_from_token(authorization: Optional[str] = Header(None)) -> Optional[str]:
    """JWT 토큰에서 사용자 ID 추출"""
    if not authorization:
        return None

    try:
        token = authorization.split(" ")[1] if authorization.startswith("Bearer ") else authorization
        payload = jwt.decode(token, os.getenv("SECRET_KEY", "your-secret-key"), algorithms=["HS256"])
        return payload.get("user_id")
    except Exception:
        return None

# ============ API 엔드포인트들 (1.localserver.py와 동일한 기능) ============

@router.post("/survey/login")
async def login(login_data: LoginData):
    """사용자 로그인 (1.localserver.py와 동일)"""
    global current_user_id
    current_user_id = login_data.user_id
    
    # 사용자별 데이터 초기화
    if current_user_id not in user_selections_dict:
        user_selections_dict[current_user_id] = {
            "activity": None,
            "activity_level": None,
            "time": None,
            "season": None,
            "preference": None
        }
    
    if current_user_id not in user_votes_dict:
        user_votes_dict[current_user_id] = []
    
    return {
        "status": "success",
        "user_id": current_user_id,
        "message": f"사용자 {current_user_id}로 로그인되었습니다.",
        "next_step": "activity"
    }

@router.get("/survey/logout")
async def logout():
    """사용자 로그아웃 (1.localserver.py와 동일)"""
    global current_user_id
    current_user_id = None
    return {"status": "success", "message": "로그아웃되었습니다."}

@router.get("/survey/current-user")
async def get_current_user():
    """현재 로그인한 사용자 확인 (1.localserver.py와 동일)"""
    return {
        "user_id": current_user_id,
        "logged_in": current_user_id is not None
    }

@router.post("/survey/select")
async def make_selection(selection: SurveySelectionData):
    """사용자 선택 처리 (1.localserver.py와 동일)"""
    global current_user_id
    
    if not current_user_id:
        return {"error": "로그인이 필요합니다.", "redirect": "login"}
    
    # 현재 사용자의 선택 데이터 가져오기
    user_selections = user_selections_dict.get(current_user_id, {})
    
    if selection.step == "activity":
        user_selections["activity"] = selection.value
        user_selections_dict[current_user_id] = user_selections
        return {"next_step": "activity_level", "selections": user_selections, "user_id": current_user_id}
    elif selection.step == "activity_level":
        user_selections["activity_level"] = selection.value
        user_selections_dict[current_user_id] = user_selections
        return {"next_step": "time", "selections": user_selections, "user_id": current_user_id}
    elif selection.step == "time":
        user_selections["time"] = selection.value
        user_selections_dict[current_user_id] = user_selections
        return {"next_step": "season", "selections": user_selections, "user_id": current_user_id}
    elif selection.step == "season":
        user_selections["season"] = selection.value
        user_selections_dict[current_user_id] = user_selections
        return {"next_step": "preference", "selections": user_selections, "user_id": current_user_id}
    elif selection.step == "preference":
        user_selections["preference"] = selection.value
        user_selections_dict[current_user_id] = user_selections
        return {"next_step": "complete", "selections": user_selections, "user_id": current_user_id}

@router.get("/survey/recommendations")
async def get_recommendations():
    """사용자 선택을 바탕으로 관광지 추천 (1.localserver.py와 동일)"""
    if not current_user_id:
        return {"error": "로그인이 필요합니다."}
    
    user_selections = user_selections_dict.get(current_user_id, {})
    
    # 모든 선택이 완료되었는지 확인
    if not all(value is not None for value in user_selections.values()):
        return {
            "status": "incomplete",
            "message": "모든 선택을 완료해주세요.",
            "missing_fields": [key for key, value in user_selections.items() if value is None]
        }
    
    # 스키마 데이터 생성
    schema_data = convert_to_schema_format(user_selections, current_user_id)
    
    # 추천 아이템 찾기
    recommendations = find_recommended_items(schema_data)
    
    if "error" in recommendations:
        return {
            "status": "error",
            "message": recommendations["error"]
        }
    
    return {
        "status": "success",
        "recommendations": recommendations
    }

@router.post("/survey/vote")
async def submit_vote(vote: VoteData):
    """사용자의 선택 결과 저장 (1.localserver.py와 동일)"""
    if not current_user_id:
        return {"error": "로그인이 필요합니다."}
    
    if current_user_id not in user_votes_dict:
        user_votes_dict[current_user_id] = []
    
    user_votes_dict[current_user_id].append({
        "round": vote.round_number,
        "choice": vote.choice,
        "item_name": vote.item_name,
        "timestamp": "현재시간"
    })
    
    return {
        "status": "success",
        "message": f"라운드 {vote.round_number}: {vote.item_name}을(를) 선택했습니다!",
        "round": vote.round_number,
        "choice": vote.choice,
        "total_votes": len(user_votes_dict[current_user_id])
    }

@router.get("/survey/data")
async def get_data():
    """선택된 데이터와 투표 기록을 스키마 형식으로 반환 (1.localserver.py와 동일)"""
    if not current_user_id:
        return {"error": "로그인이 필요합니다."}
    
    user_selections = user_selections_dict.get(current_user_id, {})
    user_votes = user_votes_dict.get(current_user_id, [])
    
    # 모든 선택이 완료되었는지 확인
    if not all(value is not None for value in user_selections.values()):
        return {
            "status": "incomplete",
            "message": "모든 선택을 완료해주세요.",
            "current_selections": user_selections,
            "missing_fields": [key for key, value in user_selections.items() if value is None]
        }
    
    # 기본 사용자 스키마
    base_schema = convert_to_schema_format(user_selections, current_user_id)
    
    # 투표 기록이 있으면 스키마로 변환
    vote_schemas = create_vote_schemas(current_user_id) if len(user_votes) == 5 else None
    
    return {
        "status": "complete",
        "base_schema": base_schema,
        "vote_schemas": vote_schemas,
        "total_votes": len(user_votes),
        "raw_selections": user_selections,
        "raw_votes": user_votes
    }

@router.get("/survey/logs")
async def get_survey_logs():
    """사용자의 설문조사 로그 조회 (8요소 구조화된 형태)"""
    if not current_user_id:
        return {"error": "로그인이 필요합니다."}
    
    try:
        if IMPORTS_AVAILABLE and ml_recommendation_service:
            survey_logs = await ml_recommendation_service.get_survey_logs(current_user_id)
            return {
                "status": "success",
                "user_id": current_user_id,
                "survey_logs": survey_logs,
                "total_logs": len(survey_logs),
                "message": f"사용자 {current_user_id}의 설문조사 로그 {len(survey_logs)}개를 조회했습니다."
            }
        else:
            return {
                "status": "error", 
                "message": "ML 추천 서비스가 사용할 수 없습니다."
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"설문조사 로그 조회 실패: {str(e)}"
        }

@router.get("/survey/ml-recommendations")
async def get_ml_recommendations(k: int = 10):
    """ML 모델을 사용한 개인화된 추천 (1.localserver.py와 동일)"""
    if not current_user_id:
        return {"error": "로그인이 필요합니다."}
    
    user_votes = user_votes_dict.get(current_user_id, [])
    user_selections = user_selections_dict.get(current_user_id, {})
    
    # 5라운드 투표가 완료되었는지 확인
    if len(user_votes) < 5:
        return {
            "status": "incomplete",
            "message": "5라운드 심화 설문조사를 먼저 완료해주세요.",
            "current_votes": len(user_votes),
            "required_votes": 5
        }
    
    # 투표 스키마가 생성되었는지 확인
    vote_schemas = create_vote_schemas(current_user_id)
    if not vote_schemas:
        return {
            "status": "error",
            "message": "투표 스키마를 생성할 수 없습니다."
        }
    
    print(f"🎯 ML 추천 요청 - 사용자 투표: {len(user_votes)}개, 스키마: {len(vote_schemas)}개")
    
    # ML 모델을 사용한 추천 수행
    try:
        # vote_schemas를 survey_preferences 형식으로 변환
        survey_dict = []
        for schema in vote_schemas:
            if len(schema) >= 8:
                survey_dict.append({
                    "user_id": schema[0],
                    "category_group": schema[1],
                    "activity_level_idx": schema[2],
                    "time_period": schema[3],
                    "season": schema[4],
                    "preference": schema[5],
                    "pos_item_index": schema[6],
                    "neg_item_index": schema[7]
                })
        
        # ML 추천 서비스 호출
        if IMPORTS_AVAILABLE and ml_recommendation_service:
            ml_result = await ml_recommendation_service.get_recommendations(
                user_id=current_user_id,
                count=k,
                survey_preferences=survey_dict,
                save_to_logs=True
            )
            
            if ml_result:
                # 기본 설문조사 정보도 포함
                base_schema = convert_to_schema_format(user_selections, current_user_id)
                
                return {
                    "status": "success",
                    "ml_recommendations": {
                        "recommendations": ml_result,
                        "model_used": "SymmetricResidualCategoryNCF (Context-Aware)",
                        "total_items_scored": len(ml_result)
                    },
                    "base_user_info": {
                        "user_id": base_schema[0],
                        "preferred_category": base_schema[1],
                        "activity_level": ["높음", "중간", "낮음"][base_schema[2]] if base_schema[2] in [0, 1, 2] else "알 수 없음",
                        "preferred_time": ["오전", "오후", "저녁"][base_schema[3]] if base_schema[3] in [0, 1, 2] else "알 수 없음",
                        "preferred_season": ["봄", "여름", "가을", "겨울"][base_schema[4]] if base_schema[4] in [0, 1, 2, 3] else "알 수 없음",
                        "preference_type": ["활동성", "시간대"][base_schema[5]] if base_schema[5] in [0, 1] else "알 수 없음"
                    },
                    "vote_summary": {
                        "total_votes": len(user_votes),
                        "vote_schemas_generated": len(vote_schemas),
                        "selected_items": [schema[6] for schema in vote_schemas[:5]]  # 첫 5개 라운드의 positive items
                    },
                    "personalization_info": {
                        "model_type": "Neural Collaborative Filtering (NCF)",
                        "training_data": "부산 관광지 사용자 상호작용 데이터",
                        "recommendation_basis": "사용자의 선택 패턴과 유사한 사용자들의 선호도"
                    }
                }
        
        # ML 서비스가 없거나 실패한 경우 기본 추천으로 폴백
        base_schema = convert_to_schema_format(user_selections, current_user_id)
        basic_recommendations = find_recommended_items(base_schema)
        
        if "error" not in basic_recommendations:
            return {
                "status": "success",
                "message": "ML 모델이 없어 기본 설문조사 기반 추천을 제공합니다.",
                "recommendations": basic_recommendations,
                "method": "basic_survey"
            }
        else:
            return {
                "status": "error",
                "message": f"추천 생성 실패: {basic_recommendations.get('error', '알 수 없는 오류')}"
            }

    except Exception as e:
        print(f"❌ ML 추천 오류: {e}")
        traceback.print_exc()
        return {
            "status": "error",
            "message": f"ML 추천 중 오류가 발생했습니다: {str(e)}"
        }

@router.get("/survey/reset")
async def reset_selections():
    """선택 초기화 (투표 기록은 유지) (1.localserver.py와 동일)"""
    if not current_user_id:
        return {"error": "로그인이 필요합니다."}
    
    user_selections_dict[current_user_id] = {
        "activity": None,
        "activity_level": None,
        "time": None,
        "season": None,
        "preference": None
    }
    return {"message": "선택이 초기화되었습니다. (투표 기록은 유지됨)"}

@router.get("/survey/reset-all")
async def reset_all():
    """모든 데이터 초기화 (투표 기록 포함) (1.localserver.py와 동일)"""
    if not current_user_id:
        return {"error": "로그인이 필요합니다."}
    
    user_selections_dict[current_user_id] = {
        "activity": None,
        "activity_level": None,
        "time": None,
        "season": None,
        "preference": None
    }
    user_votes_dict[current_user_id] = []
    return {"message": "모든 데이터가 초기화되었습니다."}

@router.get("/survey/model-status")
async def get_model_status():
    """ML 모델 상태 확인 (1.localserver.py와 동일)"""
    status = {
        "imports_available": IMPORTS_AVAILABLE,
        "ml_service_available": ml_recommendation_service is not None,
        "current_user": current_user_id
    }
    
    if IMPORTS_AVAILABLE and ml_recommendation_service and ml_recommendation_service.is_loaded:
        status["model_loaded"] = True
        status["model_type"] = "SymmetricResidualCategoryNCF"
        status["device"] = str(ml_recommendation_service.device)
    else:
        status["model_loaded"] = False
    
    return status

@router.post("/survey/load-model")
async def load_model_endpoint():
    """ML 모델 수동 로딩 (1.localserver.py와 동일)"""
    if not IMPORTS_AVAILABLE or not ml_recommendation_service:
        return {
            "status": "error",
            "message": "ML 서비스를 사용할 수 없습니다."
        }
    
    success = await ml_recommendation_service.load_model()
    
    if success:
        return {
            "status": "success",
            "message": "ML 모델이 성공적으로 로드되었습니다.",
            "model_info": await get_model_status()
        }
    else:
        return {
            "status": "error",
            "message": "ML 모델 로딩에 실패했습니다."
        }
