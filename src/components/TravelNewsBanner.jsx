import React, { useState } from 'react';
import { Container, Typography, Box, Link, Grid, Paper } from '@mui/material';
import NewspaperIcon from '@mui/icons-material/Newspaper';
import './TravelNewsBanner.scss';

const TravelNewsBanner = () => {
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
    <Box className="travel-news-banner">
      <Container maxWidth="lg">
        <Typography variant="h5" className="travel-news-banner__title" gutterBottom>
          오늘의 여행 소식
        </Typography>

        <Grid container spacing={2}>
          {newsList.map((news) => (
            <Grid item xs={12} sm={6} md={3} key={news.id}>
              <Paper elevation={3} className="travel-news-banner__item">
                <Box display="flex" alignItems="center" mb={1}>
                  <NewspaperIcon fontSize="small" className="travel-news-banner__icon" />
                  <Typography variant="subtitle2" className="travel-news-banner__source">
                    {news.source}
                  </Typography>
                </Box>
                <Link
                  href={`/news/${news.id}`}
                  underline="hover"
                  color="inherit"
                  className="travel-news-banner__link"
                >
                  {news.title}
                </Link>
                <Typography variant="caption" color="textSecondary" className="travel-news-banner__date">
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
