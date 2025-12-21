import React from 'react';
import { useNavigate } from 'react-router-dom'; // useNavigate 임포트
import { Card, CardContent, CardMedia, Typography, Box, IconButton } from '@mui/material';
import { Star, Heart } from 'lucide-react';
import { useWishlist } from '../contexts/WishlistContext'; // WishlistContext 임포트
import './TouristList.scss'; // 필요한 경우 SCSS 파일 추가

const TouristList = ({ items }) => {
  const navigate = useNavigate();
  const { isWishlisted, addToWishlist, removeFromWishlist } = useWishlist();

  const handleItemClick = (id) => {
    navigate(`/tourist/${id}`); // 상세 페이지로 이동
  };

  const handleWishlistToggle = (event, item) => {
    event.stopPropagation(); // 카드 클릭 이벤트가 발생하지 않도록 방지
    if (isWishlisted(item.id)) {
      removeFromWishlist(item.id);
    } else {
      addToWishlist(item.id);
    }
  };

  return (
    <Box sx={{ mt: 3, display: 'grid', gap: 3, gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))' }}>
      {items.length === 0 ? (
        <Typography variant="h6" color="text.secondary" sx={{ gridColumn: '1 / -1', textAlign: 'center', py: 5 }}>
          해당 조건의 관광지가 없습니다.
        </Typography>
      ) : (
        items.map((item) => (
          <Card
            key={item.id}
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
            onClick={() => handleItemClick(item.id)} // 카드 클릭 시 상세 페이지로 이동
          >
            <CardMedia
              component="img"
              height="180"
              image={item.image}
              alt={item.title}
              sx={{ objectFit: 'cover' }}
            />
            <CardContent sx={{ flexGrow: 1, position: 'relative' }}>
              <Typography variant="h6" component="div" sx={{ mb: 1 }}>
                {item.title}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                {item.location}
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <Star color="action" size={16} style={{ marginRight: 4 }} />
                <Typography variant="body2" color="text.secondary">
                  {item.rating || 'N/A'} ({item.reviewCount ? item.reviewCount.toLocaleString() : 0})
                </Typography>
              </Box>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 1 }}>
                {item.tags?.slice(0, 3).map((tag, idx) => (
                  <Typography
                    key={idx}
                    variant="caption"
                    sx={{
                      backgroundColor: '#e0e0e0',
                      borderRadius: '4px',
                      px: 0.8,
                      py: 0.3,
                      fontSize: '0.75rem',
                      color: '#555',
                    }}
                  >
                    #{tag}
                  </Typography>
                ))}
              </Box>
              <IconButton
                sx={{ position: 'absolute', top: 8, right: 8, background: 'rgba(255,255,255,0.7)', '&:hover': { background: 'rgba(255,255,255,0.9)' } }}
                onClick={(event) => handleWishlistToggle(event, item)}
              >
                <Heart
                  size={20}
                  color={isWishlisted(item.id) ? '#dc3545' : '#777'}
                  fill={isWishlisted(item.id) ? '#dc3545' : 'none'}
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