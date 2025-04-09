// src/components/CategoryDetail.js
import React from 'react';
import SubCategoryList from './SubCategoryList';

const CategoryDetail = ({ selectedCategory, categoriesData, onSelectSubCategory }) => {
  const categoryData = categoriesData.find(cat => cat.label === selectedCategory);

  if (!categoryData) {
    return <div>선택된 카테고리 정보가 없습니다.</div>;
  }

  return (
    <div>
      <SubCategoryList
        subCategories={categoryData.subCategories}
        onSelectSubCategory={onSelectSubCategory}
      />
    </div>
  );
};

export default CategoryDetail;
