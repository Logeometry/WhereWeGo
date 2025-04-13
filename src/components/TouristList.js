// src/components/TouristList.js
import React from 'react';
import { Box, Typography } from '@mui/material';
import TouristListItem from './TouristListItem';

const TouristList = ({ items, totalCount, currentPage, itemsPerPage }) => {
  const startIndex = (currentPage - 1) * itemsPerPage + 1;
  const endIndex = startIndex + items.length - 1;

  return (
    <Box>
      <Typography variant="body2" sx={{ mb: 2 }}>
        {startIndex}–{endIndex} / 총 {totalCount}건
      </Typography>
      {items.map((item, i) => (
        <TouristListItem key={i} item={item} />
      ))}
    </Box>
  );
};

export default TouristList;
