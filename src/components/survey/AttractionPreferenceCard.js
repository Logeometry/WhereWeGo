import React from 'react';
import { Card, CardMedia, CardContent, Typography, Button, Stack } from '@mui/material';
import styles from './AttractionPreferenceCard.module.scss';

function AttractionPreferenceCard({ attraction, onPreference }) {
  const handleLike = () => {
    onPreference(attraction.id, 'like');
  };

  const handleNeutral = () => {
    onPreference(attraction.id, 'neutral');
  };

  const handleDislike = () => {
    onPreference(attraction.id, 'dislike');
  };

  return (
    <Card className={styles.card}>
      <CardMedia
        className={styles.media}
        image={attraction.imageUrl || 'https://via.placeholder.com/300x200'} // 이미지 URL이 없으면 기본 이미지 표시
        title={attraction.name}
      />
      <CardContent className={styles.content}>
        <Typography variant="h6" component="div">
          {attraction.name}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          {attraction.description && attraction.description.substring(0, 100) + '...'} {/* 간단한 설명 */}
        </Typography>
      </CardContent>
      <Stack className={styles.buttons} direction="row" spacing={2}>
        <Button variant="contained" color="primary" onClick={handleLike}>좋아요</Button>
        <Button variant="outlined" onClick={handleNeutral}>모르겠어요</Button>
        <Button variant="contained" color="error" onClick={handleDislike}>싫어요</Button>
      </Stack>
    </Card>
  );
}

export default AttractionPreferenceCard;