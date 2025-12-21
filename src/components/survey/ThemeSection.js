import React, { useState, useRef, useEffect } from 'react';
import { Typography, Box } from '@mui/material';
import Swiper from 'react-id-swiper';
import 'swiper/swiper-bundle.css';
import AttractionCard from './AttractionCard';
import styles from './ThemeSection.module.scss'; // 필요하다면 스타일 파일 생성

function ThemeSection({ theme, attractions, onPreference, currentIndex }) {
  const swiperRef = useRef(null);
  const [currentSlideIndex, setCurrentSlideIndex] = useState(0);

  const params = {
    slidesPerView: 'auto',
    spaceBetween: 10,
    // pagination: { el: '.swiper-pagination', clickable: true },
    // navigation: { nextEl: '.swiper-button-next', prevEl: '.swiper-button-prev' },
    on: {
      slideChange: () => {
        if (swiperRef.current && swiperRef.current.swiper) {
          setCurrentSlideIndex(swiperRef.current.swiper.realIndex);
        }
      },
    },
  };

  useEffect(() => {
    if (attractions && swiperRef.current && swiperRef.current.swiper && currentIndex < attractions.length) {
      swiperRef.current.swiper.slideTo(currentIndex, 0);
    }
  }, [currentIndex, attractions]);

  if (!attractions || attractions.length === 0) {
    return null;
  }

  return (
    <Box className={styles.themeSection}>
      <Typography variant="h5" gutterBottom>{theme.label}</Typography>
      <div className="swiper-container">
        <Swiper {...params} ref={swiperRef}>
          {attractions.map((attraction, index) => (
            <div key={attraction.id}>
              <AttractionCard
                attraction={attraction}
                onPreference={onPreference}
                isCurrent={index === currentSlideIndex}
              />
            </div>
          ))}
        </Swiper>
        {/* <div className="swiper-pagination"></div> */}
        {/* <div className="swiper-button-prev"></div> */}
        {/* <div className="swiper-button-next"></div> */}
      </div>
    </Box>
  );
}

export default ThemeSection;