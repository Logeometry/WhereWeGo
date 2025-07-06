import logging
from fastapi import APIRouter, HTTPException, Query, logger
from typing import List, Optional
from pydantic import BaseModel, Extra
from services.data_loader import load_location_data_from_db
from schemas import Tourism
from db import places_col, _place_db
import re

router = APIRouter()

# 로거 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# 반환 모델 정의
# 프론트엔드에서 사용할 응답 모델 정의, 필요에 따라 필드 추가 가능
# 예시로 id, name, tags 필드를 포함
class Respose_model(BaseModel):
    id: str
    name: str
    tags: List[str]

    class Config:
        varidate_by_name = True
        extra = Extra.ignore

# 카테고리 라우터터
@router.get("/category", response_model=Respose_model)
async def get_places_by_category(
    category: Optional[str] = Query(None, description="검색할 카테고리")
):
    query = {}
    if category:
        regex = re.compile(re.escape(category), re.IGNORECASE)
        query = {
            "$or": [
                {"category": {"$regex": regex}},
                {"category_group": {"$regex": regex}}
            ]
        }
    try:
        cusor = places_col.find({})
        docs = await cursor.to_list(length=None)
        return docs
    
    except Exception as e:
        logger.error(f"DB 조회 중 오류: {e}")
        raise HTTPException(status_code=500, detail=f"카테고리 조회 중 오류 발생: {str(e)}")



## 전 카테고리 구현 라우터, 키워드 여러개 사용 가능함

"""
async def search_categoyries(keywords:Optional[List[str]] = Query(None)):
    try: 
        all_places: List[Tourism] = await load_location_data_from_db()
    except Exception:
        raise HTTPException(status_code=500, detail="여행지 데이터를 불러오는 중 오류가 발생했습니다.")
    
    if not keywords:
        return
    for place in all_places:
        # categoty 와 일치하는지만 검사
        category_value = 



    # 2) 키워드가 없으면 전체 반환
    if not keywords:
        return 

    # 3) 키워드가 있으면 필터링
    lower_keywords = [kw.lower().strip() for kw in keywords]
    filtered: List[Tourism] = []

    for place in all_places:
        # (1) category 단일 문자열 검사
        category_value = place.category or ""
        if any(kw in category_value.lower() for kw in lower_keywords):
            filtered.append(place)
            continue

        # (2) category_group 리스트 내 문자열 검사
        # 예: ["음식","한식","부산"] 중 하나라도 키워드가 포함되면 매칭
        for grp in (place.category_group or []):
            grp_lower = grp.lower()
            if any(kw in grp_lower for kw in lower_keywords):
                filtered.append(place)
                break

    return filtered
"""