import React from 'react';
import { Box, Typography } from '@mui/material';

const HeroMarketplace = () => {
  return (
    <Box
      sx={{
        width: '100%',
        height: { xs: '200px', md: '300px' },
        backgroundColor: '#f7f7f7',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        mt: { xs: 7, md: 8 }, // 고정 헤더 높이 보정
        mb: 4,
        textAlign: 'center',
      }}
    >
      <Typography variant="h4" sx={{ fontWeight: 'bold', mb: 1 }}>
        반응형 부산 관광지 템플릿
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ maxWidth: 600 }}>
        원하는 스타일과 테마에 맞춰 다양한 부산 관광지를 찾아보세요.
      </Typography>
    </Box>
  );
};

export default HeroMarketplace;
