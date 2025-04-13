import React from 'react';
import {
  Box,
  Container,
  Typography,
  Grid,
  Card,
  CardMedia,
  CardContent,
  IconButton,
} from '@mui/material';
import FavoriteBorderIcon from '@mui/icons-material/FavoriteBorder';

const WishlistPage = () => {
  const wishlist = [];

  const recommendedSpots = [
    { name: '해운대', image: '/image/haeundae.jpg' },
    { name: '광안리', image: '/image/gwangalli.jpg' },
    { name: '감천문화마을', image: '/image/gamcheon.jpg' },
    { name: '태종대', image: '/image/taejongdae.jpg' },
  ];

  const planningSpots = [
    { image: '/image/busan-food.jpg', title: '부산 맛집 지도' },
    { image: '/image/busan-metro.jpg', title: '지하철로 여행하기' },
    { image: '/image/busan-festival.jpg', title: '축제 & 행사 일정' },
  ];

  return (
    <Box sx={{ backgroundColor: '#fffaf3' }}>
      {/* ✅ 상단 Hero 이미지 + 제목 */}
      <Box
        sx={{
          position: 'relative',
          height: '300px',
          backgroundImage: 'url(/image/wish-bgr.jpg)', 
          backgroundSize: 'cover',
          backgroundPosition: 'center',
        }}
      >
        <Box
          sx={{
            position: 'absolute',
            bottom: 40,
            left: '50%',
            transform: 'translateX(-50%)',
            color: '#fff',
            textAlign: 'center',
            textShadow: '1px 1px 5px rgba(0,0,0,0.5)',
          }}
        >
          <Typography variant="h4" fontWeight="bold">
            나의 위시리스트
          </Typography>
        </Box>
      </Box>

      {/* ✅ 본문 콘텐츠 (기존 내용 그대로 유지) */}
      <Container maxWidth="md" sx={{ pt: 6 }}>
        <Typography variant="h6" gutterBottom>
          여행지
        </Typography>

        {wishlist.length === 0 && (
          <Box
            sx={{
              backgroundColor: '#eef6f9',
              textAlign: 'center',
              borderRadius: 2,
              py: 6,
              mb: 5,
            }}
          >
            <FavoriteBorderIcon sx={{ fontSize: 48, color: '#ccc' }} />
            <Typography variant="subtitle1" sx={{ mt: 2 }}>
              아직 저장된 여행지가 없습니다
            </Typography>
            <Typography variant="body2" color="text.secondary">
              관광지의 ♥ 버튼을 눌러 여행지를 추가해보세요
            </Typography>
          </Box>
        )}

        {/* 추천 여행지 */}
        <Typography variant="h6" gutterBottom>
          추천 여행지
        </Typography>
        <Grid container spacing={2} sx={{ mb: 6 }}>
          {recommendedSpots.map((spot, i) => (
            <Grid item xs={6} sm={3} key={i}>
              <Card sx={{ position: 'relative', borderRadius: 2 }}>
                <CardMedia
                  component="img"
                  height="140"
                  image={spot.image}
                  alt={spot.name}
                />
                <CardContent sx={{ p: 1, pb: '8px !important', textAlign: 'center' }}>
                  <Typography fontWeight="bold">{spot.name}</Typography>
                </CardContent>
                <IconButton
                  sx={{
                    position: 'absolute',
                    top: 8,
                    right: 8,
                    color: '#fff',
                    backgroundColor: 'rgba(0,0,0,0.3)',
                  }}
                >
                  <FavoriteBorderIcon />
                </IconButton>
              </Card>
            </Grid>
          ))}
        </Grid>

        {/* 여행 계획하기 */}
        <Typography variant="h6" gutterBottom>
          여행 계획하기
        </Typography>
        <Grid container spacing={2}>
          {planningSpots.map((spot, i) => (
            <Grid item xs={12} sm={6} md={4} key={i}>
              <Card sx={{ borderRadius: 2 }}>
                <CardMedia
                  component="img"
                  height="160"
                  image={spot.image}
                  alt={spot.title}
                />
              </Card>
            </Grid>
          ))}
        </Grid>
      </Container>
    </Box>
  );
};

export default WishlistPage;
