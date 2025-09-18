# # services/survey_service.py
# """
# 업그레이드된 설문조사 서비스
# 1.localserver.py의 향상된 기능들을 완전히 포함
# """
#
# from typing import List, Dict, Optional
# from schemas import SurveyResponse
# from services.db_handler import tourism_collection
# from bson import ObjectId
# import numpy as np
# from sklearn.metrics.pairwise import cosine_similarity
# import random
# import time
# import json
# import os
# import sys
# import uuid
#
# # 상위 디렉토리를 Python 경로에 추가
# current_dir = os.path.dirname(os.path.abspath(__file__))
# parent_dir = os.path.dirname(current_dir)
# if parent_dir not in sys.path:
#     sys.path.insert(0, parent_dir)
#
# # 전역 변수 (1.localserver.py와 동일)
# user_selections = {
#     "activity": None,
#     "activity_level": None,
#     "time": None,
#     "season": None,
#     "preference": None
# }
# user_votes = []
#
#
# def convert_to_schema_format(selections, user_id=None):
#     """사용자 선택을 스키마 형식으로 변환 (1.localserver.py와 완전히 동일)"""
#     # UUID4로 매번 랜덤한 사용자 ID 생성
#     if user_id is None:
#         user_id = int(uuid.uuid4().int) % 1000000  # 6자리 숫자로 변환
#
#     # 활동 카테고리 (문자열로 저장)
#     activity = str(selections.get("activity", ""))
#
#     # 활동성 변환: 높음=0, 중간=1, 낮음=2
#     activity_level_map = {"높음": 0, "중간": 1, "낮음": 2}
#     activity_level = int(activity_level_map.get(selections.get("activity_level"), -1))
#
#     # 시간대 변환: 오전=0, 오후=1, 저녁=2
#     time_map = {"오전": 0, "오후": 1, "저녁": 2}
#     time = int(time_map.get(selections.get("time"), -1))
#
#     # 계절 변환: 봄=0, 여름=1, 가을=2, 겨울=3
#     season_map = {"봄": 0, "여름": 1, "가을": 2, "겨울": 3}
#     season = int(season_map.get(selections.get("season"), -1))
#
#     # 선호도 변환: 활동성=0, 시간대=1
#     preference_map = {"활동성": 0, "시간대": 1}
#     preference = int(preference_map.get(selections.get("preference"), -1))
#
#     return [
#         user_id,  # int - 학습 데이터와 일치
#         activity,  # str
#         activity_level,  # int (byte 범위)
#         time,  # int (byte 범위)
#         season,  # int (byte 범위)
#         preference  # int (byte 범위)
#     ]
#
#
# def load_tourism_data():
#     """관광지 데이터 로드 (1.localserver.py와 동일)"""
#     try:
#         # 여러 경로에서 데이터 파일 찾기
#         file_paths = [
#             'sort3Wpreference.json',
#             os.path.join(parent_dir, 'model', 'sort3Wpreference.json'),
#             os.path.join(parent_dir, 'model', 'ncf_inner', 'sort3Wpreference.json'),
#             'C:/Users/user/Desktop/새 폴더 (2)/.vscode/WhereWeGo-backend/model/sort3Wpreference.json'
#         ]
#
#         for file_path in file_paths:
#             try:
#                 with open(file_path, 'r', encoding='utf-8') as f:
#                     data = json.load(f)
#                     print(f"✅ 관광지 데이터 로드 성공: {file_path}")
#                     return data
#             except FileNotFoundError:
#                 continue
#
#         print("❌ 관광지 데이터 파일을 찾을 수 없습니다.")
#         return None
#     except Exception as e:
#         print(f"관광지 데이터 로드 오류: {e}")
#         return None
#
#
# def get_category_group_mapping():
#     """카테고리 그룹 매핑 (1.localserver.py와 동일)"""
#     return {
#         "자연풍경": ["해변", "산", "강", "호수", "폭포", "계곡"],
#         "자연산림": ["산림", "공원", "숲", "트레킹", "등산"],
#         "관람및체험": ["박물관", "미술관", "전시관", "체험관", "과학관"],
#         "휴양": ["휴양지", "리조트", "스파", "온천", "캠핑"],
#         "테마거리": ["쇼핑", "거리", "시장", "상점가", "문화거리"],
#         "예술감상": ["공연장", "극장", "음악회", "전시회", "문화센터"],
#         "공연관람": ["공연", "뮤지컬", "연극", "콘서트", "축제"],
#         "트레킹": ["트레킹", "등산", "산책", "자전거", "워킹"]
#     }
#
#
# def get_activity_level_keywords():
#     """활동성 레벨 키워드 (1.localserver.py와 동일)"""
#     return {
#         "높음": ["트레킹", "등산", "자전거", "워킹", "체험", "액티비티", "스포츠"],
#         "중간": ["관람", "체험", "산책", "탐방", "방문", "투어"],
#         "낮음": ["휴양", "휴식", "감상", "구경", "쇼핑", "식사", "카페"]
#     }
#
#
# def get_season_keywords():
#     """계절 키워드 (1.localserver.py와 동일)"""
#     return {
#         "봄": ["벚꽃", "봄", "꽃", "신록", "따뜻"],
#         "여름": ["해변", "수영", "여름", "시원", "바다"],
#         "가을": ["단풍", "가을", "추수", "시원", "풍경"],
#         "겨울": ["눈", "겨울", "스키", "온천", "따뜻"]
#     }
#
#
# def get_time_period_keywords():
#     """시간대 키워드 (1.localserver.py와 동일)"""
#     return {
#         "오전": ["아침", "오전", "일출", "산책", "운동"],
#         "오후": ["오후", "관람", "체험", "탐방", "투어"],
#         "저녁": ["저녁", "일몰", "야경", "공연", "식사"]
#     }
#
#
# def calculate_weighted_score(item: Dict, user_schema: List) -> float:
#     """가중치 점수 계산 (1.localserver.py와 동일)"""
#     try:
#         base_score = item.get("final_score", 0.0)
#         return float(base_score)
#     except:
#         return 0.0
#
#
# def estimate_item_activity_level(item: Dict, user_category: str = None) -> str:
#     """아이템의 활동성 레벨 추정 (1.localserver.py와 동일)"""
#     try:
#         name = item.get("name", "").lower()
#         description = item.get("description", "").lower()
#         category = item.get("category", "").lower()
#
#         high_keywords = ["트레킹", "등산", "자전거", "워킹", "체험", "액티비티", "스포츠", "산", "트레일"]
#         low_keywords = ["휴양", "휴식", "감상", "구경", "쇼핑", "식사", "카페", "박물관", "미술관"]
#
#         text = f"{name} {description} {category}"
#
#         high_count = sum(1 for keyword in high_keywords if keyword in text)
#         low_count = sum(1 for keyword in low_keywords if keyword in text)
#
#         if high_count > low_count:
#             return "높음"
#         elif low_count > high_count:
#             return "낮음"
#         else:
#             return "중간"
#     except:
#         return "중간"
#
#
# def estimate_item_season_suitability(item: Dict, season: str, user_category: str = None) -> bool:
#     """아이템의 계절 적합성 추정 (1.localserver.py와 동일)"""
#     try:
#         name = item.get("name", "").lower()
#         description = item.get("description", "").lower()
#
#         season_keywords = get_season_keywords()
#         keywords = season_keywords.get(season, [])
#
#         text = f"{name} {description}"
#         return any(keyword in text for keyword in keywords)
#     except:
#         return True
#
#
# def estimate_item_time_suitability(item: Dict, time_period: str, user_category: str = None) -> bool:
#     """아이템의 시간대 적합성 추정 (1.localserver.py와 동일)"""
#     try:
#         name = item.get("name", "").lower()
#         description = item.get("description", "").lower()
#
#         time_keywords = get_time_period_keywords()
#         keywords = time_keywords.get(time_period, [])
#
#         text = f"{name} {description}"
#         return any(keyword in text for keyword in keywords)
#     except:
#         return True
#
#
# def get_intersection_based_recommendations(items: List[Dict], user_schema: List) -> List[Dict]:
#     """교집합 기반 추천 (1.localserver.py와 동일)"""
#     try:
#         user_category = user_schema[1]
#         user_activity_level = user_schema[2]
#         user_time_period = user_schema[3]
#         user_season = user_schema[4]
#         user_preference = user_schema[5]
#
#         # 활동성/시간대 키워드 매핑
#         activity_keywords = get_activity_level_keywords()
#         time_keywords = get_time_period_keywords()
#
#         activity_level_names = ["높음", "중간", "낮음"]
#         time_period_names = ["오전", "오후", "저녁"]
#
#         user_activity_name = activity_level_names[user_activity_level]
#         user_time_name = time_period_names[user_time_period]
#
#         filtered_items = []
#
#         for item in items:
#             item_activity = estimate_item_activity_level(item, user_category)
#             item_time_suitable = estimate_item_time_suitability(item, user_time_name, user_category)
#             item_season_suitable = estimate_item_season_suitability(item, user_season, user_category)
#
#             # 교집합 조건 확인
#             if user_preference == 0:  # 활동성 선호
#                 if item_activity == user_activity_name:
#                     item["weighted_score"] = calculate_weighted_score(item, user_schema) + 0.5
#                     filtered_items.append(item)
#             else:  # 시간대 선호
#                 if item_time_suitable:
#                     item["weighted_score"] = calculate_weighted_score(item, user_schema) + 0.3
#                     filtered_items.append(item)
#
#         # 점수순 정렬
#         filtered_items.sort(key=lambda x: x.get("weighted_score", 0), reverse=True)
#         return filtered_items[:50]  # 상위 50개 반환
#
#     except Exception as e:
#         print(f"교집합 기반 추천 오류: {e}")
#         return items[:20]
#
#
# def filter_items_by_preferences(items: List[Dict], user_schema: List) -> List[Dict]:
#     """선호도 기반 필터링 (1.localserver.py와 동일)"""
#     try:
#         return get_intersection_based_recommendations(items, user_schema)
#     except:
#         return items[:20]
#
#
# def find_recommended_items(user_schema: List) -> Dict:
#     """추천 아이템 찾기 (1.localserver.py의 5라운드 시스템과 동일)"""
#     try:
#         print(f"🎯 추천 아이템 찾기 시작: {user_schema}")
#
#         # 관광지 데이터 로드
#         tourism_data = load_tourism_data()
#         if not tourism_data:
#             return {"error": "관광지 데이터를 로드할 수 없습니다."}
#
#         # 모든 아이템 수집
#         all_items = []
#         for group in tourism_data.get("groups", []):
#             for item in group.get("items", []):
#                 if "index" in item and "name" in item:
#                     all_items.append(item)
#
#         print(f"📊 총 {len(all_items)}개 아이템 로드")
#
#         # 교집합 기반 필터링
#         filtered_items = filter_items_by_preferences(all_items, user_schema)
#         print(f"🔍 필터링 후 {len(filtered_items)}개 아이템")
#
#         if len(filtered_items) < 10:
#             print("⚠️ 필터링된 아이템이 부족하여 전체 아이템 사용")
#             filtered_items = all_items[:100]
#
#         # 5라운드 추천 생성
#         rounds = []
#         used_items = set()
#
#         for round_num in range(1, 6):
#             # 주 카테고리 아이템 선택 (교집합 조건 만족)
#             primary_candidates = [item for item in filtered_items
#                                   if item.get("index") not in used_items]
#
#             if not primary_candidates:
#                 # 사용 가능한 아이템이 없으면 전체에서 선택
#                 primary_candidates = [item for item in all_items
#                                       if item.get("index") not in used_items]
#
#             if not primary_candidates:
#                 break
#
#             # 주 카테고리 아이템 선택 (가장 높은 점수)
#             primary_item = max(primary_candidates,
#                                key=lambda x: x.get("weighted_score", x.get("final_score", 0)))
#             used_items.add(primary_item.get("index"))
#
#             # 대안 카테고리 아이템 선택 (다른 카테고리에서)
#             alternative_candidates = [item for item in all_items
#                                       if (item.get("index") not in used_items and
#                                           item.get("category") != primary_item.get("category"))]
#
#             if not alternative_candidates:
#                 alternative_candidates = [item for item in all_items
#                                           if item.get("index") not in used_items]
#
#             if alternative_candidates:
#                 alternative_item = max(alternative_candidates,
#                                        key=lambda x: x.get("final_score", 0))
#                 used_items.add(alternative_item.get("index"))
#             else:
#                 alternative_item = primary_item
#
#             # 라운드 데이터 생성
#             round_data = {
#                 "round_number": round_num,
#                 "option_a": {
#                     "item": primary_item,
#                     "weighted_score": primary_item.get("weighted_score", primary_item.get("final_score", 0)),
#                     "reason": f"교집합 기반 맞춤 추천 - {user_schema[1]} 카테고리와 활동성/시간대 교집합",
#                     "is_primary_category": True
#                 },
#                 "option_b": {
#                     "item": alternative_item,
#                     "weighted_score": alternative_item.get("final_score", 0),
#                     "reason": f"대안 추천 - {alternative_item.get('category', '기타')} 카테고리",
#                     "is_primary_category": False
#                 }
#             }
#
#             rounds.append(round_data)
#
#         print(f"✅ {len(rounds)}개 라운드 생성 완료")
#
#         return {
#             "status": "success",
#             "rounds": rounds,
#             "total_rounds": len(rounds)
#         }
#
#     except Exception as e:
#         print(f"추천 아이템 찾기 오류: {e}")
#         return {"error": f"추천 생성 실패: {str(e)}"}
#
#
# def create_vote_schemas():
#     """투표 스키마 생성 (1.localserver.py와 동일)"""
#     try:
#         if len(user_votes) < 5:
#             print(f"⚠️ 투표가 완료되지 않음: {len(user_votes)}/5")
#             return None
#
#         print(f"🎯 투표 스키마 생성 시작: {len(user_votes)}개 투표")
#
#         # 기본 사용자 스키마 생성
#         base_schema = convert_to_schema_format(user_selections)
#         if not base_schema or len(base_schema) < 6:
#             print("❌ 기본 스키마 생성 실패")
#             return None
#
#         vote_schemas = []
#
#         for vote in user_votes:
#             # 각 투표마다 5개의 스키마 생성 (1.localserver.py와 동일)
#             round_number = vote.get("round_number", 1)
#             choice = vote.get("choice", "option_a")
#             item_index = vote.get("item_index", 1)
#
#             # 1. 원본 스키마 (실제 선택하지 않은 관광지를 부정 아이템으로 사용)
#             original_schema = base_schema.copy()
#             original_schema[6] = item_index  # pos_item_index
#             # 부정 아이템은 다른 라운드에서 선택된 아이템 중 랜덤 선택
#             other_items = [v.get("item_index", 1) for v in user_votes if v.get("round_number") != round_number]
#             original_schema[7] = random.choice(other_items) if other_items else 2
#             vote_schemas.append(original_schema)
#
#             # 2-5. 랜덤 스키마들 (동일한 긍정 아이템 + 랜덤 부정 아이템)
#             for i in range(4):
#                 random_schema = base_schema.copy()
#                 random_schema[6] = item_index  # pos_item_index
#                 random_schema[7] = random.randint(1, 1000)  # 랜덤 부정 아이템
#                 vote_schemas.append(random_schema)
#
#         print(f"✅ 투표 스키마 생성 완료: {len(vote_schemas)}개 스키마")
#         return vote_schemas
#
#     except Exception as e:
#         print(f"투표 스키마 생성 오류: {e}")
#         return None
#
#
# def add_vote(round_number: int, choice: str, item_name: str, item_index: int):
#     """투표 추가 (1.localserver.py와 동일)"""
#     vote = {
#         "round_number": round_number,
#         "choice": choice,
#         "item_name": item_name,
#         "item_index": item_index,
#         "timestamp": time.time()
#     }
#     user_votes.append(vote)
#     print(f"🗳️ 투표 추가: 라운드 {round_number}, 선택: {choice}, 아이템: {item_name}")
#
#
# def reset_selections():
#     """선택 초기화 (1.localserver.py와 동일)"""
#     global user_selections, user_votes
#     user_selections = {
#         "activity": None,
#         "activity_level": None,
#         "time": None,
#         "season": None,
#         "preference": None
#     }
#     # 투표 기록은 유지 (1.localserver.py와 동일)
#     print("✅ 선택이 초기화되었습니다. (투표 기록은 유지됨)")
#
#
# async def recommend_similar_places_from_survey(survey: List[SurveyResponse]) -> List[dict]:
#     """새로운 설문 구조에 기반한 장소 추천 (업그레이드 버전)"""
#
#     # 선호 카테고리 그룹 추출
#     preferred_categories = [s.category_group for s in survey if s.pos_item_index > s.neg_item_index]
#
#     # 활동성 레벨과 시간대 기반 필터링
#     activity_preferences = {}
#     time_preferences = {}
#
#     for s in survey:
#         if s.preference == 0:  # 활동성 선호
#             activity_preferences[s.activity_level_idx] = activity_preferences.get(s.activity_level_idx, 0) + 1
#         else:  # 시간대 선호
#             time_preferences[s.time_period] = time_preferences.get(s.time_period, 0) + 1
#
#     # MongoDB 쿼리 구성
#     query_filter = {}
#     if preferred_categories:
#         query_filter["category_group"] = {"$in": preferred_categories}
#
#     query_filter["vector_full"] = {"$exists": True, "$ne": None}
#
#     candidates = await tourism_collection.find(query_filter).to_list(length=2000)
#
#     scored = []
#     for place in candidates:
#         vector = place.get("vector_full")
#         if not vector:
#             continue
#
#         # 기본 점수 계산
#         score = 1.0
#
#         # 카테고리 매칭 보너스
#         if place.get("category_group") in preferred_categories:
#             score += 0.5
#
#         # 활동성 레벨 매칭 보너스
#         if activity_preferences:
#             place_activity = estimate_place_activity_level(place)
#             for activity_level, count in activity_preferences.items():
#                 if place_activity == activity_level:
#                     score += 0.3 * count
#
#         # 시간대 매칭 보너스
#         if time_preferences:
#             place_time = estimate_place_time_suitability(place)
#             for time_period, count in time_preferences.items():
#                 if place_time == time_period:
#                     score += 0.2 * count
#
#         place["_id"] = str(place["_id"])
#         place["recommendation_score"] = float(score)
#         scored.append(place)
#
#     scored.sort(key=lambda x: -x["recommendation_score"])
#     return scored[:10]
#
#
# def estimate_place_activity_level(place: dict) -> int:
#     """장소의 활동성 레벨 추정 (0: 높음, 1: 중간, 2: 낮음)"""
#     try:
#         name = place.get("name", "").lower()
#         description = place.get("description", "").lower()
#         category = place.get("category", "").lower()
#
#         high_keywords = ["트레킹", "등산", "자전거", "워킹", "체험", "액티비티", "스포츠", "산", "트레일"]
#         low_keywords = ["휴양", "휴식", "감상", "구경", "쇼핑", "식사", "카페", "박물관", "미술관"]
#
#         text = f"{name} {description} {category}"
#
#         high_count = sum(1 for keyword in high_keywords if keyword in text)
#         low_count = sum(1 for keyword in low_keywords if keyword in text)
#
#         if high_count > low_count:
#             return 0  # 높음
#         elif low_count > high_count:
#             return 2  # 낮음
#         else:
#             return 1  # 중간
#     except:
#         return 1  # 기본값: 중간
#
#
# def estimate_place_time_suitability(place: dict) -> int:
#     """장소의 시간대 적합성 추정 (0: 오전, 1: 오후, 2: 저녁)"""
#     try:
#         name = place.get("name", "").lower()
#         description = place.get("description", "").lower()
#
#         morning_keywords = ["아침", "오전", "일출", "산책", "운동"]
#         afternoon_keywords = ["오후", "관람", "체험", "탐방", "투어"]
#         evening_keywords = ["저녁", "일몰", "야경", "공연", "식사"]
#
#         text = f"{name} {description}"
#
#         morning_count = sum(1 for keyword in morning_keywords if keyword in text)
#         afternoon_count = sum(1 for keyword in afternoon_keywords if keyword in text)
#         evening_count = sum(1 for keyword in evening_keywords if keyword in text)
#
#         if evening_count > afternoon_count and evening_count > morning_count:
#             return 2  # 저녁
#         elif morning_count > afternoon_count and morning_count > evening_count:
#             return 0  # 오전
#         else:
#             return 1  # 오후 (기본값)
#     except:
#         return 1  # 기본값: 오후
#
#
# # ============ 1.localserver.py의 모든 함수들 추가 ============
#
# def get_tourism_data_in_tester_format():
#     """tester.py 형식으로 관광지 데이터를 변환 (1.localserver.py와 동일)"""
#     tourism_data = load_tourism_data()
#     if not tourism_data:
#         return {}
#
#     # tester.py 형식으로 변환: {index: {name, category, category_group, ...}}
#     tourism_dict = {}
#     for group in tourism_data.get('groups', []):
#         for item in group.get('items', []):
#             if 'index' in item and 'name' in item:
#                 tourism_dict[item['index']] = {
#                     'name': item['name'],
#                     'category': item.get('category', ''),
#                     'category_group': item.get('category_group', ''),
#                     'popular_score': item.get('popular_score', 0),
#                     'visitors_count': item.get('visitors_count', 0),
#                     'final_score': item.get('final_score', 0)
#                 }
#     return tourism_dict
#
#
# def get_category_rules():
#     """카테고리별 상세 규칙 매핑 - 교집합 기반 추천을 위한 규칙 (1.localserver.py와 완전히 동일)"""
#     return {
#         "자연풍경": {
#             "categories": ["전망대", "섬", "해수욕장,해변", "섬(내륙)", "워터테마파크", "방조제", "아쿠아리움"],
#             "activity_rules": {
#                 "high": ["해수욕장,해변", "섬", "워터테마파크"],
#                 "medium": ["전망대", "섬(내륙)"],
#                 "low": ["방조제", "아쿠아리움"]
#             },
#             "time_rules": {
#                 0: ["전망대", "해수욕장,해변", "섬"],  # 아침
#                 1: ["워터테마파크", "섬(내륙)", "아쿠아리움"],  # 오후
#                 2: ["전망대", "방조제"]  # 저녁
#             },
#             "season_rules": {
#                 0: ["전망대", "섬", "섬(내륙)"],  # 봄
#                 1: ["전망대", "섬", "해수욕장,해변", "섬(내륙)", "워터테마파크", "방조제", "아쿠아리움"],  # 여름
#                 2: ["전망대", "섬", "섬(내륙)"],  # 가을
#                 3: ["전망대", "아쿠아리움"]  # 겨울
#             },
#             "interaction_ratio": {"popular": 0.31, "random": 0.69}
#         },
#         "예술 감상": {
#             "categories": ["전시관", "미술관"],
#             "activity_rules": {
#                 "high": ["전시관", "미술관"],
#                 "medium": ["전시관", "미술관"],
#                 "low": ["전시관", "미술관"]
#             },
#             "time_rules": {
#                 0: ["전시관", "미술관"],  # 아침
#                 1: ["전시관", "미술관"],  # 오후
#                 2: ["전시관", "미술관"]  # 저녁
#             },
#             "season_rules": {
#                 0: ["전시관", "미술관"],  # 봄
#                 1: ["전시관", "미술관"],  # 여름
#                 2: ["전시관", "미술관"],  # 가을
#                 3: ["전시관", "미술관"]  # 겨울
#             },
#             "interaction_ratio": {"popular": 0.31, "random": 0.69}
#         },
#         "공연관람": {
#             "categories": ["공연장,연극극장"],
#             "activity_rules": {
#                 "high": ["공연장,연극극장"],
#                 "medium": ["공연장,연극극장"],
#                 "low": ["공연장,연극극장"]
#             },
#             "time_rules": {
#                 0: ["공연장,연극극장"],  # 아침
#                 1: ["공연장,연극극장"],  # 오후
#                 2: ["공연장,연극극장"]  # 저녁
#             },
#             "season_rules": {
#                 0: ["공연장,연극극장"],  # 봄
#                 1: ["공연장,연극극장"],  # 여름
#                 2: ["공연장,연극극장"],  # 가을
#                 3: ["공연장,연극극장"]  # 겨울
#             },
#             "interaction_ratio": {"popular": 0.31, "random": 0.69}
#         },
#         "관람및체험": {
#             "categories": ["박물관", "기념관", "테마파크", "도자기/도예촌", "과학관", "실내동물원", "자전거여행", "동물원"],
#             "exclude": ["눈썰매장", "천문대"],
#             "activity_rules": {
#                 "high": ["테마파크", "자전거여행", "동물원"],
#                 "medium": ["실내동물원", "도자기/도예촌"],
#                 "low": ["과학관", "박물관", "기념관"]
#             },
#             "time_rules": {
#                 0: ["박물관", "과학관"],  # 아침
#                 1: ["테마파크", "동물원", "실내동물원", "박물관", "과학관"],  # 오후
#                 2: ["기념관", "도자기/도예촌"]  # 저녁
#             },
#             "season_rules": {
#                 0: ["박물관", "기념관", "테마파크", "도자기/도예촌", "과학관", "실내동물원", "자전거여행", "천문대", "동물원"],  # 봄
#                 1: ["박물관", "기념관", "과학관", "실내동물원", "천문대", "동물원"],  # 여름
#                 2: ["박물관", "기념관", "테마파크", "도자기/도예촌", "과학관", "실내동물원", "자전거여행", "천문대", "동물원"],  # 가을
#                 3: ["박물관", "기념관", "테마파크", "도자기/도예촌", "과학관", "실내동물원", "눈썰매장", "자전거여행", "천문대", "동물원"]  # 겨울
#             },
#             "interaction_ratio": {"popular": 0.31, "random": 0.69}
#         },
#         "트레킹": {
#             "categories": ["갈맷길", "도보여행", "금정산둘레길", "둘레길", "남파랑길"],
#             "exclude": ["봉래산둘레길", "서구종단트레킹숲길", "무장애나눔길"],
#             "activity_rules": {
#                 "high": ["갈맷길", "도보여행", "금정산둘레길", "둘레길", "남파랑길"],
#                 "medium": ["자연풍경", "자연산림"],  # 대체 카테고리
#                 "low": ["자연풍경", "자연산림"]  # 대체 카테고리
#             },
#             "time_rules": {
#                 0: ["갈맷길", "도보여행"],  # 아침
#                 1: ["갈맷길", "도보여행", "둘레길"],  # 오후
#                 2: ["자연풍경", "자연산림"]  # 저녁 (대체)
#             },
#             "season_rules": {
#                 0: ["갈맷길", "도보여행"],  # 봄
#                 1: ["갈맷길"],  # 여름
#                 2: ["갈맷길", "도보여행"],  # 가을
#                 3: ["갈맷길", "도보여행"]  # 겨울
#             },
#             "interaction_ratio": {"popular": 0.31, "random": 0.69}
#         },
#         "휴양": {
#             "categories": [],
#             "activity_rules": {
#                 "high": ["자연휴양림", "관광농원"],  # 대체 카테고리
#                 "medium": ["숲", "수목원,식물원"],  # 대체 카테고리
#                 "low": ["온천", "리조트", "스파"]  # 휴양 카테고리 사용
#             },
#             "time_rules": {
#                 0: ["숲", "자연휴양림", "리조트", "스파", "온천"],  # 아침
#                 1: ["숲", "자연휴양림", "리조트", "스파", "온천"],  # 오후
#                 2: ["온천", "리조트", "스파"]  # 저녁
#             },
#             "season_rules": {
#                 0: ["저수지", "수목원,식물원", "숲", "관광농원", "자연휴양림"],  # 봄
#                 1: ["수목원,식물원", "온천", "숲", "관광농원", "자연휴양림"],  # 여름
#                 2: ["저수지", "숲", "관광농원", "자연휴양림"],  # 가을
#                 3: ["저수지", "수목원,식물원", "온천", "관광농원"]  # 겨울
#             },
#             "interaction_ratio": {"popular": 0.31, "random": 0.69}
#         },
#         "테마거리": {
#             "categories": ["테마거리", "먹자골목", "카페거리"],
#             "activity_rules": {
#                 "high": ["테마거리"],
#                 "medium": ["먹자골목"],
#                 "low": ["카페거리"]
#             },
#             "time_rules": {
#                 0: ["카페거리"],  # 아침
#                 1: ["테마거리", "먹자골목"],  # 오후
#                 2: ["카페거리", "먹자골목"]  # 저녁
#             },
#             "season_rules": {
#                 0: ["테마거리", "먹자골목", "카페거리"],  # 봄
#                 1: ["카페거리"],  # 여름
#                 2: ["테마거리", "먹자골목", "카페거리"],  # 가을
#                 3: ["먹자골목", "카페거리"]  # 겨울
#             },
#             "interaction_ratio": {"popular": 0.31, "random": 0.69}
#         },
#         "자연산림": {
#             "categories": ["산", "계곡", "유원지"],
#             "exclude": ["강", "호수"],
#             "activity_rules": {
#                 "high": ["산"],
#                 "medium": ["계곡"],
#                 "low": ["유원지"]
#             },
#             "time_rules": {
#                 0: ["산", "계곡"],  # 아침
#                 1: ["유원지", "계곡"],  # 오후
#                 2: ["산"]  # 저녁
#             },
#             "season_rules": {
#                 0: ["산"],  # 봄
#                 1: ["산", "계곡", "유원지"],  # 여름
#                 2: ["산"],  # 가을
#                 3: ["산"]  # 겨울
#             },
#             "interaction_ratio": {"popular": 0.31, "random": 0.69}
#         }
#     }
#
#
# def get_intersection_based_recommendations_enhanced(items: List[Dict], user_schema: List) -> List[Dict]:
#     """교집합 기반 맞춤 추천 - 활동성/시간대 선호도에 따른 교집합만 필터링 (1.localserver.py와 동일)"""
#     if not user_schema or len(user_schema) < 6:
#         return items
#
#     user_id, category_group, activity_level, time_period, season, preference = user_schema
#
#     # 활동성 변환 (인덱스 → 문자열)
#     activity_map = {0: "high", 1: "medium", 2: "low"}
#     activity_str = activity_map.get(activity_level, "medium")
#
#     # 시간대 변환 (인덱스 → 문자열)
#     time_map = {0: "오전", 1: "오후", 2: "저녁"}
#     time_str = time_map.get(time_period, "오전")
#
#     # 카테고리 규칙 가져오기
#     category_rules = get_category_rules()
#
#     if category_group not in category_rules:
#         # 규칙이 없으면 모든 아이템 반환
#         return items
#
#     rules = category_rules[category_group]
#
#     # 교집합 계산을 위한 키워드 세트 생성
#     intersection_keywords = set()
#
#     if preference == 0:  # 활동성 선호
#         # 카테고리 + 활동성 교집합
#         if activity_str in rules.get("activity_rules", {}):
#             activity_keywords = rules["activity_rules"][activity_str]
#             intersection_keywords.update(activity_keywords)
#             print(f"🎯 활동성 선호 교집합: {category_group} + {activity_str} = {activity_keywords}")
#
#     elif preference == 1:  # 시간대 선호
#         # 카테고리 + 시간대 교집합
#         if time_period in rules.get("time_rules", {}):
#             time_keywords = rules["time_rules"][time_period]
#             intersection_keywords.update(time_keywords)
#             print(f"🎯 시간대 선호 교집합: {category_group} + {time_str} = {time_keywords}")
#
#     # 교집합 키워드가 없으면 모든 아이템 반환
#     if not intersection_keywords:
#         print(f"⚠️ 교집합 키워드가 없어 모든 아이템 반환")
#         return items
#
#     # 교집합 키워드와 매칭되는 아이템만 필터링
#     filtered_items = []
#     for item in items:
#         category = item.get('category', '').lower()
#         name = item.get('name', '').lower()
#         category_group_item = item.get('category_group', '').lower()
#
#         text_to_check = f"{name} {category} {category_group_item}"
#
#         # 교집합 키워드 매칭 확인
#         matched_keywords = []
#         for keyword in intersection_keywords:
#             if keyword.lower() in text_to_check:
#                 matched_keywords.append(keyword)
#
#         # 교집합 키워드가 하나라도 매칭되면 포함
#         if matched_keywords:
#             item['matched_keywords'] = matched_keywords  # 디버깅용
#             filtered_items.append(item)
#
#     print(f"🎯 교집합 기반 필터링 완료: {len(intersection_keywords)}개 키워드로 {len(filtered_items)}개 아이템 필터링")
#
#     # 필터링된 아이템이 없으면 원본 아이템 반환
#     if not filtered_items:
#         print(f"⚠️ 교집합 매칭 아이템이 없어 원본 아이템 반환")
#         return items
#
#     return filtered_items
#
#
# def find_recommended_items_enhanced(user_schema: List) -> Dict:
#     """사용자 스키마를 바탕으로 5라운드 추천 아이템 찾기 (총 10개 서로 다른 관광지) - 강화된 랜덤성 (1.localserver.py와 동일)"""
#     try:
#         # 매번 다른 결과를 위해 현재 시간을 시드로 사용
#         import time
#         random.seed(int(time.time() * 1000) % 1000000)
#
#         tourism_data = load_tourism_data()
#         if not tourism_data:
#             return {"error": "관광지 데이터를 불러올 수 없습니다."}
#
#         # tourism_data 구조 검증
#         if 'groups' not in tourism_data or not tourism_data['groups']:
#             return {"error": "관광지 데이터 구조가 올바르지 않습니다."}
#
#         user_id, activity, activity_level, time_period, season, preference = user_schema
#
#         # 카테고리 매핑
#         category_mapping = get_category_group_mapping()
#         target_category_group = category_mapping.get(activity, activity)
#
#         # 특별 케이스: 트레킹과 휴양의 상호작용 처리
#         activity_level_map = {0: "high", 1: "medium", 2: "low"}
#         user_activity_str = activity_level_map.get(activity_level, "medium")
#
#         # 트레킹 상호작용: 활동성이 높으면 트레킹, 아니면 자연풍경/자연산림 중 선택
#         if activity == "트레킹":
#             if user_activity_str != "high":
#                 # 자연풍경과 자연산림 중 랜덤 선택
#                 alternative_categories = ["자연풍경", "자연산림"]
#                 target_category_group = random.choice(alternative_categories)
#                 print(f"🎯 트레킹 상호작용: 활동성 {user_activity_str} → {target_category_group}으로 변경")
#
#         # 휴양 상호작용: 활동성이 낮으면 휴양, 아니면 자연풍경/자연산림 중 선택
#         elif activity == "휴양":
#             if user_activity_str != "low":
#                 # 자연풍경과 자연산림 중 랜덤 선택
#                 alternative_categories = ["자연풍경", "자연산림"]
#                 target_category_group = random.choice(alternative_categories)
#                 print(f"🎯 휴양 상호작용: 활동성 {user_activity_str} → {target_category_group}으로 변경")
#
#         # 해당 카테고리 그룹의 아이템들 찾기
#         target_items = []
#         other_category_items = []
#
#         for group in tourism_data.get('groups', []):
#             if group.get('category_group') == target_category_group:
#                 items = group.get('items', [])
#                 if items:
#                     target_items.extend(items)
#             else:
#                 items = group.get('items', [])
#                 if items:
#                     other_category_items.extend(items)
#
#         # 아이템이 충분하지 않은 경우 처리
#         if not target_items:
#             print(f"⚠️ {target_category_group} 카테고리에 아이템이 없습니다. 모든 카테고리에서 선택합니다.")
#             # 모든 카테고리에서 아이템 수집
#             for group in tourism_data.get('groups', []):
#                 items = group.get('items', [])
#                 if items:
#                     target_items.extend(items)
#                     if len(target_items) >= 10:  # 충분한 아이템이 모이면 중단
#                         break
#
#         # 🎯 교집합 기반 맞춤 추천 적용
#         print(f"🎯 교집합 기반 추천 시작: {activity} 카테고리, 활동성={activity_level}, 시간대={time_period}, 선호도={preference}")
#         filtered_target_items = get_intersection_based_recommendations_enhanced(target_items, user_schema)
#
#         # 필터링된 아이템의 매칭된 키워드 출력
#         print(f"📊 교집합 매칭 아이템:")
#         for i, item in enumerate(filtered_target_items[:5]):
#             matched_keywords = item.get('matched_keywords', [])
#             print(f"  {i + 1}. {item.get('name', 'Unknown')} - 매칭 키워드: {matched_keywords}")
#
#         if not filtered_target_items:
#             return {"error": f"{activity} 카테고리에서 관광지를 찾을 수 없습니다."}
#
#         # 랜덤 정렬 (final_score 제거)
#         random.shuffle(filtered_target_items)
#
#         # 🎲 강화된 랜덤성: 상위 50% 아이템들을 "고품질 풀"로 확장하고 더 많은 랜덤 선택
#         top_percentage = 0.5  # 20% → 50%로 확장
#         top_count = max(5, int(len(filtered_target_items) * top_percentage))  # 최소 5개는 보장
#         high_quality_pool = filtered_target_items[:top_count]
#
#         # 고품질 풀 자체를 랜덤하게 섞기
#         random.shuffle(high_quality_pool)
#
#         print(f"🎲 강화된 고품질 풀 생성: 상위 {top_count}개 아이템을 랜덤 섞어서 선택")
#
#         # 다른 카테고리 아이템들도 단순한 점수 부여
#         other_category_scored = []
#         for item in other_category_items:
#             item['weighted_score'] = 0.5
#             other_category_scored.append(item)
#
#         # 랜덤 정렬 (final_score 제거)
#         random.shuffle(other_category_scored)
#
#         # 🎲 다른 카테고리 아이템들도 랜덤하게 섞기
#         random.shuffle(other_category_scored)
#         other_category_items = other_category_scored
#
#         # 사용된 관광지 인덱스 추적
#         used_indices = set()
#         rounds = []
#
#         # 5라운드 생성
#         for round_num in range(5):
#             # 🎲 주 카테고리에서 아이템 선택 - 더 넓은 풀에서 랜덤하게 선택
#             primary_item = None
#
#             # 사용되지 않은 고품질 아이템들 중에서 랜덤 선택
#             available_high_quality = [item for item in high_quality_pool if item['index'] not in used_indices]
#
#             if available_high_quality:
#                 # 🎲 고품질 풀에서 랜덤 선택 (더 다양한 선택)
#                 primary_item = random.choice(available_high_quality)
#                 used_indices.add(primary_item['index'])
#                 print(f"🎲 라운드 {round_num + 1}: 고품질 풀에서 랜덤 선택 - {primary_item['name']}")
#             else:
#                 # 고품질 풀이 부족하면 전체 풀에서 랜덤 선택
#                 available_items = [item for item in filtered_target_items if item['index'] not in used_indices]
#                 if available_items:
#                     primary_item = random.choice(available_items)
#                     used_indices.add(primary_item['index'])
#                     print(f"🎲 라운드 {round_num + 1}: 전체 풀에서 랜덤 선택 - {primary_item['name']}")
#
#             if not primary_item:
#                 return {"error": f"라운드 {round_num + 1}에서 충분한 주 카테고리 관광지를 찾을 수 없습니다."}
#
#             # 아이템에 누락된 필드들 추가
#             if 'region' not in primary_item:
#                 primary_item['region'] = '부산'
#             if 'address' not in primary_item:
#                 primary_item['address'] = '주소 정보 없음'
#             if 'visitors_count' not in primary_item:
#                 primary_item['visitors_count'] = 0
#
#             # 🎲 다른 카테고리 아이템에서 랜덤 선택
#             alternative_item = None
#
#             # 사용되지 않은 다른 카테고리 아이템들 중에서 랜덤 선택
#             available_items = [item for item in other_category_items if item['index'] not in used_indices]
#             if available_items:
#                 alternative_item = random.choice(available_items)
#                 used_indices.add(alternative_item['index'])
#                 print(f"🎯 대안 아이템 랜덤 선택: {alternative_item['name']}")
#
#             if not alternative_item:
#                 return {"error": f"라운드 {round_num + 1}에서 충분한 대안 관광지를 찾을 수 없습니다."}
#
#             # alternative_item에도 누락된 필드들 추가
#             if 'region' not in alternative_item:
#                 alternative_item['region'] = '부산'
#             if 'address' not in alternative_item:
#                 alternative_item['address'] = '주소 정보 없음'
#             if 'visitors_count' not in alternative_item:
#                 alternative_item['visitors_count'] = 0
#
#             # 🎲 랜덤하게 두 옵션의 순서를 섞기
#             random_order = random.random()
#             if random_order < 0.4:  # 40% 확률로 alternative가 첫 번째
#                 option_a = {
#                     "item": alternative_item,
#                     "reason": f"{alternative_item.get('category_group', '다른')} 카테고리의 추천 관광지",
#                     "is_primary_category": False
#                 }
#                 option_b = {
#                     "item": primary_item,
#                     "reason": f"{activity} 카테고리의 추천 관광지",
#                     "is_primary_category": True
#                 }
#             else:  # 60% 확률로 primary가 첫 번째
#                 option_a = {
#                     "item": primary_item,
#                     "reason": f"{activity} 카테고리의 추천 관광지",
#                     "is_primary_category": True
#                 }
#                 option_b = {
#                     "item": alternative_item,
#                     "reason": f"{alternative_item.get('category_group', '다른')} 카테고리의 추천 관광지",
#                     "is_primary_category": False
#                 }
#
#             rounds.append({
#                 "round_number": round_num + 1,
#                 "option_a": option_a,
#                 "option_b": option_b,
#                 "randomized": True,
#                 "random_seed": int(time.time() * 1000) % 1000000  # 랜덤 시드 기록
#             })
#
#         return {
#             "rounds": rounds,
#             "total_rounds": int(5),  # numpy.int64 → int 변환
#             "total_places": int(10),  # numpy.int64 → int 변환
#             "randomization_info": {
#                 "enhanced_randomness": True,
#                 "quality_pool_expanded": True,
#                 "shuffled_pools": True,
#                 "varied_selection_probability": True
#             },
#             "user_preferences": {
#                 "activity": str(activity),  # 문자열 보장
#                 "activity_level": str(["높음", "중간", "낮음"][activity_level]),  # 문자열 보장
#                 "time_period": str(["오전", "오후", "저녁"][time_period]),  # 문자열 보장
#                 "season": str(["봄", "여름", "가을", "겨울"][season]),  # 문자열 보장
#                 "preference": str(["활동성", "시간대"][preference])  # 문자열 보장
#             }
#         }
#
#     except Exception as e:
#         print(f"❌ find_recommended_items 오류: {e}")
#         import traceback
#         traceback.print_exc()
#         return {"error": f"추천 생성 중 오류가 발생했습니다: {str(e)}"}
#
#
# def create_vote_schemas_enhanced():
#     """투표 기록을 스키마 형식으로 변환 - 각 투표마다 추가 랜덤 부정 아이템 4개 포함 (1.localserver.py와 완전히 동일)"""
#     try:
#         print(f"🔍 create_vote_schemas 호출됨")
#         print(f"📊 user_votes 상태: {len(user_votes) if user_votes else 0}개")
#
#         if not user_votes or len(user_votes) < 5:
#             print(f"⚠️ 투표가 충분하지 않음: {len(user_votes) if user_votes else 0}/5")
#             return None
#
#         # 중복 투표 제거 (같은 라운드에 여러 투표가 있는 경우)
#         unique_votes = []
#         seen_rounds = set()
#         for vote in user_votes:
#             round_num = vote.get('round_number', vote.get('round', 1))
#             if round_num not in seen_rounds:
#                 unique_votes.append(vote)
#                 seen_rounds.add(round_num)
#
#         if len(unique_votes) < 5:
#             print(f"⚠️ 고유 투표가 충분하지 않음: {len(unique_votes)}/5")
#             return None
#
#         print(f"✅ 고유 투표 {len(unique_votes)}개 확인됨")
#
#         # 기본 사용자 스키마 정보
#         try:
#             base_schema = convert_to_schema_format(user_selections)
#             user_id, category_group, activity_level_idx, time_period, season, preference = base_schema
#             print(f"✅ 기본 스키마 파싱 완료: {base_schema}")
#         except Exception as e:
#             print(f"❌ 기본 스키마 파싱 실패: {e}")
#             return None
#
#         # 추천 데이터에서 선택된 아이템들 찾기
#         tourism_data = load_tourism_data()
#         if not tourism_data:
#             print(f"❌ 관광지 데이터 로드 실패")
#             return None
#
#         print(f"✅ 관광지 데이터 로드 완료: {len(tourism_data.get('groups', []))}개 그룹")
#
#         # 모든 아이템을 인덱스로 매핑 및 전체 아이템 인덱스 수집
#         all_items = {}
#         all_item_indices = []
#         for group in tourism_data.get('groups', []):
#             for item in group.get('items', []):
#                 all_items[item['index']] = item
#                 all_item_indices.append(item['index'])
#
#         print(f"📊 전체 아이템 수: {len(all_item_indices)}개")
#
#         vote_schemas = []
#         used_negative_items = set()  # 이미 사용된 부정 아이템들 추적
#
#         # 각 투표에 대해 스키마 생성
#         for i, vote in enumerate(unique_votes):
#             print(f"🔄 투표 {i + 1}/5 처리 중: {vote}")
#             round_num = vote.get('round_number', vote.get('round', 1))
#             choice = vote.get('choice', 'option_a')  # 'option_a' 또는 'option_b'
#
#             # 🚨 수정: 저장된 아이템 인덱스 직접 사용 (새로운 추천 생성하지 않음)
#             try:
#                 pos_item_index = int(vote.get('item_index', 1))  # 사용자가 선택한 아이템 인덱스
#                 print(f"✅ 라운드 {round_num}: 사용자가 선택한 아이템 인덱스 = {pos_item_index}")
#
#                 # 🚨 수정: 선택하지 않은 아이템을 부정 아이템으로 사용
#                 # 투표 기록에서 선택하지 않은 아이템 찾기
#                 round_data = None
#                 try:
#                     # 해당 라운드의 추천 데이터에서 선택하지 않은 아이템 찾기
#                     recommendations = find_recommended_items_enhanced(base_schema)
#                     if "error" in recommendations:
#                         print(f"❌ 라운드 {round_num} 추천 생성 실패: {recommendations['error']}")
#                         # 부정 아이템을 랜덤하게 선택
#                         available_neg_items = [idx for idx in all_item_indices if idx != pos_item_index]
#                         if available_neg_items:
#                             original_neg_item_index = random.choice(available_neg_items)
#                         else:
#                             original_neg_item_index = 0  # 기본값
#                         print(f"🎲 라운드 {round_num}: 랜덤 부정 아이템 선택 = {original_neg_item_index}")
#                     else:
#                         round_data = recommendations['rounds'][round_num - 1]
#
#                         # 선택하지 않은 아이템 찾기
#                         if choice == 'option_a':
#                             neg_item = round_data['option_b']['item']
#                         else:  # choice == 'option_b'
#                             neg_item = round_data['option_a']['item']
#
#                         original_neg_item_index = int(neg_item['index'])
#                         print(f"✅ 라운드 {round_num}: pos_item={pos_item_index}, neg_item={original_neg_item_index}")
#                 except Exception as e:
#                     print(f"⚠️ 라운드 {round_num} 부정 아이템 찾기 실패: {e}")
#                     # 부정 아이템을 랜덤하게 선택
#                     available_neg_items = [idx for idx in all_item_indices if idx != pos_item_index]
#                     if available_neg_items:
#                         original_neg_item_index = random.choice(available_neg_items)
#                     else:
#                         original_neg_item_index = 0  # 기본값
#                     print(f"🎲 라운드 {round_num}: 랜덤 부정 아이템 선택 = {original_neg_item_index}")
#
#             except Exception as e:
#                 print(f"❌ 라운드 {round_num} 아이템 파싱 실패: {e}")
#                 continue
#
#             # 1. 원본 스키마 (실제 선택하지 않은 아이템)
#             original_schema = [
#                 user_id,  # user_id
#                 category_group,  # category_group
#                 activity_level_idx,  # activity_level_idx (0: high, 1: medium, 2: low)
#                 time_period,  # time_period (0: 아침, 1: 오후, 2: 저녁)
#                 season,  # season (0: 봄, 1: 여름, 2: 가을, 3: 겨울)
#                 preference,  # preference (0: 활동성 선호, 1: 시간대 선호)
#                 pos_item_index,  # pos_item['index']
#                 original_neg_item_index  # neg_item['index']
#             ]
#             vote_schemas.append(original_schema)
#
#             # 사용된 아이템들을 추적 (긍정 아이템과 원본 부정 아이템)
#             used_negative_items.add(pos_item_index)  # 긍정 아이템은 부정 아이템으로 사용 불가
#             used_negative_items.add(original_neg_item_index)  # 원본 부정 아이템도 중복 방지
#
#             # 2. 추가 랜덤 부정 아이템 4개 생성
#             available_negative_items = [idx for idx in all_item_indices
#                                         if idx not in used_negative_items and idx != pos_item_index]
#
#             if len(available_negative_items) >= 4:
#                 # 랜덤하게 4개 선택
#                 random_neg_items = random.sample(available_negative_items, 4)
#
#                 for random_neg_index in random_neg_items:
#                     random_schema = [
#                         user_id,  # user_id
#                         category_group,  # category_group
#                         activity_level_idx,  # activity_level_idx (0: high, 1: medium, 2: low)
#                         time_period,  # time_period (0: 아침, 1: 오후, 2: 저녁)
#                         season,  # season (0: 봄, 1: 여름, 2: 가을, 3: 겨울)
#                         preference,  # preference (0: 활동성 선호, 1: 시간대 선호)
#                         pos_item_index,  # pos_item['index'] - 동일한 긍정 아이템
#                         random_neg_index  # 랜덤 부정 아이템
#                     ]
#                     vote_schemas.append(random_schema)
#                     used_negative_items.add(random_neg_index)  # 중복 방지를 위해 추가
#             else:
#                 print(f"⚠️ 라운드 {round_num}: 추가 랜덤 부정 아이템 4개 생성에 충분한 아이템이 없습니다.")
#
#         print(f"✅ 투표 스키마 생성 완료: 총 {len(vote_schemas)}개")
#         return vote_schemas
#
#     except Exception as e:
#         print(f"❌ create_vote_schemas 오류: {e}")
#         import traceback
#         traceback.print_exc()
#         return None
