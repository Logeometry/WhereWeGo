from fastapi import APIRouter, Query, HTTPException
from typing import List, Optional
from schemas import Tourism 
from services.data_loader import load_location_data_from_db
from services.click_log_service import save_click_log

router = APIRouter()

# 장소 data load(장소에 대한 페이지 생성시)
@router.get("/detail0", response_model=List[Tourism])           # 수정 완료
async def location_detail(
    query: Optional[str] = None,
    user_id : Optional[str] = Query(None)
):
    try:
        all_places: List[Tourism] = await load_location_data_from_db()
    except Exception as e:
        raise HTTPException(status_code=500, detail="장소 데이터를 불러오는 중 오류가 발생했습니다.")
    if not query:
        return all_places
    lower_q = query.lower().strip()
    filtered: List[Tourism] = [
        place for place in all_places
        if lower_q == place.id.lower()
    ]
    if user_id and user_id.lower() != "null" and user_id.strip() != "":
        try:
            await save_click_log(user_id=user_id, target_id=query)
        except Exception:
            pass

    return filtered

# 간단 정보만 반환함 (로그 X)               # 수정완료
@router.get("/simple_detail", response_model=List[Tourism])
async def simple_location_detail(
    query: Optional[str] = None,
):
    try:
        all_places: List[Tourism] = await load_location_data_from_db()
    except Exception as e:
        raise HTTPException(status_code=500, detail="장소 데이터를 불러오는 중 오류가 발생했습니다.")

    if not query:
        return all_places

    lower_q = query.lower().strip()

    filtered: List[Tourism] = [
        place for place in all_places
        if lower_q == place.id.lower()
            or lower_q in place.name.lower()
            or (place.address and lower_q in place.address.lower())
    ]
    return filtered