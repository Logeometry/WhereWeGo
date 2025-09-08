# backend/app/services/survey_compute_service.py

from typing import List, Dict
from pathlib import Path

from schemas import SurveyResponse, CategoryScore
# from services.data_loader import load_location_data_from_json  # 사용하지 않음

# JSON 파일 경로 지정
DATA_PATH = Path(__file__).parent.parent / 'data' / 'survey_attractions.json'

async def compute_category_scores(responses: List[SurveyResponse]) -> List[CategoryScore]:
    """새로운 설문 구조에 기반한 카테고리 점수 계산"""
    
    # 1) 카테고리 점수 초기화
    scores: Dict[str, int] = {}
    
    # 2) 새로운 응답 구조로 점수 계산
    for resp in responses:
        category = resp.category_group
        
        # 선호/비선호 아이템 인덱스 비교로 점수 계산
        if resp.pos_item_index > resp.neg_item_index:
            delta = 2  # 강한 선호
        elif resp.pos_item_index < resp.neg_item_index:
            delta = -2  # 강한 비선호
        else:
            delta = 0  # 중립
        
        # 활동성 선호도 추가 가중치
        if resp.preference == 0:  # 활동성 선호
            if resp.activity_level_idx == 0:  # high activity
                delta += 1
            elif resp.activity_level_idx == 2:  # low activity
                delta -= 1
        
        scores[category] = scores.get(category, 0) + delta
    
    # 3) 정렬 후 반환
    result = [CategoryScore(category=cat, score=sc) for cat, sc in scores.items()]
    return sorted(result, key=lambda x: x.score, reverse=True)
