import React, { useState } from 'react';
import { Container, Typography } from '@mui/material';
import { categoriesData } from '../data/categoriesData';
import SubCategoryTags from '../components/SubCategoryTags'; // 가로 태그 리스트
import TouristList from '../components/TouristList'; // 관광지 리스트

const CategoryDetailPage = ({ selectedCategory }) => {
  const category = categoriesData.find(c => c.label === selectedCategory);
  const subCategories = category?.subCategories || [];

  const [selectedSubCategory, setSelectedSubCategory] = useState('전체');

  const touristData = [
    {
      title: '해운대해수욕장',
      location: '부산 해운대구',
      description: '부산의 대표적인 해변 관광지',
      image: '',
      tags: ['해변', '바다', '여름'],
      subCategory: '해변',
    },
    {
      title: '유명산계곡',
      location: '가평',
      description: '자연과 물이 어우러진 힐링 장소',
      image: '',
      tags: ['산', '계곡', '물놀이'],
      subCategory: '산/계곡',
    },
    // ...추가 관광지들
  ];

  const filteredTouristData =
    selectedSubCategory === '전체'
      ? touristData.filter(item =>
          subCategories.some(sub => sub.label === item.subCategory)
        )
      : touristData.filter(item => item.subCategory === selectedSubCategory);

  return (
    <Container maxWidth="md" sx={{ py: 6 }}>
      <Typography variant="h4" gutterBottom>
        {selectedCategory}의 소분류
      </Typography>

      <SubCategoryTags
        subCategories={subCategories}
        selected={selectedSubCategory}
        onSelect={setSelectedSubCategory}
      />

      <TouristList items={filteredTouristData} />
    </Container>
  );
};


export default CategoryDetailPage;
