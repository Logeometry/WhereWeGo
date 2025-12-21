import React from 'react';
import { Box, IconButton } from '@mui/material';
import FavoriteIcon from '@mui/icons-material/Favorite';
import ClearIcon from '@mui/icons-material/Clear';
import VisibilityOffIcon from '@mui/icons-material/VisibilityOff';
import styles from './PreferenceButtons.module.scss'; // 필요하다면 스타일 파일 생성

function PreferenceButtons({ attractionId, onPreference }) {
  return (
    <Box className={styles.preferenceButtons}>
      <IconButton color="secondary" onClick={() => onPreference(attractionId, '싫어요')}>
        <ClearIcon fontSize="large" />
      </IconButton>
      <IconButton color="primary" onClick={() => onPreference(attractionId, '좋아요')}>
        <FavoriteIcon fontSize="large" />
      </IconButton>
      <IconButton color="default" onClick={() => onPreference(attractionId, '관심없음')}>
        <VisibilityOffIcon fontSize="large" />
      </IconButton>
    </Box>
  );
}

export default PreferenceButtons;