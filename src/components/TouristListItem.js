// src/components/TouristListItem.js
import React from 'react';
import { Box, Typography, IconButton, Avatar } from '@mui/material';
import MoreVertIcon from '@mui/icons-material/MoreVert';

const TouristListItem = ({ item }) => {
  return (
    <Box
      sx={{
        display: 'flex',
        gap: 2,
        alignItems: 'flex-start',
        py: 2,
        borderBottom: '1px solid #eee',
      }}
    >
      {/* 썸네일 */}
      <Avatar
        variant="rounded"
        src={item.image}
        alt={item.title}
        sx={{ width: 100, height: 80 }}
      />

      {/* 콘텐츠 영역 */}
      <Box sx={{ flexGrow: 1 }}>
        <Typography variant="subtitle1" fontWeight="bold">
          {item.title}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          {item.location}
        </Typography>
        <Typography variant="body2" sx={{ mt: 0.5 }}>
          {item.description}
        </Typography>
        <Typography variant="caption" sx={{ color: '#888', display: 'block', mt: 1 }}>
          {item.tags.map((tag, i) => `#${tag} `)}
        </Typography>
      </Box>

      <IconButton>
        <MoreVertIcon />
      </IconButton>
    </Box>
  );
};

export default TouristListItem;
