// src/pages/TouristDetailPage.js
import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Chip,
  Button,
  Grid,
  Card,
  CardContent,
  Divider,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Rating,
  IconButton,
} from '@mui/material';
import {
  ArrowBack,
  LocationOn,
  AccessTime,
  Phone,
  Public,
  Directions,
  Restaurant,
  Hotel,
  PhotoCamera,
  AttachMoney,
  LocalOffer as TagIcon,
  Deck as FacilitiesIcon,
  Map as NearbyAttractionIcon,
} from '@mui/icons-material';
import FavoriteIcon from '@mui/icons-material/Favorite';
import FavoriteBorderIcon from '@mui/icons-material/FavoriteBorder';
import { useWishlist } from '../contexts/WishlistContext'; // 경로 확인!

// 1단계: 기본 관광지 정보 정의 (ID 1-5)
const baseTouristDetailsData = {
  1: {
    id: 1,
    title: "해운대 해수욕장",
    location: "부산광역시 해운대구",
    fullAddress: "부산광역시 해운대구 우동 (해운대해변로 264)",
    description: "부산을 대표하는 해수욕장으로, 넓은 백사장과 아름다운 해안선이 유명합니다. 여름철에는 수많은 피서객들로 붐비며, 다양한 축제와 행사가 연중 개최됩니다. 동백섬과 달맞이언덕 등 주변 관광 명소와도 접근성이 좋습니다.",
    image: "/api/placeholder/800/400?text=해운대해수욕장",
    gallery: [
      "/api/placeholder/400/300?text=해운대풍경1",
      "/api/placeholder/400/300?text=해운대야경",
      "/api/placeholder/400/300?text=해운대축제",
      "/api/placeholder/400/300?text=동백섬뷰",
    ],
    tags: ['해변', '여름', '부산대표', '가족여행', '축제', '야경'],
    subCategory: '해변',
    rating: 4.7,
    reviewCount: 3250,
    hours: "24시간 개방 (해수욕 가능 시간: 09:00 - 18:00, 계절별 변동)",
    phone: "051-749-7611 (해운대관광안내소)",
    website: "www.haeundae.go.kr/tour",
    entranceFee: "무료 (해수욕장 시설 이용료 별도)",
    facilities: ["샤워실", "탈의실", "화장실", "공영주차장", "파라솔 대여", "튜브 대여", "안전요원", "음수대"],
    nearbyAttractions: [
      { id: 101, title: "SEA LIFE 부산아쿠아리움", image: "/api/placeholder/120/120?text=아쿠아리움", distance: "0.5km" },
      { id: 102, title: "동백섬 (누리마루 APEC 하우스)", image: "/api/placeholder/120/120?text=동백섬", distance: "1.0km" },
      { id: 103, title: "더베이 101", image: "/api/placeholder/120/120?text=더베이101", distance: "1.5km" },
      { id: 108, title: "달맞이길", image: "/api/placeholder/120/120?text=달맞이길", distance: "2.0km" },
    ],
    nearbyRestaurants: [
      { id: 201, title: "해운대 암소갈비집", image: "/api/placeholder/120/120?text=암소갈비", cuisine: "한식 (갈비)" },
      { id: 202, title: "해운대시장 횟집거리", image: "/api/placeholder/120/120?text=횟집", cuisine: "해산물 (회)" },
      { id: 203, title: "옵스 해운대점", image: "/api/placeholder/120/120?text=옵스빵집", cuisine: "베이커리" },
      { id: 208, title: "해운대 버거인뉴욕", image: "/api/placeholder/120/120?text=수제버거", cuisine: "양식 (수제버거)" },
    ],
    nearbyAccommodations: [
      { id: 301, title: "파라다이스 호텔 부산", image: "/api/placeholder/120/120?text=파라다이스호텔", type: "5성급 호텔" },
      { id: 302, title: "해운대 게스트하우스 단지", image: "/api/placeholder/120/120?text=게스트하우스", type: "게스트하우스" },
      { id: 306, title: "그랜드 조선 부산", image: "/api/placeholder/120/120?text=그랜드조선", type: "5성급 호텔" },
    ],
  },
  2: {
    id: 2,
    title: "감천문화마을",
    location: "부산광역시 사하구",
    fullAddress: "부산광역시 사하구 감내2로 203",
    description: "한국의 마추픽추, 또는 산토리니라고도 불리는 아름다운 마을입니다. 계단식으로 빼곡히 들어선 파스텔톤의 집들과 골목마다 숨겨진 예술 작품들이 인상적입니다. 어린왕자와 사막여우 포토존이 특히 유명하며, 다양한 공방과 아기자기한 카페들이 즐비하여 방문객들에게 다채로운 경험을 선사합니다.",
    image: "/api/placeholder/800/400?text=감천문화마을",
    gallery: [
      "/api/placeholder/400/300?text=감천마을전경",
      "/api/placeholder/400/300?text=어린왕자포토존",
      "/api/placeholder/400/300?text=감천골목길아트",
      "/api/placeholder/400/300?text=감천공방체험",
    ],
    tags: ['문화마을', '예술', '골목길', '어린왕자', '사진명소', '데이트', '체험'],
    subCategory: '문화/예술',
    rating: 4.5,
    reviewCount: 2880,
    hours: "상시개방 (시설별 운영시간 상이, 보통 09:00 - 18:00)",
    phone: "051-204-1444 (감천문화마을 안내센터)",
    website: "www.gamcheon.or.kr",
    entranceFee: "무료 (일부 체험 프로그램 및 지도 구매 유료)",
    facilities: ["안내센터", "화장실", "주차장 (협소, 대중교통 권장)", "기념품샵", "카페", "공방", "전망대"],
    nearbyAttractions: [
      { id: 104, title: "송도해상케이블카", image: "/api/placeholder/120/120?text=송도케이블카", distance: "3.5km (차량 이동)" },
      { id: 105, title: "비프광장 (BIFF Square)", image: "/api/placeholder/120/120?text=BIFF광장", distance: "4.0km (대중교통)" },
      { id: 109, title: "아미산 전망대", image: "/api/placeholder/120/120?text=아미산전망대", distance: "2.0km" },
    ],
    nearbyRestaurants: [
      { id: 204, title: "감천문화마을 내 분식집", image: "/api/placeholder/120/120?text=마을분식", cuisine: "분식 (떡볶이, 어묵)" },
      { id: 205, title: "마을 전망 좋은 카페", image: "/api/placeholder/120/120?text=마을카페", cuisine: "카페/디저트" },
      { id: 209, title: "아방가르드 카페", image: "/api/placeholder/120/120?text=아방가르드", cuisine: "브런치/카페" },
    ],
    nearbyAccommodations: [
      { id: 303, title: "남포동 호텔 존", image: "/api/placeholder/120/120?text=남포동호텔", type: "호텔 (인근 남포동)" },
      { id: 307, title: "감천마을 내 게스트하우스", image: "/api/placeholder/120/120?text=감천게하", type: "게스트하우스" },
    ],
  },
  3: {
    id: 3,
    title: "자갈치시장",
    location: "부산광역시 중구",
    fullAddress: "부산광역시 중구 자갈치해안로 52",
    description: "부산을 대표하는 수산물 시장으로, '오이소, 보이소, 사이소!'라는 정겨운 구호가 유명합니다. 싱싱한 활어회는 물론 다양한 해산물과 건어물을 저렴하게 구매하고 맛볼 수 있습니다. 활기찬 시장의 분위기와 함께 부산 사람들의 생생한 삶의 현장을 느낄 수 있는 곳입니다.",
    image: "/api/placeholder/800/400?text=자갈치시장",
    gallery: [
      "/api/placeholder/400/300?text=자갈치시장전경",
      "/api/placeholder/400/300?text=싱싱한해산물",
      "/api/placeholder/400/300?text=꼼장어구이",
      "/api/placeholder/400/300?text=자갈치시장야경",
    ],
    tags: ['시장', '수산물', '해산물', '먹거리', '부산명물', '활기찬', '현지체험'],
    subCategory: '시장/상가',
    rating: 4.3,
    reviewCount: 1950,
    hours: "05:00 - 22:00 (점포별 상이, 회센터 보통 10:00 - 22:00)",
    phone: "051-713-8000 (자갈치시장 고객센터)",
    website: "bisco.or.kr/jagalchimarket",
    entranceFee: "무료",
    facilities: ["공영주차장", "화장실", "고객지원센터", "수유실", "해수정수시설", "식당가"],
    nearbyAttractions: [
      { id: 105, title: "비프광장 (BIFF Square)", image: "/api/placeholder/120/120?text=BIFF광장", distance: "0.5km" },
      { id: 106, title: "국제시장 & 깡통시장", image: "/api/placeholder/120/120?text=국제시장", distance: "0.7km" },
      { id: 107, title: "용두산공원 (부산타워)", image: "/api/placeholder/120/120?text=부산타워", distance: "1.2km" },
      { id: 110, title: "영도대교", image: "/api/placeholder/120/120?text=영도대교", distance: "0.3km" },
    ],
    nearbyRestaurants: [
      { id: 206, title: "자갈치시장 내 횟집", image: "/api/placeholder/120/120?text=시장횟집", cuisine: "해산물 (회, 해물탕)" },
      { id: 207, title: "꼼장어 골목 (시장 주변)", image: "/api/placeholder/120/120?text=꼼장어", cuisine: "해산물 (꼼장어구이)" },
      { id: 210, title: "부산족발 (남포동)", image: "/api/placeholder/120/120?text=부산족발", cuisine: "한식 (냉채족발)" },
    ],
    nearbyAccommodations: [
      { id: 304, title: "남포동 GNB 호텔", image: "/api/placeholder/120/120?text=GNB호텔", type: "호텔" },
      { id: 305, title: "부산 관광호텔", image: "/api/placeholder/120/120?text=부산관광호텔", type: "호텔" },
      { id: 308, title: "자갈치역 주변 비즈니스 호텔", image: "/api/placeholder/120/120?text=비즈니스호텔", type: "비즈니스 호텔" },
    ],
  },
  4: {
    id: 4,
    title: "태종대공원",
    location: "부산광역시 영도구",
    fullAddress: "부산광역시 영도구 전망로 24",
    description: "울창한 숲과 기암괴석, 푸른 바다가 어우러진 부산의 대표적인 해안 명승지입니다. 신선바위, 망부석 등 전설이 깃든 바위들과 영도등대, 전망대 등이 있으며, 맑은 날에는 대마도까지 조망할 수 있습니다. 다누비 열차를 이용하면 공원 내부를 편리하게 둘러볼 수 있습니다.",
    image: "/api/placeholder/800/400?text=태종대공원",
    gallery: [
      "/api/placeholder/400/300?text=태종대전망대",
      "/api/placeholder/400/300?text=영도등대",
      "/api/placeholder/400/300?text=신선바위",
      "/api/placeholder/400/300?text=다누비열차",
    ],
    tags: ['공원', '자연경관', '전망대', '바다', '다누비열차', '산책'],
    subCategory: '공원/유원지',
    rating: 4.6,
    reviewCount: 1500,
    hours: "04:00 - 24:00 (다누비 열차: 09:20 - 17:30, 계절별 변동)",
    phone: "051-405-2004 (태종대유원지사업소)",
    website: "www.bisco.or.kr/taejongdae",
    entranceFee: "무료 (다누비 열차 및 유람선 유료)",
    facilities: ["다누비열차", "전망대", "영도등대", "화장실", "주차장", "음식점", "카페", "유람선 선착장"],
    nearbyAttractions: [
      { id: 111, title: "흰여울문화마을", image: "/api/placeholder/120/120?text=흰여울마을", distance: "3.0km" },
      { id: 110, title: "영도대교", image: "/api/placeholder/120/120?text=영도대교", distance: "5.0km" },
    ],
    nearbyRestaurants: [
      { id: 211, title: "태종대 자갈마당 조개구이촌", image: "/api/placeholder/120/120?text=조개구이", cuisine: "해산물 (조개구이)" },
      { id: 212, title: "태종대 짬뽕", image: "/api/placeholder/120/120?text=태종대짬뽕", cuisine: "중식 (짬뽕)" },
    ],
    nearbyAccommodations: [
      { id: 309, title: "영도 라마다 앙코르 호텔", image: "/api/placeholder/120/120?text=라마다영도", type: "호텔" },
    ],
  },
  5: {
    id: 5,
    title: "광안리 해수욕장 & 광안대교",
    location: "부산광역시 수영구",
    fullAddress: "부산광역시 수영구 광안해변로 219",
    description: "젊음과 낭만이 넘치는 해변으로, 특히 밤에는 아름다운 광안대교 야경을 감상할 수 있는 명소입니다. 해변을 따라 다양한 카페, 레스토랑, 펍들이 즐비하며, 여름에는 다양한 해양 스포츠와 축제가 열립니다. 드론쇼도 유명합니다.",
    image: "/api/placeholder/800/400?text=광안리해수욕장",
    gallery: [
      "/api/placeholder/400/300?text=광안대교야경",
      "/api/placeholder/400/300?text=광안리해변카페",
      "/api/placeholder/400/300?text=광안리드론쇼",
      "/api/placeholder/400/300?text=광안리낮풍경",
    ],
    tags: ['해변', '야경', '광안대교', '데이트', '카페거리', '드론쇼', '젊음'],
    subCategory: '해변',
    rating: 4.8,
    reviewCount: 2900,
    hours: "24시간 개방",
    phone: "051-622-4251 (광안리 관광안내소)",
    website: "www.suyeong.go.kr/tour/main.asp",
    entranceFee: "무료",
    facilities: ["샤워실", "탈의실", "화장실", "공영주차장", "카페", "레스토랑", "수상레저 시설"],
    nearbyAttractions: [
      { id: 112, title: "민락수변공원", image: "/api/placeholder/120/120?text=민락수변공원", distance: "1.0km" },
      { id: 103, title: "더베이 101 (해운대 방면)", image: "/api/placeholder/120/120?text=더베이101", distance: "4.0km" },
    ],
    nearbyRestaurants: [
      { id: 213, title: "광안리 횟집거리", image: "/api/placeholder/120/120?text=광안리횟집", cuisine: "해산물 (회)" },
      { id: 214, title: "광안리 카페거리 브런치", image: "/api/placeholder/120/120?text=광안리카페", cuisine: "브런치/카페" },
      { id: 215, title: "매드독스 시카고피자", image: "/api/placeholder/120/120?text=시카고피자", cuisine: "양식 (피자)" },
    ],
    nearbyAccommodations: [
      { id: 310, title: "호텔 아쿠아펠리스", image: "/api/placeholder/120/120?text=아쿠아펠리스", type: "호텔 (워터파크)" },
      { id: 311, title: "켄트호텔 광안리 by 켄싱턴", image: "/api/placeholder/120/120?text=켄트호텔", type: "호텔" },
    ],
  },
};

// 2단계: 최종 touristDetails 객체 생성 및 확장 (ID 6-10)
// WishlistContext 등 다른 모듈에서 import 할 수 있도록 export 합니다.
export const touristDetails = { ...baseTouristDetailsData };

// 이제 baseTouristDetailsData가 완전히 정의되었으므로 안전하게 참조 가능
touristDetails[6] = {
  ...baseTouristDetailsData[1], // 해운대 기반
  id: 6,
  title: "송정 해수욕장 (해운대 인근)",
  description: "해운대보다 한적하고 서핑 명소로 유명한 송정 해수욕장입니다. 조용하게 해수욕을 즐기거나 서핑을 배우기에 좋습니다. 죽도공원 산책도 추천합니다.",
  image: "/api/placeholder/800/400?text=송정해수욕장",
  gallery: [
    "/api/placeholder/400/300?text=송정서핑",
    "/api/placeholder/400/300?text=송정일출",
  ],
  tags: ['해변', '서핑', '조용한', '일출', '드라이브'],
  rating: 4.4,
  reviewCount: 980,
  nearbyAttractions: [
      { id: 601, title: "죽도공원", image: "/api/placeholder/120/120?text=죽도공원", distance: "0.5km" },
      { id: 1, title: "해운대 해수욕장", image: "/api/placeholder/120/120?text=해운대", distance: "5km (차량)" }, // ID 1을 참조
  ],
  nearbyRestaurants: [
      { id: 602, title: "송정집 (김치찜)", image: "/api/placeholder/120/120?text=송정집", cuisine: "한식" },
      { id: 603, title: "문토스트", image: "/api/placeholder/120/120?text=문토스트", cuisine: "간식 (토스트)" },
  ],
  nearbyAccommodations: [
    { id: 604, title: "송정 호텔 라온", image: "/api/placeholder/120/120?text=호텔라온", type: "호텔" },
  ]
};

touristDetails[7] = {
  ...baseTouristDetailsData[2], // 감천문화마을 기반
  id: 7,
  title: "흰여울문화마을 (영도)",
  description: "영화 '변호인' 촬영지로 유명해진 절벽 위 아름다운 마을입니다. 푸른 바다를 배경으로 아기자기한 집들과 카페들이 있으며, 해안산책로가 특히 아름답습니다.",
  image: "/api/placeholder/800/400?text=흰여울문화마을",
  gallery: [
    "/api/placeholder/400/300?text=흰여울해안길",
    "/api/placeholder/400/300?text=흰여울카페",
  ],
  tags: ['문화마을', '바다뷰', '영화촬영지', '산책로', '카페', '영도'],
  rating: 4.6,
  reviewCount: 1200,
  nearbyAttractions: [
      { id: 4, title: "태종대공원", image: "/api/placeholder/120/120?text=태종대", distance: "3km" }, // ID 4를 참조
      { id: 110, title: "영도대교", image: "/api/placeholder/120/120?text=영도대교", distance: "2km" }, // 이전에 정의된 ID 사용
  ],
   nearbyRestaurants: [
      { id: 701, title: "흰여울점빵 (라면)", image: "/api/placeholder/120/120?text=흰여울점빵", cuisine: "분식" },
      { id: 702, title: "손목서가 (북카페)", image: "/api/placeholder/120/120?text=손목서가", cuisine: "카페/디저트" },
  ],
  nearbyAccommodations: [
    { id: 703, title: "흰여울마을 내 민박", image: "/api/placeholder/120/120?text=흰여울민박", type: "민박" },
  ]
};

touristDetails[8] = {
  ...baseTouristDetailsData[3], // 자갈치시장 기반
  id: 8,
  title: "국제시장 & 부평깡통시장",
  description: "없는 것 빼고 다 있다는 국제시장과 다양한 길거리 음식, 수입과자 등으로 유명한 부평깡통시장은 서로 인접해 있어 함께 둘러보기 좋습니다. 부산의 역사와 활기를 느낄 수 있는 곳입니다.",
  image: "/api/placeholder/800/400?text=국제깡통시장",
  gallery: [
    "/api/placeholder/400/300?text=국제시장골목",
    "/api/placeholder/400/300?text=깡통야시장",
  ],
  tags: ['시장', '먹자골목', '쇼핑', '빈티지', '길거리음식', '야시장'],
  rating: 4.2,
  reviewCount: 1800,
  nearbyAttractions: [
      { id: 3, title: "자갈치시장", image: "/api/placeholder/120/120?text=자갈치", distance: "0.5km" }, // ID 3을 참조
      { id: 105, title: "비프광장 (BIFF Square)", image: "/api/placeholder/120/120?text=BIFF광장", distance: "0.2km" },
  ],
  nearbyRestaurants: [
      { id: 801, title: "이가네떡볶이 (깡통시장)", image: "/api/placeholder/120/120?text=이가네떡볶이", cuisine: "분식" },
      { id: 802, title: "씨앗호떡 (비프광장)", image: "/api/placeholder/120/120?text=씨앗호떡", cuisine: "간식" },
  ],
  nearbyAccommodations: [ // 국제시장/남포동 지역 숙소
    { ...baseTouristDetailsData[3].nearbyAccommodations[0], id: 803 }, // 자갈치 숙소 정보 활용
  ]
};

touristDetails[9] = {
  ...baseTouristDetailsData[4], // 태종대 기반
  id: 9,
  title: "오륙도 스카이워크 & 해파랑길",
  description: "바다 위를 걷는 듯한 아찔한 경험을 할 수 있는 오륙도 스카이워크와 아름다운 해안 절경을 따라 걷는 해파랑길 시작점입니다. 오륙도의 멋진 풍경을 감상하기에 좋습니다.",
  image: "/api/placeholder/800/400?text=오륙도스카이워크",
  gallery: [
    "/api/placeholder/400/300?text=오륙도뷰",
    "/api/placeholder/400/300?text=해파랑길시작",
  ],
  tags: ['스카이워크', '바다', '해안산책로', '오륙도', '해파랑길', '풍경'],
  rating: 4.5,
  reviewCount: 1100,
  nearbyAttractions: [
      { id: 901, title: "이기대 도시자연공원", image: "/api/placeholder/120/120?text=이기대", distance: "인접 (해파랑길 연결)" },
  ],
  nearbyRestaurants: [
      { id: 902, title: "오륙도 근처 횟집", image: "/api/placeholder/120/120?text=오륙도횟집", cuisine: "해산물" },
      { id: 903, title: "용호동 할매팥빙수", image: "/api/placeholder/120/120?text=할매팥빙수", cuisine: "디저트" },
  ],
  nearbyAccommodations: [
    { id: 904, title: "이기대 주변 펜션", image: "/api/placeholder/120/120?text=이기대펜션", type: "펜션" },
  ]
};

touristDetails[10] = {
  ...baseTouristDetailsData[5], // 광안리 기반
  id: 10,
  title: "서면 젊음의 거리 & 전포 카페거리",
  description: "부산 최대의 번화가인 서면은 쇼핑, 맛집, 유흥을 즐길 수 있는 곳입니다. 인근의 전포 카페거리는 개성 넘치는 개인 카페들이 많아 젊은이들에게 인기가 높습니다.",
  image: "/api/placeholder/800/400?text=서면전포",
  gallery: [
    "/api/placeholder/400/300?text=서면거리",
    "/api/placeholder/400/300?text=전포카페",
  ],
  tags: ['번화가', '쇼핑', '맛집', '카페거리', '젊음', '교통중심지'],
  rating: 4.4,
  reviewCount: 2200,
  nearbyAttractions: [
      { id: 1001, title: "부산시민공원", image: "/api/placeholder/120/120?text=부산시민공원", distance: "2km" },
      { id: 1004, title: "삼정타워", image: "/api/placeholder/120/120?text=삼정타워", distance: "0.5km" },
  ],
  nearbyRestaurants: [
      { id: 1002, title: "서면 돼지국밥 골목", image: "/api/placeholder/120/120?text=돼지국밥", cuisine: "한식" },
      { id: 1003, title: "전포 카페거리 유명 카페", image: "/api/placeholder/120/120?text=전포카페", cuisine: "카페/디저트" },
      { id: 1005, title: "서면 개미집 (낙곱새)", image: "/api/placeholder/120/120?text=낙곱새", cuisine: "한식" },
  ],
  nearbyAccommodations: [
    { id: 1006, title: "롯데호텔 부산 (서면)", image: "/api/placeholder/120/120?text=롯데호텔부산", type: "5성급 호텔" },
    { id: 1007, title: "서면 비즈니스 호텔 아르반", image: "/api/placeholder/120/120?text=아르반호텔", type: "비즈니스 호텔" },
  ]
};


const TouristDetailPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [tourist, setTourist] = useState(null);
  const [loading, setLoading] = useState(true);
  const { addToWishlist, removeFromWishlist, isWishlisted } = useWishlist();

  const numericId = parseInt(id, 10);

  useEffect(() => {
    setLoading(true);
    // console.log(`요청된 관광지 ID: ${numericId}`); // 디버깅용 로그
    setTimeout(() => {
      const touristData = touristDetails[numericId]; // 이제 touristDetails는 완전히 초기화된 상태
      if (touristData) {
        // console.log(`찾은 관광지 데이터:`, touristData); // 디버깅용 로그
        setTourist(touristData);
      } else {
        console.warn(`ID ${numericId}에 해당하는 관광지 정보를 찾을 수 없습니다.`);
      }
      setLoading(false);
    }, 300);
  }, [numericId]);

  const handleWishlistToggle = () => {
    if (!tourist) return;
    if (isWishlisted(tourist.id)) {
      removeFromWishlist(tourist.id);
    } else {
      addToWishlist(tourist.id);
    }
  };

  if (loading) {
    return (
      <Box className="max-w-6xl mx-auto py-16 px-4 flex justify-center">
        <Typography>관광지 정보를 불러오는 중...</Typography>
      </Box>
    );
  }

  if (!tourist) {
    return (
      <Box className="max-w-6xl mx-auto py-16 px-4 text-center">
        <Typography variant="h5" className="mb-4">
          해당 관광지 정보를 찾을 수 없습니다. (ID: {id})
        </Typography>
        <Button
          variant="contained"
          startIcon={<ArrowBack />}
          onClick={() => navigate(-1)}
        >
          이전 페이지로 돌아가기
        </Button>
      </Box>
    );
  }

  // --- 이하 UI 렌더링 부분은 이전 답변과 동일하게 유지 (생략 없이 전체 포함) ---
  return (
    <Box className="max-w-6xl mx-auto py-8 px-4">
      <Button
        startIcon={<ArrowBack />}
        onClick={() => navigate(-1)}
        className="mb-4 text-gray-700 hover:text-gray-900"
        variant="text"
      >
        목록으로 돌아가기
      </Button>

      <Box
        className="relative rounded-lg overflow-hidden mb-6 h-72 md:h-96 bg-cover bg-center shadow-lg"
        style={{
          backgroundImage: `url(${tourist.image || '/api/placeholder/800/400?text=이미지없음'})`,
        }}
      >
        <Box className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/30 to-transparent flex flex-col justify-end p-6">
          <IconButton
            onClick={handleWishlistToggle}
            sx={{
              position: 'absolute',
              top: 16,
              right: 16,
              backgroundColor: 'rgba(0, 0, 0, 0.4)',
              '&:hover': {
                backgroundColor: 'rgba(0, 0, 0, 0.6)',
              },
            }}
            aria-label="add to wishlist"
          >
            {isWishlisted(tourist.id) ? (
              <FavoriteIcon sx={{ color: 'red' }} />
            ) : (
              <FavoriteBorderIcon sx={{ color: 'white' }} />
            )}
          </IconButton>

          <Typography variant="h3" component="h1" className="text-white font-bold mb-1 drop-shadow-md">
            {tourist.title}
          </Typography>
          <Box className="flex items-center mb-2">
            <Rating value={parseFloat(tourist.rating)} precision={0.1} readOnly sx={{ color: 'yellow.400', mr:1 }} />
            <Typography variant="body1" className="text-white drop-shadow-sm">
              ({tourist.reviewCount} 리뷰)
            </Typography>
          </Box>
          <Box className="flex items-center text-gray-200">
            <LocationOn fontSize="small" className="mr-1" />
            <Typography variant="body1">{tourist.location}</Typography>
          </Box>
        </Box>
      </Box>

      <Box className="flex flex-wrap gap-2 mb-6">
        {tourist.subCategory && <Chip icon={<TagIcon />} label={tourist.subCategory} className="bg-green-100 text-green-700 font-semibold" />}
        {tourist.tags && tourist.tags.map((tag, index) => (
          <Chip
            key={index}
            label={tag}
            className="bg-sky-100 text-sky-700"
            variant="outlined"
          />
        ))}
      </Box>

      <Grid container spacing={4}>
        <Grid item xs={12} md={8}>
          <Card className="mb-6 shadow-md">
            <CardContent>
              <Typography variant="h6" component="h2" className="font-bold mb-3 text-gray-800">
                관광지 소개
              </Typography>
              <Typography variant="body1" className="text-gray-700 leading-relaxed">
                {tourist.description}
              </Typography>
            </CardContent>
          </Card>

          {tourist.gallery && tourist.gallery.length > 0 && (
            <Card className="mb-6 shadow-md">
              <CardContent>
                <Typography variant="h6" component="h2" className="font-bold mb-3 text-gray-800">
                  사진 갤러리
                </Typography>
                <Grid container spacing={2}>
                  {tourist.gallery.map((img, index) => (
                    <Grid item xs={6} sm={4} md={3} key={index}>
                      <Box
                        className="aspect-w-1 aspect-h-1 rounded-lg overflow-hidden shadow hover:shadow-lg transition-shadow duration-300"
                        style={{
                          backgroundImage: `url(${img})`,
                          backgroundPosition: 'center',
                          backgroundSize: 'cover',
                          cursor: 'pointer',
                        }}
                      />
                    </Grid>
                  ))}
                </Grid>
              </CardContent>
            </Card>
          )}

          {tourist.facilities && tourist.facilities.length > 0 && (
            <Card className="mb-6 shadow-md">
              <CardContent>
                <Box className="flex items-center mb-3">
                    <FacilitiesIcon color="primary" className="mr-2"/>
                    <Typography variant="h6" component="h2" className="font-bold text-gray-800">
                        편의 시설
                    </Typography>
                </Box>
                <Grid container spacing={1}>
                  {tourist.facilities.map((facility, index) => (
                    <Grid item xs={6} sm={4} key={index}>
                      <Chip
                        label={facility}
                        className="bg-gray-100 text-gray-700 w-full py-2"
                        size="small"
                      />
                    </Grid>
                  ))}
                </Grid>
              </CardContent>
            </Card>
          )}

          {tourist.nearbyAttractions && tourist.nearbyAttractions.length > 0 && (
            <Card className="mb-6 shadow-md">
              <CardContent>
                <Box className="flex items-center mb-3">
                    <NearbyAttractionIcon color="primary" className="mr-2"/>
                    <Typography variant="h6" component="h2" className="font-bold text-gray-800">
                        주변 가볼만한 곳
                    </Typography>
                </Box>
                <Grid container spacing={2}>
                  {tourist.nearbyAttractions.map((place) => (
                    <Grid item xs={12} sm={6} md={4} key={place.id}>
                      <Box
                        className="flex items-center cursor-pointer hover:bg-gray-50 p-2 rounded-lg transition-colors duration-200 border border-gray-200 hover:border-gray-300"
                        onClick={() => navigate(`/tourist/${place.id}`)}
                      >
                        <Box
                          className="w-16 h-16 rounded-md overflow-hidden mr-3 flex-shrink-0 bg-gray-200"
                          style={{
                            backgroundImage: `url(${place.image || '/api/placeholder/120/120?text=주변명소'})`,
                            backgroundPosition: 'center',
                            backgroundSize: 'cover',
                          }}
                        />
                        <Box>
                          <Typography variant="body1" className="font-semibold text-gray-800">
                            {place.title}
                          </Typography>
                          <Typography variant="body2" className="text-gray-600">
                            {place.distance} 거리
                          </Typography>
                        </Box>
                      </Box>
                    </Grid>
                  ))}
                </Grid>
              </CardContent>
            </Card>
          )}
        </Grid>

        <Grid item xs={12} md={4}>
          <Card className="mb-6 shadow-md sticky top-8">
            <CardContent>
              <Typography variant="h6" component="h2" className="font-bold mb-4 text-gray-800">
                기본 정보
              </Typography>
              <List disablePadding>
                {[
                  { icon: <LocationOn color="action" />, primary: "주소", secondary: tourist.fullAddress },
                  { icon: <AccessTime color="action" />, primary: "운영시간", secondary: tourist.hours },
                  { icon: <Phone color="action" />, primary: "전화번호", secondary: tourist.phone },
                  { icon: <Public color="action" />, primary: "웹사이트", secondary: tourist.website ? <a href={`http://${tourist.website.replace(/^https?:\/\//, '')}`} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">{tourist.website}</a> : "정보 없음" },
                  { icon: <AttachMoney color="action" />, primary: "입장료", secondary: tourist.entranceFee },
                ].map((item, index) => (
                  <React.Fragment key={index}>
                    <ListItem className="px-0 py-2">
                      <ListItemIcon className="min-w-fit mr-3 text-gray-500">{item.icon}</ListItemIcon>
                      <ListItemText
                        primary={item.primary}
                        secondary={item.secondary}
                        primaryTypographyProps={{ className: "font-semibold text-gray-700" }}
                        secondaryTypographyProps={{ className: "text-gray-600" }}
                      />
                    </ListItem>
                    {index < 4 && <Divider component="li" light />}
                  </React.Fragment>
                ))}
              </List>

              <Box className="mt-6">
                <Button
                  variant="contained"
                  color="primary"
                  fullWidth
                  startIcon={<Directions />}
                  className="mb-2 py-2 font-semibold"
                  onClick={() => {
                    if (tourist.fullAddress) {
                      window.open(`https://map.naver.com/p/search/${encodeURIComponent(tourist.title + " " + tourist.fullAddress)}`, '_blank');
                    } else if (tourist.title) {
                      window.open(`https://map.naver.com/p/search/${encodeURIComponent(tourist.title)}`, '_blank');
                    } else {
                      alert('길찾기 정보를 제공할 수 없습니다.');
                    }
                  }}
                >
                  지도에서 길찾기
                </Button>
              </Box>
            </CardContent>
          </Card>

          {tourist.nearbyRestaurants && tourist.nearbyRestaurants.length > 0 && (
            <Card className="mb-6 shadow-md">
              <CardContent>
                <Box className="flex justify-between items-center mb-3">
                  <Typography variant="h6" component="h2" className="font-bold text-gray-800">
                    주변 맛집
                  </Typography>
                  <Restaurant color="secondary" />
                </Box>
                <Divider className="mb-3" />
                {tourist.nearbyRestaurants.map((restaurant) => (
                  <Box key={restaurant.id} className="flex items-center mb-3 last:mb-0 p-2 hover:bg-gray-50 rounded-md transition-colors duration-200">
                    <Box
                      className="w-14 h-14 rounded-md overflow-hidden mr-3 flex-shrink-0 bg-gray-200"
                      style={{
                        backgroundImage: `url(${restaurant.image || '/api/placeholder/120/120?text=맛집'})`,
                        backgroundPosition: 'center',
                        backgroundSize: 'cover',
                      }}
                    />
                    <Box>
                      <Typography variant="body1" className="font-semibold text-gray-800">
                        {restaurant.title}
                      </Typography>
                      <Typography variant="body2" className="text-gray-600">
                        {restaurant.cuisine}
                      </Typography>
                    </Box>
                  </Box>
                ))}
              </CardContent>
            </Card>
          )}

          {tourist.nearbyAccommodations && tourist.nearbyAccommodations.length > 0 && (
            <Card className="shadow-md">
              <CardContent>
                <Box className="flex justify-between items-center mb-3">
                  <Typography variant="h6" component="h2" className="font-bold text-gray-800">
                    주변 숙소
                  </Typography>
                  <Hotel color="secondary" />
                </Box>
                <Divider className="mb-3" />
                {tourist.nearbyAccommodations.map((accommodation) => (
                  <Box key={accommodation.id} className="flex items-center mb-3 last:mb-0 p-2 hover:bg-gray-50 rounded-md transition-colors duration-200">
                    <Box
                      className="w-14 h-14 rounded-md overflow-hidden mr-3 flex-shrink-0 bg-gray-200"
                      style={{
                        backgroundImage: `url(${accommodation.image || '/api/placeholder/120/120?text=숙소'})`,
                        backgroundPosition: 'center',
                        backgroundSize: 'cover',
                      }}
                    />
                    <Box>
                      <Typography variant="body1" className="font-semibold text-gray-800">
                        {accommodation.title}
                      </Typography>
                      <Typography variant="body2" className="text-gray-600">
                        {accommodation.type}
                      </Typography>
                    </Box>
                  </Box>
                ))}
              </CardContent>
            </Card>
          )}
        </Grid>
      </Grid>
    </Box>
  );
};

export default TouristDetailPage;