import React from 'react';
import { LinearProgress, Typography, Box } from '@mui/material';
import styles from './ProgressBar.module.scss'; // 필요하다면 스타일 파일 생성

function ProgressBar({ current, total }) {
  const progress = total > 0 ? (current / total) * 100 : 0;

  return (
    <Box className={styles.progressBarContainer}>
      <LinearProgress variant="determinate" value={progress} className={styles.progressBar} />
      <Typography>{current} / {total} Completed</Typography>
    </Box>
  );
}

export default ProgressBar;