// src/components/SubCategoryListItem.js
import React from 'react';
import { Box, Typography, IconButton, Divider } from '@mui/material';
import MoreVertIcon from '@mui/icons-material/MoreVert';
import { Link } from 'react-router-dom';
import { busanSampleData } from '../data/busanSampleData';

const SubCategoryListItem = ({ subCategory, onSelect }) => {
  // 🔽🔽🔽 수정 시작: 필터링 로직 개선 🔽🔽🔽
  const placesInSubCategory = busanSampleData.filter(item => {
    // item.category가 '해수욕장,해변'이라면, ['해수욕장', '해변']으로 분리하여 각 부분이 subCategory.label과 일치하는지 확인
    const itemCategories = item.category.split(',').map(cat => cat.trim());

    // subCategory.label과 item.category 또는 item.category_group이 정확히 일치하거나,
    // item.category에 subCategory.label이 포함되어 있거나,
    // item.category_group에 subCategory.label이 포함되어 있는지 확인
    const matchesCategory = itemCategories.includes(subCategory.label); // 정확한 카테고리 일치
    const matchesCategoryGroup = item.category_group === subCategory.label; // 정확한 카테고리 그룹 일치

    // 또는 더 유연하게: subCategory.label이 item.category 문자열 안에 있는지 (콤마 분리 전)
    const includesInCategory = item.category.includes(subCategory.label);
    const includesInCategoryGroup = item.category_group.includes(subCategory.label);


    return matchesCategory || matchesCategoryGroup || includesInCategory || includesInCategoryGroup;
  });
  // 🔼🔼🔼 수정 끝 🔼🔼🔼


  console.log('SubCategoryListItem Debug');
  console.log('subCategory.label:', subCategory.label);
  console.log('placesInSubCategory:', placesInSubCategory);

  return (
    <>
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          py: 2,
        }}
      >
        <Box sx={{ flexGrow: 1 }}>
          <Typography variant="subtitle1" fontWeight="bold">
            {subCategory.label}
          </Typography>
          {subCategory.description && (
            <Typography variant="body2" color="text.secondary">
              {subCategory.description}
            </Typography>
          )}
        </Box>
        <IconButton>
          <MoreVertIcon />
        </IconButton>
      </Box>
      <Divider />

      {placesInSubCategory.length > 0 ? (
        <Box sx={{ mt: 1, pl: 2, pr:1 }}>
          {placesInSubCategory.map(place => (
            <Box
              key={place._id}
              sx={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                py: 0.8,
                borderBottom: '1px dashed #eee',
                '&:last-child': {
                    borderBottom: 'none',
                }
              }}
            >
              <Link to={`/tourist/${place.id || place._id}`} style={{ textDecoration: 'none', color: 'inherit', flexGrow: 1 }}>
                <Typography variant="body1" sx={{ '&:hover': { textDecoration: 'underline', color: 'primary.main' } }}>
                  {place.name}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {place.category}
                </Typography>
              </Link>
              <IconButton size="small">
                <MoreVertIcon fontSize="small" />
              </IconButton>
            </Box>
          ))}
        </Box>
      ) : (
        <Box sx={{ pl: 2, py: 1 }}>
          <Typography variant="body2" color="text.secondary">
            해당 서브 카테고리의 관광지 정보가 없습니다.
          </Typography>
        </Box>
      )}
    </>
  );
};

export default SubCategoryListItem;