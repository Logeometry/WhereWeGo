// src/App.js
import React, { useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import LandingPage from './pages/LandingPage';
import CategoryDetailPage from './pages/CategoryDetailPage';
import SearchResultPage from './pages/SearchResultPage';
import Header from './components/Header'; // 실제 Header 컴포넌트 경로로 수정 필요
import { createTheme, ThemeProvider } from '@mui/material/styles';
import './App.scss';
import { categoriesData } from './data/categoriesData'; // 실제 categoriesData 경로로 수정 필요
import WishlistPage from './pages/WishlistPage';
import { SearchProvider } from './SearchContext'; // 실제 SearchContext 경로로 수정 필요
import SurveyPage from './pages/SurveyPage';
import TouristDetailPage from './pages/TouristDetailPage';

import { WishlistProvider } from './contexts/WishlistContext'; // 경로 확인

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
  let defaultCategoryLabel = '';
  if (categoriesData && categoriesData.length > 0 && categoriesData[0] && categoriesData[0].label) {
    defaultCategoryLabel = categoriesData[0].label;
  } else {
    console.warn("Default category could not be determined from categoriesData. Check data/categoriesData.js.");
  }
  const [selectedCategoryForHeader, setSelectedCategoryForHeader] = useState(defaultCategoryLabel);

  return (
    <ThemeProvider theme={theme}>
      <SearchProvider>
        <WishlistProvider>
          <BrowserRouter>
            <Header onSelectCategory={setSelectedCategoryForHeader} currentCategory={selectedCategoryForHeader} />
            <Routes>
              <Route path="/" element={<LandingPage />} />
              <Route path="/survey" element={<SurveyPage />} />
              <Route
                path="/category"
                element={
                  defaultCategoryLabel ?
                  <Navigate to={`/category/${encodeURIComponent(defaultCategoryLabel)}`} /> :
                  <Navigate to="/" />
                }
              />
              <Route
                path="/category/:categoryLabelFromUrl"
                element={
                  <CategoryDetailPage
                    onSelectSubCategory={(subLabel) => console.log("선택된 소분류:", subLabel)}
                  />
                }
              />
              <Route path="/wishlist" element={<WishlistPage />} />
              <Route path="/search" element={<SearchResultPage />} />
              <Route path="/tourist/:id" element={<TouristDetailPage />} />
            </Routes>
          </BrowserRouter>
        </WishlistProvider>
      </SearchProvider>
    </ThemeProvider>
  );
}

export default App;