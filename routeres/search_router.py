from fastapi import APIRouter, Query, HTTPException
from typing import List, Optional
from schemas import Tourism
from services.data_loader import load_location_data_from_db
from services.search_log_service import save_search_log

router = APIRouter()

@router.get("/search", response_model=List[dict])
async def search_places(query: Optional[str] = Query(None, description="검색 키워드")):
    """
    관광지를 키워드로 검색합니다.
    
    Args:
        query: 검색 키워드 (장소명, 주소 등)
    
    Returns:
        List[dict]: 검색 결과 관광지 목록
    """
    try:
        # DB에서 관광지 데이터 로드
        places = await load_location_data_from_db()
        
        if not query:
            # 검색어가 없으면 모든 장소 반환 (최대 20개)
            return [place.dict() for place in places[:20]]
        
        # 검색어로 필터링
        query_lower = query.lower()
        filtered_places = []
        
        for place in places:
            # 이름, 주소, 설명에서 검색
            searchable_text = f"{place.name or ''} {place.address or ''} {place.description or ''}".lower()
            
            if query_lower in searchable_text:
                filtered_places.append(place)
        
        # 검색 로그 저장 (선택사항)
        try:
            await save_search_log(query, len(filtered_places))
        except:
            pass  # 로그 저장 실패해도 검색은 계속 진행
        
        return [place.dict() for place in filtered_places[:20]]  # 최대 20개 반환
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"검색 중 오류 발생: {str(e)}")
