// src/components/SubCategoryCardGrid.js
import React, { useState, useEffect } from 'react';
import { Box, Grid, Typography, CircularProgress, Alert, Button } from '@mui/material';
import SubCategoryCard from './SubCategoryCard';
import { getPlacesBySubCategory, getAllPlaces } from '../api/category';
import { busanSampleData } from '../data/busanSampleData';

const SubCategoryCardGrid = ({ subCategoryLabel, categoryGroup }) => {
  const [places, setPlaces] = useState([]);
  const [allPlaces, setAllPlaces] = useState([]);
  const [displayCount, setDisplayCount] = useState(8);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchPlaces = async () => {
      console.log('SubCategoryCardGrid - 데이터 페칭 시작:', { subCategoryLabel, categoryGroup });
      setLoading(true);
      setError(null);
      
      try {
        // 실제 MongoDB API 호출 시도
        let apiPlaces = [];
        let apiError = null;
        
        try {
          console.log('서브카테고리 API 호출 시도:', subCategoryLabel);
          apiPlaces = await getPlacesBySubCategory(subCategoryLabel);
          console.log('서브카테고리 API 성공:', apiPlaces);
        } catch (err) {
          apiError = err;
          console.warn('서브카테고리 API 호출 실패:', err.message);
          
          try {
            console.log('전체 관광지 API 호출 시도');
            const allPlacesResponse = await getAllPlaces(1, 100);
            apiPlaces = allPlacesResponse.places || [];
            console.log('전체 관광지 API 성공:', apiPlaces.length, '개');
          } catch (allPlacesError) {
            console.warn('전체 관광지 API 호출도 실패:', allPlacesError.message);
            apiPlaces = [];
          }
        }
        
        // 서브카테고리와 매칭하는 로직 (DB 기반으로 개선)
        const filteredPlaces = apiPlaces.filter(place => {
          // MongoDB 데이터 구조에 맞게 필터링
          const placeCategories = place.category ? place.category.split(',').map(cat => cat.trim()) : [];
          
          // 1. 정확한 카테고리 매칭 (우선순위 높음)
          const exactCategoryMatch = place.category === subCategoryLabel;
          
          // 2. 카테고리 배열에서 매칭
          const categoryArrayMatch = placeCategories.includes(subCategoryLabel);
          
          // 3. 카테고리 그룹 매칭 (categoryGroup이 DB의 category_group과 일치)
          const categoryGroupMatch = place.category_group === categoryGroup;
          
          // 4. 부분 문자열 매칭 (마지막 옵션)
          const partialMatch = place.category && place.category.includes(subCategoryLabel);
          
          const isMatch = exactCategoryMatch || categoryArrayMatch || categoryGroupMatch || partialMatch;
          
          if (isMatch) {
            console.log('매칭된 관광지:', place.name, { 
              id: place.id || place._id,
              category: place.category, 
              category_group: place.category_group,
              searchCategory: subCategoryLabel,
              searchCategoryGroup: categoryGroup,
              matchType: exactCategoryMatch ? 'exact' : categoryArrayMatch ? 'array' : categoryGroupMatch ? 'group' : 'partial'
            });
          }
          
          return isMatch;
        });

        console.log('필터링 결과:', filteredPlaces.length, '개');

        // 모든 데이터를 저장하고 처음에는 8개만 표시
        setAllPlaces(filteredPlaces);
        setPlaces(filteredPlaces.slice(0, displayCount));
        
        // API에서 데이터를 가져오지 못한 경우 샘플 데이터 사용
        if (filteredPlaces.length === 0) {
          console.warn('API에서 데이터를 가져오지 못함, 샘플 데이터 사용');
          const sampleFilteredPlaces = busanSampleData.filter(place => {
            const placeCategories = place.category ? place.category.split(',').map(cat => cat.trim()) : [];
            const matchesCategory = placeCategories.includes(subCategoryLabel);
            const matchesCategoryGroup = place.category_group === categoryGroup;
            const includesInCategory = place.category && place.category.includes(subCategoryLabel);
            
            return matchesCategory || matchesCategoryGroup || includesInCategory;
          });
          console.log('샘플 데이터 필터링 결과:', sampleFilteredPlaces.length, '개');
          setAllPlaces(sampleFilteredPlaces);
          setPlaces(sampleFilteredPlaces.slice(0, displayCount));
        }
        
      } catch (err) {
        console.error('전체 에러 발생:', err);
        
        // 타임아웃 에러인지 확인
        if (err.message.includes('시간 초과') || err.message.includes('AbortError')) {
          setError('서버 응답이 지연되고 있습니다. 샘플 데이터를 표시합니다.');
        } else {
          setError(`관광지 정보를 불러오는 중 오류가 발생했습니다: ${err.message}`);
        }
        
        // 에러 발생 시 샘플 데이터 사용
        console.log('에러 발생으로 샘플 데이터 사용');
        const sampleFilteredPlaces = busanSampleData.filter(place => {
          const placeCategories = place.category ? place.category.split(',').map(cat => cat.trim()) : [];
          const matchesCategory = placeCategories.includes(subCategoryLabel);
          const matchesCategoryGroup = place.category_group === categoryGroup;
          const includesInCategory = place.category && place.category.includes(subCategoryLabel);
          
          return matchesCategory || matchesCategoryGroup || includesInCategory;
        });
        console.log('에러 시 샘플 데이터 필터링 결과:', sampleFilteredPlaces.length, '개');
        setAllPlaces(sampleFilteredPlaces);
        setPlaces(sampleFilteredPlaces.slice(0, displayCount));
      } finally {
        setLoading(false);
      }
    };

    if (subCategoryLabel) {
      fetchPlaces();
    }
  }, [subCategoryLabel, categoryGroup]);

  // 서브카테고리가 변경될 때마다 displayCount 초기화
  useEffect(() => {
    console.log('서브카테고리 변경됨, displayCount를 8로 초기화:', { subCategoryLabel, categoryGroup });
    setDisplayCount(8);
  }, [subCategoryLabel, categoryGroup]);

  // displayCount가 변경될 때마다 표시할 places 업데이트
  useEffect(() => {
    if (allPlaces.length > 0) {
      setPlaces(allPlaces.slice(0, displayCount));
    }
  }, [displayCount, allPlaces]);

  // 더보기 버튼 핸들러
  const handleLoadMore = () => {
    setDisplayCount(prevCount => {
      const newCount = prevCount + 8;
      console.log('더보기 클릭, displayCount 증가:', prevCount, '->', newCount);
      return newCount;
    });
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', py: 4 }}>
        <CircularProgress />
        <Typography sx={{ ml: 2 }}>관광지 정보를 불러오는 중...</Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ mb: 2 }}>
        {error}
      </Alert>
    );
  }

  if (places.length === 0) {
    return (
      <Box sx={{ 
        mb: 4,
        px: { xs: 4, sm: 2, md: 0 }
      }}>
        <Typography variant="h5" gutterBottom sx={{ mb: 3, fontWeight: 'bold' }}>
          {subCategoryLabel}
        </Typography>
        
        <Grid container spacing={{ xs: 2, sm: 3 }}>
        </Grid>
        
        <Box sx={{ textAlign: 'center', py: 4 }}>
          <Typography variant="h6" color="text.secondary" gutterBottom>
            {subCategoryLabel} 카테고리가 아직 없습니다
          </Typography>
          <Typography variant="body2" color="text.secondary">
            첫 번째 장소를 등록해보세요! 📍
          </Typography>
        </Box>
      </Box>
    );
  }

  return (
    <Box sx={{ 
      mb: 4,
      px: { xs: 4, sm: 2, md: 0 } // 모바일에서 적당한 좌우 여백 (32px)
    }}>
      <Typography variant="h5" gutterBottom sx={{ mb: 3, fontWeight: 'bold' }}>
        {subCategoryLabel}
      </Typography>
      
      <Grid container spacing={{ xs: 2, sm: 3 }}>
        {places.map((place, index) => (
          <Grid item xs={12} sm={6} md={4} lg={3} key={place._id || place.id || `place-${index}`}>
            <SubCategoryCard 
              place={place} 
              subCategoryLabel={subCategoryLabel}
            />
          </Grid>
        ))}
      </Grid>
      
      {places.length < allPlaces.length && (
        <Box sx={{ textAlign: 'center', mt: 3 }}>
          <Button 
            variant="outlined" 
            onClick={handleLoadMore}
            sx={{ 
              px: 4, 
              py: 1.5,
              borderRadius: 2,
              textTransform: 'none',
              fontSize: '16px'
            }}
          >
            더보기 ({allPlaces.length - places.length}개 더 있음)
          </Button>
        </Box>
      )}
      
      {places.length === allPlaces.length && allPlaces.length > 8 && (
        <Box sx={{ textAlign: 'center', mt: 3 }}>
          <Typography variant="body2" color="text.secondary">
            모든 {subCategoryLabel}를 표시했습니다 (총 {allPlaces.length}개)
          </Typography>
        </Box>
      )}
    </Box>
  );
};

export default SubCategoryCardGrid;
