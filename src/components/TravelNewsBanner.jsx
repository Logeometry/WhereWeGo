import React, { useState } from 'react';
import { Container, Typography, Box, Link, Grid, Paper, useMediaQuery, useTheme } from '@mui/material';
import NewspaperIcon from '@mui/icons-material/Newspaper';
import './TravelNewsBanner.scss';

const TravelNewsBanner = () => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm')); // 600px 이하
  // 샘플 데이터 (백엔드 연동 시 fetch/axios로 대체)
  const [newsList] = useState([
    {
      id: 1,
      title: '광안리 해변 야간 드론쇼, 4월부터 주 3회로 확대 운영',
      source: '부산시청',
      date: '2025-03-27',
    },
    {
      id: 2,
      title: '해운대 모래축제 5월 중순 개막, 이색 전시·체험 프로그램 눈길',
      source: '부산관광공사',
      date: '2025-03-26',
    },
    {
      id: 3,
      title: '부산 시티투어 버스, 태종대 노선 신규 개설',
      source: '부산시티투어',
      date: '2025-03-25',
    },
    {
      id: 4,
      title: '전포 카페거리 봄맞이 디저트 축제, 달콤한 봄 여행 즐기기',
      source: '부산중구청',
      date: '2025-03-24',
    },
  ]);

  return (
    <Box 
      className="travel-news-banner"
      sx={{
        width: '100%',
        maxWidth: '100%',
        px: { 
          xs: 1.5,    // 모바일: 12px 좌우 (통일)
          sm: 3,      // 태블릿: 24px 좌우
          md: 4,      // 중형: 32px 좌우
          lg: 5       // 대형: 40px 좌우
        },
        py: { xs: 2, sm: 3, md: 4 },
        boxSizing: 'border-box',
        overflowX: 'hidden'
      }}
    >
      <Container 
        maxWidth="lg"
        disableGutters
        sx={{
          maxWidth: {
            xs: '100%',
            sm: '100%',
            md: '900px',
            lg: '1200px',
            xl: '1536px'
          },
          margin: '0 auto',
          px: 0
        }}
      >
        <Typography 
          variant="h5" 
          className="travel-news-banner__title" 
          gutterBottom
          sx={{
            fontSize: {
              xs: '1.125rem',  // 모바일: 18px (더 작게)
              sm: '1.375rem',  // 태블릿: 22px
              md: '1.625rem'   // 중형: 26px
            },
            fontWeight: 700,
            mb: { xs: 2, sm: 2.5, md: 3 },
            color: '#1a1a1a',
            letterSpacing: '-0.5px'
          }}
        >
          오늘의 여행 소식
        </Typography>

        <Grid 
          container 
          spacing={{ xs: 2, sm: 2.5, md: 3 }}
        >
          {newsList.map((news) => (
            <Grid item xs={12} sm={6} md={6} lg={3} key={news.id}>
              <Paper 
                elevation={3} 
                className="travel-news-banner__item"
                sx={{
                  p: { xs: 1.5, sm: 2 },
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  borderRadius: { xs: 2, md: 3 },
                  transition: 'transform 0.2s ease, box-shadow 0.2s ease',
                  '&:hover': {
                    transform: 'translateY(-4px)',
                    boxShadow: 4,
                  }
                }}
              >
                <Box 
                  display="flex" 
                  alignItems="center" 
                  mb={1}
                  sx={{ gap: 0.5 }}
                >
                  <NewspaperIcon 
                    className="travel-news-banner__icon"
                    sx={{ 
                      fontSize: { xs: '1rem', sm: '1.25rem' }
                    }}
                  />
                  <Typography 
                    variant="subtitle2" 
                    className="travel-news-banner__source"
                    sx={{
                      fontSize: { xs: '0.75rem', sm: '0.875rem' }
                    }}
                  >
                    {news.source}
                  </Typography>
                </Box>
                <Link
                  href={`/news/${news.id}`}
                  underline="hover"
                  color="inherit"
                  className="travel-news-banner__link"
                  sx={{
                    fontSize: { xs: '0.875rem', sm: '0.938rem', md: '1rem' },
                    fontWeight: 500,
                    lineHeight: 1.4,
                    mb: 1,
                    flex: 1,
                    display: 'block'
                  }}
                >
                  {news.title}
                </Link>
                <Typography 
                  variant="caption" 
                  color="textSecondary" 
                  className="travel-news-banner__date"
                  sx={{
                    fontSize: { xs: '0.688rem', sm: '0.75rem' }
                  }}
                >
                  {news.date}
                </Typography>
              </Paper>
            </Grid>
          ))}
        </Grid>
      </Container>
    </Box>
  );
};

export default TravelNewsBanner;
