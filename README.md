🏠 루트: 앱 초기화 및 전역 설정
📦 assets: 정적 리소스
🧩 components: 재사용 가능한 UI 컴포넌트
  └── survey: 설문조사 전용 컴포넌트
🌐 contexts: 전역 상태 관리
📊 data: 정적 데이터 및 설정
🪝 hooks: 커스텀 훅
📄 pages: 페이지 컴포넌트
  └── SurveyForm: 설문 폼 전용

의존성 설치
처음 설치 시 기존 캐시 및 모듈 제거 후 재설치하는 것을 권장합니다.
Remove-Item -Recurse -Force node_modules
Remove-Item -Force package-lock.json
npm install

npm start
기본 실행 주소: http://localhost:3000

🛠 주요 라이브러리
React: 18.0.0

MUI:

@mui/material 6.4.8

@mui/icons-material 6.4.12

Emotion (스타일링): 11.14.0

Framer Motion: 12.23.15

React Router DOM: 7.4.1
