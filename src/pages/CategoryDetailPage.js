import React, { useState } from 'react';
import { Container, Typography, Box, Pagination } from '@mui/material';
import { categoriesData } from '../data/categoriesData';
import SubCategoryTags from '../components/SubCategoryTags';
import TouristList from '../components/TouristList';

const ITEMS_PER_PAGE = 10;

const CategoryDetailPage = ({ selectedCategory }) => {
  const category = categoriesData.find(c => c.label === selectedCategory);
  const subCategories = category?.subCategories || [];
  const [selectedSubCategory, setSelectedSubCategory] = useState('전체');
  const [currentPage, setCurrentPage] = useState(1);

  // 샘플 관광지 데이터
  const touristData = [
    ...Array.from({ length: 27 }).map((_, i) => ({
      title: `관광지 ${i + 1}`,
      location: '서울특별시',
      description: '아름다운 명소입니다',
      image: '',
      tags: ['가을', '드라이브'],
      subCategory: i % 2 === 0 ? '해변' : '산/계곡',
    })),
  ];

  // 소분류 필터링
  const filteredData =
    selectedSubCategory === '전체'
      ? touristData.filter((item) =>
          subCategories.some((sub) => sub.label === item.subCategory)
        )
      : touristData.filter((item) => item.subCategory === selectedSubCategory);

  // 현재 페이지 항목 추출
  const startIdx = (currentPage - 1) * ITEMS_PER_PAGE;
  const currentItems = filteredData.slice(startIdx, startIdx + ITEMS_PER_PAGE);

  const totalPages = Math.ceil(filteredData.length / ITEMS_PER_PAGE);

  const handlePageChange = (_, value) => {
    setCurrentPage(value);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <Container maxWidth="md" sx={{ py: 6 }}>
      <Typography variant="h4" gutterBottom>
        {selectedCategory}의 소분류
      </Typography>

      <SubCategoryTags
        subCategories={subCategories}
        selected={selectedSubCategory}
        onSelect={(label) => {
          setSelectedSubCategory(label);
          setCurrentPage(1);
        }}
      />

      {/* ✅ TouristList에 totalCount, currentPage, itemsPerPage 전달 */}
      <TouristList
        items={currentItems}
        totalCount={filteredData.length}
        currentPage={currentPage}
        itemsPerPage={ITEMS_PER_PAGE}
      />

      {/* 페이지네이션 */}
      <Box sx={{ mt: 4, display: 'flex', justifyContent: 'center' }}>
        <Pagination
          count={totalPages}
          page={currentPage}
          onChange={handlePageChange}
          shape="rounded"
          color="primary"
          size="large"
        />
      </Box>
    </Container>
  );
};

export default CategoryDetailPage;
