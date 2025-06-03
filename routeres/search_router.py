from fastapi import APIRouter, Query
from typing import List, Optional
from schemas import Tourism
from services.data_loader import load_location_data_from_db
from services.search_log_service import save_search_log

router = APIRouter()

# 수정해야함
async def load_location_data_from_db() -> List[Tourism]:
    """
    MongoDB `places` 컬렉션에서 모든 문서를 읽어 와,
    Pydantic `Tourism` 리스트로 리턴.
    """
    results: List[Tourism] = []
    cursor = places_col.find({})

    async for doc in cursor:
        # Pydantic이 alias="_id"와 extra="ignore"로 설정되어 있으면
        # MongoDB 문서의 _id와 추가 필드는 자동으로 처리된다.
        results.append(Tourism(**doc))

    return results
