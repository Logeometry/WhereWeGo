import React from 'react';
import { Container, Box, useMediaQuery, useTheme } from '@mui/material';
import Header from '../components/Header';
import AiPlannerBanner from '../components/AiPlannerBanner'
import Footer from '../components/Footer';
import './LandingPage.scss';
import RecommendationGallery from '../components/RecommendationGallery';
import FestivalGallery from '../components/FestivalGallery';

const LandingPage = () => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm')); // 600px 이하
  const isTablet = useMediaQuery(theme.breakpoints.down('md')); // 900px 이하

  return (
    <Box 
      className="landing-page" 
      sx={{ 
        // 반응형 웹 전용 설정 (모바일/태블릿: xs, sm)
        width: { xs: '100vw', md: '100%' },  // 모바일: 100vw, 데스크톱: 100%
        maxWidth: { xs: '96vw', md: '100vw' },
        overflowX: { xs: 'hidden', md: 'hidden' },
        overflowY: 'auto',
        minHeight: '100vh',
        display: 'flex',
        flexDirection: 'column',
        backgroundColor: '#fafafa',
        position: 'relative',
        // 반응형 전용: 모바일에서 마진/패딩 제거
        margin: { xs: 0, md: 'auto' },
        padding: { xs: 0, md: 0 },
        boxSizing: 'border-box'
      }}
    >
      <Header />
      
      {/* AI 플래너 배너 영역 */}
      <Box 
        component="section"
        sx={{ 
          width: '100%',
          maxWidth: '100%',
          backgroundColor: '#fafafa', // 회색 배경 명시
          // 반응형 패딩 설정: 모바일(xs)에서 여백 최소화, 데스크톱(md+)에서 여백 추가
          px: { 
            xs: 0.5,      // 모바일: 4px (여백 최소화)
            sm: 1,        // 태블릿: 8px
            md: 3,        // 중형: 24px
            lg: 4         // 대형: 32px
          }, 
          pt: { xs: 1.5, sm: 2, md: 2 },
          pb: { xs: 2, sm: 3, md: 4 },
          boxSizing: 'border-box',
          overflowX: 'hidden'
        }}
      >
        <AiPlannerBanner />
      </Box>
      
      {/* 추천 갤러리 영역 */}
      <Box 
        component="section"
        sx={{
          width: '100%',
          maxWidth: '100%',
          // 반응형 패딩 설정: 모바일에서 여백 최소화
          px: { 
            xs: 0.5,      // 모바일: 4px (여백 최소화)
            sm: 1.5,      // 태블릿: 12px
            md: 4,        // 중형: 32px
            lg: 5         // 대형: 40px
          },
          py: { 
            xs: 2,        // 모바일: 16px
            sm: 3,        // 태블릿: 24px
            md: 4         // 중형: 32px
          },
          backgroundColor: '#fff',
          boxSizing: 'border-box',
          overflowX: 'hidden'
        }}
      >
        <Box
          sx={{
            maxWidth: '1400px',
            margin: '0 auto',
            width: '100%'
          }}
        >
          <RecommendationGallery />
        </Box>
      </Box>
      
      {/* 여행 소식 배너 영역 */}
      <Box
  component="section"
  sx={{
    width: '100%',
    maxWidth: '100%',
    backgroundColor: '#fafafa',
    py: { xs: 3, sm: 4, md: 5 },
    overflowX: 'hidden'
  }}
>
  <FestivalGallery />
</Box>
      
      <Footer />
    </Box>
  );
};

export default LandingPage;
