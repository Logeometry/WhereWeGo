# services/recommendation.py

from typing import List
from geopy.distance import geodesic
from bson import ObjectId

from schemas import Tourism
from db import places_col  # db.py에서 정의된 MongoDB 컬렉션

async def get_place_by_id(place_id: str) -> Tourism:
    """
    content_id를 이용해 MongoDB에서 문서를 조회한 뒤 Tourism 모델로 반환.
    """
    doc = await places_col.find_one({"content_id": place_id})
    if not doc:
        raise ValueError(f"Place ID {place_id} not found in DB.")
    return Tourism(**doc)


async def recommend_nearby_places(
    place_id: str,
    max_distance: float = 5.0
) -> List[Tourism]:
    """
    1) get_place_by_id(place_id)로 기준 장소 조회 → base_coords = (map_y, map_x)
    2) places_col.find({})로 전체 문서를 async for로 순회하며:
       - 동일 content_id 스킵
       - map_y 또는 map_x가 없으면 스킵
       - geodesic으로 base_coords와 target_coords 간 거리 계산
       - 거리 <= max_distance면 (Tourism, dist) 튜플로 nearby_with_dist에 추가
    3) 거리 기준 오름차순 정렬 후, 상위 10개 Tourism 객체만 반환
    """
    # 1) 기준 장소 조회
    base_place = await get_place_by_id(place_id)
    base_coords = (base_place.map_y, base_place.map_x)

    nearby_with_dist: List[tuple[Tourism, float]] = []
    cursor = places_col.find({})

    # 2) 전체 장소 순회
    async for doc in cursor:
        if doc.get("content_id") == place_id:
            continue

        y = doc.get("map_y")
        x = doc.get("map_x")
        if y is None or x is None:
            continue

        try:
            dist_km = geodesic(base_coords, (y, x)).km
        except Exception:
            continue

        if dist_km <= max_distance:
            place_obj = Tourism(**doc)
            nearby_with_dist.append((place_obj, dist_km))

    # 3) 거리 기준 오름차순 정렬
    nearby_with_dist.sort(key=lambda x: x[1])

    # 최대 10개 장소만 추출
    return [place for place, _ in nearby_with_dist[:10]]
