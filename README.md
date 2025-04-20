# 부산 관광지 추천 서비스

부산 지역 관광지를 사용자 맞춤형으로 추천하는 머신러닝 기반 관광 추천 시스템입니다

## 프로젝트 소개

이 프로젝트는 사용자의 선호도와 여행 스타일에 맞는 부산 지역 관광지를 추천하는 서비스 개발을 목표로 합니다.    
Foursquare API를 통해 수집한 관광지 데이터와 머신러닝 알고리즘을 활용하여 사용자의 취향에 맞는 관광지를 추천합니다.

## 기술 스택

- **Backend**: FastAPI
- **Database**: MongoDB, PyMongo
- **머신러닝**: pytorch
- **API 통합**: Foursquare Places API
- **Frontend**: React.Js, MUI, SCSS

## 코드 컨벤션

### 명명 규칙
- **모듈명**: snake_case, 기능을 직관적으로 표시 (예: data_processor)
- **클래스명**: PascalCase (예: DataProcessor)
- **함수명**: snake_case, 동사나 동사구로 시작 (예: get_recommendations())
- **변수명**: snake_case, 약어 대신 직관적인 이름 사용 (예: place_id)
- **상수명**: 대문자와 언더바 (예: MAX_RESULTS)

### 코드 스타일
- **들여쓰기**: 스페이스 4회
- **공백**: 함수, 클래스 간 공백 1줄
- **연산자**: 연산자 양쪽에 공백 추가 (예: top_k: int = 5)

### 코딩 패턴
- **비동기 함수**: 데이터베이스 조회, API 요청, 파일 작업은 비동기 함수로 구현
- **비동기 키워드**: async 함수, async with 컨텍스트 매니저 사용
- **타입 힌팅**: 함수 파라미터와 반환값에 타입 힌팅 사용 (예: def get_data(user_id: str) -> dict:)
