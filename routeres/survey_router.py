from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List, Dict
import json
import random
import torch
import torch.nn as nn
import numpy as np
from pathlib import Path
import os
import sys
from datetime import datetime
import uuid
from jose import jwt, JWTError
from dotenv import load_dotenv
from pymongo import MongoClient
from services.data_loader import load_location_data_from_db
from schemas import Tourism

# 환경변수 로드
load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")

# MongoDB 연결
MONGO_ATLAS_URI = os.getenv("MONGO_ATLAS_URI", "")
print(
    f"🔍 MongoDB 연결 확인 - MONGO_ATLAS_URI: {MONGO_ATLAS_URI[:20]}..." if MONGO_ATLAS_URI else "❌ MONGO_ATLAS_URI가 설정되지 않음")

if MONGO_ATLAS_URI:
    try:
        _client = MongoClient(MONGO_ATLAS_URI)
        _user_db = _client.get_database("user_db")
        user_interaction_col = _user_db.get_collection("user_interaction")
        print(f"✅ MongoDB 연결 성공 - user_interaction 컬렉션 준비됨")
    except Exception as e:
        print(f"❌ MongoDB 연결 실패: {e}")
        user_interaction_col = None
else:
    print(f"❌ MONGO_ATLAS_URI가 없어서 user_interaction 컬렉션을 사용할 수 없습니다.")
    user_interaction_col = None

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

# FastAPI Router 생성
router = APIRouter()

# 템플릿 설정
templates = Jinja2Templates(
    directory=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "templates"))

# 사용자 선택 데이터를 저장할 전역 변수
user_selections = {
    "activity": None,
    "activity_level": None,
    "time": None,
    "season": None,
    "preference": None
}

# 로그인 관련 전역 변수
user_votes = []
positive_items = []
current_user_uuid = None
base_schema_storage = []


def get_current_user(request: Request) -> str:
    """JWT 토큰에서 사용자 ID 추출 (쿠키와 Authorization 헤더 모두 지원)"""
    # 쿠키에서 토큰 확인
    token = request.cookies.get("access_token")
    
    # Authorization 헤더에서 토큰 확인 (Bearer 토큰)
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
    
    if not token:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("sub")

        if not user_id:
            raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다")

        return user_id
    except jwt.JWTError as e:
        raise HTTPException(status_code=401, detail=f"토큰 검증 실패: {e}")


class SelectionData(BaseModel):
    step: str
    value: str

class CompleteSurveyData(BaseModel):
    """전체 설문조사 데이터 (인증 없이 사용)"""
    activity: str
    activity_level: str
    time: str
    season: str
    preference: str


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


def convert_to_base_schema_format(selections, user_uuid=None, user_votes=None):
    """사용자 선택을 base_schema 형식으로 변환 (UUID 문자열 사용 + 실제 투표 데이터 포함) - 5개의 개별 스키마 배열 반환"""
    # 로그인된 사용자의 UUID를 사용하거나, 없으면 랜덤 생성
    if user_uuid:
        # UUID 문자열을 그대로 사용
        user_id = user_uuid
    else:
        # UUID4로 매번 랜덤한 사용자 ID 생성 (문자열)
        user_id = str(uuid.uuid4())

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

    # 기본 스키마 정보
    base_info = [
        user_id,  # str - UUID 문자열
        activity,  # str
        activity_level,  # int (byte 범위)
        time,  # int (byte 범위)
        season,  # int (byte 범위)
        preference  # int (byte 범위)
    ]

    # 5개의 개별 스키마 배열 생성
    base_schemas = []

    # 투표 데이터가 있으면 실제 POS ITEM과 NEG ITEM 추가 (랜덤 NEG ITEM 4개는 추가하지 않음)
    if user_votes and len(user_votes) >= 5:
        try:
            # 중복 투표 제거 (같은 라운드에 여러 투표가 있는 경우)
            unique_votes = []
            seen_rounds = set()
            for vote in user_votes:
                if vote['round'] not in seen_rounds:
                    unique_votes.append(vote)
                    seen_rounds.add(vote['round'])

            if len(unique_votes) >= 5:
                # 관광지 데이터 로드
                tourism_data = load_tourism_data()
                if tourism_data:
                    # 모든 아이템을 인덱스로 매핑
                    all_items = {}
                    for group in tourism_data.get('groups', []):
                        for item in group.get('items', []):
                            all_items[item['index']] = item

                    # 각 라운드별로 개별 스키마 생성
                    for i in range(5):
                        if i < len(unique_votes):
                            vote = unique_votes[i]

                            # 사용자가 선택한 관광지 이름으로 올바른 인덱스 찾기
                            selected_item_name = vote.get('item_name', '')
                            pos_item_index = None

                            # 관광지 이름으로 인덱스 찾기
                            for group in tourism_data.get('groups', []):
                                for item in group.get('items', []):
                                    if item.get('name') == selected_item_name:
                                        pos_item_index = int(item['index'])
                                        print(f"🔍 관광지 이름 '{selected_item_name}' -> 인덱스 {pos_item_index}")
                                        break
                                if pos_item_index is not None:
                                    break

                            # 인덱스를 찾지 못한 경우 기존 방식 사용
                            if pos_item_index is None:
                                pos_item_index = int(vote.get('item_index', 0))
                                print(f"⚠️ 관광지 이름으로 인덱스를 찾지 못해 기존 값 사용: {pos_item_index}")

                            # NEG ITEM 찾기 (실제 선택하지 않은 아이템)
                            try:
                                # 해당 라운드의 추천 데이터에서 선택하지 않은 아이템 찾기
                                schema_data = convert_to_schema_format(selections)
                                recommendations = find_recommended_items(schema_data)

                                if "error" not in recommendations and i < len(recommendations['rounds']):
                                    round_data = recommendations['rounds'][i]
                                    choice = vote['choice']

                                    # 선택하지 않은 아이템 찾기
                                    if choice == 'option_a':
                                        neg_item = round_data['option_b']['item']
                                    else:  # choice == 'option_b'
                                        neg_item = round_data['option_a']['item']

                                    neg_item_index = int(neg_item['index'])
                                else:
                                    # 추천 데이터가 없으면 랜덤하게 선택
                                    available_items = [idx for idx in all_items.keys() if idx != pos_item_index]
                                    neg_item_index = random.choice(available_items) if available_items else 0

                            except Exception as e:
                                print(f"⚠️ 라운드 {i + 1} NEG ITEM 찾기 실패: {e}")
                                # 기본값 사용
                                neg_item_index = 0

                            # 개별 스키마 생성: [user_id, category_group, activity_level_idx, time_period, season, preference, pos_item, neg_item]
                            individual_schema = base_info + [pos_item_index, neg_item_index]
                            base_schemas.append(individual_schema)
                            print(f"✅ 라운드 {i + 1}: POS={pos_item_index}, NEG={neg_item_index}")
                        else:
                            # 투표가 없는 라운드는 0으로 채움
                            individual_schema = base_info + [0, 0]
                            base_schemas.append(individual_schema)
                            print(f"⚠️ 라운드 {i + 1}: 투표 없음, 0으로 채움")
                else:
                    print("❌ 관광지 데이터 로드 실패 - 기본 스키마만 반환")
                    # 기본 스키마 5개 생성
                    for i in range(5):
                        individual_schema = base_info + [0, 0]
                        base_schemas.append(individual_schema)
            else:
                print(f"⚠️ 고유 투표가 충분하지 않음: {len(unique_votes)}/5")
                # 기본 스키마 5개 생성
                for i in range(5):
                    individual_schema = base_info + [0, 0]
                    base_schemas.append(individual_schema)
        except Exception as e:
            print(f"❌ 투표 데이터 처리 중 오류: {e}")
            # 기본 스키마 5개 생성
            for i in range(5):
                individual_schema = base_info + [0, 0]
                base_schemas.append(individual_schema)
    else:
        print("⚠️ 투표 데이터가 없거나 충분하지 않음 - 기본 스키마 5개 생성")
        # 기본 스키마 5개 생성
        for i in range(5):
            individual_schema = base_info + [0, 0]
            base_schemas.append(individual_schema)

    return base_schemas


def load_tourism_data():
    """관광지 데이터 로드 - 개선된 오류 처리"""
    try:
        # 현재 디렉토리에서 찾고, 없으면 상위 디렉토리에서 찾기
        # ncf_modular 프로젝트 구조에 맞게 경로 설정
        ncf_modular_root = os.path.dirname(current_dir)  # test몽므의 상위 디렉토리 (.vscode)
        project_root = os.path.dirname(ncf_modular_root)  # .vscode의 상위 디렉토리

        file_paths = [
            # 현재 디렉토리에서 찾기
            'sort3preference.json',
            'sort3Wpreference.json',
            # ncf_modular 루트에서 찾기 (이미지에서 확인된 위치)
            os.path.join(ncf_modular_root, 'sort3preference.json'),
            os.path.join(ncf_modular_root, 'sort3Wpreference.json'),
            # 상위 디렉토리에서 찾기
            '../sort3preference.json',
            '../sort3Wpreference.json',
            # WhereWeGo-backend 경로들
            '../WhereWeGo-backend/model/sort3preference.json',
            '../WhereWeGo-backend/model/sort3Wpreference.json',
            'WhereWeGo-backend/model/sort3preference.json',
            'WhereWeGo-backend/model/sort3Wpreference.json',
            '../backend/model/sort4preference.json',
            os.path.join(project_root, 'WhereWeGo-backend/model/sort4preference.json'),
            os.path.join(project_root, 'WhereWeGo-backend/model/sort4Wpreference.json'),
            os.path.join(ncf_modular_root, 'WhereWeGo-backend/model/sort4preference.json'),
            os.path.join(ncf_modular_root, 'WhereWeGo-backend/model/sort4Wpreference.json'),
            # 절대 경로
            'C:/Users/user/Desktop/새 폴더 (3)/.vscode/WhereWeGo-backend/model/sort3preference.json',
            'C:/Users/user/Desktop/새 폴더 (3)/.vscode/WhereWeGo-backend/model/sort3Wpreference.json',
            'C:/Users/user/PycharmProjects/ncf_modular/sort4preference.json',
            'C:/Users/user/PycharmProjects/ncf_modular/sort4Wpreference.json'
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

                            # 첫 번째 그룹의 첫 번째 아이템 정보 출력 (디버깅용)
                            if data.get('groups') and len(data['groups']) > 0:
                                first_group = data['groups'][0]
                                if first_group.get('items') and len(first_group['items']) > 0:
                                    first_item = first_group['items'][0]
                                    print(
                                        f"🔍 첫 번째 아이템 예시: index={first_item.get('index')}, name={first_item.get('name')}")

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


def get_activity_level_keywords():
    """활동성 레벨별 키워드 매핑 - 새로운 매핑 시스템"""
    return {
        "자연풍경": {
            "high": ["해수욕장,해변", "섬", "워터테마파크"],
            "medium": ["전망대", "섬(내륙)"],
            "low": ["방조제", "아쿠아리움"]
        },
        "예술 감상": {
            "high": ["전시관", "미술관"],
            "medium": ["전시관", "미술관"],
            "low": ["전시관", "미술관"]
        },
        "관람및체험": {
            "high": ["테마파크", "자전거여행", "동물원"],
            "medium": ["실내동물원", "도자기/도예촌"],
            "low": ["과학관", "박물관", "기념관"]
        },
        "트레킹": {
            "high": ["갈맷길", "도보여행", "금정산둘레길", "둘레길", "남파랑길"],
            "medium": ["자연풍경", "자연산림"],  # 대체 카테고리
            "low": ["자연풍경", "자연산림"]  # 대체 카테고리
        },
        "휴양": {
            "high": ["자연휴양림", "관광농원"],  # 대체 카테고리
            "medium": ["숲", "수목원,식물원"],  # 대체 카테고리
            "low": ["온천", "리조트", "스파"]  # 휴양 카테고리 사용
        },
        "테마거리": {
            "high": ["테마거리"],
            "medium": ["먹자골목"],
            "low": ["카페거리"]
        },
        "자연산림": {
            "high": ["산"],
            "medium": ["계곡"],
            "low": ["유원지"]
        },
        "공연관람": {
            "high": ["공연장,연극극장"],
            "medium": ["공연장,연극극장"],
            "low": ["공연장,연극극장"]
        }
    }


def get_season_keywords():
    """계절별 추천 키워드 매핑 - 새로운 매핑 시스템"""
    return {
        "휴양": {
            0: ["저수지", "수목원,식물원", "숲", "관광농원", "자연휴양림"],  # 봄
            1: ["수목원,식물원", "온천", "숲", "관광농원", "자연휴양림"],  # 여름
            2: ["저수지", "숲", "관광농원", "자연휴양림"],  # 가을
            3: ["저수지", "수목원,식물원", "온천", "관광농원"]  # 겨울
        }
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


def get_time_period_keywords():
    """시간대별 추천 키워드 매핑 - 새로운 매핑 시스템"""
    return {
        "오전": {
            "자연풍경": ["전망대", "해수욕장,해변", "섬"],
            "자연산림": ["산", "계곡"],
            "관람및체험": ["박물관", "과학관"],
            "예술 감상": ["전시관", "미술관"],
            "트레킹": ["갈맷길", "도보여행"],
            "휴양": ["숲", "자연휴양림", "리조트", "스파", "온천"],
            "테마거리": ["카페거리"],
            "공연관람": ["공연장,연극극장"]
        },
        "오후": {
            "자연풍경": ["워터테마파크", "섬(내륙)", "아쿠아리움"],
            "자연산림": ["유원지", "계곡"],
            "관람및체험": ["테마파크", "동물원", "실내동물원", "박물관", "과학관"],
            "트레킹": ["갈맷길", "도보여행", "둘레길"],
            "테마거리": ["테마거리", "먹자골목"],
            "휴양": ["숲", "자연휴양림", "리조트", "스파", "온천"],
            "예술 감상": ["전시관", "미술관"],
            "공연관람": ["공연장,연극극장"]
        },
        "저녁": {
            "자연풍경": ["전망대", "방조제"],
            "자연산림": ["산"],
            "관람및체험": ["기념관", "도자기/도예촌"],
            "트레킹": ["자연풍경", "자연산림"],  # 대체
            "테마거리": ["카페거리", "먹자골목"],
            "휴양": ["온천", "리조트", "스파"],
            "예술 감상": ["전시관", "미술관"],
            "공연관람": ["공연장,연극극장"]
        }
    }


def calculate_weighted_score(item: Dict, user_schema: List) -> float:
    """ML 모델 메인 시스템에서는 단순한 기본 점수만 반환 (디버그 출력 제거)"""
    # ML 모델이 메인으로 작동하므로 룰 기반 점수 계산은 최소화
    # 기본적으로 모든 아이템에 동일한 점수 부여
    return 0.5


def estimate_item_activity_level(item: Dict, user_category: str = None) -> str:
    """아이템의 활동성 레벨 추정 - 사용자 카테고리 기반 정확한 매칭"""
    category = item.get('category', '').lower()
    name = item.get('name', '').lower()
    category_group = item.get('category_group', '').lower()

    # 텍스트 검사용 문자열 생성
    text_to_check = f"{name} {category} {category_group}"

    # 사용자 카테고리가 있으면 해당 카테고리의 키워드 사용
    if user_category:
        activity_keywords = get_activity_level_keywords()
        if user_category in activity_keywords:
            keywords_map = activity_keywords[user_category]

            # 높은 활동성 키워드 확인
            for keyword in keywords_map.get("high", []):
                if keyword.lower() in text_to_check:
                    return "high"

            # 낮은 활동성 키워드 확인
            for keyword in keywords_map.get("low", []):
                if keyword.lower() in text_to_check:
                    return "low"

            # 중간 활동성 키워드 확인
            for keyword in keywords_map.get("medium", []):
                if keyword.lower() in text_to_check:
                    return "medium"

    # 기존 방식 (fallback)
    # 높은 활동성 키워드
    high_activity_keywords = ['트레킹', '등산', '하이킹', '워터파크', '테마파크', '체험', '어드벤처', '갈맷길', '도보여행']
    # 낮은 활동성 키워드
    low_activity_keywords = ['휴양', '카페', '전시', '박물관', '아쿠아리움', '온천', '스파', '기념관', '과학관']

    for keyword in high_activity_keywords:
        if keyword in text_to_check:
            return "high"

    for keyword in low_activity_keywords:
        if keyword in text_to_check:
            return "low"

    # 기본값은 중간
    return "medium"


def estimate_item_season_suitability(item: Dict, season: str, user_category: str = None) -> bool:
    """아이템의 계절 적합성 추정 - 사용자 카테고리 기반 정확한 매칭"""
    category = item.get('category', '').lower()
    name = item.get('name', '').lower()
    category_group = item.get('category_group', '').lower()

    text_to_check = f"{name} {category} {category_group}"

    # 사용자 카테고리가 휴양이면 새로운 계절별 규칙 사용
    if user_category == "휴양":
        season_keywords_map = get_season_keywords()
        if "휴양" in season_keywords_map:
            # 계절 인덱스 변환 (봄=0, 여름=1, 가을=2, 겨울=3)
            season_map = {"봄": 0, "여름": 1, "가을": 2, "겨울": 3}
            season_idx = season_map.get(season, -1)

            if season_idx >= 0 and season_idx in season_keywords_map["휴양"]:
                suitable_keywords = season_keywords_map["휴양"][season_idx]

                # 적합한 키워드가 있으면 True
                for keyword in suitable_keywords:
                    if keyword.lower() in text_to_check:
                        return True

    # 기존 방식 (fallback)
    # 계절별 적합한 키워드
    season_keywords = {
        "봄": ['벚꽃', '꽃', '산책', '공원', '전망대'],
        "여름": ['해변', '해수욕장', '워터파크', '수영', '시원', '바다'],
        "가을": ['단풍', '산', '트레킹', '전망대', '공원'],
        "겨울": ['온천', '스파', '실내', '박물관', '전시', '카페']
    }

    # 계절에 부적합한 키워드
    unsuitable_keywords = {
        "봄": ['워터파크', '해수욕장'],
        "여름": ['온천', '스파'],
        "가을": ['해수욕장', '워터파크'],
        "겨울": ['해수욕장', '워터파크', '해변']
    }

    # 부적합 키워드가 있으면 False
    for keyword in unsuitable_keywords.get(season, []):
        if keyword in text_to_check:
            return False

    # 적합 키워드가 있으면 True
    for keyword in season_keywords.get(season, []):
        if keyword in text_to_check:
            return True

    # 기본적으로 모든 계절에 적합
    return True


def estimate_item_time_suitability(item: Dict, time_period: str, user_category: str = None) -> bool:
    """아이템의 시간대 적합성 추정 - 사용자 카테고리 기반 정확한 매칭"""
    category = item.get('category', '').lower()
    name = item.get('name', '').lower()
    category_group = item.get('category_group', '').lower()

    text_to_check = f"{name} {category} {category_group}"

    # 사용자 카테고리가 있으면 해당 카테고리의 시간대별 키워드 사용
    if user_category:
        time_keywords = get_time_period_keywords()
        if time_period in time_keywords and user_category in time_keywords[time_period]:
            suitable_keywords = time_keywords[time_period][user_category]

            # 적합한 키워드가 있으면 True
            for keyword in suitable_keywords:
                if keyword.lower() in text_to_check:
                    return True

    # 기존 방식 (fallback)
    # 시간대별 적합한 키워드
    time_keywords = {
        "오전": ['전망대', '산', '공원', '산책', '카페', '박물관', '과학관'],
        "오후": ['해변', '테마파크', '체험', '관람', '쇼핑', '동물원', '워터파크'],
        "저녁": ['야경', '전망대', '카페', '식당', '공연', '문화', '방조제']
    }

    # 시간대에 부적합한 키워드
    unsuitable_keywords = {
        "오전": ['야경', '공연', '클럽', '방조제'],
        "오후": ['야경', '클럽'],
        "저녁": ['해수욕장', '워터파크', '등산']
    }

    # 부적합 키워드가 있으면 False
    for keyword in unsuitable_keywords.get(time_period, []):
        if keyword in text_to_check:
            return False

    # 적합 키워드가 있으면 True
    for keyword in time_keywords.get(time_period, []):
        if keyword in text_to_check:
            return True

    # 기본적으로 모든 시간대에 적합
    return True


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
        # 규칙이 없으면 모든 아이템 반환
        return items

    rules = category_rules[category_group]

    # 교집합 계산을 위한 키워드 세트 생성
    intersection_keywords = set()

    if preference == 0:  # 활동성 선호
        # 카테고리 + 활동성 교집합
        if activity_str in rules.get("activity_rules", {}):
            activity_keywords = rules["activity_rules"][activity_str]
            intersection_keywords.update(activity_keywords)
            print(f"🎯 활동성 선호 교집합: {category_group} + {activity_str} = {activity_keywords}")

    elif preference == 1:  # 시간대 선호
        # 카테고리 + 시간대 교집합
        if time_period in rules.get("time_rules", {}):
            time_keywords = rules["time_rules"][time_period]
            intersection_keywords.update(time_keywords)
            print(f"🎯 시간대 선호 교집합: {category_group} + {time_str} = {time_keywords}")

    # 교집합 키워드가 없으면 모든 아이템 반환
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

        # 교집합 키워드 매칭 확인
        matched_keywords = []
        for keyword in intersection_keywords:
            if keyword.lower() in text_to_check:
                matched_keywords.append(keyword)

        # 교집합 키워드가 하나라도 매칭되면 포함
        if matched_keywords:
            item['matched_keywords'] = matched_keywords  # 디버깅용
            filtered_items.append(item)

    print(f"🎯 교집합 기반 필터링 완료: {len(intersection_keywords)}개 키워드로 {len(filtered_items)}개 아이템 필터링")

    # 필터링된 아이템이 없으면 원본 아이템 반환
    if not filtered_items:
        print(f"⚠️ 교집합 매칭 아이템이 없어 원본 아이템 반환")
        return items

    return filtered_items


def filter_items_by_preferences(items: List[Dict], user_schema: List) -> List[Dict]:
    """ML 모델 메인 시스템에서는 단순한 필터링만 수행 (디버그 출력 제거)"""
    # ML 모델이 메인으로 작동하므로 룰 기반 필터링은 최소화
    # 기본적으로 모든 아이템에 동일한 점수 부여하고 그대로 반환
    for item in items:
        item['weighted_score'] = 0.5

    return items


def find_recommended_items(user_schema: List) -> Dict:
    """사용자 스키마를 바탕으로 5라운드 추천 아이템 찾기 (총 10개 서로 다른 관광지) - 강화된 랜덤성"""
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

        for group in tourism_data.get('groups', []):
            if group.get('category_group') == target_category_group:
                items = group.get('items', [])
                if items:
                    target_items.extend(items)
            else:
                items = group.get('items', [])
                if items:
                    other_category_items.extend(items)

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
        filtered_target_items = get_intersection_based_recommendations(target_items, user_schema)

        # 필터링된 아이템의 매칭된 키워드 출력
        print(f"📊 교집합 매칭 아이템:")
        for i, item in enumerate(filtered_target_items[:5]):
            matched_keywords = item.get('matched_keywords', [])
            print(f"  {i + 1}. {item.get('name', 'Unknown')} - 매칭 키워드: {matched_keywords}")

        if not filtered_target_items:
            return {"error": f"{activity} 카테고리에서 관광지를 찾을 수 없습니다."}

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
                "primary": primary_item,  # 프론트엔드 호환성
                "alternative": alternative_item,  # 프론트엔드 호환성
                "randomized": True,
                "random_seed": int(time.time() * 1000) % 1000000  # 랜덤 시드 기록
            })

        return {
            "rounds": rounds,
            "total_rounds": int(5),  # numpy.int64 → int 변환
            "total_places": int(10),  # numpy.int64 → int 변환
            "randomization_info": {
                "enhanced_randomness": True,
                "quality_pool_expanded": True,
                "shuffled_pools": True,
                "varied_selection_probability": True
            },
            "user_preferences": {
                "activity": str(activity),  # 문자열 보장
                "activity_level": str(["높음", "중간", "낮음"][activity_level]),  # 문자열 보장
                "time_period": str(["오전", "오후", "저녁"][time_period]),  # 문자열 보장
                "season": str(["봄", "여름", "가을", "겨울"][season]),  # 문자열 보장
                "preference": str(["활동성", "시간대"][preference])  # 문자열 보장
            }
        }

    except Exception as e:
        print(f"❌ find_recommended_items 오류: {e}")
        import traceback
        traceback.print_exc()
        return {"error": f"추천 생성 중 오류가 발생했습니다: {str(e)}"}


@router.get("", response_class=HTMLResponse)
async def read_root(request: Request):
    """메인 페이지 - 로그인 상태 확인 후 설문조사 진행"""
    # 로그인 상태 확인
    print(f"🔍 설문조사 페이지 접근 - 쿠키 확인 중...")
    print(f"🔍 요청 쿠키: {request.cookies}")

    token = request.cookies.get("access_token")

    if not token:
        # 로그인되지 않은 경우 즉시 Google 로그인 페이지로 리다이렉트
        print("🔐 로그인되지 않음")
        return # (url="http://localhost:8000/api/v1/auth/google/login", status_code=302)

    try:
        # 토큰 검증
        print(f"🔍 토큰 검증 시작 - SECRET_KEY: {SECRET_KEY[:20]}...")
        print(f"🔍 토큰: {token[:50]}...")

        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("sub")

        print(f"🔍 토큰 디코딩 성공 - user_id: {user_id}")

        if not user_id:
            # 유효하지 않은 토큰인 경우 즉시 Google 로그인 페이지로 리다이렉트
            print("🔐 유효하지 않은 토큰")
            return # RedirectResponse(url="http://localhost:8000/api/v1/auth/google/login", status_code=302)

        # 로그인된 사용자 - 설문조사 진행
        print(f"✅ 로그인된 사용자: {user_id} - 설문조사 시작")
        global current_user_uuid
        current_user_uuid = user_id

        return templates.TemplateResponse("index.html", {
            "request": request,
            "step": "activity",
            "selections": user_selections,
            "user_id": user_id
        })

    except jwt.JWTError as e:
        # 토큰 검증 실패 - 즉시 Google 로그인 페이지로 리다이렉트
        print(f"🔐 토큰 검증 실패: {e}")
        return # RedirectResponse(url="http://localhost:8000/api/v1/auth/google/login", status_code=302)


@router.post("/select")
async def make_selection(selection: SelectionData, request: Request, user_id: str = Depends(get_current_user)):
    """사용자 선택 처리"""
    if selection.step == "activity":
        user_selections["activity"] = selection.value
        return {"next_step": "activity_level", "selections": user_selections}
    elif selection.step == "activity_level":
        user_selections["activity_level"] = selection.value
        return {"next_step": "time", "selections": user_selections}
    elif selection.step == "time":
        user_selections["time"] = selection.value
        return {"next_step": "season", "selections": user_selections}
    elif selection.step == "season":
        user_selections["season"] = selection.value
        return {"next_step": "preference", "selections": user_selections}
    elif selection.step == "preference":
        user_selections["preference"] = selection.value
        return {"next_step": "complete", "selections": user_selections}


@router.post("/submit")
async def submit_complete_survey(survey_data: CompleteSurveyData):
    """
    전체 설문조사 데이터를 한 번에 처리 (인증 불필요)
    프론트엔드에서 모든 설문 데이터를 한 번에 전송할 때 사용
    """
    global user_selections, current_user_uuid
    
    # 전역 user_selections 업데이트
    user_selections.update({
        "activity": survey_data.activity,
        "activity_level": survey_data.activity_level,
        "time": survey_data.time,
        "season": survey_data.season,
        "preference": survey_data.preference
    })
    
    print(f"✅ 설문조사 완료: {user_selections}")
    
    # DB에 설문 결과 저장
    try:
        if user_interaction_col is not None:
            # 임시 user_id 생성 (로그인하지 않은 경우)
            user_id = current_user_uuid if current_user_uuid else str(uuid.uuid4())
            
            # 설문 결과 문서 생성
            survey_doc = {
                "user_id": user_id,
                "type": "survey_submission",
                "survey_data": {
                    "activity": survey_data.activity,
                    "activity_level": survey_data.activity_level,
                    "time": survey_data.time,
                    "season": survey_data.season,
                    "preference": survey_data.preference
                },
                "timestamp": datetime.now()
            }
            
            # MongoDB에 저장
            result = user_interaction_col.insert_one(survey_doc)
            print(f"✅ 설문 결과 DB 저장 완료: {result.inserted_id}")
            print(f"📊 저장된 설문 데이터: {survey_doc}")
        else:
            print(f"⚠️ user_interaction 컬렉션을 사용할 수 없어 DB 저장 생략")
    except Exception as e:
        print(f"❌ 설문 결과 DB 저장 실패: {e}")
    
    return {
        "status": "success",
        "message": "설문조사가 완료되었습니다.",
        "selections": user_selections,
        "next_step": "ml_recommendations"
    }


def create_vote_schemas(user_uuid=None):
    """투표 기록을 스키마 형식으로 변환 - 각 투표마다 추가 랜덤 부정 아이템 4개 포함"""
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
            if vote['round'] not in seen_rounds:
                unique_votes.append(vote)
                seen_rounds.add(vote['round'])

        if len(unique_votes) < 5:
            print(f"⚠️ 고유 투표가 충분하지 않음: {len(unique_votes)}/5")
            return None

        print(f"✅ 고유 투표 {len(unique_votes)}개 확인됨")

        # 기본 사용자 스키마 정보 (vote_schema용 - UUID 6자리 랜덤)
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
            round_num = vote['round']
            choice = vote['choice']  # 'option_a' 또는 'option_b'

            # 🚨 수정: 저장된 아이템 인덱스 직접 사용 (새로운 추천 생성하지 않음)
            try:
                pos_item_index = int(vote['item_index'])  # 사용자가 선택한 아이템 인덱스
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
                            neg_item = round_data['option_b']['item']
                        else:  # choice == 'option_b'
                            neg_item = round_data['option_a']['item']

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


@router.get("/data")
async def get_user_survey_data(request: Request, user_id: str = Depends(get_current_user)):
    """DB에서 사용자의 설문조사 데이터 조회"""
    try:
        print(f"🔍 /data 엔드포인트 호출됨 - user_id: {user_id}")
        
        # MongoDB에서 사용자 데이터 조회
        if user_interaction_col:
            try:
                # 사용자의 설문조사 데이터 조회
                user_data = user_interaction_col.find_one({"user_id": user_id})
                print(f"🔍 DB에서 조회된 사용자 데이터: {user_data}")
                
                if user_data and user_data.get("user_schema"):
                    print(f"✅ 기존 설문조사 데이터 발견")
                    return {
                        "status": "success",
                        "user_schema": user_data.get("user_schema", {}),
                        "message": "기존 설문조사 데이터를 찾았습니다."
                    }
                else:
                    print(f"📝 기존 설문조사 데이터 없음")
                    return {
                        "status": "no_data",
                        "message": "기존 설문조사 데이터가 없습니다.",
                        "user_schema": {}
                    }
            except Exception as e:
                print(f"❌ DB 조회 오류: {e}")
                return {
                    "status": "error",
                    "message": f"데이터베이스 조회 중 오류가 발생했습니다: {str(e)}"
                }
        else:
            print(f"⚠️ MongoDB 연결 없음 - 메모리 데이터 사용")
            # MongoDB 연결이 없는 경우 메모리 데이터 사용
            if not all(value is not None for value in user_selections.values()):
                missing_fields = [str(key) for key, value in user_selections.items() if value is None]
                print(f"⚠️ 선택이 완료되지 않음. 누락된 필드: {missing_fields}")
                return {
                    "status": "incomplete",
                    "message": "모든 선택을 완료해주세요.",
                    "current_selections": user_selections,
                    "missing_fields": missing_fields
                }

        # 기본 사용자 스키마 생성 (base_schema용으로 UUID 문자열 사용 + 실제 투표 데이터 포함)
        try:
            base_schema = convert_to_base_schema_format(user_selections, user_id, user_votes)
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
                vote_schemas = create_vote_schemas(user_id)
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
            "BASE_SCHEMA": base_schema,  # 5개의 개별 스키마 배열
            "vote_schemas": vote_schemas,
            "total_votes": len(user_votes),
            "raw_selections": user_selections,
            "raw_votes": user_votes,
            "database_info": {
                "collection": "user_interaction",
                "database": "user_db",
                "BASE_SCHEMA_saved": len(user_votes) >= 5,
                "schema_count": len(base_schema) if base_schema else 0,
                "description": "BASE_SCHEMA는 5라운드 설문조사 완료 시 MongoDB user_interaction 컬렉션에 자동 저장됩니다."
            },
            "schema_explanation": {
                "base_format": "[user_id, category_group, activity_level_idx, time_period, season, preference, pos_item, neg_item] (5개의 개별 스키마 배열)",
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
                    "user_id": "로그인 UUID 문자열 (base_schema용)",
                    "category_group": "선택한 활동 카테고리",
                    "activity_level_idx": "0: high, 1: medium, 2: low",
                    "time_period": "0: 아침, 1: 오후, 2: 저녁",
                    "season": "0: 봄, 1: 여름, 2: 가을, 3: 겨울",
                    "preference": "0: 활동성 선호, 1: 시간대 선호",
                    "pos_item": "각 라운드에서 사용자가 선택한 관광지 인덱스",
                    "neg_item": "각 라운드에서 사용자가 선택하지 않은 관광지 인덱스 (랜덤 NEG ITEM 4개는 포함하지 않음)"
                },
                "vote_count": int(len(user_votes)) if vote_schemas else 0,  # numpy.int64 → int 변환
                "schema_count": int(len(vote_schemas)) if vote_schemas else 0,  # numpy.int64 → int 변환
                "description": "BASE_SCHEMA: 5라운드의 실제 선택 데이터만 포함 (POS ITEM + 실제 선택하지 않은 NEG ITEM). VOTE_SCHEMA: 각 라운드마다 선택한 관광지(positive)와 5가지 부정 아이템(실제 + 랜덤 4개)의 triplet 생성",
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
        print(f"❌ /data 엔드포인트 오류: {e}")
        import traceback
        traceback.print_exc()
        return {
            "status": "error",
            "message": f"/data 엔드포인트에서 오류가 발생했습니다: {str(e)}",
            "error_details": {
                "error_type": str(type(e).__name__),
                "error_message": str(e)
            }
        }


@router.get("/recommend")
async def get_recommend(request: Request, user_id: str = Depends(get_current_user)):
    """단수형 경로 '/recommend' 요청을 '/recommendations'로 처리"""
    return await get_recommendations(request, user_id)

@router.get("/place-recommendations")
async def get_recommendations(request: Request, user_id: str = Depends(get_current_user)):
    """사용자 선택을 바탕으로 관광지 추천 - 강화된 랜덤성"""
    try:
        # 모든 선택이 완료되었는지 확인
        if not all(value is not None for value in user_selections.values()):
            return {
                "status": "incomplete",
                "message": "모든 선택을 완료해주세요.",
                "missing_fields": [str(key) for key, value in user_selections.items() if value is None]
            }

        # 🎲 매번 다른 결과를 위해 추가 랜덤 시드 설정
        import time
        random.seed(int(time.time() * 1000) % 1000000)

        # 스키마 데이터 생성 (vote_schema용 - UUID 6자리 랜덤)
        schema_data = convert_to_schema_format(user_selections)

        # 스키마 데이터 검증
        if not schema_data or len(schema_data) < 6:
            return {
                "status": "error",
                "message": "사용자 선택 데이터가 올바르지 않습니다."
            }

        # 추천 아이템 찾기 (룰 기반 추천)
        recommendations = find_recommended_items(schema_data)

        if "error" in recommendations:
            return {
                "status": "error",
                "message": recommendations["error"]
            }

        return {
            "status": "success",
            "recommendations": recommendations.get("rounds", []),  # ✅ 배열로 반환
            "total_rounds": recommendations.get("total_rounds", 5),
            "total_places": recommendations.get("total_places", 10),
            "user_preferences": recommendations.get("user_preferences", {}),
            "randomization_info": {
                "enhanced_randomness": True,
                "timestamp_seed": int(int(time.time() * 1000) % 1000000),
                "description": "매번 다른 결과를 위해 시간 기반 랜덤 시드 적용",
                **recommendations.get("randomization_info", {})
            }
        }

    except Exception as e:
        print(f"❌ get_recommendations 오류: {e}")
        import traceback
        traceback.print_exc()
        return {
            "status": "error",
            "message": f"추천 서비스에 문제가 발생했습니다: {str(e)}"
        }


class VoteData(BaseModel):
    round_number: int  # 1-5 라운드 번호
    choice: str  # "option_a" 또는 "option_b"
    item_name: str  # 선택한 관광지 이름
    item_index: int  # 선택한 관광지 인덱스

class SingleVote(BaseModel):
    """프론트엔드에서 보내는 단일 투표 데이터"""
    round: int  # 1-5 라운드 번호
    choice: str  # "option_a" 또는 "option_b"
    item_name: str  # 선택한 관광지 이름

class VotesSubmission(BaseModel):
    """프론트엔드에서 보내는 전체 투표 데이터"""
    votes: List[SingleVote]  # 투표 배열

class MLRecommendationResponse(BaseModel):
    """ML 추천 응답"""
    status: str
    recommendations: List[Dict]
    total_count: int
    model_info: Dict
    message: str


# 사용자 선택 결과 저장
user_votes = []

# ML 모델 전역 변수 (추론 전용)
loaded_ncf_model = None
model_data = None
MODEL_PATH = "checkpoints/model_epoch_new.pth"


# 서버 시작 시점에 모델 로드
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
            os.path.join(current_dir, 'checkpoints', 'model_epoch_new.pth'),
            os.path.join(current_dir, '..', MODEL_PATH),
            os.path.join(current_dir, 'ncf_inner', MODEL_PATH),
            os.path.join(current_dir, '..', 'dataMaking', 'ncf_inner', 'checkpoints', 'model_epoch_new.pth'),
            os.path.join(current_dir, '..', 'WhereWeGo-backend', 'model', MODEL_PATH),
            os.path.join(current_dir, '..', 'WhereWeGo-backend', 'checkpoints', 'model_epoch_new.pth'),
            'C:/Users/user/Desktop/새 폴더 (2)/.vscode/WhereWeGo-backend/checkpoints/model_epoch_new.pth',
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


def get_tourism_data_in_tester_format():
    """tester.py 형식으로 관광지 데이터를 변환"""
    tourism_data = load_tourism_data()
    if not tourism_data:
        return {}

    # tester.py 형식으로 변환: {index: {name, category, category_group, db_id, ...}}
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
                    'final_score': item.get('final_score', 0),  # final_score 복원
                    'db_id': item.get('_id', ''),  # 실제 DB ID (MongoDB ObjectId) 추가
                    'content_id': item.get('content_id', '')  # content_id도 있다면 추가
                }
    return tourism_dict


def get_survey_matching_recommendations(user_context, tourism_data, selected_items, valid_indices, predictions_np,
                                        count=3):
    """사용자 설문조사 조건에 맞는 관광지들을 ML 점수 순으로 추천"""
    print(
        f"🏆 설문조사 조건 매칭 추천 시작: {user_context['category_group']} 카테고리, 활동성={user_context['activity_level']}, 시간대={user_context['time_period']}, 계절={user_context['season']}")

    # ML 점수와 함께 매칭 아이템들을 저장 (점수 순서 유지)
    matching_items_with_scores = []

    # valid_indices는 이미 ML 점수 순으로 정렬되어 있음
    for item_idx in valid_indices:
        if item_idx in selected_items:
            continue

        if item_idx not in tourism_data:
            continue

        item_info = tourism_data[item_idx]

        # 카테고리 매칭 확인
        item_category = item_info.get('category_group', '')
        if item_category != user_context['category_group']:
            continue

        # 활동성 레벨 매칭 확인
        activity_level_map = {0: "high", 1: "medium", 2: "low"}
        user_activity_str = activity_level_map.get(user_context['activity_level'], "medium")

        # 아이템의 활동성 레벨 추정
        estimated_activity = estimate_item_activity_level(item_info, user_context['category_group'])

        # 활동성 매칭 (정확히 일치하거나 유사한 경우)
        if estimated_activity == user_activity_str or estimated_activity == "medium":
            # ML 점수와 함께 저장 (이미 valid_indices가 점수 순이므로 순서 유지)
            ml_score = predictions_np[item_idx] if item_idx < len(predictions_np) else 0.0
            matching_items_with_scores.append((item_idx, ml_score))
            print(f"   ✅ 매칭 아이템: {item_info['name']} (활동성: {estimated_activity}, ML점수: {ml_score:.4f})")

    print(f"📊 설문조사 조건 매칭 후보: {len(matching_items_with_scores)}개")

    # 후보가 충분하지 않으면 조건을 완화 (ML 점수 순서 유지)
    if len(matching_items_with_scores) < count:
        print(f"⚠️ 매칭 후보 부족 ({len(matching_items_with_scores)}개), 조건 완화하여 재검색")
        for item_idx in valid_indices:
            if item_idx in selected_items:
                continue
            if any(item_idx == existing_item for existing_item, _ in matching_items_with_scores):
                continue

            if item_idx not in tourism_data:
                continue

            item_info = tourism_data[item_idx]

            # 카테고리만 매칭 (활동성 조건 완화)
            item_category = item_info.get('category_group', '')
            if item_category == user_context['category_group']:
                ml_score = predictions_np[item_idx] if item_idx < len(predictions_np) else 0.0
                matching_items_with_scores.append((item_idx, ml_score))
                print(f"   ✅ 완화 조건 매칭: {item_info['name']} (ML점수: {ml_score:.4f})")

    # 여전히 부족하면 다른 카테고리에서도 찾기 (ML 점수 순서 유지)
    if len(matching_items_with_scores) < count:
        print(f"⚠️ 여전히 후보 부족 ({len(matching_items_with_scores)}개), 다른 카테고리에서도 검색")
        for item_idx in valid_indices:
            if item_idx in selected_items:
                continue
            if any(item_idx == existing_item for existing_item, _ in matching_items_with_scores):
                continue

            if item_idx not in tourism_data:
                continue

            item_info = tourism_data[item_idx]
            ml_score = predictions_np[item_idx] if item_idx < len(predictions_np) else 0.0
            matching_items_with_scores.append((item_idx, ml_score))
            print(
                f"   ✅ 다른 카테고리 후보: {item_info['name']} ({item_info.get('category_group', '')}) (ML점수: {ml_score:.4f})")

    # ML 점수 순으로 정렬 (내림차순) - 이미 valid_indices가 정렬되어 있지만 확실히 하기 위해
    matching_items_with_scores.sort(key=lambda x: x[1], reverse=True)

    # 상위 count개 선택 (ML 점수 순으로)
    if len(matching_items_with_scores) >= count:
        selected = [item_idx for item_idx, _ in matching_items_with_scores[:count]]
    else:
        selected = [item_idx for item_idx, _ in matching_items_with_scores]  # 후보가 부족하면 모든 후보 선택

    print(f"🎯 설문조사 조건 매칭 최종 선택: {len(selected)}개 (ML 점수 순)")
    for i, item_idx in enumerate(selected):
        if item_idx in tourism_data:
            item_info = tourism_data[item_idx]
            ml_score = predictions_np[item_idx] if item_idx < len(predictions_np) else 0.0
            print(f"   {i + 1}. {item_info['name']} ({item_info.get('category_group', '')}) - ML점수: {ml_score:.4f}")

    return selected


def get_developer_recommendations(user_category, tourism_data, selected_items, count=3):
    """개발자 추천: final_score가 2-3점인 아이템들을 랜덤으로 선택"""
    print(f"👨‍💻 개발자 추천 시작: {user_category} 카테고리에서 final_score 2-3점 아이템 찾기")

    # 사용자 카테고리에 해당하는 아이템들 중에서 final_score가 2-3점인 것들 필터링
    candidate_items = []

    for item_id, item_info in tourism_data.items():
        # 이미 선택된 아이템은 제외
        if item_id in selected_items:
            continue

        # 카테고리 매칭 확인
        item_category = item_info.get('category_group', '')
        if item_category != user_category:
            continue

        # final_score가 2-3점인지 확인
        final_score = item_info.get('final_score', 0)
        if 2.0 <= final_score <= 3.0:
            candidate_items.append(item_id)
            print(f"   ✅ 후보 아이템: {item_info['name']} (final_score: {final_score})")

    print(f"📊 개발자 추천 후보: {len(candidate_items)}개")

    # 후보가 충분하지 않으면 final_score 범위를 확장
    if len(candidate_items) < count:
        print(f"⚠️ 후보 부족 ({len(candidate_items)}개), final_score 범위 확장 (1.5-3.5)")
        for item_id, item_info in tourism_data.items():
            if item_id in selected_items or item_id in candidate_items:
                continue

            item_category = item_info.get('category_group', '')
            if item_category != user_category:
                continue

            final_score = item_info.get('final_score', 0)
            if 1.5 <= final_score <= 3.5:
                candidate_items.append(item_id)
                print(f"   ✅ 확장 후보: {item_info['name']} (final_score: {final_score})")

    # 여전히 부족하면 다른 카테고리에서도 찾기
    if len(candidate_items) < count:
        print(f"⚠️ 여전히 후보 부족 ({len(candidate_items)}개), 다른 카테고리에서도 검색")
        for item_id, item_info in tourism_data.items():
            if item_id in selected_items or item_id in candidate_items:
                continue

            final_score = item_info.get('final_score', 0)
            if 1.5 <= final_score <= 3.5:
                candidate_items.append(item_id)
                print(
                    f"   ✅ 다른 카테고리 후보: {item_info['name']} ({item_info.get('category_group', '')}) (final_score: {final_score})")

    # 랜덤하게 선택
    if len(candidate_items) >= count:
        selected = random.sample(candidate_items, count)
    else:
        selected = candidate_items  # 후보가 부족하면 모든 후보 선택

    print(f"🎯 개발자 추천 최종 선택: {len(selected)}개")
    for item_id in selected:
        if item_id in tourism_data:
            item_info = tourism_data[item_id]
            print(f"   - {item_info['name']} (final_score: {item_info.get('final_score', 0)})")

    return selected


async def recommend_with_vote_context(model, user_vote_schemas, data, tourism_data, device, top_k=10):
    """vote_schema 컨텍스트를 기반으로 한 추천 (3가지 카테고리로 분류) - 10개 추천"""
    # 매번 다른 결과를 위해 현재 시간을 시드로 사용
    import time
    random.seed(int(time.time() * 1000) % 1000000)

    print(f"🎯 Vote schema 기반 컨텍스트 추천 시작 (10개 추천, 3가지 카테고리)")
    
    # DB에서 Tourism 데이터 로드
    try:
        db_tourism_list = await load_location_data_from_db()
        db_tourism_dict = {place.name: place for place in db_tourism_list}  # 이름으로 매칭
        print(f"✅ DB에서 {len(db_tourism_dict)}개 Tourism 데이터 로드 완료")
    except Exception as e:
        print(f"⚠️ DB Tourism 데이터 로드 실패: {e}, 기본 정보만 사용")
        db_tourism_dict = {}

    # vote_schema에서 사용자 컨텍스트 정보 추출 (첫 번째 스키마 사용)
    if not user_vote_schemas or len(user_vote_schemas[0]) < 6:
        print("❌ vote_schema 형식이 올바르지 않습니다.")
        return []

    first_schema = user_vote_schemas[0]
    user_context = {
        'category_group': first_schema[1],  # category_group (str)
        'activity_level': first_schema[2],  # activity_level (int: 0-2)
        'time_period': first_schema[3],  # time_period (int: 0-2)
        'season': first_schema[4],  # season (int: 0-3)
        'preference': first_schema[5]  # preference (int: 0-1)
    }

    print(f"📊 추출된 사용자 컨텍스트: {user_context}")

    # 선택된 아이템들 (positive items) 추출 - 중복 제거
    selected_items = set()
    for schema in user_vote_schemas:
        if len(schema) >= 7:  # pos_item_index가 7번째 인덱스
            selected_items.add(schema[6])  # pos_item_index

    selected_items = list(selected_items)
    print(f"🚫 제외할 아이템들: {selected_items} (총 {len(selected_items)}개)")

    # 첫 번째 스키마에서 user_id 추출
    first_schema = user_vote_schemas[0]
    user_id_from_schema = first_schema[0]  # UUID4로 생성된 랜덤 ID

    # 모델의 사용자 수 확인
    model_n_users = model.user_embedding_gmf.weight.shape[0]

    # user_id를 모델 인덱스로 변환 (동적 매핑)
    if 'user_id_to_idx' in data and user_id_from_schema in data['user_id_to_idx']:
        user_idx = data['user_id_to_idx'][user_id_from_schema]
    else:
        # 새로운 사용자 ID에 대해 동적으로 인덱스 할당
        if 'user_id_to_idx' not in data:
            data['user_id_to_idx'] = {}

        # 사용 가능한 인덱스 찾기 (0부터 시작)
        existing_indices = set(data['user_id_to_idx'].values())
        user_idx = 0
        while user_idx in existing_indices and user_idx < model_n_users - 1:
            user_idx += 1

        # 새로운 사용자 ID 매핑 추가
        data['user_id_to_idx'][user_id_from_schema] = user_idx
        print(f"🆕 새로운 사용자 ID {user_id_from_schema}에 인덱스 {user_idx} 할당")

    print(f"🎭 실제 사용자 ID: {user_id_from_schema}, 모델 인덱스: {user_idx}")
    print(f"📊 모델 사용자 수: {model_n_users}")

    # 모든 아이템에 대한 예측 점수 계산
    all_item_indices = list(data['item_id_to_model_idx'].values()) if 'item_id_to_model_idx' in data else list(
        range(data['n_items']))

    with torch.no_grad():
        # 사용자와 모든 아이템 조합 생성
        user_tensor = torch.tensor([user_idx] * len(all_item_indices), device=device)
        items_tensor = torch.tensor(all_item_indices, device=device)

        # 컨텍스트 정보를 포함하여 예측 수행 (tester.py 방식)
        try:
            # 모든 컨텍스트 키가 있는지 확인
            if all(key in user_context for key in
                   ['category_group', 'activity_level', 'time_period', 'season', 'preference']):
                # 기본 예측 (SymmetricResidualCategoryNCF는 user_ids, item_ids만 받음)
                predictions = torch.sigmoid(model(user_tensor, items_tensor))
                print("✅ 컨텍스트 포함 예측 성공")
            else:
                # 기본 예측
                predictions = torch.sigmoid(model(user_tensor, items_tensor))
                print("⚠️ 컨텍스트 불완전, 기본 예측 사용")

        except Exception as context_error:
            print(f"⚠️ 컨텍스트 포함 예측 실패: {context_error}")
            print("🔄 기본 예측으로 대체")
            # 기본 예측으로 대체
            predictions = torch.sigmoid(model(user_tensor, items_tensor))

        predictions_np = predictions.cpu().numpy()

        # 선택된 아이템들의 점수를 -1.0으로 설정하여 제외 (tester.py 방식)
        for item_id in selected_items:
            if 'item_id_to_model_idx' in data and item_id in data['item_id_to_model_idx']:
                model_idx = data['item_id_to_model_idx'][item_id]
                if model_idx in all_item_indices:
                    idx_pos = all_item_indices.index(model_idx)
                    predictions_np[idx_pos] = -1.0
            elif item_id < len(all_item_indices):  # 직접 인덱스로 사용
                if item_id < len(predictions_np):
                    predictions_np[item_id] = -1.0

        # 🎯 3가지 카테고리로 추천 분류
        # 1. 상위 3개 (사용자 설문조사 조건에 맞는 관광지 중 ML 점수 높은 3개)
        # 2. ML 점수 높은 4개 (상위 4-7위)
        # 3. 개발자 추천 3개 (final_score 2-3점 랜덤)

        # 전체 아이템을 점수 순으로 정렬
        sorted_indices = np.argsort(predictions_np)[::-1]
        valid_indices = [idx for idx in sorted_indices if predictions_np[idx] > 0]

        print(f"📊 유효한 아이템 수: {len(valid_indices)}개")

        # 1. 상위 3개 추천 (사용자 설문조사 조건에 맞는 관광지 중 ML 점수 높은 3개)
        top_3_items = get_survey_matching_recommendations(user_context, tourism_data, selected_items, valid_indices,
                                                          predictions_np, 3)
        print(f"🏆 설문조사 조건 맞는 상위 3개 (ML 점수 순): {top_3_items}")

        # 2. ML 점수 높은 4개 (4-7위)
        ml_high_items = valid_indices[3:7] if len(valid_indices) >= 7 else valid_indices[3:]
        print(f"🤖 ML 높은 점수 4개: {ml_high_items}")

        # 3. 개발자 추천 3개 (final_score 2-3점 랜덤)
        developer_items = get_developer_recommendations(user_context['category_group'], tourism_data, selected_items, 3)
        print(f"👨‍💻 개발자 추천 3개: {developer_items}")

        # 최종 추천 리스트 구성
        final_recommendations = []

        # 상위 3개 추가
        for i, item_idx in enumerate(top_3_items):
            final_recommendations.append({
                'item_idx': int(item_idx),
                'category': 'top_3',
                'rank': i + 1
            })

        # ML 높은 점수 4개 추가
        for i, item_idx in enumerate(ml_high_items):
            final_recommendations.append({
                'item_idx': int(item_idx),
                'category': 'ml_high',
                'rank': i + 1
            })

        # 개발자 추천 3개 추가
        for i, item_idx in enumerate(developer_items):
            final_recommendations.append({
                'item_idx': int(item_idx),
                'category': 'developer',
                'rank': i + 1
            })

        # 추천 결과 생성
        recommendations = []
        for i, rec in enumerate(final_recommendations):
            item_idx = rec['item_idx']
            category_type = rec['category']

            # ML 점수 계산
            if item_idx in all_item_indices:
                score = float(predictions_np[all_item_indices.index(item_idx)])
            else:
                score = 0.5  # 기본 점수

            # 관광지 정보 가져오기
            if item_idx in tourism_data:
                item_info = tourism_data[item_idx]
                item_name = item_info['name']
                category_info = f"{item_info['category']} ({item_info['category_group']})"
                # 실제 DB ID 사용 (MongoDB ObjectId)
                db_id = item_info.get('db_id', '')
                content_id = item_info.get('content_id', '')
            else:
                item_name = f"관광지_{item_idx}"
                category_info = "알 수 없음"
                db_id = ''
                content_id = ''

            # 카테고리별 추천 이유 설정
            if category_type == 'top_3':
                reason = f"🏆 설문조사 조건 매칭 + ML 점수 순 - 사용자 선호도와 AI 예측을 모두 고려한 관광지 (ML 점수: {score:.4f})"
            elif category_type == 'ml_high':
                reason = f"🤖 AI 추천 - 높은 예측 점수 (ML 점수: {score:.4f})"
            else:  # developer
                reason = f"👨‍💻 개발자 추천 - 숨겨진 보석 같은 관광지"

            # DB에서 상세 정보 가져오기
            db_place = db_tourism_dict.get(item_name)
            
            if db_place:
                # DB Tourism 데이터 사용
                final_item_id = db_place.id
                address = db_place.address
                rating = float(db_place.rating)
                description = db_place.description
                location_coords = db_place.location.coordinates  # [lng, lat]
                region = db_place.region
                category_full = db_place.category
                review_count = db_place.review_count
                visitors_count = db_place.visitors_count
                print(f"      ✅ 추천 {i+1}: {item_name} (DB 데이터 사용)")
            else:
                # DB에 없으면 기본값 사용
                final_item_id = str(db_id) if db_id else str(item_idx)
                address = item_info.get('address', '') if item_idx in tourism_data else ''
                rating = 0.0
                description = ''
                location_coords = [0.0, 0.0]
                region = ''
                category_full = category_info
                review_count = 0
                visitors_count = 0
                print(f"      ⚠️ 추천 {i+1}: {item_name} (DB 데이터 없음, 기본값 사용)")
            
            recommendations.append({
                'rank': int(i + 1),
                # 프론트엔드가 기대하는 필드명
                '_id': str(final_item_id),
                'id': str(final_item_id),
                'name': str(item_name),
                'address': str(address),
                'rating': float(rating),
                'description': str(description),
                'location': {
                    'type': 'Point',
                    'coordinates': location_coords  # [lng, lat]
                },
                'region': str(region),
                'category': str(category_full),
                'category_group': str(item_info.get('category_group', '')) if item_idx in tourism_data else '',
                'review_count': int(review_count),
                'visitors_count': int(visitors_count),
                # ML 관련 필드
                'ml_score': float(score),
                'score': float(score),  # 호환성
                'reason': str(reason),
                'category_type': str(category_type),
                # 추가 필드
                'ml_index': int(item_idx),
                'content_id': str(content_id) if content_id else '',
                'photoUrl': '',  # 이미지는 별도 처리 필요
                'image': '',
                'randomized': True,
                'source': 'ml'
            })

    print(f"✅ 3가지 카테고리 추천 완료: 총 {len(recommendations)}개 관광지 추천")
    print(f"   - 상위 3개: {len([r for r in recommendations if r['category_type'] == 'top_3'])}개")
    print(f"   - ML 높은 점수: {len([r for r in recommendations if r['category_type'] == 'ml_high'])}개")
    print(f"   - 개발자 추천: {len([r for r in recommendations if r['category_type'] == 'developer'])}개")

    return recommendations


async def get_ml_recommendations_for_user(user_vote_schemas, top_k=10):
    """ML 모델을 사용한 추론 전용 추천 시스템 - 10개 추천"""
    global loaded_ncf_model, model_data

    print(f"🚀 get_ml_recommendations_for_user 호출됨 - top_k: {top_k}")
    print(f"🔍 user_vote_schemas 개수: {len(user_vote_schemas) if user_vote_schemas else 0}")

    try:
        if loaded_ncf_model is None:
            print("❌ ML 모델이 로드되지 않았습니다.")
            return {"error": "ML 모델을 로드할 수 없습니다."}

        device = next(loaded_ncf_model.parameters()).device
        print(f"🎯 ML 추론 시작 - 디바이스: {device}")
        print(f"📊 Vote schemas 수: {len(user_vote_schemas)}")

        # 데이터 로딩
        if model_data is None:
            try:
                model_data = load_data()
                print(f"✅ 모델 데이터 로드 완료: 사용자 {model_data['n_users']}명, 아이템 {model_data['n_items']}개")
            except Exception as e:
                print(f"⚠️ 모델 데이터 로딩 실패: {e}")
                return {"error": "모델 데이터를 로드할 수 없습니다."}

        # 관광지 데이터 로딩
        tourism_data = get_tourism_data_in_tester_format()
        if not tourism_data:
            return {"error": "관광지 데이터를 로드할 수 없습니다."}

        print(f"📍 관광지 데이터 로드 완료: {len(tourism_data)}개")

        # ML 모델 추론 수행 (10개 추천)
        print(f"🔍 recommend_with_vote_context 호출 시작 - top_k: {top_k}")
        recommendations = await recommend_with_vote_context(
            loaded_ncf_model, user_vote_schemas, model_data, tourism_data, device, top_k
        )
        print(f"🔍 recommend_with_vote_context 호출 완료 - 결과: {len(recommendations) if recommendations else 0}개")

        if recommendations and len(recommendations) >= 5:  # 최소 5개는 있어야 성공으로 간주
            print("✅ ML 모델 추론 성공")
            return {
                "status": "success",
                "recommendations": recommendations,
                "method": "ML_Inference",
                "confidence": "high"
            }
        else:
            print("⚠️ ML 추론 결과 부족 - 룰 기반 fallback 사용")
            return get_rule_based_fallback_recommendations(user_vote_schemas, top_k)

    except Exception as e:
        print(f"❌ ML 추론 오류: {e}")
        print("🔄 룰 기반 fallback으로 전환")
        return get_rule_based_fallback_recommendations(user_vote_schemas, top_k)


def get_rule_based_fallback_recommendations(user_vote_schemas, top_k=10):
    """룰 기반 fallback 추천 시스템 - 10개 추천"""
    print("🔄 룰 기반 fallback 추천 시작 (10개 추천)")

    try:
        # 사용자 스키마에서 기본 정보 추출
        if not user_vote_schemas or len(user_vote_schemas[0]) < 6:
            return {"error": "사용자 스키마 정보가 부족합니다."}

        first_schema = user_vote_schemas[0]
        user_context = {
            'category_group': first_schema[1],
            'activity_level': first_schema[2],
            'time_period': first_schema[3],
            'season': first_schema[4],
            'preference': first_schema[5]
        }

        # 룰 기반 추천 수행 (vote_schema용 - UUID 6자리 랜덤)
        schema_data = convert_to_schema_format(user_selections)
        recommendations = find_recommended_items(schema_data)

        if "error" in recommendations:
            return {"error": recommendations["error"]}

        # 추천 결과를 ML 형식으로 변환 (10개까지)
        formatted_recommendations = []
        for round_data in recommendations['rounds']:  # 모든 라운드 사용
            for option in ['option_a', 'option_b']:
                if len(formatted_recommendations) >= top_k:
                    break
                item_data = round_data[option]['item']
                # 실제 DB ID 가져오기
                db_id = item_data.get('_id', '')
                content_id = item_data.get('content_id', '')
                
                formatted_recommendations.append({
                    "item_id": str(db_id) if db_id else str(item_data['index']),  # 실제 DB ID 사용
                    "ml_index": int(item_data['index']),  # ML 모델 인덱스는 별도 필드로 보존
                    "content_id": str(content_id) if content_id else '',  # content_id도 포함
                    "score": 0.5,  # 기본 점수
                    "name": str(item_data['name']),
                    "category": str(item_data['category']),
                    "category_group": str(item_data['category_group']),
                    "reason": "룰 기반 fallback 추천",
                    "rank": len(formatted_recommendations) + 1,
                    "context_match": True,
                    "category_type": "fallback"
                })

        return {
            "status": "success",
            "recommendations": formatted_recommendations[:top_k],
            "method": "Rule-based",
            "confidence": "medium"
        }

    except Exception as e:
        print(f"❌ 룰 기반 fallback 오류: {e}")
        return {"error": f"룰 기반 추천 중 오류가 발생했습니다: {str(e)}"}


def analyze_user_selection_patterns(user_vote_schemas, tourism_data):
    """사용자의 선택 패턴 분석 (tester.py 방식)"""
    if not user_vote_schemas:
        return {}

    selected_items = []
    for schema in user_vote_schemas:
        if len(schema) >= 7:
            selected_items.append(schema[6])  # pos_item_index

    # 선택된 아이템들의 특성 분석
    category_analysis = {}
    score_analysis = {"scores": [], "avg_score": 0}

    for item_id in selected_items:
        if item_id in tourism_data:
            item_info = tourism_data[item_id]

            # 카테고리 분석
            category = item_info.get('category_group', '알 수 없음')
            if category not in category_analysis:
                category_analysis[category] = {
                    'count': 0,
                    'items': [],
                    # final_score 제거
                    'scores': []
                }

            category_analysis[category]['count'] += 1
            category_analysis[category]['items'].append(item_info.get('name', f'아이템_{item_id}'))

            # final_score 제거

    # final_score 제거로 인한 평균 점수 계산 제거

    return {
        'selected_items': selected_items,
        'selection_count': len(selected_items),
        'category_preferences': category_analysis,
        # final_score 제거로 인한 score_analysis 제거
        'diversity_score': len(category_analysis)  # 선택한 카테고리 다양성
    }


def get_context_aware_filtering_rules(user_context, selection_patterns):
    """컨텍스트 기반 필터링 규칙 생성 (tester.py 스타일)"""
    filtering_rules = {
        'boost_categories': [],
        'season_appropriate': True,
        'activity_level_match': True,
        'time_preference': True,
        'diversity_factor': 0.1  # 다양성 가중치
    }

    # 사용자가 선택한 카테고리들을 우선시
    if 'category_preferences' in selection_patterns:
        preferred_categories = list(selection_patterns['category_preferences'].keys())
        filtering_rules['boost_categories'] = preferred_categories

    # 계절별 필터링 규칙
    season_map = {
        0: "봄",  # 봄: 야외 활동 선호
        1: "여름",  # 여름: 물놀이, 시원한 곳 선호
        2: "가을",  # 가을: 단풍, 트레킹 선호
        3: "겨울"  # 겨울: 실내 활동, 온천 선호
    }

    if 'season' in user_context:
        current_season = season_map.get(user_context['season'], "알 수 없음")
        filtering_rules['current_season'] = current_season

    return filtering_rules


def convert_user_to_model_format(user_vote_schemas):
    """사용자 투표 스키마를 모델 입력 형식으로 변환"""
    # 이 함수는 필요에 따라 사용자 스키마를 모델이 이해할 수 있는 형식으로 변환
    # 현재는 기본적으로 그대로 반환
    return user_vote_schemas


def extract_user_preferences_from_votes(user_vote_schemas):
    """사용자 투표에서 선호도 패턴 추출 (추론 전용)"""
    if not user_vote_schemas:
        return {}

    # 선택된 아이템들 추출
    selected_items = []
    for schema in user_vote_schemas:
        if len(schema) >= 7:
            selected_items.append(schema[6])  # pos_item_index

    # 사용자 컨텍스트 정보 추출
    first_schema = user_vote_schemas[0]
    user_context = {
        'category_group': first_schema[1],
        'activity_level': first_schema[2],
        'time_period': first_schema[3],
        'season': first_schema[4],
        'preference': first_schema[5]
    }

    return {
        'selected_items': selected_items,
        'user_context': user_context,
        'selection_count': len(selected_items)
    }


def save_base_schema_to_user_interaction(user_id: str, base_schemas: List, positive_items: List) -> bool:
    """base schema를 user_interaction 컬렉션에 저장하는 함수 (효율적인 구조로)"""
    try:
        print(f"🔍 save_base_schema_to_user_interaction 호출됨")
        print(f"📊 user_id: {user_id}")
        print(f"📊 base_schemas 개수: {len(base_schemas) if base_schemas else 0}")
        print(f"📊 positive_items: {positive_items}")

        if user_interaction_col is None:
            print("❌ user_interaction 컬렉션을 사용할 수 없습니다.")
            return False

        if not base_schemas or len(base_schemas) == 0:
            print("❌ base_schemas가 비어있습니다.")
            return False

        # 첫 번째 스키마에서 공통 설문 정보 추출
        first_schema = base_schemas[0]
        
        # 투표 결과만 추출 (각 라운드의 pos/neg 아이템)
        votes = []
        for i, schema in enumerate(base_schemas):
            if len(schema) >= 8:
                votes.append({
                    "round": i + 1,
                    "pos_item_index": int(schema[6]),  # pos_item
                    "neg_item_index": int(schema[7])   # neg_item
                })
        
        # 효율적인 문서 구조로 저장
        interaction_doc = {
            "user_id": user_id,
            "type": "vote_submission",
            "survey_data": {
                "category_group": str(first_schema[1]),
                "activity_level_idx": int(first_schema[2]),
                "time_period": int(first_schema[3]),
                "season": int(first_schema[4]),
                "preference": int(first_schema[5])
            },
            "votes": votes,  # 5개 라운드 투표 결과
            "timestamp": datetime.now()
        }

        print(f"📋 저장할 문서 구조:")
        print(f"  - user_id: {user_id}")
        print(f"  - survey_data: {interaction_doc['survey_data']}")
        print(f"  - votes: {len(votes)}개 라운드")

        # MongoDB에 저장
        result = user_interaction_col.insert_one(interaction_doc)
        print(f"✅ user_interaction 컬렉션에 투표 결과 저장 완료: {result.inserted_id}")
        return True

    except Exception as db_error:
        print(f"❌ user_interaction 저장 중 오류: {db_error}")
        import traceback
        traceback.print_exc()
        return False


def find_item_index_by_name(item_name: str) -> int:
    """관광지 이름으로 인덱스 찾기"""
    try:
        tourism_data = load_tourism_data()
        if not tourism_data:
            print(f"❌ 관광지 데이터 로드 실패")
            return 0
        
        # 모든 그룹에서 아이템 찾기
        for group in tourism_data.get('groups', []):
            for item in group.get('items', []):
                if item.get('name') == item_name:
                    print(f"✅ 관광지 '{item_name}' 인덱스 찾음: {item['index']}")
                    return int(item['index'])
        
        print(f"⚠️ 관광지 '{item_name}' 인덱스를 찾지 못함")
        return 0
    except Exception as e:
        print(f"❌ 인덱스 찾기 오류: {e}")
        return 0

@router.post("/votes")
async def submit_votes(votes_data: VotesSubmission, request: Request, user_id: str = Depends(get_current_user)):
    """사용자의 전체 투표 결과 저장 (5라운드 일괄 제출) - 로그인 필요"""
    global positive_items, current_user_uuid, base_schema_storage, user_votes
    
    print(f"📥 투표 제출 받음: {len(votes_data.votes)}개 라운드")
    
    # 투표 데이터 초기화 (새로운 제출 시작)
    user_votes.clear()
    positive_items.clear()
    
    # 각 투표 처리
    for vote in votes_data.votes:
        # item_name으로 item_index 찾기
        item_index = find_item_index_by_name(vote.item_name)
        
        # 긍정 아이템 저장
        positive_items.append(item_index)
        
        # 프론트엔드 choice 값을 백엔드 형식으로 변환
        # "primary" → "option_a", "alternative" → "option_b"
        choice_mapping = {
            "primary": "option_a",
            "alternative": "option_b",
            "option_a": "option_a",  # 직접 option_a를 보내는 경우도 지원
            "option_b": "option_b"   # 직접 option_b를 보내는 경우도 지원
        }
        backend_choice = choice_mapping.get(vote.choice, vote.choice)
        
        # user_votes에 추가
        user_votes.append({
            "round": vote.round,
            "choice": backend_choice,  # 변환된 choice 사용
            "item_name": vote.item_name,
            "item_index": item_index,
            "timestamp": datetime.now().isoformat()
        })
        print(f"  ✅ 라운드 {vote.round}: {vote.choice} → {backend_choice} - {vote.item_name} (인덱스: {item_index})")
    
    # 5라운드 완료 확인
    if len(user_votes) >= 5:
        print(f"🎯 5라운드 완료 - BASE_SCHEMA 저장 시작")
        print(f"📊 current_user_uuid: {current_user_uuid}")
        print(f"📊 user_id: {user_id}")
        print(f"📊 user_selections: {user_selections}")
        print(f"📊 user_votes 개수: {len(user_votes)}")
        print(f"📊 positive_items: {positive_items}")

        try:
            # 현재 사용자 UUID 사용 (base_schema용으로 UUID 문자열 사용 + 실제 투표 데이터 포함)
            if current_user_uuid:
                print(f"🔄 current_user_uuid 사용: {current_user_uuid}")
                base_schemas = convert_to_base_schema_format(user_selections, current_user_uuid, user_votes)
                user_uuid_str = current_user_uuid
            else:
                print(f"🔄 user_id 사용: {user_id}")
                base_schemas = convert_to_base_schema_format(user_selections, user_id, user_votes)
                user_uuid_str = user_id

            print(f"✅ base_schemas 생성 완료: {len(base_schemas)}개")
            print(f"📋 첫 번째 base_schema 예시: {base_schemas[0] if base_schemas else 'None'}")

            # base_schemas는 5개의 개별 스키마 배열이므로 그대로 저장
            base_schema_storage.extend(base_schemas)

            # user_interaction 컬렉션에 base schema 저장
            print(f"💾 user_interaction 컬렉션에 저장 시작...")
            save_success = save_base_schema_to_user_interaction(user_uuid_str, base_schemas, positive_items)

            if save_success:
                print(f"🎯 5라운드 완료 - BASE_SCHEMA 저장: {len(base_schemas)}개")
                print(f"📊 저장된 긍정 아이템들: {positive_items}")
                print(f"💾 MongoDB user_interaction 컬렉션에 BASE_SCHEMA 저장 완료")
                print(
                    f"📋 BASE_SCHEMA 형식: [user_id, category_group, activity_level_idx, time_period, season, preference, pos_item, neg_item]")
            else:
                print(f"❌ BASE_SCHEMA 저장 실패")

            # 긍정 아이템 리스트 초기화 (다음 설문을 위해)
            positive_items = []

        except Exception as e:
            print(f"❌ base_schema 저장 중 오류: {e}")
            import traceback
            traceback.print_exc()

    return {
        "status": "success",
        "message": f"총 {len(user_votes)}개 라운드 투표가 제출되었습니다!",
        "total_votes": int(len(user_votes)),
        "positive_items_count": len(positive_items),
        "is_complete": len(user_votes) >= 5,
        "total_base_schemas": len(base_schema_storage),
        "votes_details": [
            {
                "round": v["round"],
                "choice": v["choice"],
                "item_name": v["item_name"],
                "item_index": v["item_index"]
            }
            for v in user_votes
        ]
    }


@router.get("/status")
async def get_survey_status(request: Request):
    """로그인 상태 및 설문조사 상태 확인"""
    try:
        # JWT 토큰 확인 (optional)
        token = request.cookies.get("access_token")
        
        # Authorization 헤더에서도 확인
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
        
        logged_in = False
        user_id = None
        
        if token:
            try:
                payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
                user_id = payload.get("sub")
                if user_id:
                    logged_in = True
            except JWTError:
                logged_in = False
        
        # 설문조사 완료 여부 확인
        has_survey_data = all(value is not None for value in user_selections.values())
        
        # 투표 완료 여부 확인 (5개 라운드)
        has_votes = len(user_votes) >= 5
        
        # 전체 상태 결정
        if logged_in and has_survey_data and has_votes:
            status = "완료"
        elif logged_in and has_survey_data:
            status = "투표 대기"
        elif logged_in:
            status = "설문조사 대기"
        else:
            status = "로그인 필요"
        
        return {
            "logged_in": logged_in,
            "user_id": user_id,
            "has_survey_data": has_survey_data,
            "has_votes": has_votes,
            "status": status,
            "total_votes": len(user_votes),
            "current_selections": user_selections if has_survey_data else {}
        }
    except Exception as e:
        print(f"❌ /status 엔드포인트 오류: {e}")
        return {
            "logged_in": False,
            "user_id": None,
            "has_survey_data": False,
            "has_votes": False,
            "status": "오류",
            "error": str(e)
        }


@router.get("/reset")
async def reset_selections(request: Request, user_id: str = Depends(get_current_user)):
    """선택 초기화 (투표 기록은 유지)"""
    global user_selections
    user_selections = {
        "activity": None,
        "activity_level": None,
        "time": None,
        "season": None,
        "preference": None
    }
    # user_votes는 초기화하지 않음 - 투표 기록 유지
    return {"message": "선택이 초기화되었습니다. (투표 기록은 유지됨)"}


@router.get("/base-schemas")
async def get_base_schemas(request: Request, user_id: str = Depends(get_current_user)):
    """저장된 base_schema 목록 조회 - 로그인 필요"""
    return {
        "status": "success",
        "total_schemas": len(base_schema_storage),
        "base_schemas": base_schema_storage,
        "user_id": user_id
    }


@router.get("/ml-recommendations", response_model=MLRecommendationResponse)
async def get_ml_recommendations(k: int = 20, user_id: str = None):
    """ML 모델을 사용한 추론 전용 개인화된 추천 - 20개 추천"""
    # 5라운드 투표가 완료되었는지 확인
    if len(user_votes) < 5:
        return MLRecommendationResponse(
            status="incomplete",
            recommendations=[],
            total_count=0,
            model_info={"model_type": "none"},
            message="5라운드 심화 설문조사를 먼저 완료해주세요."
        )

    # 투표 스키마가 생성되었는지 확인
    vote_schemas = create_vote_schemas(user_id)
    if not vote_schemas:
        return MLRecommendationResponse(
            status="error",
            recommendations=[],
            total_count=0,
            model_info={"model_type": "none"},
            message="투표 스키마를 생성할 수 없습니다."
        )

    print(f"🎯 ML 추론 요청 - 사용자 투표: {len(user_votes)}개, 스키마: {len(vote_schemas)}개, 추천 수: {k}개")

    # 사용자 선호도 패턴 추출
    user_preferences = extract_user_preferences_from_votes(vote_schemas)

    # ML 모델을 사용한 추론 수행 (20개 추천)
    ml_result = await get_ml_recommendations_for_user(vote_schemas, top_k=k)

    if "error" in ml_result:
        return MLRecommendationResponse(
            status="error",
            recommendations=[],
            total_count=0,
            model_info={"model_type": "none"},
            message=ml_result["error"]
        )

    # ml_result에서 recommendations 추출
    recommendations = ml_result.get("recommendations", [])
    method = ml_result.get("method", "Unknown")
    confidence = ml_result.get("confidence", "medium")
    
    # 기본 설문조사 정보도 포함 (vote_schema용 - UUID 6자리 랜덤)
    vote_schema = convert_to_schema_format(user_selections)

    # base_schema 정보도 별도로 생성 (UUID 문자열 + 실제 투표 데이터)
    base_schema = convert_to_base_schema_format(user_selections, user_id, user_votes)

    return MLRecommendationResponse(
        status="success",
        recommendations=recommendations,
        total_count=len(recommendations),
        model_info={
            "model_type": "Neural Collaborative Filtering (NCF)",
            "method": method,
            "confidence": confidence,
            "input_type": "survey_data",
            "recommendation_count": k,
            "training_data": "부산 관광지 사용자 상호작용 데이터",
            "recommendation_basis": "사용자의 선택 패턴과 유사한 사용자들의 선호도 기반 추론"
        },
        message="ML 모델 기반 추천이 완료되었습니다."
    )


@router.get("/health")
async def health_check():
    """서버 상태 확인"""
    try:
        # 관광지 데이터 로드 테스트
        tourism_data = load_tourism_data()
        data_status = "ok" if tourism_data else "error"

        return {
            "status": "ok",
            "server": "running",
            "tourism_data": data_status,
            "model_loaded": loaded_ncf_model is not None,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "error",
            "server": "running",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


@router.get("/debug")
async def debug_info():
    """디버그 정보 확인"""
    return {
        "user_selections": user_selections,
        "user_votes": user_votes,
        "user_selections_complete": all(value is not None for value in user_selections.values()),
        "user_votes_count": len(user_votes),
        "tourism_data_available": load_tourism_data() is not None,
        "model_loaded": loaded_ncf_model is not None
    }


@router.get("/model-status")
async def get_model_status():
    """ML 모델 상태 확인 (추론 전용)"""
    global loaded_ncf_model

    status = {
        "ncf_available": NCF_AVAILABLE,
        "model_loaded": loaded_ncf_model is not None,
        "model_path": MODEL_PATH,
        "mode": "inference_only"
    }

    if NCF_AVAILABLE and loaded_ncf_model is not None:
        device = next(loaded_ncf_model.parameters()).device
        status["device"] = str(device)
        status["model_type"] = "SymmetricResidualCategoryNCF"
        status["model_mode"] = "eval"  # 추론 모드

    return status


@router.post("/load-model")
async def load_model_endpoint():
    """ML 모델 수동 로딩 (추론 전용)"""
    success = initialize_model()

    if success:
        return {
            "status": "success",
            "message": "ML 모델이 성공적으로 로드되었습니다. (추론 전용 모드)",
            "model_info": await get_model_status()
        }
    else:
        return {
            "status": "error",
            "message": "ML 모델 로딩에 실패했습니다."
        }


@router.delete("/reset")
async def reset_all_data():
    """모든 데이터 초기화 (DELETE 메서드)"""
    global user_selections, user_votes, positive_items, base_schema_storage
    user_selections = {
        "activity": None,
        "activity_level": None,
        "time": None,
        "season": None,
        "preference": None
    }
    user_votes = []  # 투표 기록도 완전 초기화
    positive_items = []
    base_schema_storage = []
    
    return {
        "status": "success",
        "message": "모든 설문조사 및 투표 데이터가 초기화되었습니다.",
        "reset_items": ["user_selections", "user_votes", "positive_items", "base_schema_storage"]
    }


@router.get("/reset-all")
async def reset_all():
    """모든 데이터 초기화 (투표 기록 포함)"""
    global user_selections, user_votes
    user_selections = {
        "activity": None,
        "activity_level": None,
        "time": None,
        "season": None,
        "preference": None
    }
    user_votes = []  # 투표 기록도 완전 초기화
    return {"message": "모든 데이터가 초기화되었습니다."}


# 모델 초기화 함수 (main.py에서 호출됨)
def initialize_survey_model():
    """survey_router 모델 초기화"""
    return initialize_model()
