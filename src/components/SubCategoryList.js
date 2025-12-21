// src/components/SubCategoryList.js
import React from 'react';
import SubCategoryListItem from './SubCategoryListItem';
import { Box } from '@mui/material';

const SubCategoryList = ({ subCategories, onSelectSubCategory }) => {
  return (
    <Box>
      {subCategories.map((sub, idx) => (
        <SubCategoryListItem
          key={idx}
          subCategory={sub}
          onSelect={onSelectSubCategory}
        />
      ))}
    </Box>
  );
};

export default SubCategoryList;
