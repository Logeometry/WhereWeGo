from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from schemas import Tourism
from services.data_loader import load_location_data_from_db

router = APIRouter()


@router.get("/categories", response_model=List[Tourism])
async def search_categories(keywords: Optional[List[str]] = Query(None)):
    # 1) MongoDB에서 전체 장소 데이터 가져오기
    try:
        all_places: List[Tourism] = await load_location_data_from_db()
    except Exception:
        raise HTTPException(status_code=500, detail="장소 데이터를 불러오는 중 오류가 발생했습니다.")

    # 2) 키워드가 없으면 전체 반환
    if not keywords:
        return all_places

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
