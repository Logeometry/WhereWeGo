// src/components/TouristList.js
import React from 'react';
import { Box, Typography } from '@mui/material';
import TouristListItem from './TouristListItem';

const TouristList = ({ items }) => {
  return (
    <Box>
      <Typography variant="h6" sx={{ mb: 2 }}>
        총 {items.length}건
      </Typography>
      {items.map((item, i) => (
        <TouristListItem key={i} item={item} />
      ))}
    </Box>
  );
};

export default TouristList;
