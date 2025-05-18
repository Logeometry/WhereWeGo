// src/pages/CategoryDetailPage.js
import React, { useState, useEffect, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Container, Typography, Box, Pagination, Button } from '@mui/material';
import { categoriesData } from '../data/categoriesData'; // Ensure this path is correct
import SubCategoryTags from '../components/SubCategoryTags'; // Assuming this component exists
import TouristList from '../components/TouristList'; // Assuming this component exists

const ITEMS_PER_PAGE = 10;

const CategoryDetailPage = ({ onSelectSubCategory }) => { // onSelectSubCategory is kept from App.js
  const { categoryLabelFromUrl } = useParams();
  const navigate = useNavigate();

  const currentCategoryLabel = useMemo(() => 
    categoryLabelFromUrl ? decodeURIComponent(categoryLabelFromUrl) : undefined
  , [categoryLabelFromUrl]);

  const [category, setCategory] = useState(null);
  const [subCategories, setSubCategories] = useState([]);
  const [selectedSubCategory, setSelectedSubCategory] = useState('전체');
  const [currentPage, setCurrentPage] = useState(1);
  const [isLoading, setIsLoading] = useState(true);

  // Sample tourist data - In a real app, this would likely be fetched
  // or be more structured, perhaps associated with categoriesData.
  const allTouristData = useMemo(() => [
    ...Array.from({ length: 27 }).map((_, i) => ({
      id: i + 1,
      title: `관광지 ${i + 1}`,
      location: '서울특별시',
      description: '아름다운 명소입니다',
      image: `/api/placeholder/400/200?text=관광지${i + 1}`,
      tags: ['가을', '드라이브'],
      // This subCategory assignment is for example purposes.
      // It should align with actual subCategory labels in categoriesData.
      subCategory: categoriesData[0]?.subCategories[(i % (categoriesData[0]?.subCategories.length || 1))]?.label || (i % 2 === 0 ? '해변' : '산/계곡'),
      // Ideally, items might also have a parentCategory label to ensure correct filtering.
      parentCategory: categoriesData[0]?.label // Example: associate with the first main category
    })),
  ], []); // Empty dependency array means this runs once. Be careful if categoriesData can change.


  useEffect(() => {
    setIsLoading(true);
    if (currentCategoryLabel) {
      const foundCategory = categoriesData.find(c => c.label === currentCategoryLabel);
      if (foundCategory) {
        setCategory(foundCategory);
        setSubCategories(foundCategory.subCategories || []);
        setSelectedSubCategory('전체'); // Reset subcategory selection
        setCurrentPage(1); // Reset page
      } else {
        setCategory(null); // Category not found
        setSubCategories([]);
        console.warn(`Category with label "${currentCategoryLabel}" not found.`);
      }
    } else {
      setCategory(null); // No category label in URL
      setSubCategories([]);
    }
    setIsLoading(false);
  }, [currentCategoryLabel]);

  const filteredTouristData = useMemo(() => {
    if (!category) return [];

    // Filter allTouristData to include only items relevant to the current main category
    // This is a simplified assumption; real data might be structured differently or fetched per category.
    const itemsForMainCategory = allTouristData.filter(item => {
        // A more robust filter might be needed if `allTouristData` contains items from many main categories.
        // For example, if item.parentCategory === category.label
        // For now, we assume `subCategories.some(...)` check is sufficient if subcategories are unique enough
        // or `allTouristData` is already somewhat pre-filtered or meant for this broad use.
        return true; // Assuming items are generally relevant or filtered later by subCategory
    });


    if (selectedSubCategory === '전체') {
      // Show items whose subCategory is one of the valid subCategories for the current main category
      return itemsForMainCategory.filter(item => 
        subCategories.some(sc => sc.label === item.subCategory)
      );
    }
    return itemsForMainCategory.filter(item => item.subCategory === selectedSubCategory);
  }, [category, selectedSubCategory, subCategories, allTouristData]);

  const startIdx = (currentPage - 1) * ITEMS_PER_PAGE;
  const currentItemsOnPage = filteredTouristData.slice(startIdx, startIdx + ITEMS_PER_PAGE);
  const totalPages = Math.ceil(filteredTouristData.length / ITEMS_PER_PAGE);

  const handlePageChange = (_, value) => {
    setCurrentPage(value);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleSubCategorySelect = (label) => {
    setSelectedSubCategory(label);
    setCurrentPage(1);
    if (onSelectSubCategory) { // Call the prop from App.js if it exists
        onSelectSubCategory(label);
    }
  };

  if (isLoading) {
    return <Container maxWidth="md" sx={{ py: 6 }}><Typography>카테고리 정보를 불러오는 중...</Typography></Container>;
  }

  if (!category) {
    return (
      <Container maxWidth="md" sx={{ py: 6, textAlign: 'center' }}>
        <Typography variant="h5" gutterBottom>
          '{currentCategoryLabel || "알 수 없는"}' 카테고리를 찾을 수 없습니다.
        </Typography>
        <Button variant="contained" onClick={() => navigate('/')}>홈으로 돌아가기</Button>
      </Container>
    );
  }

  return (
    <Container maxWidth="md" sx={{ py: 6 }}>
      <Typography variant="h4" gutterBottom>
        여행지 #{category.label}
      </Typography>

      <SubCategoryTags
        subCategories={subCategories}
        selected={selectedSubCategory}
        onSelect={handleSubCategorySelect}
      />

      <TouristList
        items={currentItemsOnPage}
        // Props required by TouristList might need adjustment based on its actual implementation
        // totalCount={filteredTouristData.length} 
        // currentPage={currentPage}
        // itemsPerPage={ITEMS_PER_PAGE}
      />

      {totalPages > 0 && (
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
      )}
    </Container>
  );
};

export default CategoryDetailPage;