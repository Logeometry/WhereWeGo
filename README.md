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
```

## 📊 BPR 추천 알고리즘을 위한 데이터 구성

### 📁 `BPR/data/log/`

- 유저의 설문 응답, 클릭 기록 등 **로그 데이터**가 저장되는 폴더입니다.
- JSON 형식으로 유저의 활동 정보가 저장되며, 관심 있는 항목은 `1`, 그 외는 `0`으로 구성됩니다.
- 이 데이터는 벡터화 과정을 통해 학습용 형식으로 변환됩니다.
- 현재는 코드만 존재, 로그인 구현 후 반영 예정

---

### 🧾 설문 기반 학습 데이터: `survey_vectors.json`

- 현재 `training` 폴더에는 **`survey_vectors.json`** 파일이 존재합니다.
- 이 파일은 사용자의 **설문 응답 데이터**를 벡터로 변환하여 저장한 학습용 데이터입니다.

#### 📍 경로
- 원본 설문 응답 데이터:  
  `backend/data/survey_results.json`

- 벡터화된 설문 응답 벡터 파일:  
  `backend/BPR/data/training/survey_vectors.json`

#### 🔄 생성 방식
- `utils/vectorizer.py` 또는 유사한 전처리 스크립트를 통해 생성됩니다.
- 예시 구조:
  ```json
  {
    "test1": [0, 1, 0, 0, 1, 0, 1, 0, 0, 1]
  }
---

### 🛠️ `BPR/utils/`

- `log` 폴더의 원본 데이터를 **벡터 형태로 전처리**하는 Python 스크립트가 위치합니다.
- 관심사 및 행동 기반의 정보를 0과 1의 벡터로 변환합니다.
- 예: `{ "username": "test1", "vector": [0, 1, 0, 1, ...] }`

---

### 📁 `BPR/data/training/`

- 벡터화된 학습용 데이터가 저장되는 폴더입니다.
- BPR 추천 모델이 직접 참조하는 데이터 파일들이 이곳에 위치합니다.
- 포맷 예시:
  ```json
  {
    "test1": [0, 1, 0, 1, 0, 0, 1]
  } ```



# 🧩 Google 로그인 연동 방법 

FastAPI에서 Google OAuth를 처리하고 JWT를 발급.
프론트에서는 로그인 버튼과 토큰 관리 정도만 신경 써주세요.

---

## ✅ 1. 로그인 버튼 구현

gogole 로그인 시작을 위해, 로그인 버튼을 구현하고 아래처럼 로그인 url로 리디렉션해주시면 됩니다.

```tsx
  window.location.href = "http://localhost:8000/auth/google/login";
```

## ✅ 2. JWT 저장

로그인이 완료된다면 백엔드에서 JWT token이 포함된 json형태의 응답이 내려옵니다.
프론트에서 이 토큰을 따로 저장해주세요(사용자 식별을 위해 필요함)
- FastApi는 비동식 HTTP API 서버에 특화되어있기션을 파일/메모리에 유지하는 방식보다 JWT가 유리하다고 판단햇습니다. 

## ✅ 3. 공통 요청 헤더 자동설정

모든 API요청에 토큰을 붙일 수 없으니, Axios를 통해 공통헤더 처리를 하는 것을 추천드립니다. 

혹은 JWT를 쿠키에 저장하는 방식을 고려하는 중입니다. 그러나 현재 back과 front의 도메인이 다르기도하고 구현에도 어려움이 있기에 해당 방식으로 우선 구현했습니다.
해당 방식으로 확인 후 쿠키 저장 방식으로 전환 예정.

## ✅ 4, 로그아웃 처리

```tsx
localStorage.removeItem("access_token");
```