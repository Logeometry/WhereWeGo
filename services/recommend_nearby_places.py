# services/recommendation.py

from typing import List
from geopy.distance import geodesic
from bson import ObjectId

from schemas import Tourism, Cafe, Restaurant
from db import places_col, cafa_col, restaurant_col  # db.py에서 정의된 MongoDB 컬렉션

async def get_place_by_id(place_id: str) -> Tourism:
    """
    MongoDB _id를 이용해 문서를 조회한 뒤 Tourism 모델로 반환.
    """
    from bson import ObjectId
    try:
        # 먼저 문자열로 검색해보기
        doc = await places_col.find_one({"_id": place_id})
        if not doc:
            # ObjectId로 변환해서 검색해보기
            try:
                object_id = ObjectId(place_id)
                doc = await places_col.find_one({"_id": object_id})
            except:
                pass
        
        if not doc:
            raise ValueError(f"Place ID {place_id} not found in DB.")
        
        # ObjectId를 문자열로 변환
        doc["_id"] = str(doc["_id"])
        return Tourism(**doc)
    except Exception as e:
        raise ValueError(f"Invalid Place ID format: {place_id}. Must be a valid MongoDB ObjectId.")


async def get_cafe_by_id(cafe_id: str) -> dict:
    """
    cafe_id를 이용해 MongoDB에서 카페 문서를 조회하여 반환.
    """
    doc = await cafa_col.find_one({"_id": ObjectId(cafe_id)})
    if not doc:
        raise ValueError(f"Cafe ID {cafe_id} not found in DB.")
    return doc


async def get_restaurant_by_id(restaurant_id: str) -> dict:
    """
    restaurant_id를 이용해 MongoDB에서 식당 문서를 조회하여 반환.
    """
    doc = await restaurant_col.find_one({"_id": ObjectId(restaurant_id)})
    if not doc:
        raise ValueError(f"Restaurant ID {restaurant_id} not found in DB.")
    return doc


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
    
    # 기준 좌표 설정 (기존 데이터는 map_y, map_x 사용, 새로운 데이터는 location 사용)
    if hasattr(base_place, 'map_y') and hasattr(base_place, 'map_x'):
        base_coords = (base_place.map_y, base_place.map_x)
    elif hasattr(base_place, 'location') and base_place.location:
        coords = base_place.location.coordinates
        base_coords = (coords[1], coords[0])  # [경도, 위도] -> (위도, 경도)
    else:
        raise ValueError("기준 장소의 좌표 정보를 찾을 수 없습니다.")

    nearby_with_dist: List[tuple[Tourism, float]] = []
    cursor = places_col.find({})

    # 2) 전체 장소 순회
    async for doc in cursor:
        if str(doc.get("_id")) == place_id:
            continue

        # 대상 좌표 설정
        target_coords = None
        if doc.get("map_y") and doc.get("map_x"):
            target_coords = (doc["map_y"], doc["map_x"])
        elif doc.get("location") and doc["location"].get("coordinates"):
            coords = doc["location"]["coordinates"]
            target_coords = (coords[1], coords[0])  # [경도, 위도] -> (위도, 경도)
        
        if target_coords is None:
            continue

        try:
            dist_km = geodesic(base_coords, target_coords).km
        except Exception:
            continue

        if dist_km <= max_distance:
            # ObjectId를 문자열로 변환
            doc_copy = doc.copy()
            doc_copy["_id"] = str(doc_copy["_id"])
            place_obj = Tourism(**doc_copy)
            nearby_with_dist.append((place_obj, dist_km))

    # 3) 거리 기준 오름차순 정렬
    nearby_with_dist.sort(key=lambda x: x[1])

    # 최대 10개 장소만 추출
    return [place for place, _ in nearby_with_dist[:10]]


async def recommend_nearby_cafes(
    place_id: str,
    max_distance: float = 5.0
) -> List[dict]:
    """
    기준 장소 주변의 카페들을 추천하는 함수
    
    Args:
        place_id: 기준 장소의 MongoDB ObjectId
        max_distance: 최대 거리 (km)
    
    Returns:
        List[dict]: 주변 카페 목록 (거리순 정렬, 최대 10개)
    """
    # 1) 기준 장소 조회
    base_place = await get_place_by_id(place_id)
    
    # 기준 좌표 설정 (기존 데이터는 map_y, map_x 사용, 새로운 데이터는 location 사용)
    if hasattr(base_place, 'map_y') and hasattr(base_place, 'map_x'):
        base_coords = (base_place.map_y, base_place.map_x)
    elif hasattr(base_place, 'location') and base_place.location:
        coords = base_place.location.coordinates
        base_coords = (coords[1], coords[0])  # [경도, 위도] -> (위도, 경도)
    else:
        raise ValueError("기준 장소의 좌표 정보를 찾을 수 없습니다.")

    # print(f"기준 좌표: {base_coords}")
    # print(f"최대 거리: {max_distance}km")

    # 카페 컬렉션 확인
    cafe_count_total = await cafa_col.count_documents({})
    print(f"카페 컬렉션 총 문서 수: {cafe_count_total}")

    if cafe_count_total == 0:
        print("⚠️ 카페 컬렉션이 비어있습니다.")
        return []

    nearby_cafes_with_dist: List[tuple[dict, float]] = []
    cursor = cafa_col.find({})
    
    cafe_count = 0
    valid_coords_count = 0

    # 2) 전체 카페 순회
    async for doc in cursor:
        cafe_count += 1
        
        # 다양한 좌표 필드 확인
        target_coords = None
        
        # 1) location.coordinates 형식 확인
        location = doc.get("location")
        if location and "coordinates" in location:
            coords = location["coordinates"]
            if len(coords) >= 2:
                # MongoDB는 [경도, 위도] 순서이므로 그대로 사용
                target_coords = (coords[1], coords[0])  # [경도, 위도] -> (위도, 경도)
        
        # 2) map_y, map_x 형식 확인
        if not target_coords and doc.get("map_y") and doc.get("map_x"):
            target_coords = (doc["map_y"], doc["map_x"])
        
        # 3) lat, lng 형식 확인
        if not target_coords and doc.get("lat") and doc.get("lng"):
            target_coords = (doc["lat"], doc["lng"])
        
        if target_coords is None:
            continue
            
        valid_coords_count += 1

        try:
            dist_km = geodesic(base_coords, target_coords).km
        except Exception as e:
            print(f"거리 계산 오류: {e}")
            continue

        if dist_km <= max_distance:
            # 거리 정보를 카페 데이터에 추가
            cafe_data = doc.copy()
            cafe_data["distance"] = round(dist_km, 2)
            # ObjectId를 문자열로 변환
            cafe_data["_id"] = str(cafe_data["_id"])
            nearby_cafes_with_dist.append((cafe_data, dist_km))

    # print(f"총 카페 수: {cafe_count}")
    # print(f"유효한 좌표를 가진 카페 수: {valid_coords_count}")
    # print(f"최대 거리 내 카페 수: {len(nearby_cafes_with_dist)}")

    # 3) 거리 기준 오름차순 정렬
    nearby_cafes_with_dist.sort(key=lambda x: x[1])

    # 최대 10개 카페만 추출
    return [cafe for cafe, _ in nearby_cafes_with_dist[:10]]


async def recommend_nearby_restaurants(
    place_id: str,
    max_distance: float = 5.0
) -> List[dict]:
    """
    기준 장소 주변의 식당들을 추천하는 함수
    
    Args:
        place_id: 기준 장소의 content_id
        max_distance: 최대 거리 (km)
    
    Returns:
        List[dict]: 주변 식당 목록 (거리순 정렬, 최대 10개)
    """
    # 1) 기준 장소 조회
    base_place = await get_place_by_id(place_id)
    
    # 기준 좌표 설정 (기존 데이터는 map_y, map_x 사용, 새로운 데이터는 location 사용)
    if hasattr(base_place, 'map_y') and hasattr(base_place, 'map_x'):
        base_coords = (base_place.map_y, base_place.map_x)
    elif hasattr(base_place, 'location') and base_place.location:
        coords = base_place.location.coordinates
        base_coords = (coords[1], coords[0])  # [경도, 위도] -> (위도, 경도)
    else:
        raise ValueError("기준 장소의 좌표 정보를 찾을 수 없습니다.")

    nearby_restaurants_with_dist: List[tuple[dict, float]] = []
    cursor = restaurant_col.find({})

    # 2) 전체 식당 순회
    async for doc in cursor:
        location = doc.get("location")
        if not location or "coordinates" not in location:
            continue
            
        coords = location["coordinates"]
        if len(coords) < 2:
            continue
            
        y, x = coords[1], coords[0]  # MongoDB는 [경도, 위도] 순서

        try:
            dist_km = geodesic(base_coords, (y, x)).km
        except Exception:
            continue

        if dist_km <= max_distance:
            # 거리 정보를 식당 데이터에 추가
            restaurant_data = doc.copy()
            restaurant_data["distance"] = round(dist_km, 2)
            # ObjectId를 문자열로 변환
            restaurant_data["_id"] = str(restaurant_data["_id"])
            nearby_restaurants_with_dist.append((restaurant_data, dist_km))

    # 3) 거리 기준 오름차순 정렬
    nearby_restaurants_with_dist.sort(key=lambda x: x[1])

    # 최대 10개 식당만 추출
    return [restaurant for restaurant, _ in nearby_restaurants_with_dist[:10]]
