//현재 사용하지 않음

import React from 'react';
import { Box, Button, Typography } from '@mui/material';
import './SidebarFilter.scss';

const categories = [
  '인기 관광지',
  '맛집 투어',
  '야경 명소',
  '쇼핑/전통시장',
  '자연/공원',
  '역사/문화',
];

const SidebarFilter = () => {
  return (
    <Box className="sidebar-filter">
      <Typography variant="h6" className="sidebar-filter__title">
        카테고리
      </Typography>
      <Box className="sidebar-filter__buttons">
        {categories.map((cat, idx) => (
          <Button
            key={idx}
            variant="outlined"
            size="medium"
            className="sidebar-filter__button"
            sx={{
              textTransform: 'none',
              borderRadius: '20px',
              width: '100%',
              transition: 'all 0.3s',
              '&:hover': {
                backgroundColor: '#3498db',
                color: '#fff',
                borderColor: '#3498db',
              },
            }}
          >
            {cat}
          </Button>
        ))}
      </Box>
    </Box>
  );
};

export default SidebarFilter;
