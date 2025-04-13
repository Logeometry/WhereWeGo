// src/App.js
import React, { useState } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import LandingPage from './pages/LandingPage';
import SurveyForm from './pages/SurveyForm/SurveyForm';
import CategoryDetailPage from './pages/CategoryDetailPage';
import Header from './components/Header';
import { createTheme, ThemeProvider } from '@mui/material/styles';
import './App.scss';
import { categoriesData } from './data/categoriesData';
import WishlistPage from './pages/WishlistPage';

const theme = createTheme({
  palette: {
    primary: { main: '#ff1150' },
    secondary: { main: '#ff6f61' },
  },
  typography: { fontFamily: `'Pretendard', sans-serif` },
  
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
          '&:hover': { backgroundColor: '#ff6f61' },
        },
        outlinedPrimary: {
          borderColor: '#ff1150',
          color: '#ff1150',
          '&:hover': { borderColor: '#ff6f61', color: '#ff6f61' },
        },
        textPrimary: {
          color: '#ff1150',
          '&:hover': { backgroundColor: 'rgba(255, 17, 80, 0.08)' },
        },
      },
    },
  },
});

function App() {
  // 초기 값으로 categoriesData의 첫번째 대분류 사용 (예: '자연/해변')
  const [selectedCategory, setSelectedCategory] = useState(categoriesData[0]?.label || '');

  return (
    <ThemeProvider theme={theme}>
      <BrowserRouter>
        <Header onSelectCategory={setSelectedCategory} />
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/survey" element={<SurveyForm />} />
          <Route
            path="/category"
            element={
              <CategoryDetailPage 
                selectedCategory={selectedCategory} 
                onSelectSubCategory={(subLabel) => console.log("선택된 소분류:", subLabel)}
              />
            }
          />
          <Route path="/wishlist" element={<WishlistPage />} />
        </Routes>
      </BrowserRouter>
    </ThemeProvider>
  );
}

export default App;
