# 🗺️ WhereWeGo 설문조사 시스템 테스트 가이드

## 📋 개요
JWT 토큰 기반 보안 설문조사 및 추천 시스템의 완전한 테스트 환경입니다.

## 🚀 테스트 파일들

### 1. `login_test_simple.html`
- **목적**: 간단한 로그인 테스트
- **기능**: 
  - Google/Kakao 로그인
  - 로그인 상태 확인
  - 로그아웃
  - 설문조사 테스트 페이지로 이동

### 2. `survey_system_test.html`
- **목적**: 완전한 설문조사 시스템 테스트
- **기능**:
  - 로그인 상태 관리
  - 설문조사 제출
  - 5라운드 투표 시스템
  - ML 모델 추천 (20곳)
  - 데이터 관리

## 🔧 테스트 환경 설정

### 1. 백엔드 서버 실행
```bash
# 프로젝트 루트에서
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 2. 환경 변수 확인
`.env` 파일에 다음 변수들이 설정되어 있는지 확인:
```env
SECRET_KEY=your_secret_key
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
KAKAKO_REST_API_KEY=your_kakao_rest_api_key
FRONTEND_URL=http://localhost:3000
MONGO_ATLAS_URI=your_mongodb_connection_string
```

## 📱 테스트 시나리오

### 시나리오 1: 완전한 설문조사 플로우
1. **로그인**
   - `login_test_simple.html` 접속
   - Google 또는 Kakao로 로그인
   - 로그인 상태 확인

2. **설문조사 제출**
   - `survey_system_test.html` 접속
   - 모든 설문조사 항목 선택:
     - 활동 유형: 자연풍경, 역사문화, 쇼핑, 맛집, 액티비티
     - 활동 수준: 낮음, 보통, 높음
     - 시간대: 오전, 오후, 저녁, 밤
     - 계절: 봄, 여름, 가을, 겨울
     - 선호도: 활동성, 휴식, 문화, 자연
   - "설문조사 제출" 버튼 클릭

3. **장소 추천 및 투표**
   - "장소 추천 받기" 버튼 클릭
   - 5라운드 투표 진행 (각 라운드에서 2개 장소 중 선택)
   - "투표 제출" 버튼 클릭

4. **ML 추천**
   - "ML 추천 받기 (20곳)" 버튼 클릭
   - 20개 장소 추천 결과 확인

### 시나리오 2: 에러 처리 테스트
1. **로그인 없이 접근**
   - 로그아웃 상태에서 설문조사 제출 시도
   - 401 Unauthorized 에러 확인

2. **불완전한 데이터**
   - 일부 설문조사 항목만 선택하고 제출
   - 400 Bad Request 에러 확인

3. **데이터 없이 추천 요청**
   - 설문조사 없이 ML 추천 요청
   - 404 Not Found 에러 확인

## 🔐 보안 테스트

### 1. JWT 토큰 검증
- 쿠키에서 `access_token` 제거 후 API 호출
- 401 Unauthorized 응답 확인

### 2. 사용자 데이터 격리
- 다른 사용자로 로그인 후 데이터 접근 시도
- 자신의 데이터만 접근 가능한지 확인

### 3. 토큰 만료 처리
- 토큰 만료 후 API 호출
- 적절한 에러 메시지 및 재로그인 요구 확인

## 📊 API 엔드포인트 테스트

### 인증 관련
- `GET /api/v1/survey/status` - 로그인 상태 확인
- `POST /api/v1/auth/logout` - 로그아웃

### 설문조사 관련
- `POST /api/v1/survey/submit` - 설문조사 제출
- `POST /api/v1/survey/votes` - 투표 제출

### 추천 관련
- `GET /api/v1/survey/place-recommendations` - 5라운드 장소 추천
- `GET /api/v1/survey/ml-recommendations` - ML 모델 추천 (20곳)

### 관리 관련
- `GET /api/v1/survey/model-status` - ML 모델 상태 확인
- `DELETE /api/v1/survey/reset` - 데이터 초기화

## 🐛 디버깅 팁

### 1. 브라우저 개발자 도구
- **Network 탭**: API 호출 및 응답 확인
- **Application 탭**: 쿠키 상태 확인
- **Console 탭**: JavaScript 에러 확인

### 2. 백엔드 로그
- FastAPI 서버 콘솔에서 상세 로그 확인
- JWT 토큰 검증 과정 추적

### 3. 데이터베이스 확인
- MongoDB에서 `user_log` 컬렉션 확인
- 설문조사 및 투표 데이터 저장 상태 확인

## 📝 예상 결과

### 성공적인 테스트 결과
1. **로그인**: JWT 토큰이 쿠키에 저장됨
2. **설문조사**: `user_log` 컬렉션에 데이터 저장
3. **투표**: 5라운드 투표 데이터 저장
4. **ML 추천**: 20개 장소 추천 결과 반환

### 에러 케이스
1. **401 Unauthorized**: 로그인 필요
2. **400 Bad Request**: 잘못된 요청 데이터
3. **404 Not Found**: 필요한 데이터 없음
4. **500 Internal Server Error**: 서버 내부 오류

## 🔄 데이터 초기화
테스트 완료 후 다음 방법으로 데이터 초기화:
1. HTML 페이지에서 "모든 데이터 초기화" 버튼 클릭
2. 또는 MongoDB에서 직접 데이터 삭제

## 📞 문제 해결

### 자주 발생하는 문제
1. **CORS 에러**: 백엔드 CORS 설정 확인
2. **쿠키 저장 안됨**: `credentials: 'include'` 설정 확인
3. **JWT 토큰 오류**: SECRET_KEY 환경변수 확인
4. **DB 연결 오류**: MongoDB 연결 문자열 확인

### 로그 확인 방법
```bash
# 백엔드 서버 로그
tail -f server.log

# 브라우저 콘솔
F12 → Console 탭
```

---

**🎉 테스트 완료 후 실제 프론트엔드 개발에 참고하세요!**
