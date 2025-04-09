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
          코스픽 부산 (COSPICK BUSAN)
        </Typography>
        <Typography variant="body1" className="ai-banner__subtitle">
          AI가 분석해 추천하는 부산 여행 BEST 코스!
          <br />
          나만을 위한 맞춤 여행 코스를 시작해보세요.
        </Typography>

        <Stack direction="row" spacing={1} className="ai-banner__hashtags">
          <span>#해운대 코스</span>
          <span>#개인화된 취향 반영</span>
          <span>#BEST 코스</span>
        </Stack>

        <Button
          variant="contained"
          color="primary"
          className="ai-banner__btn"
          component={RouterLink}
          to="/survey"
        >
          AI 추천 받기 →
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
