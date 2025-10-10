# 실시간 검색어 순위 반환 라우터
"""
현재는 사용하지 않는 라우터, 추후 삭제 예정
"""
from fastapi import APIRouter, Query
from typing import List, Optional
from schemas import Tourism
from services.data_loader import load_logs_data_from_json
from services.search_log_service import save_search_log

router = APIRouter()

FILE_PATH = 'BPR/data/logs/search_logs.json'
categories_data = load_logs_data_from_json(FILE_PATH)