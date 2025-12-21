// src/pages/CategoryDetailPage.js
import React, { useState, useEffect, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Container, Typography, Box, Button } from '@mui/material';
import { categoriesData } from '../data/categoriesData';
import { busanSampleData } from '../data/busanSampleData';
import SubCategoryNavigation from '../components/SubCategoryNavigation';
import SubCategoryCardGrid from '../components/SubCategoryCardGrid';

const CategoryDetailPage = ({ onSelectSubCategory }) => {
  const { categoryLabelFromUrl } = useParams();
  const navigate = useNavigate();

  const currentCategoryLabel = useMemo(
    () => (categoryLabelFromUrl ? decodeURIComponent(categoryLabelFromUrl) : undefined),
    [categoryLabelFromUrl]
  );

  const [category, setCategory] = useState(null);
  const [subCategories, setSubCategories] = useState([]);
  const [selectedSubCategory, setSelectedSubCategory] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    console.log('CategoryDetailPage - currentCategoryLabel (decoded):', currentCategoryLabel);
    console.log('CategoryDetailPage - categoriesData:', categoriesData);
    setIsLoading(true);
    setError(null);
    
    if (currentCategoryLabel) {
      const foundCategory = categoriesData.find(c => c.label === currentCategoryLabel);
      console.log('CategoryDetailPage - 찾은 category:', foundCategory);
      
      if (foundCategory) {
        setCategory(foundCategory);
        const existingSubCategories = foundCategory.subCategories || [];
        console.log('CategoryDetailPage - 기존 subCategories:', existingSubCategories);
        
        setSubCategories(existingSubCategories);
        
        // 첫 번째 서브카테고리를 기본 선택으로 설정
        if (existingSubCategories.length > 0) {
          setSelectedSubCategory(existingSubCategories[0].label);
        } else {
          setSelectedSubCategory(null);
        }
      } else {
        setCategory(null);
        setSubCategories([]);
        setSelectedSubCategory(null);
        setError(`레이블 "${currentCategoryLabel}"을 가진 카테고리를 찾을 수 없습니다.`);
        console.warn(`레이블 "${currentCategoryLabel}"을 가진 카테고리를 찾을 수 없습니다.`);
      }
    } else {
      setCategory(null);
      setSubCategories([]);
      setSelectedSubCategory(null);
    }
    setIsLoading(false);
  }, [currentCategoryLabel]);

  const handleSubCategorySelect = (label) => {
    setSelectedSubCategory(label);
    if (onSelectSubCategory) {
      onSelectSubCategory(label);
    }
  };

  if (isLoading) {
    return (
      <Container maxWidth="lg" sx={{ py: 6 }}>
        <Typography>데이터 로드 중...</Typography>
      </Container>
    );
  }

  if (error) {
    return (
      <Container maxWidth="lg" sx={{ py: 6, textAlign: 'center' }}>
        <Typography color="error" variant="h6" gutterBottom>
          오류 발생
        </Typography>
        <Typography color="text.secondary" gutterBottom>
          {error}
        </Typography>
        <Button variant="contained" onClick={() => navigate('/')} sx={{ mt: 2 }}>
          홈으로 돌아가기
        </Button>
      </Container>
    );
  }

  if (!category) {
    return (
      <Container maxWidth="lg" sx={{ py: 6, textAlign: 'center' }}>
        <Typography variant="h5" gutterBottom>
          '{currentCategoryLabel || "알 수 없는"}' 카테고리를 찾을 수 없습니다.
        </Typography>
        <Button variant="contained" onClick={() => navigate('/')}>
          홈으로 돌아가기
        </Button>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      {/* 페이지 제목 */}
      <Typography variant="h4" gutterBottom sx={{ fontWeight: 'bold', mb: 4 }}>
        #{category.label}
      </Typography>

      {/* 서브카테고리 네비게이션 */}
      {subCategories.length > 0 && (
        <SubCategoryNavigation
          subCategories={subCategories}
          selectedSubCategory={selectedSubCategory}
          onSubCategorySelect={handleSubCategorySelect}
          categoryIcon={category.icon}
        />
      )}

      {/* 선택된 서브카테고리의 관광지 카드 그리드 */}
      {selectedSubCategory && (
        <SubCategoryCardGrid
          subCategoryLabel={selectedSubCategory}
          categoryGroup={category.dbGroup || category.label}
        />
      )}

      {/* 서브카테고리가 없는 경우 */}
      {subCategories.length === 0 && (
        <Box sx={{ textAlign: 'center', py: 8 }}>
          <Typography variant="h6" color="text.secondary" gutterBottom>
            이 카테고리에는 서브카테고리가 없습니다.
          </Typography>
          <Typography variant="body2" color="text.secondary">
            다른 카테고리를 선택해보세요.
          </Typography>
        </Box>
      )}
    </Container>
  );
};

export default CategoryDetailPage;