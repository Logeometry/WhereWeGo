// src/App.js
import React, { useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import LandingPage from './pages/LandingPage';
import CategoryDetailPage from './pages/CategoryDetailPage';
import SearchResultPage from './pages/SearchResultPage';
import Header from './components/Header'; // 실제 Header 컴포넌트 경로로 수정 필요
import { createTheme, ThemeProvider } from '@mui/material/styles';
import './App.scss';
import { Toolbar } from '@mui/material';
import { categoriesData } from './data/categoriesData'; // 실제 categoriesData 경로로 수정 필요
import WishlistPage from './pages/WishlistPage';
import { SearchProvider } from './SearchContext'; // 실제 SearchContext 경로로 수정 필요
import SurveyPage from './pages/SurveyPage';
import SurveyForm from './pages/SurveyForm/SurveyForm';
import TouristDetailPage from './pages/TouristDetailPage';
import TravelPlanPage from './pages/TravelPlanPage';
import { WishlistProvider } from './contexts/WishlistContext'; // 경로 확인
import TravelPlanSamplePage from "./pages/TravelPlanSamplePage";
import TouristSpotRecommendPage from "./pages/TouristSpotRecommendPage"; // 추가
import { ItineraryProvider } from './contexts/ItineraryContext'; // 
import DetailedSurveyPage from './pages/DetailedSurveyPage';
import FixedLayout from "./Layouts/FixedLayout";
import TravelPlanKakaoPage from "./pages/TravelPlanKakaoPage";
import FestivalGallery from './components/FestivalGallery';
const theme = createTheme({
  palette: {
    primary: {
      main: "#667eea",   // 보라-파랑
    },
    secondary: {
      main: "#764ba2",   // 진한 보라
    },
    success: {
      main: "#4caf50",   // 연한 초록 (성공 메시지용)
    },
    error: {
      main: "#f44336",   // 에러는 살짝만
    },
    background: {
      default: "#f9f9fc", // 전체 배경 톤 다운
    },
  },
  typography: {
    fontFamily: "'Segoe UI', 'Roboto', 'Noto Sans KR', sans-serif",
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
          <ItineraryProvider> {/* ✅ 추가: 전역 일정 컨텍스트 */}
            <BrowserRouter>
           
              <Header onSelectCategory={setSelectedCategoryForHeader} currentCategory={selectedCategoryForHeader} />
              <Toolbar sx={{ height: { xs: 64, sm: 80, md: 100 } }} />
              <Routes>
                <Route path="/" element={<LandingPage />} />
                <Route path="/survey" element={<SurveyPage />} />
                <Route path="/survey2" element={<SurveyForm />} />
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
                  element={<CategoryDetailPage onSelectSubCategory={(subLabel) => console.log("선택된 소분류:", subLabel)} />}
                />
                <Route path="/detailed-survey" element={<DetailedSurveyPage />} />

                <Route path="/travel-plan-kakao" element={<TravelPlanKakaoPage />} />
                <Route path="/tourist-spot-recommend" element={<TouristSpotRecommendPage />} />
                <Route path="/travel-plan" element={<TravelPlanSamplePage />} />
                <Route path="/wishlist" element={<WishlistPage />} />
                <Route path="/search" element={<SearchResultPage />} />
                <Route path="/tourist/:id" element={<TouristDetailPage />} />
                <Route path="/busan-travel-plan" element={<TravelPlanPage />} /> {/* 코스 구성 페이지 */}
              </Routes>
                
            </BrowserRouter>
          </ItineraryProvider>
        </WishlistProvider>
      </SearchProvider>
    </ThemeProvider>
  );
}
export default App;
