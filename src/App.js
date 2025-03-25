import React from 'react';
import LandingPage from './pages/LandingPage'; // 랜딩 페이지 컴포넌트 불러오기
import { createTheme, ThemeProvider } from '@mui/material/styles'; // MUI 테마 생성 및 제공을 위한 모듈
import './App.scss'; // 전역 스타일시트 적용

// MUI 커스텀 테마 설정
const theme = createTheme({
  palette: {
    primary: {
      main: '#ff1150', // 메인 색상 설정
    },
    secondary: {
      main: '#ff6f61', // 보조 색상 설정
    },
  },
  typography: {
    fontFamily: 'Noto Sans KR, sans-serif', // 전체 앱에서 사용할 폰트 설정
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',  // 버튼 텍스트 대문자 자동 변환 비활성화
          borderRadius: 30,       // 버튼 둥근 테두리 적용
          fontWeight: 'bold',     // 버튼 텍스트 굵게
          transition: '0.3s',     // 호버 시 부드러운 전환 효과
        },
        containedPrimary: {
          // contained + primary 타입 버튼 스타일 설정
          backgroundColor: '#ff1150',
          color: '#fff',
          '&:hover': {
            backgroundColor: '#ff6f61',
          },
        },
        outlinedPrimary: {
          // outlined + primary 타입 버튼 스타일 설정
          borderColor: '#ff1150',
          color: '#ff1150',
          '&:hover': {
            borderColor: '#ff6f61',
            color: '#ff6f61',
          },
        },
        textPrimary: {
          // text + primary 타입 버튼 스타일 설정
          color: '#ff1150',
          '&:hover': {
            backgroundColor: 'rgba(255, 17, 80, 0.08)',
          },
        },
      },
    },
  },
});

// 앱의 루트 컴포넌트
function App() {
  return (
    // 테마를 전체 앱에 적용
    <ThemeProvider theme={theme}>
      <LandingPage /> {/* 랜딩 페이지 렌더링 */}
    </ThemeProvider>
  );
}

export default App; // App 컴포넌트를 외부에서 사용할 수 있도록 내보내기
