// src/components/SubCategoryNavigation.js
import React, { useRef, useState, useEffect } from 'react';
import { Box, Typography, IconButton } from '@mui/material';
import ChevronLeftIcon from '@mui/icons-material/ChevronLeft';
import ChevronRightIcon from '@mui/icons-material/ChevronRight';

const SubCategoryNavigation = ({ 
  subCategories = [], 
  selectedSubCategory, 
  onSubCategorySelect,
  categoryIcon 
}) => {
  const scrollContainerRef = useRef(null);
  const [showLeftArrow, setShowLeftArrow] = useState(false);
  const [showRightArrow, setShowRightArrow] = useState(false);

  // 스크롤 상태 확인
  const checkScrollButtons = () => {
    const container = scrollContainerRef.current;
    if (container) {
      setShowLeftArrow(container.scrollLeft > 0);
      setShowRightArrow(
        container.scrollLeft < container.scrollWidth - container.clientWidth
      );
    }
  };

  // 컴포넌트 마운트 시와 서브카테고리 변경 시 스크롤 버튼 상태 확인
  useEffect(() => {
    checkScrollButtons();
    const container = scrollContainerRef.current;
    if (container) {
      container.addEventListener('scroll', checkScrollButtons);
      return () => container.removeEventListener('scroll', checkScrollButtons);
    }
  }, [subCategories]);

  // 좌측 스크롤
  const scrollLeft = () => {
    const container = scrollContainerRef.current;
    if (container) {
      container.scrollBy({ left: -200, behavior: 'smooth' });
    }
  };

  // 우측 스크롤
  const scrollRight = () => {
    const container = scrollContainerRef.current;
    if (container) {
      container.scrollBy({ left: 200, behavior: 'smooth' });
    }
  };

  // 서브카테고리가 5개 이하면 기존 방식 (flexWrap 사용)
  if (subCategories.length <= 5) {
    return (
      <Box sx={{ 
        display: 'flex', 
        justifyContent: 'center',
        alignItems: 'center', 
        mb: 3,
        flexWrap: 'wrap',
        gap: 1,
      }}>
        {subCategories.map((subCategory, index) => {
          const isSelected = selectedSubCategory === subCategory.label;
          return (
            <Box
              key={index}
              onClick={() => onSubCategorySelect(subCategory.label)}
              sx={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                minWidth: 100,
                cursor: 'pointer',
                p: 2,
                borderRadius: 2,
                backgroundColor: isSelected ? '#667eea' : 'white',
                color: isSelected ? 'white' : '#333',
                border: isSelected ? '2px solid #667eea' : '2px solid transparent',
                transition: 'all 0.2s ease-in-out',
                '&:hover': {
                  backgroundColor: isSelected ? '#5a6fd8' : '#f0f0f0',
                  transform: 'translateY(-2px)',
                  boxShadow: '0 4px 8px rgba(0,0,0,0.1)',
                },
              }}
            >
              <Typography
                variant="body1"
                sx={{
                  textAlign: 'center',
                  fontSize: '14px',
                  fontWeight: isSelected ? 'bold' : 'normal',
                  lineHeight: 1.2,
                  wordBreak: 'keep-all',
                }}
              >
                {subCategory.label}
              </Typography>
            </Box>
          );
        })}
      </Box>
    );
  }

  // 서브카테고리가 6개 이상이면 스크롤 방식 사용
  return (
    <Box sx={{ 
      position: 'relative',
      display: 'flex', 
      alignItems: 'center', 
      mb: 3,
      maxWidth: '100%',
    }}>
      {/* 좌측 화살표 */}
      {showLeftArrow && (
        <IconButton
          onClick={scrollLeft}
          sx={{
            position: 'absolute',
            left: -20,
            zIndex: 2,
            backgroundColor: 'rgba(255, 255, 255, 0.9)',
            boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
            '&:hover': {
              backgroundColor: 'rgba(255, 255, 255, 1)',
            },
          }}
        >
          <ChevronLeftIcon />
        </IconButton>
      )}

      {/* 스크롤 가능한 서브카테고리 컨테이너 */}
      <Box
        ref={scrollContainerRef}
        sx={{
          display: 'flex',
          alignItems: 'center',
          gap: 1,
          overflowX: 'auto',
          scrollbarWidth: 'none', // Firefox
          '&::-webkit-scrollbar': { // Chrome, Safari
            display: 'none',
          },
          px: showLeftArrow || showRightArrow ? 3 : 0,
        }}
      >
        {subCategories.map((subCategory, index) => {
          const isSelected = selectedSubCategory === subCategory.label;
          return (
            <Box
              key={index}
              onClick={() => onSubCategorySelect(subCategory.label)}
              sx={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                minWidth: 100,
                cursor: 'pointer',
                p: 2,
                borderRadius: 2,
                backgroundColor: isSelected ? '#667eea' : 'white',
                color: isSelected ? 'white' : '#333',
                border: isSelected ? '2px solid #667eea' : '2px solid transparent',
                transition: 'all 0.2s ease-in-out',
                flexShrink: 0, // 스크롤 시 크기 유지
                '&:hover': {
                  backgroundColor: isSelected ? '#5a6fd8' : '#f0f0f0',
                  transform: 'translateY(-2px)',
                  boxShadow: '0 4px 8px rgba(0,0,0,0.1)',
                },
              }}
            >
              <Typography
                variant="body1"
                sx={{
                  textAlign: 'center',
                  fontSize: '14px',
                  fontWeight: isSelected ? 'bold' : 'normal',
                  lineHeight: 1.2,
                  wordBreak: 'keep-all',
                  whiteSpace: 'nowrap', // 텍스트 줄바꿈 방지
                }}
              >
                {subCategory.label}
              </Typography>
            </Box>
          );
        })}
      </Box>

      {/* 우측 화살표 */}
      {showRightArrow && (
        <IconButton
          onClick={scrollRight}
          sx={{
            position: 'absolute',
            right: -20,
            zIndex: 2,
            backgroundColor: 'rgba(255, 255, 255, 0.9)',
            boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
            '&:hover': {
              backgroundColor: 'rgba(255, 255, 255, 1)',
            },
          }}
        >
          <ChevronRightIcon />
        </IconButton>
      )}
    </Box>
  );
};

export default SubCategoryNavigation;
