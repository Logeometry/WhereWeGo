import React from 'react';
import PaletteIcon from '@mui/icons-material/Palette';
import MovieIcon from '@mui/icons-material/Movie';
import NatureIcon from '@mui/icons-material/Nature';
import DirectionsWalkIcon from '@mui/icons-material/DirectionsWalk';
import WavesIcon from '@mui/icons-material/Waves';
import AttractionsIcon from '@mui/icons-material/Attractions';
import ShoppingBagIcon from '@mui/icons-material/ShoppingBag';

// DB 기반으로 업데이트된 카테고리 구조
export const categoriesData = [
  {
    label: '공연관람',
    dbGroup: '공연관람',
    icon: <PaletteIcon />,
    subCategories: [
      { label: '공연장,연극극장' }
    ]
  },
  {
    label: '예술 감상',
    dbGroup: '예술 감상',
    icon: <PaletteIcon />,
    subCategories: [
      { label: '미술관' },
      { label: '전시관' }
    ]
  },
  {
    label: '관람및체험',
    dbGroup: '관람및체험',
    icon: <MovieIcon />,
    subCategories: [
      { label: '과학관' },
      { label: '기념관' },
      { label: '눈썰매장' },
      { label: '도자기,도예촌' },
      { label: '동물원' },
      { label: '박물관' },
      { label: '실내동물원' },
      { label: '자전거여행' },
      { label: '천문대' },
      { label: '테마파크' }
    ]
  },
  {
    label: '자연산림',
    dbGroup: '자연산림',
    icon: <NatureIcon />,
    subCategories: [
      { label: '강' },
      { label: '계곡' },
      { label: '산' },
      { label: '유원지' },
      { label: '호수' }
    ]
  },
  {
    label: '자연풍경',
    dbGroup: '자연풍경',
    icon: <WavesIcon />,
    subCategories: [
      { label: '방조제' },
      { label: '섬' },
      { label: '섬(내륙)' },
      { label: '아쿠아리움' },
      { label: '워터테마파크' },
      { label: '전망대' },
      { label: '해수욕장,해변' }
    ]
  },
  {
    label: '테마거리',
    dbGroup: '테마거리',
    icon: <ShoppingBagIcon />,
    subCategories: [
      { label: '먹자골목' },
      { label: '카페거리' },
      { label: '테마거리' }
    ]
  },
  {
    label: '트레킹',
    dbGroup: '트레킹',
    icon: <DirectionsWalkIcon />,
    subCategories: [
      { label: '갈맷길' },
      { label: '금정산둘레길' },
      { label: '남파랑길' },
      { label: '도보여행' },
      { label: '둘레길' },
      { label: '무장애나눔길' },
      { label: '봉래산둘레길' },
      { label: '서구종단트레킹숲길' },
      { label: '해파랑길' }
    ]
  },
  {
    label: '휴양',
    dbGroup: '휴양',
    icon: <AttractionsIcon />,
    subCategories: [
      { label: '관광농원' },
      { label: '수목원,식물원' },
      { label: '숲' },
      { label: '온천' },
      { label: '자연휴양림' },
      { label: '저수지' }
    ]
  }
];
