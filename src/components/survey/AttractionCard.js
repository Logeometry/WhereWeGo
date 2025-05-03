import React from 'react';
import { Box, Typography } from '@mui/material';
import PreferenceButtons from './PreferenceButtons';
import styles from './AttractionCard.module.scss'; // 필요하다면 스타일 파일 생성

function AttractionCard({ attraction, onPreference, isCurrent }) {
  return (
    <Box className={styles.attractionCard}>
      <img src={attraction.coverImage} alt={attraction.name} className={styles.coverImage} />
      <Box className={styles.overlay}>
        <Typography variant="subtitle1">{attraction.name}</Typography>
      </Box>
      {isCurrent && (
        <PreferenceButtons attractionId={attraction.id} onPreference={onPreference} />
      )}
    </Box>
  );
}

export default AttractionCard;