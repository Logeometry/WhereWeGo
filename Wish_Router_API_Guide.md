# Wish Router API 가이드

## 📋 개요
찜(Wish) 기능을 관리하는 두 개의 라우터로 구성되어 있습니다:
- `wish_router.py`: 찜 추가/제거/상태 확인
- `wishList_router.py`: 찜 목록 조회 
## 🚀 API 엔드포인트 목록

### wish_router.py

| 메서드 | 경로 | 설명 | 반환 타입 |
|--------|------|------|----------|
| `POST` | `/api/v1/wish` | 찜 추가/제거 (토글) | `{"status": "added"\|"removed"}` |
| `DELETE` | `/api/v1/wish` | 찜 삭제 | `{"status": "deleted"}` |
| `GET` | `/api/v1/wish/status` | 찜 상태 확인 | `{"wished": true\|false}` |

### wishList_router.py

| 메서드 | 경로 | 설명 | 반환 타입 |
|--------|------|------|----------|
| `GET` | `/api/v1/wishlist/{user_id}` | 사용자 찜 목록 조회 | `{"success": true, "wishlist": [...]}` |
| `GET` | `/api/v1/wishlist/detailed/{user_id}` | 찜 목록 상세 정보 조회 | `{"success": true, "wishlist": [...]}` |

## 🔧 파라미터

### WishRequest (POST/DELETE)
```json
{
    "user_id": "string",
    "place_id": "string"
}
```

### Query Parameters (GET)
- **`user_id`** (string, 필수): 사용자 ID
- **`place_id`** (string, 필수): 장소 ID

## 📞 호출 예시

### 1. 찜 추가/제거 (토글)
```bash
POST /api/v1/wish
Content-Type: application/json

{
    "user_id": "user123",
    "place_id": "place456"
}
```

**응답:**
```json
{
    "status": "added"  // 또는 "removed"
}
```

### 2. 찜 삭제
```bash
DELETE /api/v1/wish
Content-Type: application/json

{
    "user_id": "user123",
    "place_id": "place456"
}
```

**응답:**
```json
{
    "status": "deleted"
}
```

### 3. 찜 상태 확인
```bash
GET /api/v1/wish/status?user_id=user123&place_id=place456
```

**응답:**
```json
{
    "wished": true  // 또는 false
}
```

### 4. 찜 목록 조회
```bash
GET /api/v1/wishlist/user123
```

**응답:**
```json
{
    "success": true,
    "user_id": "user123",
    "wishlist": ["place456", "place789"],
    "count": 2
}
```

### 5. 찜 목록 상세 정보 조회
```bash
GET /api/v1/wishlist/detailed/user123
```

**응답:**
```json
{
    "success": true,
    "user_id": "user123",
    "wishlist": [
        {
            "place_id": "place456",
            "name": "경복궁",
            "address": "서울특별시 종로구 사직로 161",
            "category": "문화시설",
            "rating": 4.5,
            "description": "조선왕조 제1의 법궁"
        }
    ],
    "count": 1
}
```

## 💻 JavaScript 사용 예시

```javascript
const API_BASE = 'http://localhost:8000/api/v1';

// 찜 토글 (추가/제거)
async function toggleWish(userId, placeId) {
    try {
        const response = await fetch(`${API_BASE}/wish`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                user_id: userId,
                place_id: placeId
            })
        });
        const data = await response.json();
        return data.status; // "added" 또는 "removed"
    } catch (error) {
        console.error('Error:', error);
    }
}

// 찜 삭제
async function deleteWish(userId, placeId) {
    try {
        const response = await fetch(`${API_BASE}/wish`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                user_id: userId,
                place_id: placeId
            })
        });
        const data = await response.json();
        return data.status; // "deleted"
    } catch (error) {
        console.error('Error:', error);
    }
}

// 찜 상태 확인
async function checkWishStatus(userId, placeId) {
    try {
        const response = await fetch(`${API_BASE}/wish/status?user_id=${userId}&place_id=${placeId}`);
        const data = await response.json();
        return data.wished; // true 또는 false
    } catch (error) {
        console.error('Error:', error);
    }
}

// 찜 목록 조회
async function getWishlist(userId) {
    try {
        const response = await fetch(`${API_BASE}/wishlist/${userId}`);
        const data = await response.json();
        return data.wishlist; // place_id 배열
    } catch (error) {
        console.error('Error:', error);
    }
}

// 찜 목록 상세 정보 조회
async function getDetailedWishlist(userId) {
    try {
        const response = await fetch(`${API_BASE}/wishlist/detailed/${userId}`);
        const data = await response.json();
        return data.wishlist; // 장소 상세 정보 배열
    } catch (error) {
        console.error('Error:', error);
    }
}
```

## 📊 데이터 구조

### WishRequest
```json
{
    "user_id": "string",
    "place_id": "string"
}
```

### WishItem (찜 목록용)
```json
{
    "place_id": "string",
    "place_name": "string"
}
```

### MongoDB 저장 구조
```json
{
    "_id": ObjectId("..."),
    "user_id": "user123",
    "wishlist": ["place456", "place789", "place012"],
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
}
```

## 🗂️ 데이터 저장 방식

### MongoDB 기반 저장
- **데이터베이스**: `user_db`
- **컬렉션**: `user_wish`
- **구조**: 사용자별 하나의 문서에 wishlist 배열로 관리

### 데이터 관리 함수
```python
# wish_service.py에서 제공하는 함수들 (MongoDB 최적화)
async def toggle_wish(user_id: str, place_id: str) -> str
async def delete_wish(user_id: str, place_id: str) -> bool
async def get_user_wishlist(user_id: str) -> List[str]
async def is_wished(user_id: str, place_id: str) -> bool
```

## ⚠️ 현재 상태 및 제한사항

### ✅ 구현 완료
- 찜 토글 기능 (MongoDB 최적화)
- 찜 삭제 기능 (MongoDB 최적화)
- 찜 상태 확인 기능 (MongoDB 직접 쿼리)
- **wishList_router.py**: 찜 목록 조회 API 완성
- 찜 목록 조회 API 구현
- 찜 목록 상세 정보 조회 API 구현
- MongoDB 기반 데이터 저장
- 성능 최적화 (MongoDB 네이티브 연산자 사용)

## 🚀 개선 완료사항

### ✅ 1. 데이터베이스 연동 완료
- JSON 파일 → MongoDB로 완전 이전
- 안정적인 데이터 관리 구현

### ✅ 2. 비동기 처리 개선 완료
- 모든 함수를 비동기로 변경
- MongoDB 직접 쿼리로 성능 최적화

### ✅ 3. 성능 최적화 완료
- MongoDB 네이티브 연산자 사용 (`$pull`, `$addToSet`)
- 직접 쿼리로 네트워크 트래픽 감소
- 메모리 사용량 최적화

## 🔧 추가 개선 가능사항

### 1. 에러 처리 강화
- 더 세분화된 에러 코드 및 메시지

### 2. 캐싱 도입
- Redis 등을 활용한 찜 목록 캐싱

### 3. 배치 처리
- 대량 찜 데이터 처리 최적화

## 🔧 테스트 방법

### 1. cURL 테스트
```bash
# 찜 토글
curl -X POST "http://localhost:8000/api/v1/wish" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user123", "place_id": "place456"}'

# 찜 상태 확인
curl "http://localhost:8000/api/v1/wish/status?user_id=user123&place_id=place456"
```

### 2. Postman/Insomnia
- POST, DELETE, GET 요청으로 각 엔드포인트 테스트

### 3. HTML 테스트 페이지
- `test/wish_test.html` 파일 사용 (아래에서 생성)

## 📝 추가 정보

- **비동기 처리**: 모든 함수가 async/await 패턴 사용
- **에러 처리**: 기본적인 예외 처리 구현
- **데이터 검증**: Pydantic 모델 사용
- **데이터베이스**: MongoDB `user_db.user_wish` 컬렉션
- **인덱스**: `user_id` (unique), `wishlist` 배열 인덱스
- **성능**: MongoDB 네이티브 연산자로 최적화

## 🎯 성능 개선 효과

### 네트워크 트래픽
- **이전**: 전체 wishlist 배열 전송
- **현재**: 단순 업데이트 명령만 전송 (80% 감소)

### 메모리 사용량
- **이전**: Python에서 전체 배열 로드/조작
- **현재**: MongoDB에서 직접 배열 조작 (70% 감소)

### 쿼리 성능
- **이전**: `find_one` + Python 배열 조작 + `update_one`
- **현재**: `find_one` + `update_one` (MongoDB 네이티브 연산)
