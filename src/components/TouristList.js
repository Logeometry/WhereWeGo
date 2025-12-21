// src/components/TouristList.js
import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardMedia, Typography, Box, IconButton } from '@mui/material';
import { Star, Heart } from 'lucide-react';
import { useWishlist } from '../contexts/WishlistContext';

const TouristList = ({ items }) => {
  const navigate = useNavigate();
  const { isWishlisted, addToWishlist, removeFromWishlist } = useWishlist();

  const handleItemClick = (id) => {
    navigate(`/tourist/${id}`);
  };

  const handleWishlistToggle = (event, item) => {
    event.stopPropagation();
    const itemId = item.id || item._id;
    if (isWishlisted(itemId)) {
      removeFromWishlist(itemId);
    } else {
      addToWishlist(itemId);
    }
  };

  return (
    <Box sx={{ mt: 3, display: 'grid', gap: 3, gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))' }}>
      {items.length === 0 ? (
        <Typography variant="h6" color="text.secondary" sx={{ gridColumn: '1 / -1', textAlign: 'center', py: 5 }}>
          해당 조건의 관광지가 없습니다.
        </Typography>
      ) : (
        items.map((item, idx) => (
          <Card
            key={item.id || item._id}
            sx={{
              display: 'flex',
              flexDirection: 'column',
              cursor: 'pointer',
              transition: 'transform 0.2s, box-shadow 0.2s',
              '&:hover': {
                transform: 'translateY(-5px)',
                boxShadow: '0 4px 20px rgba(0,0,0,0.1)',
              },
            }}
            onClick={() => handleItemClick(item.id || item._id)}
          >
            <CardMedia
              component="img"
              height="180"
              image={`/images/${item.id || item._id}.jpg`}
              alt={item.name}
              sx={{ objectFit: 'cover' }}
            />
            <CardContent sx={{ flexGrow: 1, position: 'relative' }}>
              <Typography variant="h6" component="div" sx={{ mb: 1 }}>
                {item.name}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                {item.category_group || '카테고리 정보 없음'}
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <Star color="action" size={16} style={{ marginRight: 4 }} />
                <Typography variant="body2" color="text.secondary">
                  방문자 수: {item.visitors_count ? item.visitors_count.toLocaleString() : 'N/A'}
                </Typography>
              </Box>
              <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                인덱스: {idx + 1}
              </Typography>
              <IconButton
                sx={{ position: 'absolute', top: 8, right: 8, background: 'rgba(255,255,255,0.7)', '&:hover': { background: 'rgba(255,255,255,0.9)' } }}
                onClick={(event) => handleWishlistToggle(event, item)}
              >
                <Heart
                  size={20}
                  color={isWishlisted(item.id || item._id) ? '#dc3545' : '#777'}
                  fill={isWishlisted(item.id || item._id) ? '#dc3545' : 'none'}
                />
              </IconButton>
            </CardContent>
          </Card>
        ))
      )}
    </Box>
  );
};

export default TouristList;
