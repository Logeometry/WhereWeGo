// src/components/SubCategoryListItem.js
import React from 'react';
import { Box, Typography, IconButton, Divider } from '@mui/material';
import MoreVertIcon from '@mui/icons-material/MoreVert';

const SubCategoryListItem = ({ subCategory, onSelect }) => {
  return (
    <>
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          py: 2,
        }}
      >
        <Box onClick={() => onSelect(subCategory.label)} sx={{ cursor: 'pointer' }}>
          <Typography variant="subtitle1" fontWeight="bold">
            {subCategory.label}
          </Typography>
          {subCategory.description && (
            <Typography variant="body2" color="text.secondary">
              {subCategory.description}
            </Typography>
          )}
        </Box>
        <IconButton>
          <MoreVertIcon />
        </IconButton>
      </Box>
      <Divider />
    </>
  );
};

export default SubCategoryListItem;
