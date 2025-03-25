import React, { useState, useEffect } from 'react';
import { Box, Typography, Button } from '@mui/material';
import './HeroSection.scss';

const images = [
  '/image/HaeundaeBeach.jpg',      // 해운대 해수욕장
  '/image/JagalchiMarket.jpg',      // 자갈치 시장
  '/image/Taejong-daeAmusementPark.jpg', // 태종대 공원
];

const HeroSection = () => {
  const [currentImageIndex, setCurrentImageIndex] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentImageIndex(prevIndex =>
        prevIndex === images.length - 1 ? 0 : prevIndex + 1
      );
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <section className="hero-section">
      {images.map((image, index) => (
        <Box
          key={index}
          className={`hero-section__slide ${index === currentImageIndex ? 'active' : ''}`}
          sx={{ backgroundImage: `url(${image})` }}
        />
      ))}
      <Box className="hero-section__overlay" />
      <Box className="hero-section__content">
        <Typography variant="h3" className="hero-section__title">
          바로 떠날 수 있는 부산 여행
        </Typography>
        <Typography variant="body1" className="hero-section__subtitle">
          최고의 관광지! 숙박, 맛집, 체험까지 한 번에 확인해보세요.
        </Typography>
        <Box className="hero-section__buttons">
          <Button variant="outlined" color="primary" className="hero-section__btn">
            맛집 소개 보기
          </Button>
          <Button variant="contained" color="primary" className="hero-section__btn">
            지금 시작하기
          </Button>
        </Box>
      </Box>
    </section>
  );
};

export default HeroSection;
