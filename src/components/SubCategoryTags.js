import React from 'react';
import { Box, Chip } from '@mui/material';

const SubCategoryTags = ({ subCategories, selected, onSelect }) => {
  // '전체' 태그를 추가하는 로직을 제거하고, props로 받은 배열을 그대로 사용합니다.
  return (
    <Box sx={{ display: 'flex', gap: 1, overflowX: 'auto', py: 2 }}>
      {/* 'allSubCategories' 대신 'subCategories'를 직접 매핑합니다. */}
      {subCategories.map((sub) => (
        <Chip
          key={sub.label}
          label={sub.label}
          onClick={() => onSelect(sub.label)}
          color={selected === sub.label ? 'primary' : 'default'}
          clickable
          sx={{
            fontSize: '1rem',
            height: 40,
            px: 2,
          }}
        />
      ))}
    </Box>
  );
};

export default SubCategoryTags;
