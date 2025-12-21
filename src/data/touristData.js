// src/data/touristData.js
// 모든 관광지 데이터를 ID를 키로 하는 객체 형태로 관리합니다.
const allTouristSpotsData = {
  'tourist-1': {
    id: 'tourist-1',
    title: '해운대 해변',
    location: '부산광역시 해운대구',
    fullAddress: '부산광역시 해운대구 우동 (해운대해변로 264)',
    description: '부산을 대표하는 해수욕장으로, 넓은 백사장과 아름다운 해안선이 유명합니다. 여름철에는 수많은 피서객들로 붐비며, 다양한 축제와 행사가 연중 개최됩니다. 동백섬과 달맞이언덕 등 주변 관광 명소와도 접근성이 좋아 부산 여행의 필수 코스로 손꼽힙니다.',
    image: 'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=800&h=400&fit=crop',
    gallery: [
      "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=400&h=300&fit=crop",
      "https://images.unsplash.com/photo-1519046904884-53103b34b206?w=400&h=300&fit=crop",
      "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=400&h=300&fit=crop",
      "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=400&h=300&fit=crop",
      "https://images.unsplash.com/photo-1544551763-46a013bb70d5?w=400&h=300&fit=crop",
      "https://images.unsplash.com/photo-1540979388789-6cee28a1cdc9?w=400&h=300&fit=crop",
      "https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=400&h=300&fit=crop",
      "https://images.unsplash.com/photo-1502780402662-acc01917874e?w=400&h=300&fit=crop"
    ],
    tags: ['바다', '해변', '부산대표', '가족여행', '축제', '야경', '수상스포츠'],
    // 카테고리 변경: 자연·생태 > 해수욕장, 해변
    parentCategory: '해양·수상',
    subCategory: '해수욕장, 해변',
    rating: 4.7,
    reviewCount: 3250,
    hours: "24시간 개방 (해수욕 가능 시간: 09:00 - 18:00)",
    phone: "051-749-7611",
    website: "www.haeundae.go.kr/tour",
    entranceFee: "무료",
    facilities: [
      "샤워실", "탈의실", "화장실", "공영주차장",
      "파라솔 대여", "튜브 대여", "안전요원", "음수대",
      "매점", "편의점", "응급실", "WiFi"
    ],
    nearbyAttractions: [
      { id: 101, title: "SEA LIFE 부산아쿠아리움", image: "https://images.unsplash.com/photo-1544551763-46a013bb70d5?w=200&h=200&fit=crop", distance: "0.5km", rating: 4.6 },
      { id: 102, title: "동백섬", image: "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=200&h=200&fit=crop", distance: "1.0km", rating: 4.5 },
    ],
    nearbyRestaurants: [
      { id: 201, title: "해운대 암소갈비집", image: "https://images.unsplash.com/photo-1544025162-d76694265947?w=200&h=200&fit=crop", cuisine: "한식 (갈비)", rating: 4.8, priceRange: "₩₩₩" },
    ],
    nearbyAccommodations: [
      { id: 301, title: "파라다이스 호텔 부산", image: "https://images.unsplash.com/photo-1564501049412-61c2a3083791?w=200&h=200&fit=crop", type: "5성급 호텔", rating: 4.7, priceRange: "₩₩₩₩" },
    ]
  },
  'tourist-2': {
    id: 'tourist-2',
    title: '감천문화마을',
    location: '부산광역시 사하구',
    fullAddress: '부산광역시 사하구 감천동 감천2로 203',
    description: '부산의 산자락에 아기자기하게 들어선 집들이 계단식으로 늘어선 독특한 경관을 자랑합니다. 한국의 마추픽추, 산토리니라고 불리며, 골목골목 아름다운 벽화와 조형물들이 가득해 사진을 찍기 좋은 곳입니다.',
    image: 'https://via.placeholder.com/800x400?text=감천문화마을+메인',
    gallery: [
      'https://via.placeholder.com/400x300?text=감천1',
      'https://via.placeholder.com/400x300?text=감천2',
    ],
    tags: ['마을', '예술', '사진찍기좋은곳', '골목길', '데이트'],
    // 카테고리 변경: 문화·예술 > 문화원 (가장 유사한 소분류) 또는 새로운 '마을' 소분류 추가 고려
    parentCategory: '문화·예술', // 또는 '테마·관광시설'도 고려 가능
    subCategory: '문화원', // '전통 마을' 카테고리도 고려해볼만함 (하지만 현재 대분류에 없음)
    rating: 4.6,
    reviewCount: 2800,
    hours: "09:00 - 18:00 (마을 개방)",
    phone: "051-204-1800",
    website: "www.gamcheon.or.kr",
    entranceFee: "무료",
    facilities: ["화장실", "안내센터", "기념품샵", "카페", "주차장"],
    nearbyAttractions: [],
    nearbyRestaurants: [],
    nearbyAccommodations: []
  },
  'tourist-3': {
    id: 'tourist-3',
    title: '광안리 해변',
    location: '부산광역시 수영구',
    fullAddress: '부산광역시 수영구 광안해변로 219',
    description: '광안대교의 아름다운 야경으로 유명한 해수욕장입니다. 낮에는 해변을 거닐거나 수상 레저를 즐기기 좋고, 밤에는 다채로운 불꽃놀이와 레이저쇼가 펼쳐져 낭만적인 분위기를 선사합니다.',
    image: 'https://via.placeholder.com/800x400?text=광안리+메인',
    gallery: [
      'https://via.placeholder.com/400x300?text=광안리1',
      'https://via.placeholder.com/400x300?text=광안리2',
    ],
    tags: ['바다', '야경', '불꽃놀이', '카페거리', '데이트'],
    // 카테고리 변경: 해양·수상 > 해수욕장, 해변
    parentCategory: '해양·수상',
    subCategory: '해수욕장, 해변',
    rating: 4.5,
    reviewCount: 2500,
    hours: "24시간 개방",
    phone: "051-610-4061",
    website: "www.suyeong.go.kr/tour",
    entranceFee: "무료",
    facilities: ["샤워실", "탈의실", "화장실", "공영주차장", "카페", "레스토랑"],
    nearbyAttractions: [],
    nearbyRestaurants: [],
    nearbyAccommodations: []
  },
  'tourist-4': {
    id: 'tourist-4',
    title: '태종대유원지',
    location: '부산광역시 영도구',
    fullAddress: '부산광역시 영도구 전망로 24',
    description: '아름다운 해안 절벽과 울창한 숲, 그리고 푸른 바다가 어우러진 유원지입니다. 순환 열차 다누비열차를 타고 주요 명소를 편안하게 둘러볼 수 있으며, 등대와 전망대에서 시원한 바다를 조망할 수 있습니다.',
    image: 'https://via.placeholder.com/800x400?text=태종대+메인',
    gallery: [
      'https://via.placeholder.com/400x300?text=태종대1',
      'https://via.placeholder.com/400x300?text=태종대2',
    ],
    tags: ['자연', '공원', '등대', '해안', '산책'],
    // 카테고리 변경: 테마·관광시설 > 유원지 또는 자연·생태 > 숲
    parentCategory: '테마·관광시설',
    subCategory: '유원지',
    rating: 4.4,
    reviewCount: 1900,
    hours: "04:00 - 24:00 (다누비열차 09:30 - 17:30)",
    phone: "051-405-2004",
    website: "www.taejongdae.or.kr",
    entranceFee: "무료 (다누비열차 유료)",
    facilities: ["주차장", "화장실", "매점", "다누비열차", "식당"],
    nearbyAttractions: [],
    nearbyRestaurants: [],
    nearbyAccommodations: []
  },
  'tourist-5': {
    id: 'tourist-5',
    title: '부산 아쿠아리움',
    location: '부산광역시 해운대구',
    fullAddress: '부산광역시 해운대구 해운대해변로 266',
    description: '다양한 해양 생물들을 만날 수 있는 도심 속 해저 세계입니다. 상어, 펭귄, 수달 등 여러 해양 동물을 관람하고, 특별한 쇼와 체험 프로그램도 즐길 수 있어 가족 단위 방문객에게 인기가 많습니다.',
    image: 'https://via.placeholder.com/800x400?text=아쿠아리움+메인',
    gallery: [
      'https://via.placeholder.com/400x300?text=아쿠아리움1',
      'https://via.placeholder.com/400x300?text=아쿠아리움2',
    ],
    tags: ['체험', '실내', '수족관', '교육', '가족'],
    // 카테고리 변경: 영화·체험 > 아쿠아리움
    parentCategory: '영화·체험',
    subCategory: '아쿠아리움',
    rating: 4.3,
    reviewCount: 1500,
    hours: "10:00 - 19:00 (주말 09:00 - 20:00)",
    phone: "051-740-1700",
    website: "www.busanaquarium.com",
    entranceFee: "유료",
    facilities: ["주차장", "화장실", "기념품샵", "카페", "유모차대여"],
    nearbyAttractions: [],
    nearbyRestaurants: [],
    nearbyAccommodations: []
  },
  'tourist-6': {
    id: 'tourist-6',
    title: '자갈치시장',
    location: '부산광역시 중구',
    fullAddress: '부산광역시 중구 자갈치해안로 52',
    description: '부산의 대표적인 어시장으로, 싱싱한 해산물과 활기찬 시장 분위기를 느낄 수 있는 곳입니다. 다양한 해산물을 직접 고르고 맛볼 수 있으며, 부산 아지매들의 정겨운 사투리도 들을 수 있습니다.',
    image: 'https://via.placeholder.com/800x400?text=자갈치시장+메인',
    gallery: [
      'https://via.placeholder.com/400x300?text=자갈치시장1',
      'https://via.placeholder.com/400x300?text=자갈치시장2',
    ],
    tags: ['시장', '먹거리', '해산물', '부산', '전통시장'],
    // 카테고리 변경: 상업·소비 > 노천매장 (가장 유사한 소분류. '전통 시장' 소분류 추가 고려)
    parentCategory: '상업·소비',
    subCategory: '노천매장', // '전통 시장' 소분류를 추가하는 것이 더 정확합니다.
    rating: 4.2,
    reviewCount: 1700,
    hours: "05:00 - 22:00 (일부 점포 휴무)",
    phone: "051-719-7800",
    website: "www.jagalchimarket.org",
    entranceFee: "무료",
    facilities: ["주차장", "화장실", "식당"],
    nearbyAttractions: [],
    nearbyRestaurants: [],
    nearbyAccommodations: []
  },
  // 기존 Array.from으로 생성되던 샘플 데이터들을 실제 객체로 추가 (ID는 `tourist-X` 형식으로 통일)
  ...Object.fromEntries(Array.from({ length: 21 }).map((_, i) => {
    const idNum = i + 7;
    // 임의로 카테고리 할당 (실제 데이터에 따라 조정 필요)
    let assignedParentCategory = '자연·생태';
    let assignedSubCategory = '숲';

    if (idNum % 3 === 0) {
      assignedParentCategory = '트레킹·산책';
      assignedSubCategory = '둘레길';
    } else if (idNum % 3 === 1) {
      assignedParentCategory = '테마·관광시설';
      assignedSubCategory = '테마파크';
    } else {
      assignedParentCategory = '문화·예술';
      assignedSubCategory = '전시관';
    }

    return [`tourist-${idNum}`, {
      id: `tourist-${idNum}`,
      title: `테마 관광지 ${idNum}`,
      location: `부산광역시 ${idNum}동`,
      fullAddress: `부산광역시 ${idNum}동`,
      description: '흥미로운 곳입니다. 이곳은 카테고리 테스트를 위한 데이터입니다.',
      image: `https://via.placeholder.com/400x200?text=관광지${idNum}`,
      gallery: [`https://via.placeholder.com/400x300?text=관광지${idNum}-1`],
      tags: ['테마', '산책'],
      subCategory: assignedSubCategory,
      parentCategory: assignedParentCategory,
      rating: 4.0,
      reviewCount: 100,
      hours: "상시 개방",
      phone: "000-0000-0000",
      website: "N/A",
      entranceFee: "무료",
      facilities: ["주차장", "화장실"],
      nearbyAttractions: [],
      nearbyRestaurants: [],
      nearbyAccommodations: []
    }];
  }))
};

export default allTouristSpotsData;