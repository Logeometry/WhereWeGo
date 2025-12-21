import React, { useState } from 'react';
import {
  Box, Paper, Typography, Grid, Card, CardContent, CardMedia,
  Chip, Rating, Button, TextField, InputAdornment, Stack,
  Avatar, Divider, IconButton, Fab, Dialog, DialogContent,
  DialogTitle, DialogActions, List, ListItem, ListItemText,
  ListItemIcon, Accordion, AccordionSummary, AccordionDetails
} from '@mui/material';
import {
  Search as SearchIcon, LocationOn as LocationOnIcon,
  Star as StarIcon, FavoriteIcon, ShareIcon, Phone as PhoneIcon,
  Schedule as ScheduleIcon, AccessTime as TimeIcon,
  LocalParking as ParkingIcon, CreditCard as CardIcon,
  DirectionsBus as DirectionsBusIcon, Train as TrainIcon,
  AttractionsIcon, PhotoCameraIcon, ExpandMore as ExpandMoreIcon,
  Close as CloseIcon, Add as AddIcon, Info as InfoIcon
} from '@mui/icons-material';
import { styled } from '@mui/material/styles';

const StyledCard = styled(Card)(({ theme }) => ({
  height: '100%',
  transition: 'all 0.3s ease',
  cursor: 'pointer',
  '&:hover': {
    transform: 'translateY(-4px)',
    boxShadow: theme.shadows[8],
  },
}));

const DetailDialog = styled(Dialog)(({ theme }) => ({
  '& .MuiDialog-paper': {
    borderRadius: theme.spacing(2),
    maxWidth: '600px',
  },
}));

const TouristRecommendPage = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('전체');
  const [openDetail, setOpenDetail] = useState(false);
  const [selectedAttraction, setSelectedAttraction] = useState(null);

  // 관광지 데이터 (10개)
  const touristAttractions = [
    {
      id: 1,
      name: '경복궁',
      category: '역사/문화',
      area: '종로구',
      rating: 4.6,
      reviews: 1423,
      image: '/api/placeholder/400/250',
      tags: ['조선왕조', '전통건축', '역사유적'],
      distance: '0.8km',
      priceRange: '3,000원',
      hours: '09:00-18:00 (3-10월), 09:00-17:00 (11-2월)',
      phone: '02-3700-3900',
      description: '조선왕조의 정궁으로 600년 역사를 간직한 대표적인 궁궐입니다. 근정전, 경회루, 향원정 등 아름다운 전통 건축물들을 감상할 수 있으며, 수문장 교대식과 궁중문화 체험 프로그램도 운영됩니다.',
      highlights: [
        '근정전에서 보는 웅장한 궁궐 건축',
        '경회루의 아름다운 연못과 누각',
        '향원정의 고즈넉한 정원',
        '수문장 교대식 (10:00, 14:00, 15:30)'
      ],
      transportation: '지하철 3호선 경복궁역 5번 출구 도보 5분',
      bestTime: '봄(벚꽃), 가을(단풍) 계절이 가장 아름다움',
      tips: '한복을 입고 가면 입장료 무료, 영어 가이드 투어 가능'
    },
    {
      id: 2,
      name: 'N서울타워',
      category: '전망/야경',
      area: '중구',
      rating: 4.4,
      reviews: 2156,
      image: '/api/placeholder/400/250',
      tags: ['야경', '전망대', '랜드마크'],
      distance: '2.1km',
      priceRange: '16,000-21,000원',
      hours: '10:00-23:00 (연중무휴)',
      phone: '02-3455-9277',
      description: '서울의 상징적인 랜드마크로 360도 서울 전경을 한눈에 볼 수 있는 최고의 전망 명소입니다. 특히 야경이 아름다우며 연인들의 사랑의 자물쇠로도 유명합니다.',
      highlights: [
        '서울 전경 360도 파노라마 뷰',
        '디지털 관측대와 하늘 화장실',
        '연인들의 사랑의 자물쇠 명소',
        '루프 테라스에서 보는 야경'
      ],
      transportation: '명동역에서 남산 순환버스 02번 또는 케이블카 이용',
      bestTime: '일몰 시간(17:30-19:00)과 야간이 최고',
      tips: '온라인 예약 시 할인, 케이블카 왕복권 패키지 추천'
    },
    {
      id: 3,
      name: '북촌한옥마을',
      category: '전통마을',
      area: '종로구',
      rating: 4.5,
      reviews: 987,
      image: '/api/placeholder/400/250',
      tags: ['한옥', '전통마을', '포토스팟'],
      distance: '1.2km',
      priceRange: '무료',
      hours: '24시간 (주민거주지역)',
      phone: '02-2148-4160',
      description: '600년 역사의 전통 한옥들이 보존된 아름다운 마을로, 현재도 주민들이 거주하고 있습니다. 8개의 주요 전망점에서 서울의 전통과 현대가 조화된 풍경을 감상할 수 있습니다.',
      highlights: [
        '북촌 8경의 아름다운 뷰포인트',
        '600년 전통 한옥 건축 양식',
        '한복 체험과 전통문화 프로그램',
        '갤러리, 공방, 전통�찻집 체험'
      ],
      transportation: '안국역 3번 출구에서 도보 5분',
      bestTime: '이른 아침이나 평일 오후 (관광객 적음)',
      tips: '주민 거주지이므로 조용히 관람, 한복 대여 추천'
    },
    {
      id: 4,
      name: '명동 쇼핑거리',
      category: '쇼핑/맛집',
      area: '중구',
      rating: 4.3,
      reviews: 1876,
      image: '/api/placeholder/400/250',
      tags: ['쇼핑', '맛집', '화장품'],
      distance: '1.5km',
      priceRange: '다양',
      hours: '10:00-22:00 (매장별 상이)',
      phone: '02-774-3000',
      description: '서울 최대의 쇼핑 및 관광 중심지로 국내외 브랜드 매장, 화장품샵, 맛집들이 밀집해 있습니다. 특히 한국 화장품과 K-뷰티 제품으로 유명하며 다양한 길거리 음식도 즐길 수 있습니다.',
      highlights: [
        '한국 화장품 브랜드 집합소',
        '다양한 길거리 음식과 레스토랑',
        '국제 브랜드 플래그십 스토어',
        '명동성당과 문화 공간'
      ],
      transportation: '명동역 6, 7, 8번 출구 바로 연결',
      bestTime: '평일 오후나 저녁 시간',
      tips: '면세점 쇼핑과 연계, 현금보다 카드 결제 편리'
    },
    {
      id: 5,
      name: '동대문 디자인 플라자(DDP)',
      category: '현대건축',
      area: '중구',
      rating: 4.2,
      reviews: 743,
      image: '/api/placeholder/400/250',
      tags: ['건축', '디자인', '야경'],
      distance: '3.2km',
      priceRange: '무료 (전시별 요금)',
      hours: '10:00-19:00 (전시관), 24시간 (외부)',
      phone: '02-2153-0000',
      description: '자하 하디드가 설계한 미래지향적 건축물로 서울의 새로운 랜드마크입니다. 독특한 곡선형 외관과 LED 조명으로 밤에는 환상적인 야경을 연출합니다.',
      highlights: [
        '자하 하디드의 미래지향적 건축 디자인',
        'LED 장미정원의 야간 경관',
        '다양한 디자인 전시와 패션쇼',
        '동대문 역사문화공원과 연계'
      ],
      transportation: '동대문역사문화공원역 1번 출구 바로 연결',
      bestTime: '야간 시간대 (LED 조명 감상)',
      tips: '무료 전시 구역 먼저 둘러보기, 주변 동대문 시장과 연계'
    },
    {
      id: 6,
      name: '한강공원',
      category: '자연/휴식',
      area: '여의도/반포',
      rating: 4.4,
      reviews: 1234,
      image: '/api/placeholder/400/250',
      tags: ['피크닉', '자전거', '야경'],
      distance: '다양',
      priceRange: '무료',
      hours: '24시간',
      phone: '02-3780-0561',
      description: '서울을 가로지르는 한강을 따라 조성된 대표적인 시민 휴식 공간입니다. 피크닉, 자전거 라이딩, 수상스포츠 등을 즐길 수 있으며, 특히 반포 무지개다리 분수쇼가 유명합니다.',
      highlights: [
        '반포 무지개다리 분수쇼',
        '여의도 벚꽃축제 (4월)',
        '한강 자전거도로와 따릉이',
        '치킨과 맥주의 한강 피크닉'
      ],
      transportation: '여의나루역, 잠실나루역 등 각 구간별 지하철역 이용',
      bestTime: '봄(벚꽃철), 저녁 시간대',
      tips: '편의점에서 음식 구매 가능, 자전거 대여 서비스 이용'
    },
    {
      id: 7,
      name: '인사동',
      category: '전통문화',
      area: '종로구',
      rating: 4.3,
      reviews: 892,
      image: '/api/placeholder/400/250',
      tags: ['전통문화', '골동품', '찻집'],
      distance: '1.0km',
      priceRange: '다양',
      hours: '10:00-22:00 (매장별 상이)',
      phone: '02-734-0222',
      description: '전통문화의 중심지로 골동품, 전통공예품, 한국 전통차와 한식을 체험할 수 있는 문화거리입니다. 주말에는 차 없는 거리로 운영되어 여유로운 산책을 즐길 수 있습니다.',
      highlights: [
        '전통 골동품과 공예품 쇼핑',
        '전통찻집과 한정식 맛집',
        '주말 차 없는 거리 체험',
        '삼청동길과 연계된 문화 탐방'
      ],
      transportation: '안국역 6번 출구에서 도보 3분',
      bestTime: '주말 오후 (차 없는 거리)',
      tips: '전통차 체험 추천, 골동품 구매 시 진품 확인 필요'
    },
    {
      id: 8,
      name: '롯데월드타워',
      category: '전망/쇼핑',
      area: '송파구',
      rating: 4.5,
      reviews: 1567,
      image: '/api/placeholder/400/250',
      tags: ['초고층', '전망대', '쇼핑몰'],
      distance: '12km',
      priceRange: '29,000원 (스카이데크)',
      hours: '10:00-22:00',
      phone: '1661-2000',
      description: '555m 높이의 대한민국 최고층 빌딩으로 117-123층에 위치한 서울스카이에서 서울 전체를 조망할 수 있습니다. 쇼핑몰과 아쿠아리움, 롯데월드 어드벤처가 함께 있어 하루 종일 즐길 수 있습니다.',
      highlights: [
        '117-123층 서울스카이 전망대',
        '500층 높이에서 보는 서울 전경',
        '스카이테라스 야외 전망대',
        '롯데월드몰과 아쿠아리움 연계'
      ],
      transportation: '잠실역 지하 연결통로로 바로 이동',
      bestTime: '일몰 시간대와 야간',
      tips: '온라인 예약 할인, 롯데월드 어드벤처 패키지 이용 가능'
    },
    {
      id: 9,
      name: '홍대 거리',
      category: '문화/유흥',
      area: '마포구',
      rating: 4.2,
      reviews: 1089,
      image: '/api/placeholder/400/250',
      tags: ['클럽', '라이브', '젊음'],
      distance: '8km',
      priceRange: '다양',
      hours: '24시간 (업소별 상이)',
      phone: '02-330-1234',
      description: '젊음과 열정이 가득한 서울의 대표적인 문화 거리로 클럽, 바, 라이브 하우스가 밀집해 있습니다. 홍익대학교 근처의 예술적 분위기와 함께 K-pop 문화를 체험할 수 있는 곳입니다.',
      highlights: [
        '다양한 클럽과 라이브 하우스',
        '거리 공연과 버스킹',
        '트렌디한 바와 레스토랑',
        '홍익대학교 주변 예술 문화'
      ],
      transportation: '홍대입구역 9번 출구에서 도보 3분',
      bestTime: '저녁 시간부터 새벽까지',
      tips: '주말 밤에 가장 활기참, 현금 준비 필요한 곳 많음'
    },
    {
      id: 10,
      name: '이태원 글로벌 빌리지',
      category: '국제문화',
      area: '용산구',
      rating: 4.1,
      reviews: 756,
      image: '/api/placeholder/400/250',
      tags: ['국제문화', '다문화', '이슬람'],
      distance: '6km',
      priceRange: '다양',
      hours: '10:00-22:00 (매장별 상이)',
      phone: '02-2199-8745',
      description: '서울의 대표적인 국제문화 거리로 세계 각국의 음식과 문화를 체험할 수 있습니다. 이슬람 사원을 중심으로 할랄 음식점과 다양한 국가의 레스토랑이 모여 있어 글로벌 문화를 즐길 수 있습니다.',
      highlights: [
        '세계 각국의 정통 음식 체험',
        '이태원 이슬람 사원 방문',
        '다문화 쇼핑과 문화 체험',
        '해밀턴 호텔과 고급 레스토랑'
      ],
      transportation: '이태원역 3번 출구에서 도보 5분',
      bestTime: '저녁 시간대 (레스토랑 이용)',
      tips: '할랄 음식 체험 추천, 다양한 언어로 소통 가능'
    }
  ];

  const categories = ['전체', '역사/문화', '전망/야경', '전통마을', '쇼핑/맛집', '현대건축', '자연/휴식', '전통문화', '문화/유흥', '국제문화'];

  const getFeatureIcon = (feature) => {
    switch (feature) {
      case 'parking': return <ParkingIcon fontSize="small" />;
      case 'card': return <CreditCard fontSize="small" />;
      default: return null;
    }
  };

  const filteredAttractions = touristAttractions.filter(attraction => {
    const matchesSearch = attraction.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         attraction.tags.some(tag => tag.toLowerCase().includes(searchTerm.toLowerCase()));
    const matchesCategory = selectedCategory === '전체' || attraction.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  const handleDetailOpen = (attraction) => {
    setSelectedAttraction(attraction);
    setOpenDetail(true);
  };

  const handleDetailClose = () => {
    setOpenDetail(false);
    setSelectedAttraction(null);
  };

  const handleAddToItinerary = (attraction) => {
    console.log('일정에 추가:', attraction.name);
    // 실제로는 여행 계획 페이지의 상태를 업데이트하는 함수 호출
  };

  return (
    <Box sx={{ maxWidth: 1200, margin: '0 auto', p: 3 }}>
      {/* Header Section */}
      <Paper sx={{ p: 3, mb: 3, borderRadius: 2 }}>
        <Typography variant="h4" sx={{ fontWeight: 600, mb: 1 }}>
          서울 추천 관광지 🏛️
        </Typography>
        <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
          모델이 추천하는 서울의 대표 관광지 10곳을 소개합니다
        </Typography>

        {/* Search */}
        <TextField
          placeholder="관광지명 또는 태그로 검색..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon />
              </InputAdornment>
            ),
          }}
          sx={{ width: '100%', mb: 3 }}
        />

        {/* Category Filter */}
        <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>
          카테고리
        </Typography>
        <Stack direction="row" spacing={1} sx={{ flexWrap: 'wrap', gap: 1 }}>
          {categories.map((category) => (
            <Chip
              key={category}
              label={category}
              onClick={() => setSelectedCategory(category)}
              variant={selectedCategory === category ? 'filled' : 'outlined'}
              color={selectedCategory === category ? 'primary' : 'default'}
              sx={{
                backgroundColor: selectedCategory === category ? '#FF6B6B' : 'transparent',
                '&:hover': {
                  backgroundColor: selectedCategory === category ? '#FF5252' : '#f5f5f5'
                }
              }}
            />
          ))}
        </Stack>
      </Paper>

      {/* Attractions Grid */}
      <Grid container spacing={3}>
        {filteredAttractions.map((attraction) => (
          <Grid item xs={12} md={6} lg={4} key={attraction.id}>
            <StyledCard onClick={() => handleDetailOpen(attraction)}>
              <CardMedia
                component="div"
                height="200"
                sx={{
                  backgroundColor: '#e8f5e8',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  position: 'relative'
                }}
              >
                <AttractionsIcon sx={{ fontSize: 60, color: '#666' }} />
                <IconButton 
                  sx={{ 
                    position: 'absolute', 
                    top: 8, 
                    right: 8,
                    backgroundColor: 'rgba(255,255,255,0.8)'
                  }}
                  onClick={(e) => {
                    e.stopPropagation();
                  }}
                >
                  <FavoriteIcon />
                </IconButton>
                <Chip 
                  label={attraction.category}
                  size="small"
                  sx={{
                    position: 'absolute',
                    top: 8,
                    left: 8,
                    backgroundColor: '#FF6B6B',
                    color: 'white'
                  }}
                />
              </CardMedia>
              
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
                  <Typography variant="h6" sx={{ fontWeight: 600 }}>
                    {attraction.name}
                  </Typography>
                  <IconButton 
                    size="small"
                    onClick={(e) => {
                      e.stopPropagation();
                    }}
                  >
                    <ShareIcon fontSize="small" />
                  </IconButton>
                </Box>

                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  <LocationOnIcon fontSize="small" color="action" sx={{ mr: 0.5 }} />
                  <Typography variant="body2" color="text.secondary">
                    {attraction.area} · {attraction.distance}
                  </Typography>
                </Box>

                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <Rating value={attraction.rating} precision={0.1} size="small" readOnly />
                  <Typography variant="body2" sx={{ ml: 1 }}>
                    {attraction.rating} ({attraction.reviews}개 리뷰)
                  </Typography>
                </Box>

                <Typography variant="body2" color="text.secondary" sx={{ mb: 2, height: 40, overflow: 'hidden' }}>
                  {attraction.description.substring(0, 60)}...
                </Typography>

                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mb: 2 }}>
                  {attraction.tags.map((tag, index) => (
                    <Chip 
                      key={index} 
                      label={tag} 
                      size="small" 
                      variant="outlined"
                      sx={{ fontSize: '0.7rem' }}
                    />
                  ))}
                </Box>

                <Divider sx={{ my: 1 }} />

                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Typography variant="body2" sx={{ fontWeight: 600, color: 'primary.main' }}>
                    {attraction.priceRange}
                  </Typography>
                  
                  <Button 
                    variant="contained" 
                    size="small"
                    startIcon={<AddIcon />}
                    sx={{ backgroundColor: '#FF6B6B' }}
                    onClick={(e) => {
                      e.stopPropagation();
                      handleAddToItinerary(attraction);
                    }}
                  >
                    일정 추가
                  </Button>
                </Box>
              </CardContent>
            </StyledCard>
          </Grid>
        ))}
      </Grid>

      {/* Detail Dialog */}
      <DetailDialog
        open={openDetail}
        onClose={handleDetailClose}
        maxWidth="md"
        fullWidth
      >
        {selectedAttraction && (
          <>
            <DialogTitle sx={{ 
              display: 'flex', 
              justifyContent: 'space-between', 
              alignItems: 'center',
              pb: 1
            }}>
              <Typography variant="h5" sx={{ fontWeight: 600 }}>
                {selectedAttraction.name}
              </Typography>
              <IconButton onClick={handleDetailClose}>
                <CloseIcon />
              </IconButton>
            </DialogTitle>
            
            <DialogContent dividers>
              {/* Image Section */}
              <Box
                sx={{
                  height: 250,
                  backgroundColor: '#e8f5e8',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  borderRadius: 2,
                  mb: 3,
                  position: 'relative'
                }}
              >
                <AttractionsIcon sx={{ fontSize: 80, color: '#666' }} />
                <Chip 
                  label={selectedAttraction.category}
                  sx={{
                    position: 'absolute',
                    top: 16,
                    left: 16,
                    backgroundColor: '#FF6B6B',
                    color: 'white'
                  }}
                />
              </Box>

              {/* Basic Info */}
              <Grid container spacing={2} sx={{ mb: 3 }}>
                <Grid item xs={6}>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                    <LocationOnIcon fontSize="small" sx={{ mr: 1, color: 'text.secondary' }} />
                    <Typography variant="body2">
                      {selectedAttraction.area} · {selectedAttraction.distance}
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={6}>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                    <Rating value={selectedAttraction.rating} precision={0.1} size="small" readOnly />
                    <Typography variant="body2" sx={{ ml: 1 }}>
                      {selectedAttraction.rating} ({selectedAttraction.reviews}개)
                    </Typography>
                  </Box>
                </Grid>
              </Grid>

              {/* Description */}
              <Typography variant="body1" sx={{ mb: 3, lineHeight: 1.6 }}>
                {selectedAttraction.description}
              </Typography>

              {/* Highlights */}
              <Accordion defaultExpanded>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Typography variant="h6">주요 볼거리</Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <List dense>
                    {selectedAttraction.highlights.map((highlight, index) => (
                      <ListItem key={index}>
                        <ListItemIcon>
                          <StarIcon fontSize="small" color="primary" />
                        </ListItemIcon>
                        <ListItemText primary={highlight} />
                      </ListItem>
                    ))}
                  </List>
                </AccordionDetails>
              </Accordion>

              {/* Practical Info */}
              <Accordion>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Typography variant="h6">이용 정보</Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <Stack spacing={2}>
                    <Box>
                      <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 0.5 }}>
                        운영시간
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {selectedAttraction.hours}
                      </Typography>
                    </Box>
                    
                    <Box>
                      <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 0.5 }}>
                        입장료
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {selectedAttraction.priceRange}
                      </Typography>
                    </Box>
                    
                    <Box>
                      <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 0.5 }}>
                        교통편
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {selectedAttraction.transportation}
                      </Typography>
                    </Box>
                    
                    <Box>
                      <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 0.5 }}>
                        최적 방문 시간
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {selectedAttraction.bestTime}
                      </Typography>
                    </Box>
                    
                    <Box>
                      <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 0.5 }}>
                        팁
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {selectedAttraction.tips}
                      </Typography>
                    </Box>
                  </Stack>
                </AccordionDetails>
              </Accordion>
            </DialogContent>

            <DialogActions sx={{ p: 3 }}>
              <Button
                variant="outlined"
                startIcon={<PhoneIcon />}
                onClick={() => window.open(`tel:${selectedAttraction.phone}`)}
              >
                전화걸기
              </Button>
              <Button
                variant="contained"
                startIcon={<AddIcon />}
                sx={{ backgroundColor: '#FF6B6B', ml: 1 }}
                onClick={() => handleAddToItinerary(selectedAttraction)}
              >
                일정에 추가
              </Button>
            </DialogActions>
          </>
        )}
      </DetailDialog>

      {/* No Results */}
      {filteredAttractions.length === 0 && (
        <Paper sx={{ p: 4, textAlign: 'center', mt: 3 }}>
          <AttractionsIcon sx={{ fontSize: 60, color: '#ccc', mb: 2 }} />
          <Typography variant="h6" color="text.secondary">
            검색 결과가 없습니다
          </Typography>
          <Typography variant="body2" color="text.secondary">
            다른 검색어나 카테고리를 선택해보세요
          </Typography>
        </Paper>
      )}
    </Box>
  );
};

export default TouristRecommendPage;
