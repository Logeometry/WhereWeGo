import React from 'react';
import { Box, Chip } from '@mui/material';

const SubCategoryTags = ({ subCategories, selected, onSelect }) => {
  const allSubCategories = [{ label: '전체' }, ...subCategories];

  return (
    <Box sx={{ display: 'flex', gap: 1, overflowX: 'auto', py: 2 }}>
      {allSubCategories.map((sub) => (
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
