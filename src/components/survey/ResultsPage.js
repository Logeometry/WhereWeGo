import React from 'react';
import { Typography, Box, List, ListItem, ListItemText } from '@mui/material';
import styles from './ResultsPage.module.scss'; // 필요하다면 스타일 파일 생성

function ResultsPage({ preferences, attractions }) {
  const likedAttractions = Object.entries(preferences)
    .filter(([, preference]) => preference === '좋아요')
    .map(([id]) => {
      for (const theme in attractions) {
        const found = attractions[theme]?.find(attr => attr.id === id);
        if (found) return found;
      }
      return null;
    })
    .filter(Boolean);

  return (
    <Box className={styles.resultsPage}>
      <Typography variant="h4" gutterBottom>Survey Results</Typography>
      {likedAttractions.length > 0 ? (
        <Box>
          <Typography variant="h6">You might like these places:</Typography>
          <List>
            {likedAttractions.map(attraction => (
              <ListItem key={attraction.id}>
                <ListItemText primary={attraction.name} />
              </ListItem>
            ))}
          </List>
        </Box>
      ) : (
        <Typography>No liked attractions yet.</Typography>
      )}
      {/* 추가적인 결과 분석 및 추천 로직 구현 필요 */}
    </Box>
  );
}

export default ResultsPage;