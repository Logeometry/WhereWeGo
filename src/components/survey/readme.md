설문조사 컴포넌트별 기능 요약
🎯 ResultsPage.js
설문 결과 표시 페이지

사용자가 '좋아요'로 선택한 관광지들을 필터링하여 표시

선호도 데이터와 관광지 데이터를 매칭하여 결과 생성

Material-UI의 List 컴포넌트를 사용해 추천 관광지 목록 렌더링

좋아하는 관광지가 없을 경우 "No liked attractions yet." 메시지 표시

🎨 ThemeSection.js
테마별 관광지 스와이퍼 섹션

Swiper 라이브러리를 활용한 카드 슬라이드 기능 구현

특정 테마의 관광지들을 가로 스크롤 형태로 표시

현재 슬라이드 인덱스 추적 및 자동 슬라이드 이동 기능

각 관광지에 대해 AttractionCard 컴포넌트 렌더링

테마 라벨과 관광지 목록이 없을 경우 null 반환

🏛️ AttractionCard.js
개별 관광지 카드

관광지 이미지와 이름을 카드 형태로 표시

현재 활성화된 카드인지 확인하는 isCurrent 상태 관리

활성화된 카드에만 PreferenceButtons 컴포넌트 표시

Material-UI Box와 Typography 사용한 깔끔한 레이아웃

💳 AttractionPreferenceCard.js
선호도 선택 카드 (대안 버전)

Card, CardMedia, CardContent를 활용한 풍부한 카드 UI

관광지 이미지, 이름, 설명(100자 제한) 표시

좋아요/모르겠어요/싫어요 버튼을 Stack으로 배치

각 버튼 클릭 시 해당 선호도로 onPreference 콜백 호출

🎛️ PreferenceButtons.js
선호도 선택 버튼 그룹

아이콘 버튼 3개로 구성 (싫어요, 좋아요, 관심없음)

Material-UI 아이콘 사용:

ClearIcon: 싫어요 (X 표시)

FavoriteIcon: 좋아요 (하트)

VisibilityOffIcon: 관심없음 (눈 가리기)

각 버튼 클릭 시 해당 관광지 ID와 선호도를 부모 컴포넌트로 전달

📊 ProgressBar.js
설문 진행률 표시

Material-UI LinearProgress로 진행률 바 구현

현재 완료된 항목 수와 전체 항목 수를 비율로 계산

"X / Y Completed" 형태의 텍스트로 진행 상황 표시

전체 항목이 0일 경우 진행률 0%로 처리

🔄 컴포넌트 간 상호작용
데이터 흐름:

ThemeSection → AttractionCard → PreferenceButtons

사용자 선택 → onPreference 콜백 → 상위 컴포넌트로 데이터 전달

수집된 선호도 데이터 → ResultsPage에서 결과 표시

UI 패턴:

카드 기반 인터페이스: 관광지 정보를 시각적으로 표현

스와이퍼 네비게이션: 다수의 관광지를 효율적으로 탐색

아이콘 기반 선택: 직관적인 선호도 표현

진행률 피드백: 사용자 경험 향상