🏠 LandingPage.js
메인 홈페이지
Header, Footer 등 기본 레이아웃 구성
AiPlannerBanner: AI 여행 계획 서비스 홍보
RecommendationGallery: 추천 관광지 갤러리
TravelNewsBanner: 여행 뉴스 및 정보 배너
전체적인 랜딩 페이지 구조를 Container로 감싸서 제공

🔍 SearchResultPage.js
검색 결과 표시 페이지
URL 쿼리 파라미터에서 검색어 추출
하드코딩된 관광지 데이터에서 검색어 매칭
제목, 위치, 설명에서 검색어 포함 여부로 필터링
TouristList 컴포넌트로 검색 결과 표시
검색 결과가 없을 경우 "검색 결과가 없습니다" 메시지

📝 SurveyPage.js
설문조사 메인 페이지
4단계 설문 프로세스: start → survey → additionalInfo → loading
관광지 선호도 조사: 8개 관광지에 대해 좋아요/싫어요/관심없음 선택
추가 정보 수집: 출발 도시, 여행 기간, 시작 날짜, 출발지점
로딩 화면: 진행률 표시, 부산 관련 팁 제공
데이터 전달: 설문 결과를 TravelPlanPage로 state 전달

🗺️ CategoryDetailPage.js
카테고리별 관광지 목록 페이지
URL 파라미터로 카테고리 라벨 받아서 해당 카테고리 데이터 로드
서브카테고리 태그 필터링 기능 (SubCategoryTags)
페이지네이션 (10개씩 표시)
busanSampleData에서 categoryGroup으로 필터링
로딩/에러 상태 처리 및 "홈으로 돌아가기" 버튼

🏛️ TouristDetailPage.js
관광지 상세 정보 페이지
URL 파라미터로 관광지 ID 받아서 상세 정보 표시
위시리스트 기능: WishlistContext 사용하여 찜하기/해제
스크롤 이벤트: 100px 이상 스크롤 시 헤더 스타일 변경
상세 정보 표시: 이미지, 설명, 위치, 연락처, 운영시간 등
네비게이션: 뒤로가기, 공유하기 버튼

❤️ WishlistPage.js
위시리스트 관리 페이지
로컬 스토리지 연동: 위시리스트 데이터 저장/불러오기
위시리스트 표시: 저장된 관광지들을 카드 형태로 나열
제거 기능: 하트 아이콘 클릭으로 위시리스트에서 제거
추천 여행지: 하드코딩된 4개 추천 장소 표시
여행 계획하기: 맛집 지도, 지하철 여행, 축제 정보 섹션
빈 상태 처리: 위시리스트가 비어있을 때 안내 메시지와 "관광지 찾아보기" 버튼

🗓️ TravelPlanPage.js
여행 일정 계획 페이지
Tmap 지도 연동: 관광지 위치 마커 표시 및 경로 그리기
드래그 앤 드롭: react-beautiful-dnd로 일정 순서 변경

일정 관리:
일자 추가/제거 기능
관광지 검색 및 특정 날짜에 추가
각 관광지별 권장 체류시간 표시
3일 기본 일정: 하드코딩된 샘플 일정 제공
여행 정보 요약: 출발지, 기간, 시작일 등 설문 결과 표시
Tmap API: 경로 탐색 API 호출 기능 (보행자 경로)

🔄 컴포넌트 간 데이터 흐름
설문 → 여행 계획:
SurveyPage에서 사용자 선호도 및 여행 정보 수집
navigate를 통해 state로 TravelPlanPage에 데이터 전달
TravelPlanPage에서 설문 결과 기반 맞춤 일정 생성

위시리스트 연동:
CategoryDetailPage/TouristDetailPage에서 위시리스트 추가
WishlistContext를 통한 전역 상태 관리
WishlistPage에서 저장된 항목 관리

검색 기능:
Header에서 검색어 입력
SearchResultPage에서 결과 표시
CategoryDetailPage에서 카테고리별 필터링