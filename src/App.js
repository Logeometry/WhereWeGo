import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import LandingPage from './pages/LandingPage';
//import SurveyForm from './pages/SurveyForm/SurveyForm';
import { createTheme, ThemeProvider } from '@mui/material/styles';
import './App.scss';

const theme = createTheme({
  palette: {
    primary: {
      main: '#ff1150', // 메인 색상
    },
    secondary: {
      main: '#ff6f61', // 보조 색상
    },
  },
  typography: {
    fontFamily: 'Noto Sans KR, sans-serif',
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          borderRadius: 30,
          fontWeight: 'bold',
          transition: '0.3s',
        },
        containedPrimary: {
          backgroundColor: '#ff1150',
          color: '#fff',
          '&:hover': {
            backgroundColor: '#ff6f61',
          },
        },
        outlinedPrimary: {
          borderColor: '#ff1150',
          color: '#ff1150',
          '&:hover': {
            borderColor: '#ff6f61',
            color: '#ff6f61',
          },
        },
        textPrimary: {
          color: '#ff1150',
          '&:hover': {
            backgroundColor: 'rgba(255, 17, 80, 0.08)',
          },
        },
      },
    },
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          {/*<Route path="/survey" element={<SurveyForm />} />*/}
        </Routes>
      </BrowserRouter>
    </ThemeProvider>
  );
}

export default App;
