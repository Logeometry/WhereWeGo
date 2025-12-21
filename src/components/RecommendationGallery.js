import React, { useMemo, useRef, useState } from 'react';
import {
  Container, Box, Grid, Card, CardMedia, CardContent, CardActions,
  IconButton, Typography, useMediaQuery, useTheme
} from '@mui/material';
import { Favorite, FavoriteBorder } from '@mui/icons-material';
import ArrowBackIosIcon from '@mui/icons-material/ArrowBackIos';
import ArrowForwardIosIcon from '@mui/icons-material/ArrowForwardIos';

const RecommendationGallery = () => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const isTablet = useMediaQuery(theme.breakpoints.down('md'));

  // ✅ 중복 없는 고유 데이터로 정의 (id 전부 고유)
  const initialSpots = useMemo(() => ([
    { id: 101, name: '해운대 해수욕장', location: '해운대구', image: '/image/HaeundaeBeach.jpg', bookmarked: false },
    { id: 102, name: '자갈치 시장',   location: '남포동',   image: '/image/JagalchiMarket.jpg', bookmarked: false },
    { id: 103, name: '태종대 공원',   location: '영도구',   image: '/image/Taejong-daeAmusementPark.jpg', bookmarked: false },
    { id: 104, name: '감천문화마을',   location: '사하구', image: '/image/Gamcheon.jpg', bookmarked: false },
  ]), []);

  // ✅ 혹시라도 중복 id가 섞여 들어오면 런타임에서 제거
  const dedupedSpots = useMemo(() => {
    const map = new Map();
    initialSpots.forEach(s => { if (!map.has(s.id)) map.set(s.id, s); });
    return Array.from(map.values());
  }, [initialSpots]);

  const [spots, setSpots] = useState(dedupedSpots);

  const scrollRef = useRef(null);

  const toggleBookmark = (id) => {
    setSpots(prev =>
      prev.map(s => (s.id === id ? { ...s, bookmarked: !s.bookmarked } : s))
    );
  };

  const handleScrollLeft = () => {
    if (!scrollRef.current) return;
    const scrollAmount = isMobile ? -250 : isTablet ? -280 : -330;
    scrollRef.current.scrollBy({ left: scrollAmount, behavior: 'smooth' });
  };

  const handleScrollRight = () => {
    if (!scrollRef.current) return;
    const scrollAmount = isMobile ? 250 : isTablet ? 280 : 330;
    scrollRef.current.scrollBy({ left: scrollAmount, behavior: 'smooth' });
  };

  return (
    <Container maxWidth="lg" disableGutters sx={{ py: { xs: 2, sm: 3, md: 4 }, px: 0, maxWidth: '100%' }}>
      <Typography
        variant="h5"
        component="h2"
        gutterBottom
        sx={{
          fontSize: { xs: '1.25rem', sm: '1.5rem', md: '1.75rem' },
          fontWeight: 600, mb: { xs: 2, md: 3 }, px: { xs: 0, sm: 0 }
        }}
      >
        당신을 위한 오늘의 AI 맞춤 추천
      </Typography>

      <Box sx={{ position: 'relative' }}>
        {!isMobile && (
          <IconButton
            onClick={handleScrollLeft}
            sx={{
              position: 'absolute',
              left: { sm: '-40px', md: '-48px' },
              top: '50%',
              transform: 'translateY(-50%)',
              backgroundColor: 'rgba(255, 255, 255, 0.7)',
              '&:hover': { backgroundColor: 'rgba(255, 255, 255, 0.9)' },
              boxShadow: 1, zIndex: 2,
              width: { sm: 36, md: 40 }, height: { sm: 36, md: 40 },
            }}
          >
            <ArrowBackIosIcon sx={{ fontSize: { sm: '1.25rem', md: '1.5rem' } }} />
          </IconButton>
        )}

        <Box
          ref={scrollRef}
          sx={{
            overflowX: 'auto', overflowY: 'hidden', scrollbarWidth: 'thin',
            '&::-webkit-scrollbar': { height: { xs: '6px', md: '8px' } },
            '&::-webkit-scrollbar-thumb': { backgroundColor: '#ccc', borderRadius: '4px' },
            px: { xs: 0, sm: 0 }, mx: { xs: 0, sm: 0 },
          }}
        >
          <Grid container wrap="nowrap" spacing={{ xs: 1.5, sm: 2 }} sx={{ width: 'max-content', px: { xs: 0, sm: 0 } }}>
            {spots.map((spot) => (
              <Grid
                item
                key={spot.id} 
                sx={{
                  flex: '0 0 auto',
                  width: { xs: 240, sm: 280, md: 330 },
                }}
              >
                <Card
                  sx={{
                    display: 'flex', flexDirection: 'column', height: '100%',
                    borderRadius: { xs: 2, md: 3 },
                    boxShadow: { xs: 1, sm: 2 },
                    transition: 'transform 0.2s ease, box-shadow 0.2s ease',
                    '&:hover': { transform: 'translateY(-4px)', boxShadow: 4 },
                  }}
                >
                  <CardMedia
                    component="img"
                    alt={spot.name}
                    sx={{
                      height: { xs: 140, sm: 160, md: 180 },
                      objectFit: 'cover',
                    }}
                    image={spot.image}
                    onError={(e) => { e.currentTarget.style.display = 'none'; }}
                  />
                  <CardContent sx={{ flexGrow: 1, p: { xs: 1.5, sm: 2 } }}>
                    <Typography
                      variant="h6"
                      sx={{
                        fontSize: { xs: '1rem', sm: '1.125rem', md: '1.25rem' },
                        fontWeight: 600, mb: 0.5,
                      }}
                    >
                      {spot.name}
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ fontSize: { xs: '0.813rem', sm: '0.875rem' } }}>
                      {spot.location}
                    </Typography>
                  </CardContent>
                  <CardActions sx={{ p: { xs: 1, sm: 1.5 }, pt: 0 }}>
                    <IconButton onClick={() => toggleBookmark(spot.id)} sx={{ p: { xs: 0.5, sm: 1 } }}>
                      {spot.bookmarked ? (
                        <Favorite sx={{ color: 'tomato', fontSize: { xs: '1.25rem', sm: '1.5rem' } }} />
                      ) : (
                        <FavoriteBorder sx={{ fontSize: { xs: '1.25rem', sm: '1.5rem' } }} />
                      )}
                    </IconButton>
                  </CardActions>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Box>

        {!isMobile && (
          <IconButton
            onClick={handleScrollRight}
            sx={{
              position: 'absolute',
              right: { sm: '-40px', md: '-48px' },
              top: '50%',
              transform: 'translateY(-50%)',
              backgroundColor: 'rgba(255, 255, 255, 0.7)',
              '&:hover': { backgroundColor: 'rgba(255, 255, 255, 0.9)' },
              boxShadow: 1, zIndex: 2,
              width: { sm: 36, md: 40 }, height: { sm: 36, md: 40 },
            }}
          >
            <ArrowForwardIosIcon sx={{ fontSize: { sm: '1.25rem', md: '1.5rem' } }} />
          </IconButton>
        )}
      </Box>
    </Container>
  );
};

export default RecommendationGallery;
