// src/data/categoriesData.js
import React from 'react';
import BeachAccessIcon from '@mui/icons-material/BeachAccess';
import MuseumIcon from '@mui/icons-material/Museum';
import MapIcon from '@mui/icons-material/Map';
import LocalActivityIcon from '@mui/icons-material/LocalActivity';
import EventIcon from '@mui/icons-material/Event';
import StarBorderIcon from '@mui/icons-material/StarBorder';

export const categoriesData = [
  {
    label: '자연/해변',
    icon: <BeachAccessIcon />,
    subCategories: [
      { label: '해변', imageUrl: 'https://example.com/beach.jpg' },
      { label: '산/계곡', imageUrl: 'https://example.com/mountain.jpg' },
      { label: '호수/강', imageUrl: 'https://example.com/lake.jpg' },
      { label: '섬 관광', imageUrl: 'https://example.com/island.jpg' },
    ],
  },
  {
    label: '역사/문화유산',
    icon: <MuseumIcon />,
    subCategories: [
      { label: '유적지', imageUrl: 'https://example.com/ruins.jpg' },
      { label: '성/요새', imageUrl: 'https://example.com/castle.jpg' },
      { label: '사찰/교회', imageUrl: 'https://example.com/temple.jpg' },
      { label: '전시관', imageUrl: 'https://example.com/exhibition.jpg' },
    ],
  },
  {
    label: '랜드마크',
    icon: <MapIcon />,
    subCategories: [
      { label: '대표 건축물', imageUrl: 'https://example.com/building.jpg' },
      { label: '전망대/타워', imageUrl: 'https://example.com/tower.jpg' },
      { label: '기념비', imageUrl: 'https://example.com/monument.jpg' },
      { label: '스카이라인', imageUrl: 'https://example.com/skyscraper.jpg' },
    ],
  },
  {
    label: '체험 관광',
    icon: <LocalActivityIcon />,
    subCategories: [
      { label: '액티비티/모험', imageUrl: 'https://example.com/adventure.jpg' },
      { label: '전통 체험', imageUrl: 'https://example.com/culture-experience.jpg' },
      { label: '자연 탐험', imageUrl: 'https://example.com/nature-exploration.jpg' },
      { label: '도보/자전거 투어', imageUrl: 'https://example.com/tour.jpg' },
    ],
  },
  {
    label: '축제/이벤트',
    icon: <EventIcon />,
    subCategories: [
      { label: '계절별 축제', imageUrl: 'https://example.com/festival.jpg' },
      { label: '문화/예술 축제', imageUrl: 'https://example.com/art-festival.jpg' },
      { label: '스포츠 이벤트', imageUrl: 'https://example.com/sports.jpg' },
      { label: '지역 행사', imageUrl: 'https://example.com/local-event.jpg' },
    ],
  },
  {
    label: '전통 마을',
    icon: <StarBorderIcon />,
    subCategories: [
      { label: '전통 건축물', imageUrl: 'https://example.com/traditional-building.jpg' },
      { label: '민속촌', imageUrl: 'https://example.com/folk-village.jpg' },
      { label: '전통 시장', imageUrl: 'https://example.com/traditional-market.jpg' },
      { label: '문화 체험', imageUrl: 'https://example.com/cultural-experience.jpg' },
    ],
  },
  {
    label: '공원/정원',
    icon: <StarBorderIcon />,
    subCategories: [
      { label: '도심 공원', imageUrl: 'https://example.com/urban-park.jpg' },
      { label: '식물원', imageUrl: 'https://example.com/botanical-garden.jpg' },
      { label: '역사적 정원', imageUrl: 'https://example.com/historical-garden.jpg' },
      { label: '산책로', imageUrl: 'https://example.com/walking-path.jpg' },
    ],
  },
];
