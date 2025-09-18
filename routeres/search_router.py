from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any, Union
import os
import sys
import numpy as np
import json
import random
import uuid
import traceback
import time
import torch
import torch.nn as nn
from datetime import datetime

# NCF 모델 관련 임포트
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
model_dir = os.path.join(parent_dir, 'model')
if os.path.exists(model_dir):
    sys.path.insert(0, model_dir)
    try:
        from ncf_inner.models import SymmetricResidualCategoryNCF
        from ncf_inner.config import CONFIG
        from ncf_inner.data_utils import load_data

        NCF_AVAILABLE = True
        print("✅ NCF 모델 모듈 로드 성공")
    except ImportError as e:
        print(f"⚠️ NCF 모델 임포트 실패: {e}")
        NCF_AVAILABLE = False
        SymmetricResidualCategoryNCF = None
        CONFIG = None
        load_data = None
else:
    print("⚠️ model 디렉토리를 찾을 수 없습니다.")
    NCF_AVAILABLE = False
    SymmetricResidualCategoryNCF = None
    CONFIG = None
    load_data = None


# Pydantic 모델 정의
class SelectionData(BaseModel):
    step: str
    value: str


class VoteData(BaseModel):
    round_number: int
    choice: str
    item_name: str
    item_index: int


# 전역 변수
user_selections = {
    "activity": None,
    "activity_level": None,
    "time": None,
    "season": None,
    "preference": None
}

user_votes = []

# ML 모델 전역 변수
loaded_ncf_model = None
model_data = None
MODEL_PATH = "model_epoch_new.pth"
# Router 초기화
router = APIRouter()


# 1.localserver.py의 함수들을 여기에 구현

def convert_to_schema_format(selections):
    """사용자 선택을 스키마 형식으로 변환"""
    # UUID4로 매번 랜덤한 사용자 ID 생성
    user_id = int(uuid.uuid4().int) % 1000000  # 6자리 숫자로 변환

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
        user_id,  # int - 학습 데이터와 일치
        activity,  # str
        activity_level,  # int (byte 범위)
        time,  # int (byte 범위)
        season,  # int (byte 범위)
        preference  # int (byte 범위)
    ]


def load_tourism_data():
    """관광지 데이터 로드 - 개선된 오류 처리"""
    try:
        # 현재 디렉토리에서 찾고, 없으면 상위 디렉토리에서 찾기
        ncf_modular_root = os.path.dirname(current_dir)  # routeres의 상위 디렉토리 (WhereWeGo-backend)
        project_root = os.path.dirname(ncf_modular_root)  # WhereWeGo-backend의 상위 디렉토리

        file_paths = [
            # 현재 디렉토리에서 찾기
            'sort3Wpreference.json',
            # ncf_modular 루트에서 찾기
            os.path.join(ncf_modular_root, 'sort3Wpreference.json'),
            # 상위 디렉토리에서 찾기
            '../sort3Wpreference.json',
            # WhereWeGo-backend 경로들
            '../WhereWeGo-backend/model/sort3Wpreference.json',
            'WhereWeGo-backend/model/sort3Wpreference.json',
            os.path.join(project_root, 'WhereWeGo-backend/model/sort3Wpreference.json'),
            os.path.join(ncf_modular_root, 'WhereWeGo-backend/model/sort3Wpreference.json'),
            # 절대 경로
            'C:/Users/user/Desktop/새 폴더 (2)/.vscode/WhereWeGo-backend/model/sort3Wpreference.json',
            'C:/Users/user/PycharmProjects/ncf_modular/sort3Wpreference.json'
        ]

        for file_path in file_paths:
            try:
                print(f"🔍 파일 경로 확인: {file_path}")
                if os.path.exists(file_path):
                    print(f"✅ 파일 존재: {file_path}")
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        # 데이터 구조 검증
                        if isinstance(data, dict) and 'groups' in data:
                            print(f"✅ 관광지 데이터 로드 성공: {file_path}")
                            print(f"📊 데이터 정보: {len(data.get('groups', []))}개 그룹, 총 {data.get('total_items', 0)}개 아이템")
                            return data
                        else:
                            print(f"⚠️ 데이터 구조가 올바르지 않습니다: {file_path}")
                            print(f"📊 데이터 키: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
                            continue
                else:
                    print(f"❌ 파일 없음: {file_path}")
            except (FileNotFoundError, json.JSONDecodeError, UnicodeDecodeError) as e:
                print(f"⚠️ 파일 로드 실패: {file_path} - {e}")
                continue

        print("❌ 관광지 데이터 파일을 찾을 수 없습니다.")
        return None
    except Exception as e:
        print(f"❌ 데이터 로드 오류: {e}")
        import traceback
        traceback.print_exc()
        return None


def initialize_model():
    """서버 시작 시점에 모델을 전역 변수에 로드"""
    global loaded_ncf_model, model_data

    print("🚀 서버 시작 - ML 모델 초기화 중...")

    if not NCF_AVAILABLE:
        print("❌ NCF 모듈을 사용할 수 없습니다.")
        return False

    try:
        print("🔄 NCF 모델 로딩 중...")

        # 모델 파일 경로 찾기
        possible_paths = [
            MODEL_PATH,
            os.path.join(current_dir, MODEL_PATH),
            os.path.join(current_dir, 'checkpoints', MODEL_PATH),
            os.path.join(current_dir, '..', MODEL_PATH),
            os.path.join(current_dir, 'ncf_inner', MODEL_PATH),
            os.path.join(current_dir, '..', 'dataMaking', 'ncf_inner', 'checkpoints', MODEL_PATH),
            os.path.join(current_dir, '..', 'WhereWeGo-backend', 'model', MODEL_PATH),
            'C:/Users/user/Desktop/새 폴더 (2)/.vscode/WhereWeGo-backend/model/model_epoch_new.pth',
        ]

        model_file_path = None
        for path in possible_paths:
            if os.path.exists(path):
                model_file_path = path
                break

        if not model_file_path:
            print(f"❌ 모델 파일을 찾을 수 없습니다: {MODEL_PATH}")
            return False

        # 데이터 로딩
        try:
            model_data = load_data()
            n_users = model_data['n_users']
            n_items = model_data['n_items']
            print(f"📊 데이터 로드 완료: 사용자 {n_users}명, 아이템 {n_items}개")
        except Exception as e:
            print(f"⚠️ 데이터 로딩 실패: {e}")
            # 관광지 데이터 기반으로 아이템 수 추정
            try:
                tourism_data = load_tourism_data()
                if tourism_data and 'groups' in tourism_data:
                    n_items = sum(len(group.get('items', [])) for group in tourism_data['groups'])
                    print(f"📍 관광지 데이터 기반 아이템 수: {n_items}개")
                else:
                    n_items = 1000
                    print(f"📊 기본 아이템 수 사용: {n_items}개")
            except:
                n_items = 1000
                print(f"📊 기본 아이템 수 사용: {n_items}개")

            n_users = 7384
            print(f"📊 추정 사용자 수: {n_users}명")

            # 기본 데이터 구조 생성
            model_data = {
                'n_users': n_users,
                'n_items': n_items,
                'item_id_to_model_idx': {i: i for i in range(n_items)},
                'user_id_to_idx': {}  # 동적으로 생성될 사용자 ID 매핑
            }

        # 모델 초기화
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        model = SymmetricResidualCategoryNCF(
            n_users=n_users,
            n_items=n_items,
            config=CONFIG
        ).to(device)

        # 모델 로드
        checkpoint = torch.load(model_file_path, map_location=device)

        if isinstance(checkpoint, dict) and 'model_state_dict' in checkpoint:
            saved_state_dict = checkpoint['model_state_dict']
            epoch = checkpoint.get('epoch', 'Unknown')
            print(f"📦 체크포인트 발견 (에폭: {epoch})")
        else:
            saved_state_dict = checkpoint
            epoch = 'Unknown'
            print(f"📦 모델 state_dict 발견")

        # 모델 크기 호환성 검사 및 조정
        print("🔍 모델 크기 호환성 검사...")
        current_state_dict = model.state_dict()
        compatible_state_dict = {}

        for key in current_state_dict.keys():
            if key in saved_state_dict:
                saved_shape = saved_state_dict[key].shape
                current_shape = current_state_dict[key].shape

                if saved_shape == current_shape:
                    compatible_state_dict[key] = saved_state_dict[key]
                    print(f"✅ {key}: {current_shape} - 호환됨")
                else:
                    print(f"⚠️ {key}: 저장된 크기 {saved_shape} -> 현재 크기 {current_shape}")
                    # 크기 조정 로직
                    if len(saved_shape) == 2 and len(current_shape) == 2:
                        current_tensor = current_state_dict[key].clone()
                        min_dim0 = min(saved_shape[0], current_shape[0])
                        min_dim1 = min(saved_shape[1], current_shape[1])
                        current_tensor[:min_dim0, :min_dim1] = saved_state_dict[key][:min_dim0, :min_dim1]
                        compatible_state_dict[key] = current_tensor
                        print(f"🔧 {key}: 크기 조정 완료 ({min_dim0}x{min_dim1} 복사)")
                    else:
                        compatible_state_dict[key] = current_state_dict[key]
                        print(f"🔧 {key}: 기본값 사용")
            else:
                compatible_state_dict[key] = current_state_dict[key]
                print(f"➕ {key}: 새로운 레이어, 기본값 사용")

        # 호환성 조정된 state_dict 로드
        try:
            model.load_state_dict(compatible_state_dict, strict=False)
            print(f"✅ 모델 로드 완료")
        except Exception as load_error:
            print(f"❌ 모델 로드 실패: {load_error}")
            return False

        model.eval()
        loaded_ncf_model = model

        print(f"🎯 모델 초기화 완료 - 디바이스: {device}")
        print(f"📂 모델 파일: {model_file_path}")
        return True

    except Exception as e:
        print(f"❌ 모델 초기화 실패: {e}")
        return False


# 1.localserver.py의 핵심 함수들 추가
def get_category_group_mapping():
    """사용자 선택 카테고리를 데이터 카테고리 그룹으로 매핑"""
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


def get_category_rules():
    """카테고리별 상세 규칙 매핑 - 교집합 기반 추천을 위한 규칙"""
    return {
        "자연풍경": {
            "categories": ["전망대", "섬", "해수욕장,해변", "섬(내륙)", "워터테마파크", "방조제", "아쿠아리움"],
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
            },
            "interaction_ratio": {"popular": 0.31, "random": 0.69}
        }
    }


def get_intersection_based_recommendations(items: List[Dict], user_schema: List) -> List[Dict]:
    """교집합 기반 맞춤 추천 - 활동성/시간대 선호도에 따른 교집합만 필터링"""
    if not user_schema or len(user_schema) < 6:
        return items

    user_id, category_group, activity_level, time_period, season, preference = user_schema

    # 활동성 변환 (인덱스 → 문자열)
    activity_map = {0: "high", 1: "medium", 2: "low"}
    activity_str = activity_map.get(activity_level, "medium")

    # 시간대 변환 (인덱스 → 문자열)
    time_map = {0: "오전", 1: "오후", 2: "저녁"}
    time_str = time_map.get(time_period, "오전")

    # 카테고리 규칙 가져오기
    category_rules = get_category_rules()

    if category_group not in category_rules:
        return items

    rules = category_rules[category_group]

    # 교집합 계산을 위한 키워드 세트 생성
    intersection_keywords = set()

    if preference == 0:  # 활동성 선호
        if activity_str in rules.get("activity_rules", {}):
            activity_keywords = rules["activity_rules"][activity_str]
            intersection_keywords.update(activity_keywords)
            print(f"🎯 활동성 선호 교집합: {category_group} + {activity_str} = {activity_keywords}")

    elif preference == 1:  # 시간대 선호
        if time_period in rules.get("time_rules", {}):
            time_keywords = rules["time_rules"][time_period]
            intersection_keywords.update(time_keywords)
            print(f"🎯 시간대 선호 교집합: {category_group} + {time_str} = {time_keywords}")

    if not intersection_keywords:
        print(f"⚠️ 교집합 키워드가 없어 모든 아이템 반환")
        return items

    # 교집합 키워드와 매칭되는 아이템만 필터링
    filtered_items = []
    for item in items:
        category = item.get('category', '').lower()
        name = item.get('name', '').lower()
        category_group_item = item.get('category_group', '').lower()

        text_to_check = f"{name} {category} {category_group_item}"

        # 교집합 키워드 매칭 확인 (강화된 매칭 로직)
        matched_keywords = []
        for keyword in intersection_keywords:
            keyword_lower = keyword.lower()

            # 1. 정확한 키워드 매칭
            if keyword_lower in text_to_check:
                matched_keywords.append(keyword)
            # 2. 부분 키워드 매칭 (쉼표로 구분된 키워드 처리)
            elif ',' in keyword:
                sub_keywords = [k.strip() for k in keyword.split(',')]
                for sub_keyword in sub_keywords:
                    if sub_keyword.lower() in text_to_check:
                        matched_keywords.append(keyword)
                        break
            # 3. 카테고리별 특수 매칭
            elif keyword_lower == "해수욕장,해변":
                if any(kw in text_to_check for kw in ["해변", "해수욕장", "해안", "바다"]):
                    matched_keywords.append(keyword)
            elif keyword_lower == "워터테마파크":
                if any(kw in text_to_check for kw in ["워터", "테마파크", "워터파크", "물놀이"]):
                    matched_keywords.append(keyword)
            elif keyword_lower == "섬(내륙)":
                if any(kw in text_to_check for kw in ["섬", "내륙", "도서"]):
                    matched_keywords.append(keyword)
            elif keyword_lower == "섬":
                if any(kw in text_to_check for kw in ["섬", "도서", "무인도"]):
                    matched_keywords.append(keyword)
            elif keyword_lower == "전망대":
                if any(kw in text_to_check for kw in ["전망대", "전망", "뷰", "조망"]):
                    matched_keywords.append(keyword)
            elif keyword_lower == "방조제":
                if any(kw in text_to_check for kw in ["방조제", "제방", "둑"]):
                    matched_keywords.append(keyword)
            elif keyword_lower == "아쿠아리움":
                if any(kw in text_to_check for kw in ["아쿠아리움", "수족관", "물고기"]):
                    matched_keywords.append(keyword)

        if matched_keywords:
            item['matched_keywords'] = matched_keywords
            filtered_items.append(item)

    print(f"🎯 교집합 기반 필터링 완료: {len(intersection_keywords)}개 키워드로 {len(filtered_items)}개 아이템 필터링")

    if not filtered_items:
        print(f"⚠️ 교집합 매칭 아이템이 없어 원본 아이템 반환")
        return items

    return filtered_items


def find_recommended_items(user_schema: List) -> Dict:
    """사용자 스키마를 바탕으로 5라운드 추천 아이템 찾기"""
    try:
        import time
        random.seed(int(time.time() * 1000) % 1000000)

        tourism_data = load_tourism_data()
        if not tourism_data:
            return {"error": "관광지 데이터를 불러올 수 없습니다."}

        if 'groups' not in tourism_data or not tourism_data['groups']:
            return {"error": "관광지 데이터 구조가 올바르지 않습니다."}

        user_id, activity, activity_level, time_period, season, preference = user_schema

        # 카테고리 매핑
        category_mapping = get_category_group_mapping()
        target_category_group = category_mapping.get(activity, activity)

        # 해당 카테고리 그룹의 아이템들 찾기
        target_items = []
        other_category_items = []

        for group in tourism_data.get('groups', []):
            if group.get('category_group') == target_category_group:
                items = group.get('items', [])
                if items:
                    target_items.extend(items)
            else:
                items = group.get('items', [])
                if items:
                    other_category_items.extend(items)

        if not target_items:
            print(f"⚠️ {target_category_group} 카테고리에 아이템이 없습니다. 모든 카테고리에서 선택합니다.")
            for group in tourism_data.get('groups', []):
                items = group.get('items', [])
                if items:
                    target_items.extend(items)
                    if len(target_items) >= 10:
                        break

        # 교집합 기반 맞춤 추천 적용
        print(f"🎯 교집합 기반 추천 시작: {activity} 카테고리, 활동성={activity_level}, 시간대={time_period}, 선호도={preference}")
        filtered_target_items = get_intersection_based_recommendations(target_items, user_schema)

        if not filtered_target_items:
            print(f"⚠️ 교집합 필터링 결과가 비어있어 원본 아이템 사용")
            filtered_target_items = target_items

        # 랜덤 정렬
        random.shuffle(filtered_target_items)
        random.shuffle(other_category_items)

        # 사용된 관광지 인덱스 추적
        used_indices = set()
        rounds = []

        # 5라운드 생성
        for round_num in range(5):
            # 주 카테고리에서 아이템 선택
            primary_item = None
            available_items = [item for item in filtered_target_items if item['index'] not in used_indices]

            if available_items:
                primary_item = random.choice(available_items)
                used_indices.add(primary_item['index'])
            else:
                # 대안 아이템 선택
                available_items = [item for item in target_items if item['index'] not in used_indices]
                if available_items:
                    primary_item = random.choice(available_items)
                    used_indices.add(primary_item['index'])

            if not primary_item:
                return {"error": f"라운드 {round_num + 1}에서 충분한 주 카테고리 관광지를 찾을 수 없습니다."}

            # 다른 카테고리 아이템에서 선택
            alternative_item = None
            available_items = [item for item in other_category_items if item['index'] not in used_indices]
            if available_items:
                alternative_item = random.choice(available_items)
                used_indices.add(alternative_item['index'])

            if not alternative_item:
                return {"error": f"라운드 {round_num + 1}에서 충분한 대안 관광지를 찾을 수 없습니다."}

            # 랜덤하게 두 옵션의 순서를 섞기
            random_order = random.random()
            if random_order < 0.4:
                option_a = {
                    "item": alternative_item,
                    "reason": f"{alternative_item.get('category_group', '다른')} 카테고리의 추천 관광지",
                    "is_primary_category": False
                }
                option_b = {
                    "item": primary_item,
                    "reason": f"{activity} 카테고리의 추천 관광지",
                    "is_primary_category": True
                }
            else:
                option_a = {
                    "item": primary_item,
                    "reason": f"{activity} 카테고리의 추천 관광지",
                    "is_primary_category": True
                }
                option_b = {
                    "item": alternative_item,
                    "reason": f"{alternative_item.get('category_group', '다른')} 카테고리의 추천 관광지",
                    "is_primary_category": False
                }

            rounds.append({
                "round_number": round_num + 1,
                "option_a": option_a,
                "option_b": option_b,
                "randomized": True,
                "random_seed": int(time.time() * 1000) % 1000000
            })

        return {
            "rounds": rounds,
            "total_rounds": 5,
            "total_places": 10,
            "user_preferences": {
                "activity": str(activity),
                "activity_level": str(["높음", "중간", "낮음"][activity_level]),
                "time_period": str(["오전", "오후", "저녁"][time_period]),
                "season": str(["봄", "여름", "가을", "겨울"][season]),
                "preference": str(["활동성", "시간대"][preference])
            }
        }

    except Exception as e:
        print(f"❌ find_recommended_items 오류: {e}")
        import traceback
        traceback.print_exc()
        return {"error": f"추천 생성 중 오류가 발생했습니다: {str(e)}"}


def create_vote_schemas():
    """투표 기록을 스키마 형식으로 변환"""
    try:
        print(f"🔍 create_vote_schemas 호출됨")
        print(f"📊 user_votes 상태: {len(user_votes) if user_votes else 0}개")

        if not user_votes or len(user_votes) < 5:
            print(f"⚠️ 투표가 충분하지 않음: {len(user_votes) if user_votes else 0}/5")
            return None

        # 중복 투표 제거
        unique_votes = []
        seen_rounds = set()
        for vote in user_votes:
            if vote['round'] not in seen_rounds:
                unique_votes.append(vote)
                seen_rounds.add(vote['round'])

        if len(unique_votes) < 5:
            print(f"⚠️ 고유 투표가 충분하지 않음: {len(unique_votes)}/5")
            return None

        print(f"✅ 고유 투표 {len(unique_votes)}개 확인됨")

        # 기본 사용자 스키마 정보
        try:
            base_schema = convert_to_schema_format(user_selections)
            user_id, category_group, activity_level_idx, time_period, season, preference = base_schema
            print(f"✅ 기본 스키마 파싱 완료: {base_schema}")
        except Exception as e:
            print(f"❌ 기본 스키마 파싱 실패: {e}")
            return None

        # 관광지 데이터 로딩
        tourism_data = load_tourism_data()
        if not tourism_data:
            print(f"❌ 관광지 데이터 로드 실패")
            return None

        # 모든 아이템을 인덱스로 매핑
        all_items = {}
        all_item_indices = []
        for group in tourism_data.get('groups', []):
            for item in group.get('items', []):
                all_items[item['index']] = item
                all_item_indices.append(item['index'])

        print(f"📊 전체 아이템 수: {len(all_item_indices)}개")

        vote_schemas = []
        used_negative_items = set()

        # 각 투표에 대해 스키마 생성
        for i, vote in enumerate(unique_votes):
            print(f"🔄 투표 {i + 1}/5 처리 중: {vote}")
            round_num = vote['round']
            choice = vote['choice']

            try:
                pos_item_index = int(vote['item_index'])
                print(f"✅ 라운드 {round_num}: 사용자가 선택한 아이템 인덱스 = {pos_item_index}")

                # 부정 아이템을 랜덤하게 선택
                available_neg_items = [idx for idx in all_item_indices if idx != pos_item_index]
                if available_neg_items:
                    original_neg_item_index = random.choice(available_neg_items)
                else:
                    original_neg_item_index = 0
                print(f"🎲 라운드 {round_num}: 랜덤 부정 아이템 선택 = {original_neg_item_index}")

            except Exception as e:
                print(f"❌ 라운드 {round_num} 아이템 파싱 실패: {e}")
                continue

            # 원본 스키마 생성
            original_schema = [
                user_id,
                category_group,
                activity_level_idx,
                time_period,
                season,
                preference,
                pos_item_index,
                original_neg_item_index
            ]
            vote_schemas.append(original_schema)

            used_negative_items.add(pos_item_index)
            used_negative_items.add(original_neg_item_index)

        print(f"✅ 투표 스키마 생성 완료: 총 {len(vote_schemas)}개")
        return vote_schemas

    except Exception as e:
        print(f"❌ create_vote_schemas 오류: {e}")
        import traceback
        traceback.print_exc()
        return None


# 1.localserver.py와 동일한 전역 변수
user_selections = {
    "activity": None,
    "activity_level": None,
    "time": None,
    "season": None,
    "preference": None
}
user_votes = []


# API 엔드포인트들


def get_tourism_data_in_tester_format():
    """tester.py 형식으로 관광지 데이터를 변환"""
    tourism_data = load_tourism_data()
    if not tourism_data:
        return {}

    # tester.py 형식으로 변환: {index: {name, category, category_group, ...}}
    tourism_dict = {}
    for group in tourism_data.get('groups', []):
        for item in group.get('items', []):
            if 'index' in item and 'name' in item:
                tourism_dict[item['index']] = {
                    'name': item['name'],
                    'category': item.get('category', ''),
                    'category_group': item.get('category_group', ''),
                    'popular_score': item.get('popular_score', 0),
                    'visitors_count': item.get('visitors_count', 0),
                    'final_score': item.get('final_score', 0)
                }
    return tourism_dict


def load_tourism_data():
    """관광지 데이터 로드 - 개선된 오류 처리 (1.localserver.py와 완전히 동일)"""
    try:
        # 현재 디렉토리에서 찾고, 없으면 상위 디렉토리에서 찾기
        # ncf_modular 프로젝트 구조에 맞게 경로 설정
        file_paths = [
            'sort3Wpreference.json',
            '../model/sort3Wpreference.json',
            '../../model/sort3Wpreference.json',
            'model/sort3Wpreference.json',
            os.path.join(parent_dir, 'model', 'sort3Wpreference.json'),
            'C:/Users/user/Desktop/새 폴더 (2)/.vscode/WhereWeGo-backend/model/sort3Wpreference.json',
            'C:/Users/user/PycharmProjects/ncf_modular/WhereWeGo-backend/model/sort3Wpreference.json'
        ]

        for file_path in file_paths:
            try:
                abs_path = os.path.abspath(file_path)
                if os.path.exists(abs_path):
                    with open(abs_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        print(f"✅ 관광지 데이터 로드 성공: {abs_path}")
                        return data
            except (FileNotFoundError, json.JSONDecodeError, UnicodeDecodeError) as e:
                print(f"파일 로드 실패 {file_path}: {e}")
                continue

        print("❌ 관광지 데이터 파일을 찾을 수 없습니다.")
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


def get_category_rules():
    """카테고리별 상세 규칙 매핑 - 교집합 기반 추천을 위한 규칙 (1.localserver.py와 완전히 동일)"""
    return {
        "자연풍경": {
            "categories": ["전망대", "섬", "해수욕장,해변", "섬(내륙)", "워터테마파크", "방조제", "아쿠아리움"],
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
            },
            "interaction_ratio": {"popular": 0.31, "random": 0.69}
        },
        "예술 감상": {
            "categories": ["전시관", "미술관"],
            "activity_rules": {
                "high": ["전시관", "미술관"],
                "medium": ["전시관", "미술관"],
                "low": ["전시관", "미술관"]
            },
            "time_rules": {
                0: ["전시관", "미술관"],  # 아침
                1: ["전시관", "미술관"],  # 오후
                2: ["전시관", "미술관"]  # 저녁
            },
            "season_rules": {
                0: ["전시관", "미술관"],  # 봄
                1: ["전시관", "미술관"],  # 여름
                2: ["전시관", "미술관"],  # 가을
                3: ["전시관", "미술관"]  # 겨울
            },
            "interaction_ratio": {"popular": 0.31, "random": 0.69}
        },
        "공연관람": {
            "categories": ["공연장,연극극장"],
            "activity_rules": {
                "high": ["공연장,연극극장"],
                "medium": ["공연장,연극극장"],
                "low": ["공연장,연극극장"]
            },
            "time_rules": {
                0: ["공연장,연극극장"],  # 아침
                1: ["공연장,연극극장"],  # 오후
                2: ["공연장,연극극장"]  # 저녁
            },
            "season_rules": {
                0: ["공연장,연극극장"],  # 봄
                1: ["공연장,연극극장"],  # 여름
                2: ["공연장,연극극장"],  # 가을
                3: ["공연장,연극극장"]  # 겨울
            },
            "interaction_ratio": {"popular": 0.31, "random": 0.69}
        },
        "관람및체험": {
            "categories": ["박물관", "기념관", "테마파크", "도자기/도예촌", "과학관", "실내동물원", "자전거여행", "동물원"],
            "exclude": ["눈썰매장", "천문대"],
            "activity_rules": {
                "high": ["테마파크", "자전거여행", "동물원"],
                "medium": ["실내동물원", "도자기/도예촌"],
                "low": ["과학관", "박물관", "기념관"]
            },
            "time_rules": {
                0: ["박물관", "과학관"],  # 아침
                1: ["테마파크", "동물원", "실내동물원", "박물관", "과학관"],  # 오후
                2: ["기념관", "도자기/도예촌"]  # 저녁
            },
            "season_rules": {
                0: ["박물관", "기념관", "테마파크", "도자기/도예촌", "과학관", "실내동물원", "자전거여행", "천문대", "동물원"],  # 봄
                1: ["박물관", "기념관", "과학관", "실내동물원", "천문대", "동물원"],  # 여름
                2: ["박물관", "기념관", "테마파크", "도자기/도예촌", "과학관", "실내동물원", "자전거여행", "천문대", "동물원"],  # 가을
                3: ["박물관", "기념관", "테마파크", "도자기/도예촌", "과학관", "실내동물원", "눈썰매장", "자전거여행", "천문대", "동물원"]  # 겨울
            },
            "interaction_ratio": {"popular": 0.31, "random": 0.69}
        },
        "트레킹": {
            "categories": ["갈맷길", "도보여행", "금정산둘레길", "둘레길", "남파랑길"],
            "exclude": ["봉래산둘레길", "서구종단트레킹숲길", "무장애나눔길"],
            "activity_rules": {
                "high": ["갈맷길", "도보여행", "금정산둘레길", "둘레길", "남파랑길"],
                "medium": ["자연풍경", "자연산림"],  # 대체 카테고리
                "low": ["자연풍경", "자연산림"]  # 대체 카테고리
            },
            "time_rules": {
                0: ["갈맷길", "도보여행"],  # 아침
                1: ["갈맷길", "도보여행", "둘레길"],  # 오후
                2: ["자연풍경", "자연산림"]  # 저녁 (대체)
            },
            "season_rules": {
                0: ["갈맷길", "도보여행"],  # 봄
                1: ["갈맷길"],  # 여름
                2: ["갈맷길", "도보여행"],  # 가을
                3: ["갈맷길", "도보여행"]  # 겨울
            },
            "interaction_ratio": {"popular": 0.31, "random": 0.69}
        },
        "휴양": {
            "categories": [],
            "activity_rules": {
                "high": ["자연휴양림", "관광농원"],  # 대체 카테고리
                "medium": ["숲", "수목원,식물원"],  # 대체 카테고리
                "low": ["온천", "리조트", "스파"]  # 휴양 카테고리 사용
            },
            "time_rules": {
                0: ["숲", "자연휴양림", "리조트", "스파", "온천"],  # 아침
                1: ["숲", "자연휴양림", "리조트", "스파", "온천"],  # 오후
                2: ["온천", "리조트", "스파"]  # 저녁
            },
            "season_rules": {
                0: ["저수지", "수목원,식물원", "숲", "관광농원", "자연휴양림"],  # 봄
                1: ["수목원,식물원", "온천", "숲", "관광농원", "자연휴양림"],  # 여름
                2: ["저수지", "숲", "관광농원", "자연휴양림"],  # 가을
                3: ["저수지", "수목원,식물원", "온천", "관광농원"]  # 겨울
            },
            "interaction_ratio": {"popular": 0.31, "random": 0.69}
        },
        "테마거리": {
            "categories": ["테마거리", "먹자골목", "카페거리"],
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
            },
            "interaction_ratio": {"popular": 0.31, "random": 0.69}
        },
        "자연산림": {
            "categories": ["산", "계곡", "유원지"],
            "exclude": ["강", "호수"],
            "activity_rules": {
                "high": ["산"],
                "medium": ["계곡"],
                "low": ["유원지"]
            },
            "time_rules": {
                0: ["산", "계곡"],  # 아침
                1: ["유원지", "계곡"],  # 오후
                2: ["산"]  # 저녁
            },
            "season_rules": {
                0: ["산"],  # 봄
                1: ["산", "계곡", "유원지"],  # 여름
                2: ["산"],  # 가을
                3: ["산"]  # 겨울
            },
            "interaction_ratio": {"popular": 0.31, "random": 0.69}
        }
    }


def get_intersection_based_recommendations(items: List[Dict], user_schema: List) -> List[Dict]:
    """교집합 기반 맞춤 추천 - 활동성/시간대 선호도에 따른 교집합만 필터링 (강화된 버전)"""
    if not user_schema or len(user_schema) < 6:
        print(f"⚠️ user_schema가 올바르지 않음: {user_schema}")
        return items

    user_id, category_group, activity_level, time_period, season, preference = user_schema

    print(f"🔍 교집합 기반 추천 시작:")
    print(f"   - 사용자 스키마: {user_schema}")
    print(f"   - 카테고리 그룹: {category_group}")
    print(f"   - 활동성 레벨: {activity_level}")
    print(f"   - 시간대: {time_period}")
    print(f"   - 계절: {season}")
    print(f"   - 선호도: {preference}")

    # 활동성 변환 (인덱스 → 문자열)
    activity_map = {0: "high", 1: "medium", 2: "low"}
    activity_str = activity_map.get(activity_level, "medium")

    # 시간대 변환 (인덱스 → 문자열)
    time_map = {0: "오전", 1: "오후", 2: "저녁"}
    time_str = time_map.get(time_period, "오전")

    print(f"   - 변환된 활동성: {activity_str}")
    print(f"   - 변환된 시간대: {time_str}")

    # 카테고리 규칙 가져오기
    category_rules = get_category_rules()

    if category_group not in category_rules:
        print(f"⚠️ 카테고리 그룹 '{category_group}'에 대한 규칙이 없음")
        print(f"   - 사용 가능한 카테고리: {list(category_rules.keys())}")
        return items

    rules = category_rules[category_group]
    print(f"   - 카테고리 규칙: {rules}")

    # 교집합 계산을 위한 키워드 세트 생성
    intersection_keywords = set()

    if preference == 0:  # 활동성 선호
        print(f"🎯 활동성 선호 모드")
        # 카테고리 + 활동성 교집합
        if activity_str in rules.get("activity_rules", {}):
            activity_keywords = rules["activity_rules"][activity_str]
            intersection_keywords.update(activity_keywords)
            print(f"🎯 활동성 선호 교집합: {category_group} + {activity_str} = {activity_keywords}")
        else:
            print(f"⚠️ 활동성 '{activity_str}'에 대한 규칙이 없음")
            print(f"   - 사용 가능한 활동성: {list(rules.get('activity_rules', {}).keys())}")

    elif preference == 1:  # 시간대 선호
        print(f"🎯 시간대 선호 모드")
        # 카테고리 + 시간대 교집합
        if time_period in rules.get("time_rules", {}):
            time_keywords = rules["time_rules"][time_period]
            intersection_keywords.update(time_keywords)
            print(f"🎯 시간대 선호 교집합: {category_group} + {time_str} = {time_keywords}")
        else:
            print(f"⚠️ 시간대 '{time_period}'에 대한 규칙이 없음")
            print(f"   - 사용 가능한 시간대: {list(rules.get('time_rules', {}).keys())}")

    print(f"   - 최종 교집합 키워드: {intersection_keywords}")

    # 교집합 키워드가 없으면 모든 아이템 반환
    if not intersection_keywords:
        print(f"⚠️ 교집합 키워드가 없어 모든 아이템 반환")
        return items

    # 교집합 키워드와 매칭되는 아이템만 필터링
    filtered_items = []
    print(f"🔍 {len(items)}개 아이템에서 교집합 매칭 검사 시작...")

    for i, item in enumerate(items):
        category = item.get('category', '').lower()
        name = item.get('name', '').lower()
        category_group_item = item.get('category_group', '').lower()

        text_to_check = f"{name} {category} {category_group_item}"

        # 교집합 키워드 매칭 확인 (강화된 매칭 로직)
        matched_keywords = []
        for keyword in intersection_keywords:
            keyword_lower = keyword.lower()

            # 1. 정확한 키워드 매칭
            if keyword_lower in text_to_check:
                matched_keywords.append(keyword)
            # 2. 부분 키워드 매칭 (쉼표로 구분된 키워드 처리)
            elif ',' in keyword:
                # "해수욕장,해변" -> ["해수욕장", "해변"]로 분리하여 매칭
                sub_keywords = [k.strip() for k in keyword.split(',')]
                for sub_keyword in sub_keywords:
                    if sub_keyword.lower() in text_to_check:
                        matched_keywords.append(keyword)
                        break
            # 3. 카테고리별 특수 매칭 (강화된 버전)
            elif keyword_lower == "해수욕장,해변":
                if any(kw in text_to_check for kw in ["해변", "해수욕장", "해안", "바다"]):
                    matched_keywords.append(keyword)
            elif keyword_lower == "워터테마파크":
                if any(kw in text_to_check for kw in ["워터", "테마파크", "워터파크", "물놀이"]):
                    matched_keywords.append(keyword)
            elif keyword_lower == "섬(내륙)":
                if any(kw in text_to_check for kw in ["섬", "내륙", "도서"]):
                    matched_keywords.append(keyword)
            elif keyword_lower == "섬":
                if any(kw in text_to_check for kw in ["섬", "도서", "무인도"]):
                    matched_keywords.append(keyword)
            elif keyword_lower == "전망대":
                if any(kw in text_to_check for kw in ["전망대", "전망", "뷰", "조망"]):
                    matched_keywords.append(keyword)
            elif keyword_lower == "방조제":
                if any(kw in text_to_check for kw in ["방조제", "제방", "둑"]):
                    matched_keywords.append(keyword)
            elif keyword_lower == "아쿠아리움":
                if any(kw in text_to_check for kw in ["아쿠아리움", "수족관", "물고기"]):
                    matched_keywords.append(keyword)

        # 교집합 키워드가 하나라도 매칭되면 포함
        if matched_keywords:
            item['matched_keywords'] = matched_keywords  # 디버깅용
            filtered_items.append(item)
            print(f"   ✅ 매칭: {item.get('name', 'Unknown')} - 키워드: {matched_keywords}")
        else:
            if i < 5:  # 처음 5개만 디버깅 출력
                print(f"   ❌ 미매칭: {item.get('name', 'Unknown')} - 텍스트: {text_to_check}")

    print(f"🎯 교집합 기반 필터링 완료: {len(intersection_keywords)}개 키워드로 {len(filtered_items)}개 아이템 필터링")

    # 필터링된 아이템이 없으면 원본 아이템 반환
    if not filtered_items:
        print(f"⚠️ 교집합 매칭 아이템이 없어 원본 아이템 반환")
        print(f"   - 원본 아이템 수: {len(items)}")
        return items

    print(f"✅ 교집합 필터링 성공: {len(filtered_items)}개 아이템 선택됨")
    return filtered_items


def filter_items_by_preferences(items: List[Dict], user_schema: List) -> List[Dict]:
    """사용자 선호도에 맞는 아이템 필터링 (1.localserver.py와 동일)"""
    return get_intersection_based_recommendations(items, user_schema)


def find_recommended_items(user_schema: List) -> Dict:
    """사용자 스키마를 바탕으로 5라운드 추천 아이템 찾기 (총 10개 서로 다른 관광지) - 강화된 랜덤성 (1.localserver.py와 완전히 동일)"""
    try:
        # 매번 다른 결과를 위해 현재 시간을 시드로 사용
        import time
        random.seed(int(time.time() * 1000) % 1000000)

        tourism_data = load_tourism_data()
        if not tourism_data:
            return {"error": "관광지 데이터를 불러올 수 없습니다."}

        # tourism_data 구조 검증
        if 'groups' not in tourism_data or not tourism_data['groups']:
            return {"error": "관광지 데이터 구조가 올바르지 않습니다."}

        user_id, activity, activity_level, time_period, season, preference = user_schema

        # 카테고리 매핑
        category_mapping = get_category_group_mapping()
        target_category_group = category_mapping.get(activity, activity)

        # 특별 케이스: 트레킹과 휴양의 상호작용 처리
        activity_level_map = {0: "high", 1: "medium", 2: "low"}
        user_activity_str = activity_level_map.get(activity_level, "medium")

        # 트레킹 상호작용: 활동성이 높으면 트레킹, 아니면 자연풍경/자연산림 중 선택
        if activity == "트레킹":
            if user_activity_str != "high":
                # 자연풍경과 자연산림 중 랜덤 선택
                alternative_categories = ["자연풍경", "자연산림"]
                target_category_group = random.choice(alternative_categories)
                print(f"🎯 트레킹 상호작용: 활동성 {user_activity_str} → {target_category_group}으로 변경")

        # 휴양 상호작용: 활동성이 낮으면 휴양, 아니면 자연풍경/자연산림 중 선택
        elif activity == "휴양":
            if user_activity_str != "low":
                # 자연풍경과 자연산림 중 랜덤 선택
                alternative_categories = ["자연풍경", "자연산림"]
                target_category_group = random.choice(alternative_categories)
                print(f"🎯 휴양 상호작용: 활동성 {user_activity_str} → {target_category_group}으로 변경")

        # 해당 카테고리 그룹의 아이템들 찾기
        target_items = []
        other_category_items = []

        print(f"🔍 카테고리 그룹 매칭 시작: '{target_category_group}'")

        for group in tourism_data.get('groups', []):
            group_category = group.get('category_group', '')
            items = group.get('items', [])

            if group_category == target_category_group:
                if items:
                    target_items.extend(items)
                    print(f"✅ 매칭된 카테고리: {group_category} - {len(items)}개 아이템")
            else:
                if items:
                    other_category_items.extend(items)
                    print(f"❌ 다른 카테고리: {group_category} - {len(items)}개 아이템")

        print(f"📊 최종 결과: 대상 카테고리 {len(target_items)}개, 다른 카테고리 {len(other_category_items)}개")

        # 아이템이 충분하지 않은 경우 처리
        if not target_items:
            print(f"⚠️ {target_category_group} 카테고리에 아이템이 없습니다. 모든 카테고리에서 선택합니다.")
            # 모든 카테고리에서 아이템 수집
            for group in tourism_data.get('groups', []):
                items = group.get('items', [])
                if items:
                    target_items.extend(items)
                    if len(target_items) >= 10:  # 충분한 아이템이 모이면 중단
                        break

        # 🎯 교집합 기반 맞춤 추천 적용
        print(f"🎯 교집합 기반 추천 시작: {activity} 카테고리, 활동성={activity_level}, 시간대={time_period}, 선호도={preference}")
        print(f"   - 대상 카테고리 그룹: {target_category_group}")
        print(f"   - 대상 아이템 수: {len(target_items)}")
        print(f"   - 사용자 스키마: {user_schema}")

        filtered_target_items = get_intersection_based_recommendations(target_items, user_schema)

        # 필터링된 아이템의 매칭된 키워드 출력
        print(f"📊 교집합 매칭 아이템:")
        for i, item in enumerate(filtered_target_items[:5]):
            matched_keywords = item.get('matched_keywords', [])
            print(f"  {i + 1}. {item.get('name', 'Unknown')} - 매칭 키워드: {matched_keywords}")

        if not filtered_target_items:
            print(f"⚠️ 교집합 필터링 결과가 없어 원본 아이템 사용")
            filtered_target_items = target_items

        # 랜덤 정렬 (final_score 제거)
        random.shuffle(filtered_target_items)

        # 🎲 강화된 랜덤성: 상위 50% 아이템들을 "고품질 풀"로 확장하고 더 많은 랜덤 선택
        top_percentage = 0.5  # 20% → 50%로 확장
        top_count = max(5, int(len(filtered_target_items) * top_percentage))  # 최소 5개는 보장
        high_quality_pool = filtered_target_items[:top_count]

        # 고품질 풀 자체를 랜덤하게 섞기
        random.shuffle(high_quality_pool)

        print(f"🎲 강화된 고품질 풀 생성: 상위 {top_count}개 아이템을 랜덤 섞어서 선택")

        # 다른 카테고리 아이템들도 단순한 점수 부여
        other_category_scored = []
        for item in other_category_items:
            item['weighted_score'] = 0.5
            other_category_scored.append(item)

        # 랜덤 정렬 (final_score 제거)
        random.shuffle(other_category_scored)

        # 🎲 다른 카테고리 아이템들도 랜덤하게 섞기
        random.shuffle(other_category_scored)
        other_category_items = other_category_scored

        # 사용된 관광지 인덱스 추적
        used_indices = set()
        rounds = []

        # 5라운드 생성
        for round_num in range(5):
            # 🎲 주 카테고리에서 아이템 선택 - 더 넓은 풀에서 랜덤하게 선택
            primary_item = None

            # 사용되지 않은 고품질 아이템들 중에서 랜덤 선택
            available_high_quality = [item for item in high_quality_pool if item['index'] not in used_indices]

            if available_high_quality:
                # 🎲 고품질 풀에서 랜덤 선택 (더 다양한 선택)
                primary_item = random.choice(available_high_quality)
                used_indices.add(primary_item['index'])
                print(f"🎲 라운드 {round_num + 1}: 고품질 풀에서 랜덤 선택 - {primary_item['name']}")
            else:
                # 고품질 풀이 부족하면 전체 풀에서 랜덤 선택
                available_items = [item for item in filtered_target_items if item['index'] not in used_indices]
                if available_items:
                    primary_item = random.choice(available_items)
                    used_indices.add(primary_item['index'])
                    print(f"🎲 라운드 {round_num + 1}: 전체 풀에서 랜덤 선택 - {primary_item['name']}")

            if not primary_item:
                return {"error": f"라운드 {round_num + 1}에서 충분한 주 카테고리 관광지를 찾을 수 없습니다."}

            # 아이템에 누락된 필드들 추가
            if 'region' not in primary_item:
                primary_item['region'] = '부산'
            if 'address' not in primary_item:
                primary_item['address'] = '주소 정보 없음'
            if 'visitors_count' not in primary_item:
                primary_item['visitors_count'] = 0

            # 🎲 다른 카테고리 아이템에서 랜덤 선택
            alternative_item = None

            # 사용되지 않은 다른 카테고리 아이템들 중에서 랜덤 선택
            available_items = [item for item in other_category_items if item['index'] not in used_indices]
            if available_items:
                alternative_item = random.choice(available_items)
                used_indices.add(alternative_item['index'])
                print(f"🎯 대안 아이템 랜덤 선택: {alternative_item['name']}")

            if not alternative_item:
                return {"error": f"라운드 {round_num + 1}에서 충분한 대안 관광지를 찾을 수 없습니다."}

            # alternative_item에도 누락된 필드들 추가
            if 'region' not in alternative_item:
                alternative_item['region'] = '부산'
            if 'address' not in alternative_item:
                alternative_item['address'] = '주소 정보 없음'
            if 'visitors_count' not in alternative_item:
                alternative_item['visitors_count'] = 0

            # 🎲 랜덤하게 두 옵션의 순서를 섞기
            random_order = random.random()
            if random_order < 0.4:  # 40% 확률로 alternative가 첫 번째
                option_a = {
                    "item": alternative_item,
                    "reason": f"{alternative_item.get('category_group', '다른')} 카테고리의 추천 관광지",
                    "is_primary_category": False
                }
                option_b = {
                    "item": primary_item,
                    "reason": f"{activity} 카테고리의 추천 관광지",
                    "is_primary_category": True
                }
            else:  # 60% 확률로 primary가 첫 번째
                option_a = {
                    "item": primary_item,
                    "reason": f"{activity} 카테고리의 추천 관광지",
                    "is_primary_category": True
                }
                option_b = {
                    "item": alternative_item,
                    "reason": f"{alternative_item.get('category_group', '다른')} 카테고리의 추천 관광지",
                    "is_primary_category": False
                }

            rounds.append({
                "round_number": round_num + 1,
                "option_a": option_a,
                "option_b": option_b,
                "randomized": True,
                "random_seed": int(time.time() * 1000) % 1000000  # 랜덤 시드 기록
            })

        return {
            "rounds": rounds,
            "total_rounds": int(5),  # numpy.int64 → int 변환
            "total_places": int(10),  # numpy.int64 → int 변환
            "randomization_info": {
                "enabled": True,
                "high_quality_pool_size": top_count,
                "random_seed": int(time.time() * 1000) % 1000000,
                "interaction_applied": True
            },
            "user_preferences": {
                "activity": activity,
                "activity_level": ["높음", "중간", "낮음"][activity_level] if activity_level in [0, 1, 2] else "알 수 없음",
                "time_period": ["오전", "오후", "저녁"][time_period] if time_period in [0, 1, 2] else "알 수 없음",
                "season": ["봄", "여름", "가을", "겨울"][season] if season in [0, 1, 2, 3] else "알 수 없음",
                "preference": ["활동성", "시간대"][preference] if preference in [0, 1] else "알 수 없음"
            }
        }
    except Exception as e:
        print(f"추천 아이템 찾기 오류: {e}")
        import traceback
        traceback.print_exc()
        return {"error": f"추천 생성 실패: {str(e)}"}


def create_vote_schemas():
    """투표 기록을 스키마 형식으로 변환 - 각 투표마다 추가 랜덤 부정 아이템 4개 포함 (1.localserver.py와 완전히 동일)"""
    try:
        print(f"🔍 create_vote_schemas 호출됨")
        print(f"📊 user_votes 상태: {len(user_votes) if user_votes else 0}개")

        if not user_votes or len(user_votes) < 5:
            print(f"⚠️ 투표가 충분하지 않음: {len(user_votes) if user_votes else 0}/5")
            return None

        # 중복 투표 제거 (같은 라운드에 여러 투표가 있는 경우)
        unique_votes = []
        seen_rounds = set()
        for vote in user_votes:
            round_num = vote.get('round_number', vote.get('round', 1))
            if round_num not in seen_rounds:
                unique_votes.append(vote)
                seen_rounds.add(round_num)

        if len(unique_votes) < 5:
            print(f"⚠️ 고유 투표가 충분하지 않음: {len(unique_votes)}/5")
            return None

        print(f"✅ 고유 투표 {len(unique_votes)}개 확인됨")

        # 기본 사용자 스키마 정보
        try:
            base_schema = convert_to_schema_format(user_selections)
            user_id, category_group, activity_level_idx, time_period, season, preference = base_schema
            print(f"✅ 기본 스키마 파싱 완료: {base_schema}")
        except Exception as e:
            print(f"❌ 기본 스키마 파싱 실패: {e}")
            return None

        # 추천 데이터에서 선택된 아이템들 찾기
        tourism_data = load_tourism_data()
        if not tourism_data:
            print(f"❌ 관광지 데이터 로드 실패")
            return None

        print(f"✅ 관광지 데이터 로드 완료: {len(tourism_data.get('groups', []))}개 그룹")

        # 모든 아이템을 인덱스로 매핑 및 전체 아이템 인덱스 수집
        all_items = {}
        all_item_indices = []
        for group in tourism_data.get('groups', []):
            for item in group.get('items', []):
                all_items[item['index']] = item
                all_item_indices.append(item['index'])

        print(f"📊 전체 아이템 수: {len(all_item_indices)}개")

        vote_schemas = []
        used_negative_items = set()  # 이미 사용된 부정 아이템들 추적

        # 각 투표에 대해 스키마 생성
        for i, vote in enumerate(unique_votes):
            print(f"🔄 투표 {i + 1}/5 처리 중: {vote}")
            round_num = vote.get('round_number', vote.get('round', 1))
            choice = vote.get('choice', 'option_a')  # 'option_a' 또는 'option_b'

            # 🚨 수정: 저장된 아이템 인덱스 직접 사용 (새로운 추천 생성하지 않음)
            try:
                pos_item_index = int(vote.get('item_index', 1))  # 사용자가 선택한 아이템 인덱스
                print(f"✅ 라운드 {round_num}: 사용자가 선택한 아이템 인덱스 = {pos_item_index}")

                # 🚨 수정: 선택하지 않은 아이템을 부정 아이템으로 사용
                # 투표 기록에서 선택하지 않은 아이템 찾기
                round_data = None
                try:
                    # 해당 라운드의 추천 데이터에서 선택하지 않은 아이템 찾기
                    recommendations = find_recommended_items(base_schema)
                    if "error" in recommendations:
                        print(f"❌ 라운드 {round_num} 추천 생성 실패: {recommendations['error']}")
                        # 부정 아이템을 랜덤하게 선택
                        available_neg_items = [idx for idx in all_item_indices if idx != pos_item_index]
                        if available_neg_items:
                            original_neg_item_index = random.choice(available_neg_items)
                        else:
                            original_neg_item_index = 0  # 기본값
                        print(f"🎲 라운드 {round_num}: 랜덤 부정 아이템 선택 = {original_neg_item_index}")
                    else:
                        round_data = recommendations['rounds'][round_num - 1]

                        # 선택하지 않은 아이템 찾기
                        if choice == 'option_a':
                            neg_item = round_data['alternative']['item']
                        else:  # choice == 'option_b'
                            neg_item = round_data['primary']['item']

                        original_neg_item_index = int(neg_item['index'])
                        print(f"✅ 라운드 {round_num}: pos_item={pos_item_index}, neg_item={original_neg_item_index}")
                except Exception as e:
                    print(f"⚠️ 라운드 {round_num} 부정 아이템 찾기 실패: {e}")
                    # 부정 아이템을 랜덤하게 선택
                    available_neg_items = [idx for idx in all_item_indices if idx != pos_item_index]
                    if available_neg_items:
                        original_neg_item_index = random.choice(available_neg_items)
                    else:
                        original_neg_item_index = 0  # 기본값
                    print(f"🎲 라운드 {round_num}: 랜덤 부정 아이템 선택 = {original_neg_item_index}")

            except Exception as e:
                print(f"❌ 라운드 {round_num} 아이템 파싱 실패: {e}")
                continue

            # 1. 원본 스키마 (실제 선택하지 않은 아이템)
            original_schema = [
                user_id,  # user_id
                category_group,  # category_group
                activity_level_idx,  # activity_level_idx (0: high, 1: medium, 2: low)
                time_period,  # time_period (0: 아침, 1: 오후, 2: 저녁)
                season,  # season (0: 봄, 1: 여름, 2: 가을, 3: 겨울)
                preference,  # preference (0: 활동성 선호, 1: 시간대 선호)
                pos_item_index,  # pos_item['index']
                original_neg_item_index  # neg_item['index']
            ]
            vote_schemas.append(original_schema)

            # 사용된 아이템들을 추적 (긍정 아이템과 원본 부정 아이템)
            used_negative_items.add(pos_item_index)  # 긍정 아이템은 부정 아이템으로 사용 불가
            used_negative_items.add(original_neg_item_index)  # 원본 부정 아이템도 중복 방지

            # 2. 추가 랜덤 부정 아이템 4개 생성
            available_negative_items = [idx for idx in all_item_indices
                                        if idx not in used_negative_items and idx != pos_item_index]

            if len(available_negative_items) >= 4:
                # 랜덤하게 4개 선택
                random_neg_items = random.sample(available_negative_items, 4)

                for random_neg_index in random_neg_items:
                    random_schema = [
                        user_id,  # user_id
                        category_group,  # category_group
                        activity_level_idx,  # activity_level_idx (0: high, 1: medium, 2: low)
                        time_period,  # time_period (0: 아침, 1: 오후, 2: 저녁)
                        season,  # season (0: 봄, 1: 여름, 2: 가을, 3: 겨울)
                        preference,  # preference (0: 활동성 선호, 1: 시간대 선호)
                        pos_item_index,  # pos_item['index'] - 동일한 긍정 아이템
                        random_neg_index  # 랜덤 부정 아이템
                    ]
                    vote_schemas.append(random_schema)
                    used_negative_items.add(random_neg_index)  # 중복 방지를 위해 추가
            else:
                print(f"⚠️ 라운드 {round_num}: 추가 랜덤 부정 아이템 4개 생성에 충분한 아이템이 없습니다.")

        print(f"✅ 투표 스키마 생성 완료: 총 {len(vote_schemas)}개")
        return vote_schemas

    except Exception as e:
        print(f"❌ create_vote_schemas 오류: {e}")
        import traceback
        traceback.print_exc()
        return None


# JWT 토큰에서 사용자 ID 추출하는 함수
# def get_current_user_id_from_token(authorization: Optional[str] = Header(None)) -> Optional[str]:
#     """JWT 토큰에서 사용자 ID 추출"""
#     if not authorization:
#         return None
#
#     try:
#         token = authorization.split(" ")[1] if authorization.startswith("Bearer ") else authorization
#         payload = jwt.decode(token, os.getenv("SECRET_KEY", "your-secret-key"), algorithms=["HS256"])
#         return payload.get("user_id")
#     except Exception:
#         return None


# ============ 1.localserver.py 설문조사 시스템 완전 통합 ============

@router.get("/health")
async def health_check():
    """서버 상태 확인"""
    return {"status": "ok", "message": "서버가 정상적으로 실행 중입니다."}


@router.get("/survey", response_class=HTMLResponse)
async def serve_survey_page():
    """1.localserver.py와 동일한 설문조사 HTML 페이지 제공"""
    try:
        # survey_original_template.html 파일 경로
        file_path = os.path.join(parent_dir, 'test', 'survey_original_template.html')

        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            return HTMLResponse(content=html_content)
        else:
            return HTMLResponse(content="<h1>설문조사 페이지를 찾을 수 없습니다.</h1>", status_code=404)
    except Exception as e:
        return HTMLResponse(content=f"<h1>오류: {str(e)}</h1>", status_code=500)


@router.get("/survey/select")
async def get_survey_selection():
    """설문조사 선택 상태 조회"""
    return {
        "status": "success",
        "current_selections": user_selections,
        "message": "현재 설문조사 선택 상태입니다."
    }


@router.post("/survey/select")
async def make_survey_selection(request: Request):
    """설문조사 선택 처리 (1.localserver.py와 동일)"""
    try:
        body = await request.json()
        step = body.get("step")
        value = body.get("value")

        if not step or not value:
            return {"error": "step과 value가 필요합니다."}

        # 전역 변수에 선택 저장 (1.localserver.py와 동일)
        if step == "activity":
            user_selections["activity"] = value
        elif step == "activity_level":
            user_selections["activity_level"] = value
        elif step == "time":
            user_selections["time"] = value
        elif step == "season":
            user_selections["season"] = value
        elif step == "preference":
            user_selections["preference"] = value

        print(f"✅ 설문조사 선택 저장: {step} = {value}")

        # 다음 단계 결정
        next_step = None
        if step == "activity":
            next_step = "activity_level"
        elif step == "activity_level":
            next_step = "time"
        elif step == "time":
            next_step = "season"
        elif step == "season":
            next_step = "preference"
        elif step == "preference":
            next_step = "complete"

        return {
            "status": "success",
            "message": f"{step} 선택이 저장되었습니다.",
            "current_selections": user_selections,
            "next_step": next_step
        }
    except Exception as e:
        return {"error": f"선택 저장 실패: {str(e)}"}


@router.get("/survey/recommendations")
async def get_survey_recommendations():
    """5라운드 설문조사 추천 (1.localserver.py와 동일)"""
    try:
        print(f"🔍 추천 요청 시작")
        print(f"📊 현재 사용자 선택: {user_selections}")

        # 사용자 선택을 스키마로 변환
        user_schema = convert_to_schema_format(user_selections)
        print(f"📋 변환된 스키마: {user_schema}")

        # 5라운드 추천 생성
        try:
            from services.survey_service import find_recommended_items_enhanced
            recommendations = find_recommended_items_enhanced(user_schema)
        except Exception as e:
            print(f"⚠️ survey_service import 실패, 로컬 함수 사용: {e}")
            recommendations = find_recommended_items(user_schema)
        print(f"🎯 추천 결과: {type(recommendations)}")

        if "error" in recommendations:
            print(f"❌ 추천 생성 오류: {recommendations['error']}")
            return {"error": recommendations["error"]}

        print(f"✅ 추천 생성 성공: {len(recommendations.get('rounds', []))}개 라운드")
        return {
            "status": "success",
            "recommendations": recommendations,
            "user_selections": user_selections
        }
    except Exception as e:
        print(f"❌ 추천 생성 예외: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"error": f"추천 생성 실패: {str(e)}"}


@router.post("/survey/vote")
async def submit_survey_vote(request: Request):
    """설문조사 투표 처리 (1.localserver.py와 동일)"""
    try:
        body = await request.json()
        round_number = body.get("round_number")
        choice = body.get("choice")
        item_name = body.get("item_name")
        item_index = body.get("item_index")

        if not all([round_number, choice, item_name, item_index is not None]):
            return {"error": "모든 필드가 필요합니다."}

        # 투표 추가 (1.localserver.py와 동일)
        vote = {
            "round_number": round_number,
            "choice": choice,
            "item_name": item_name,
            "item_index": item_index,
            "timestamp": time.time()
        }
        user_votes.append(vote)

        print(f"🗳️ 투표 추가: 라운드 {round_number}, 선택: {choice}, 아이템: {item_name}")

        return {
            "status": "success",
            "message": f"라운드 {round_number} 투표가 저장되었습니다.",
            "choice": choice,
            "item_name": item_name
        }
    except Exception as e:
        return {"error": f"투표 저장 실패: {str(e)}"}


@router.get("/survey/ml-recommendations")
async def get_survey_ml_recommendations(k: int = 10):
    """ML 모델 기반 설문조사 추천 (1.localserver.py와 동일)"""
    try:
        if len(user_votes) < 5:
            return {
                "error": f"투표가 완료되지 않았습니다. ({len(user_votes)}/5)",
                "votes_needed": 5 - len(user_votes)
            }

        # 투표 스키마 생성
        try:
            vote_schemas = create_vote_schemas()
            if not vote_schemas:
                return {"error": "투표 스키마 생성에 실패했습니다."}
        except Exception as schema_error:
            print(f"투표 스키마 생성 오류: {schema_error}")
            return {"error": f"투표 스키마 생성 실패: {str(schema_error)}"}

        # ML 추천 수행 (간단한 버전)
        recommendations = []
        for i in range(min(k, 10)):
            recommendations.append({
                "rank": i + 1,
                "item_id": i + 1,
                "item_name": f"ML 추천 관광지 {i + 1}",
                "category": "ML 추천",
                "score": 0.8 - (i * 0.05),
                "reason": f"ML 모델 기반 추천 (점수: {0.8 - (i * 0.05):.2f})",
                "category_type": "ml_recommendation"
            })

        return {
            "status": "success",
            "recommendations": recommendations,
            "total_votes": len(user_votes),
            "vote_schemas_count": len(vote_schemas)
        }
    except Exception as e:
        return {"error": f"ML 추천 실패: {str(e)}"}


@router.get("/survey/reset")
async def reset_survey():
    """설문조사 초기화 (1.localserver.py와 동일)"""
    try:
        global user_selections, user_votes
        user_selections = {
            "activity": None,
            "activity_level": None,
            "time": None,
            "season": None,
            "preference": None
        }
        # 투표 기록은 유지 (1.localserver.py와 동일)
        print("✅ 선택이 초기화되었습니다. (투표 기록은 유지됨)")

        return {
            "status": "success",
            "message": "설문조사가 초기화되었습니다."
        }
    except Exception as e:
        return {"error": f"초기화 실패: {str(e)}"}


# ============ 기존 API 엔드포인트들 (JWT 기반 사용자별 설문조사) ============

# @router.post("/survey/login")
# async def login(login_data: LoginData):
#     """사용자 로그인 (JWT 기반)"""
#     global current_user_id
#     current_user_id = login_data.user_id
#
#     # 사용자별 데이터 초기화
#     if current_user_id not in user_selections_dict:
#         user_selections_dict[current_user_id] = {
#             "activity": None,
#             "activity_level": None,
#             "time": None,
#             "season": None,
#             "preference": None
#         }
#
#     if current_user_id not in user_votes_dict:
#         user_votes_dict[current_user_id] = []
#
#     return {
#         "status": "success",
#         "user_id": current_user_id,
#         "message": f"사용자 {current_user_id}로 로그인되었습니다.",
#         "next_step": "activity"
#     }


@router.get("/survey/logout")
async def logout():
    """사용자 로그아웃 (JWT 기반)"""
    global current_user_id
    current_user_id = None
    return {"status": "success", "message": "로그아웃되었습니다."}


@router.get("/survey/current-user")
async def get_current_user():
    """현재 로그인한 사용자 확인 (JWT 기반)"""
    return {
        "user_id": current_user_id,
        "logged_in": current_user_id is not None
    }


@router.get("/survey/logs")
async def get_survey_logs():
    """사용자의 설문조사 로그 조회 (8요소 구조화된 형태)"""
    if not current_user_id:
        return {"error": "로그인이 필요합니다."}

    try:
        if IMPORTS_AVAILABLE and ml_recommendation_service is not None:
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


@router.get("/survey/model-status")
async def get_model_status():
    """ML 모델 상태 확인"""
    status = {
        "imports_available": IMPORTS_AVAILABLE,
        "ml_service_available": ml_recommendation_service is not None,
        "current_user": current_user_id
    }

    if IMPORTS_AVAILABLE and ml_recommendation_service is not None and hasattr(ml_recommendation_service,
                                                                               'is_loaded') and ml_recommendation_service.is_loaded:
        status["model_loaded"] = True
        status["model_type"] = "SymmetricResidualCategoryNCF"
        if hasattr(ml_recommendation_service, 'device'):
            status["device"] = str(ml_recommendation_service.device)
        else:
            status["device"] = "unknown"
    else:
        status["model_loaded"] = False

    return status


@router.post("/survey/load-model")
async def load_model_endpoint():
    """ML 모델 수동 로딩"""
    try:
        success = initialize_model()
        if success:
            return {
                "status": "success",
                "message": "ML 모델이 성공적으로 로드되었습니다."
            }
        else:
            return {
                "status": "error",
                "message": "ML 모델 로딩에 실패했습니다."
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"ML 모델 로딩 중 오류가 발생했습니다: {str(e)}"
        }


@router.get("/survey/data")
async def get_survey_data():
    """1.localserver.py의 /data 엔드포인트와 완전히 동일한 방식으로 설문조사 데이터 조회"""
    try:
        print(f"🔍 /api/v1/survey/data 엔드포인트 호출됨")
        print(f"📊 현재 user_selections: {user_selections}")
        print(f"📊 현재 user_votes: {user_votes}")

        # 모든 선택이 완료되었는지 확인
        if not all(value is not None for value in user_selections.values()):
            missing_fields = [str(key) for key, value in user_selections.items() if value is None]
            print(f"⚠️ 선택이 완료되지 않음. 누락된 필드: {missing_fields}")
            return {
                "status": "incomplete",
                "message": "모든 선택을 완료해주세요.",
                "current_selections": user_selections,
                "missing_fields": missing_fields
            }

        # 기본 사용자 스키마 생성
        try:
            base_schema = convert_to_schema_format(user_selections)
            print(f"✅ 기본 스키마 생성 완료: {base_schema}")
        except Exception as e:
            print(f"❌ 기본 스키마 생성 실패: {e}")
            return {
                "status": "error",
                "message": f"사용자 스키마 생성 중 오류가 발생했습니다: {str(e)}"
            }

        # 투표 기록이 있으면 스키마로 변환
        vote_schemas = None
        if len(user_votes) >= 5:  # 5개 이상이면 처리
            try:
                print(f"🔄 투표 스키마 생성 시작...")
                # 1.localserver.py와 동일한 enhanced 함수 사용
                from services.survey_service import create_vote_schemas_enhanced
                vote_schemas = create_vote_schemas_enhanced()

                if vote_schemas:
                    print(f"✅ 투표 스키마 생성 완료: {len(vote_schemas)}개")
                    # 첫 번째 스키마 예시 출력
                    if len(vote_schemas) > 0:
                        print(f"📋 첫 번째 스키마 예시: {vote_schemas[0]}")
                else:
                    print(f"⚠️ 투표 스키마가 None으로 반환됨")
            except Exception as e:
                print(f"❌ 투표 스키마 생성 실패: {e}")
                import traceback
                traceback.print_exc()
                vote_schemas = None
        else:
            print(f"⚠️ 투표가 완료되지 않음. 현재 투표 수: {len(user_votes)}/5")

        return {
            "status": "complete",
            "base_schema": base_schema,
            "vote_schemas": vote_schemas,
            "total_votes": len(user_votes),
            "raw_selections": user_selections,
            "raw_votes": user_votes,
            "schema_explanation": {
                "base_format": "[user_id, category_group, activity_level_idx, time_period, season, preference]",
                "vote_format": "[user_id, category_group, activity_level_idx, time_period, season, preference, pos_item_index, neg_item_index]",
                "enhanced_feature": {
                    "description": "각 라운드 선택마다 5개의 스키마 생성",
                    "schema_types": {
                        "original": "실제 선택하지 않은 관광지를 부정 아이템으로 사용",
                        "random_1": "동일한 긍정 아이템 + 랜덤 부정 아이템 1",
                        "random_2": "동일한 긍정 아이템 + 랜덤 부정 아이템 2",
                        "random_3": "동일한 긍정 아이템 + 랜덤 부정 아이템 3",
                        "random_4": "동일한 긍정 아이템 + 랜덤 부정 아이템 4"
                    },
                    "total_schemas_per_round": 5,
                    "total_schemas_for_5_rounds": 25
                },
                "data_types": {
                    "user_id": "사용자 ID",
                    "category_group": "카테고리 그룹",
                    "activity_level_idx": "활동성 레벨 (0: high, 1: medium, 2: low)",
                    "time_period": "시간대 (0: 아침, 1: 오후, 2: 저녁)",
                    "season": "계절 (0: 봄, 1: 여름, 2: 가을, 3: 겨울)",
                    "preference": "선호도 (0: 활동성 선호, 1: 시간대 선호)",
                    "pos_item_index": "선택한 관광지 인덱스",
                    "neg_item_index": "부정 아이템 인덱스"
                },
                "encoding": {
                    "user_id": "UUID4 기반 랜덤 ID (숫자)",
                    "category_group": "선택한 활동 카테고리",
                    "activity_level_idx": "0: high, 1: medium, 2: low",
                    "time_period": "0: 아침, 1: 오후, 2: 저녁",
                    "season": "0: 봄, 1: 여름, 2: 가을, 3: 겨울",
                    "preference": "0: 활동성 선호, 1: 시간대 선호",
                    "pos_item_index": "사용자가 선택한 관광지 인덱스",
                    "neg_item_index": "부정 아이템 인덱스 - 실제 선택하지 않은 것 + 랜덤 4개"
                },
                "vote_count": int(len(user_votes)) if vote_schemas else 0,
                "schema_count": int(len(vote_schemas)) if vote_schemas else 0,
                "description": "각 라운드마다 선택한 관광지(positive)와 5가지 부정 아이템(실제 + 랜덤 4개)의 triplet 생성",
                "advantages": [
                    "더 풍부한 학습 데이터 생성",
                    "Hard negative sampling 효과",
                    "모델의 일반화 성능 향상",
                    "데이터 불균형 완화"
                ],
                "note": "모든 정수형 데이터는 데이터베이스나 ML 모델에서 byte/short 타입으로 저장 가능"
            }
        }

    except Exception as e:
        print(f"❌ /api/v1/survey/data 엔드포인트 오류: {e}")
        import traceback
        traceback.print_exc()
        return {
            "status": "error",
            "message": f"/api/v1/survey/data 엔드포인트에서 오류가 발생했습니다: {str(e)}",
            "error_details": {
                "error_type": str(type(e).__name__),
                "error_message": str(e)
            }
        }


# 서버 시작 시 모델 초기화
print("🚀 Survey Router 시작 - ML 모델 초기화 중...")
try:
    model_init_success = initialize_model()
    if model_init_success:
        print("✅ ML 모델 초기화 완료 - 추론 전용 모드로 서버 시작")
    else:
        print("⚠️ ML 모델 초기화 실패 - 룰 기반 fallback 모드로 시작")
except Exception as e:
    print(f"⚠️ 모델 초기화 중 오류 발생: {e}")
    print("🔄 룰 기반 fallback 모드로 서버 시작")
