## ⚠️ 주의사항
- 현재는 API 구조 및 응답 형태를 테스트하기 위한 임시 백엔드입니다.
- 모든 데이터는 JSON 파일로 저장되고 있으며, 이후 실제 DB 또는 외부 API를 연동할 예정입니다.
- 따라서 API 동작은 구조 파악 및 프론트엔드 개발 참고용으로 사용해주세요.
- 실제 DB 또는 외부 API 반영 후에는 반환 형태가 달라질 수 있습니다. 

## 📁 test 폴더
- 프론트엔드에서 사용할 API를 미리 확인해보기 위해 구성한 테스트용 코드가 위치합니다.
- 실제 API 연동 시, 제거할 예정입니다. 

## ✅ API 엔드포인트

### 🔹 `/categories`  
**Method:** `GET`  
**Description:** 전체 장소 데이터를 반환하거나, 특정 카테고리 키워드로 필터링된 데이터를 조회합니다.

**Query Parameters:**

| Name    | Type     | Required | Description                              |
|---------|----------|----------|------------------------------------------|
| keyword | `string` | No       | 카테고리 필터링 키워드 (예: "자연", "맛집") |

**Response:**

```json
[
  {
    "name": "해운대 해수욕장", 
    "location": "해운대, 부산", 
    "description": "황금빛 모래와 맑은 물로 유명한 해변.", 
    "category": ["자연/해변", "체험"], 
    "rating": 4.7
    },
  ...
]
``` 

### 🔹 `/search`  
**Method:** `GET`  
**Description:** 여행지 데이터에서 키워드 기반으로 장소를 검색합니다.  
※ `data/temporary_data.json` 에 임시 저장된 데이터를 기준으로 동작합니다.

**Query Parameters:**

| Name  | Type        | Required | Description                                     |
|-------|-------------|----------|-------------------------------------------------|
| query | `string`    | No       | 장소 이름 또는 카테고리명으로 검색 키워드 입력 |

**Response (예시):**

```json
[
   {
    "name": "해운대 해수욕장", 
    "location": "해운대, 부산", 
    "description": "황금빛 모래와 맑은 물로 유명한 해변.", 
    "category": ["자연/해변", "체험"], 
    "rating": 4.7
    },
  ...
]
``` 
## 📋 설문 응답 수신 API

설문 데이터를 수신하고 서버에 저장하기 위한 라우터입니다.  
현재는 JSON 파일(`data/survey_results.json`)에 누적 저장되며, 이후 DB 연동 예정입니다.

### 🔸 POST `/survey`

- 클라이언트에서 전송한 설문 응답 데이터를 저장합니다.
- 성공 시: `{"message": "설문이 성공적으로 저장되었습니다."}` 반환
- 실패 시: HTTP 500 에러와 함께 에러 메시지 반환

### 🔸 Request Body 예시 (`application/json`)
```json
  {
    "username": "test1",
    "travel_type": "도시 관광",
    "climate": "온화한 사계절 기후",
    "budget": "2",
    "duration": "8-14일",
    "companion": "커플/부부"
  },
'''

