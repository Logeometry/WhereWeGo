// src/components/SubCategoryCard.js
import React from 'react';
import { Card, CardContent, CardActionArea, Typography } from '@mui/material';

const SubCategoryCard = ({ subCategory, onSelect }) => {
  return (
    <Card sx={{ width: 330, m: 1 }}>
      <CardActionArea onClick={() => onSelect(subCategory.label)}>
        <CardContent sx={{ height: 120, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <Typography variant="h6">
            {subCategory.label}
          </Typography>
        </CardContent>
      </CardActionArea>
    </Card>
  );
};

export default SubCategoryCard;
