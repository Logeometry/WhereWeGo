# Nearby Place Router API 가이드

## 📋 개요
`nearby_place_router.py`는 기준 장소 주변의 관광지, 카페, 식당을 추천하고 혼잡도 정보를 제공하는 FastAPI 라우터입니다.

## 🚀 API 엔드포인트 목록

| 엔드포인트 | 설명 | 반환 타입 |
|-----------|------|----------|
| `GET /api/v1/nearby/{place_id}` | 주변 관광지 조회 | `List[Tourism]` |
| `GET /api/v1/nearby/cafes/{place_id}` | 주변 카페 조회 | `List[Cafe]` |
| `GET /api/v1/nearby/restaurants/{place_id}` | 주변 식당 조회 | `List[Restaurant]` |
| `GET /api/v1/nearby/all/{place_id}` | 모든 주변 장소 조회 | `dict` |
| `GET /api/v1/place/crowding/{place_id}` | 특정 장소 혼잡도 조회 | `dict` |

## 🔧 파라미터

### Path Parameters
- **`place_id`** (string, 필수): 기준 장소의 MongoDB ObjectId 또는 content_id

### Query Parameters
- **`max_distance`** (float, 선택): 최대 거리 (km, 기본값: 5.0)
- **`include_crowding`** (bool, 선택): 혼잡도 정보 포함 여부 (기본값: false)

## 📞 호출 예시

### 1. 주변 관광지 조회
```bash
# 기본 호출 (5km 반경)
GET /api/v1/nearby/681891fa77e67d6ebadae359

# 거리와 혼잡도 포함
GET /api/v1/nearby/681891fa77e67d6ebadae359?max_distance=3.0&include_crowding=true
```

### 2. 주변 카페 조회
```bash
GET /api/v1/nearby/cafes/681891fa77e67d6ebadae359?max_distance=2.0
```

### 3. 주변 식당 조회
```bash
GET /api/v1/nearby/restaurants/681891fa77e67d6ebadae359?max_distance=1.5
```

### 4. 모든 주변 장소 조회
```bash
GET /api/v1/nearby/all/681891fa77e67d6ebadae359?max_distance=5.0
```

### 5. 특정 장소 혼잡도 조회
```bash
GET /api/v1/place/crowding/681891fa77e67d6ebadae359
```

## 💻 JavaScript 사용 예시

```javascript
const API_BASE = 'http://localhost:8000/api/v1';

// 주변 관광지 조회
async function getNearbyPlaces(placeId, maxDistance = 5.0) {
    try {
        const response = await fetch(`${API_BASE}/nearby/${placeId}?max_distance=${maxDistance}`);
        const places = await response.json();
        return places;
    } catch (error) {
        console.error('Error:', error);
    }
}

// 주변 카페 조회
async function getNearbyCafes(placeId, maxDistance = 5.0) {
    try {
        const response = await fetch(`${API_BASE}/nearby/cafes/${placeId}?max_distance=${maxDistance}`);
        const cafes = await response.json();
        return cafes;
    } catch (error) {
        console.error('Error:', error);
    }
}

// 주변 식당 조회
async function getNearbyRestaurants(placeId, maxDistance = 5.0) {
    try {
        const response = await fetch(`${API_BASE}/nearby/restaurants/${placeId}?max_distance=${maxDistance}`);
        const restaurants = await response.json();
        return restaurants;
    } catch (error) {
        console.error('Error:', error);
    }
}

// 모든 주변 장소 조회
async function getAllNearbyPlaces(placeId, maxDistance = 5.0) {
    try {
        const response = await fetch(`${API_BASE}/nearby/all/${placeId}?max_distance=${maxDistance}`);
        const data = await response.json();
        return {
            tourist_spots: data.tourist_spots,
            cafes: data.cafes,
            restaurants: data.restaurants
        };
    } catch (error) {
        console.error('Error:', error);
    }
}

// 특정 장소 혼잡도 조회
async function getPlaceCrowding(placeId) {
    try {
        const response = await fetch(`${API_BASE}/place/crowding/${placeId}`);
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error:', error);
    }
}
```

## 📊 응답 데이터 구조

### Tourism 객체
```json
{
    "id": "681891fa77e67d6ebadae359",
    "name": "경복궁",
    "category": "문화시설",
    "category_group": "문화시설",
    "description": "조선왕조 제1의 법궁",
    "address": "서울특별시 종로구 사직로 161",
    "region": "서울",
    "location": {
        "type": "Point",
        "coordinates": [126.977969, 37.579617]
    },
    "rating": 4.5,
    "review_count": 1234,
    "visitors_count": 5678,
    "vector_version": 1,
    "updated_at": "2024-01-01T00:00:00Z"
}
```

### Cafe 객체
```json
{
    "id": "6872aaf3e80b06a7965597bb",
    "name": "스타벅스 경복궁점",
    "category": "카페",
    "address": "서울특별시 종로구 사직로 161",
    "description": "스타벅스 카페",
    "region": "서울",
    "location": {
        "type": "Point",
        "coordinates": [126.977969, 37.579617]
    },
    "rating": 4.2,
    "review_count": 567,
    "place_url": "https://place.map.kakao.com/...",
    "image_url": "https://example.com/image.jpg",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z",
    "distance": 0.3
}
```

### Restaurant 객체
```json
{
    "id": "6872aaf3e80b06a7965597cc",
    "name": "한정식집",
    "category": "한식",
    "address": "서울특별시 종로구 사직로 161",
    "description": "전통 한정식 전문점",
    "region": "서울",
    "location": {
        "type": "Point",
        "coordinates": [126.977969, 37.579617]
    },
    "rating": 4.3,
    "review_count": 234,
    "place_url": "https://place.map.kakao.com/...",
    "image_url": "https://example.com/image.jpg",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z",
    "distance": 0.5
}
```

### 모든 주변 장소 조회 응답
```json
{
    "tourist_spots": [
        {
            "id": "681891fa77e67d6ebadae359",
            "name": "경복궁",
            "address": "서울특별시 종로구 사직로 161",
            "distance": 0.8
        }
    ],
    "cafes": [
        {
            "id": "6872aaf3e80b06a7965597bb",
            "name": "스타벅스 경복궁점",
            "address": "서울특별시 종로구 사직로 161",
            "distance": 0.3
        }
    ],
    "restaurants": [
        {
            "id": "6872aaf3e80b06a7965597cc",
            "name": "한정식집",
            "address": "서울특별시 종로구 사직로 161",
            "distance": 0.5
        }
    ]
}
```

### 혼잡도 조회 응답
```json
{
    "success": true,
    "message": "장소 혼잡도 조회 성공",
    "data": {
        "id": "681891fa77e67d6ebadae359",
        "name": "경복궁",
        "address": "서울특별시 종로구 사직로 161",
        "crowding_info": {
            "poi_id": "10067845",
            "crowding_level": "보통",
            "crowding_score": 3,
            "last_updated": "2024-01-01T12:00:00Z"
        }
    }
}
```

## ⚠️ 주의사항

1. **place_id**: MongoDB ObjectId 형식이어야 함
2. **거리 단위**: km 단위로 입력
3. **최대 결과**: 각 API는 최대 10개 결과 반환
4. **에러 처리**: 404 (장소 없음), 500 (서버 오류) 등 처리 필요
5. **혼잡도 정보**: 현재 더미 POI ID 사용 중 (실제 매핑 필요)

## 🔧 테스트 방법

1. **HTML 테스트 파일 사용**:
   - `test/nearby_cafe_test.html` 파일을 브라우저에서 열기
   - 장소 ID와 거리 입력 후 각 버튼 클릭

2. **cURL 테스트**:
   ```bash
   curl "http://localhost:8000/api/v1/nearby/681891fa77e67d6ebadae359?max_distance=5.0"
   ```

3. **Postman/Insomnia**:
   - GET 요청으로 위 엔드포인트들 테스트

## 🚨 에러 코드

| 코드 | 설명 |
|------|------|
| 404 | 장소를 찾을 수 없음 |
| 429 | API 호출 한도 초과 |
| 500 | 서버 내부 오류 |

## 📝 추가 정보

- **티맵 API 연동**: 실시간 혼잡도 데이터 조회
- **거리 계산**: Haversine 공식 사용
- **비동기 처리**: 모든 함수가 async/await 패턴 사용
- **타입 안전성**: Pydantic 모델 사용
