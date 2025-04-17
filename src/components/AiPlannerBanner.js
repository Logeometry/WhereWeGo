import React from 'react';
import { Box, Typography, Button, Stack } from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';
import './AiPlannerBanner.scss';

const AiPlannerBanner = () => {
  return (
    <section className="ai-banner">
      {/* 왼쪽 텍스트 영역 */}
      <Box className="ai-banner__left">
        <Typography variant="h3" className="ai-banner__title">
          AI 맞춤 부산 여행, 지금 바로 시작하세요!
        </Typography>
        <Typography variant="subtitle1" className="ai-banner__subtitle">
          복잡한 계획은 AI에게 맡기고, <br />
          나만을 위한 특별한 부산 여행 코스를 경험해보세요.
        </Typography>

        <Stack direction="row" spacing={1} className="ai-banner__hashtags">
          <span className="hashtag">#해운대</span>
          <span className="hashtag">#광안리</span>
          <span className="hashtag">#맞춤여행</span>
          <span className="hashtag">#부산맛집</span>
        </Stack>

        <Button
          variant="contained"
          color="primary"
          className="ai-banner__btn"
          component={RouterLink}
          to="/survey"
        >
          나만의 여행 코스 만들기 →
        </Button>
      </Box>

      {/* 오른쪽 이미지 영역 */}
      <Box className="ai-banner__right">
        <img
          src="/image/BusanTouristMap.jpg"
          alt="Busan Tourist Map"
          className="ai-banner__image"
        />
      </Box>
    </section>
  );
};

export default AiPlannerBanner;