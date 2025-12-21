// src/components/SubCategoryGallery.js
import React from 'react';
import { Container, Box, Grid, Typography } from '@mui/material';
import SubCategoryCard from './SubCategoryCard';

const SubCategoryGallery = ({ subCategories, onSelectSubCategory }) => {
  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Typography variant="h5" gutterBottom>
        소분류를 선택해 주세요
      </Typography>
      <Box
        sx={{
          overflowX: 'auto',
          whiteSpace: 'nowrap',
          py: 1,
        }}
      >
        <Grid container wrap="nowrap" spacing={2} sx={{ width: 'max-content' }}>
          {subCategories.map((sub) => (
            <Grid item key={sub.label}>
              <SubCategoryCard subCategory={sub} onSelect={onSelectSubCategory} />
            </Grid>
          ))}
        </Grid>
      </Box>
    </Container>
  );
};

export default SubCategoryGallery;
