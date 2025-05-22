# user 로그 기반 추천 라우터
from fastapi import APIRouter, Query
from typing import List, Optional
from services.data_loader import load_logs_data_from_json
from schemas import LogData, RankingItem
from collections import Counter
from datetime import datetime, timedelta

router = APIRouter()

FILE_PATH = 'BPR/data/logs/click_logs.json'   # click log와 search log 반영
raw_logs = load_logs_data_from_json(FILE_PATH)
logs = [LogData(**item) for item in raw_logs]

@router.get("/ranking", response_model=List[RankingItem])
def get_ranking(top: int = 5):   # 기본 반환은 상위 5개
    now = datetime.now()
    one_month_ago = now - timedelta(days=30)    # 최근 1개월 기준으로 생성

    # 1개월 필터링
    recent_logs = [
        log for log in logs
        if datetime.fromisoformat(log.timestamp) >= one_month_ago
    ]
    
    counter = Counter(log.place_id for log in recent_logs)
    ranking = counter.most_common(top)

    return [{"place_id": place_id, "visits": visits} for place_id, visits in ranking]
