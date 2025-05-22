# backend/app/services/survey_compute_service.py

from typing import List, Dict
from pathlib import Path

from schemas import SurveyResponse, CategoryScore, Attraction
from services.data_loader import load_location_data_from_json

# JSON 파일 경로 지정
DATA_PATH = Path(__file__).parent.parent / 'data' / 'survey_attractions.json'

async def compute_category_scores(responses: List[SurveyResponse]) -> List[CategoryScore]:
    # 1) JSON에서 장소 리스트 로드
    attractions: List[Attraction] = load_location_data_from_json(str(DATA_PATH))
    id_to_cat: Dict[int, str] = {a.id: a.category for a in attractions}

    # 2) 응답 집계
    scores: Dict[str, int] = {}
    for resp in responses:
        cat = id_to_cat.get(resp.content_id)
        if not cat:
            continue
        delta = 1 if resp.responses == 'like' else -1 if resp.responses == 'dislike' else 0
        scores[cat] = scores.get(cat, 0) + delta

    # 3) 정렬 후 반환
    result = [CategoryScore(category=cat, score=sc) for cat, sc in scores.items()]
    return sorted(result, key=lambda x: x.score, reverse=True)
