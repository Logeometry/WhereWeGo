import React, { useState, useRef } from 'react';
import {
    Container,
    Box,
    Grid,
    Card,
    CardMedia,
    CardContent,
    CardActions,
    IconButton,
    Typography,
} from '@mui/material';
import { Favorite, FavoriteBorder } from '@mui/icons-material';
import ArrowBackIosIcon from '@mui/icons-material/ArrowBackIos';
import ArrowForwardIosIcon from '@mui/icons-material/ArrowForwardIos';

const RecommendationGallery = () => {
    const [spots, setSpots] = useState([
        {
            id: 1,
            name: '해운대 해수욕장',
            location: '해운대구',
            image: '/image/HaeundaeBeach.jpg',
            bookmarked: false,
        },
        {
            id: 2,
            name: '자갈치 시장',
            location: '남포동',
            image: '/image/JagalchiMarket.jpg',
            bookmarked: false,
        },
        {
            id: 3,
            name: '태종대 공원',
            location: '영도구',
            image: '/image/Taejong-daeAmusementPark.jpg',
            bookmarked: false,
        },
        {
            id: 1,
            name: '해운대 해수욕장',
            location: '해운대구',
            image: '/image/HaeundaeBeach.jpg',
            bookmarked: false,
        },
        {
            id: 2,
            name: '자갈치 시장',
            location: '남포동',
            image: '/image/JagalchiMarket.jpg',
            bookmarked: false,
        },
        {
            id: 3,
            name: '태종대 공원',
            location: '영도구',
            image: '/image/Taejong-daeAmusementPark.jpg',
            bookmarked: false,
        },

    ]);

    const scrollRef = useRef(null);

    // 북마크 토글
    const toggleBookmark = (id) => {
        setSpots((prevSpots) =>
            prevSpots.map((spot) =>
                spot.id === id ? { ...spot, bookmarked: !spot.bookmarked } : spot
            )
        );
    };

    // 왼쪽 스크롤
    const handleScrollLeft = () => {
        if (scrollRef.current) {
            scrollRef.current.scrollBy({ left: -300, behavior: 'smooth' });
        }
    };

    // 오른쪽 스크롤
    const handleScrollRight = () => {
        if (scrollRef.current) {
            scrollRef.current.scrollBy({ left: 300, behavior: 'smooth' });
        }
    };

    return (
        <Container maxWidth="lg" sx={{ py: 4 }}>
            <Typography variant="h5" component="h2" gutterBottom>
                당신을 위한 오늘의 AI 맞춤 추천
            </Typography>

            <Box sx={{ position: 'relative' }}>
                {/* 왼쪽 화살표 버튼 */}
                <IconButton
                    onClick={handleScrollLeft}
                    sx={{
                        position: 'absolute',
                        left: '-48px',
                        top: '50%',
                        transform: 'translateY(-50%)',
                        backgroundColor: 'rgba(255, 255, 255, 0.7)',
                        '&:hover': { backgroundColor: 'rgba(255, 255, 255, 0.9)' },
                        boxShadow: 1,
                        zIndex: 2,
                    }}
                >
                    <ArrowBackIosIcon />
                </IconButton>

                {/* 가로 스크롤 영역 */}
                <Box
                    ref={scrollRef}
                    sx={{
                        overflowX: 'auto',
                        overflowY: 'hidden',
                        scrollbarWidth: 'thin',
                        '&::-webkit-scrollbar': {
                            height: '8px',
                        },
                        '&::-webkit-scrollbar-thumb': {
                            backgroundColor: '#ccc',
                            borderRadius: '4px',
                        },
                    }}
                >
                    <Grid
                        container
                        wrap="nowrap"
                        spacing={2}
                        sx={{
                            width: 'max-content',
                        }}
                    >
                        {spots.map((spot) => (
                            <Grid
                                item
                                key={spot.id}
                                sx={{
                                    flex: '0 0 auto',
                                    width: 330, // 카드 폭을 330px으로 고정
                                }}
                            >
                                <Card
                                    sx={{
                                        display: 'flex',
                                        flexDirection: 'column',
                                        // 필요 시 전체 카드 높이도 고정 가능
                                        // height: 400,
                                    }}
                                >
                                    <CardMedia
                                        component="img"
                                        alt={spot.name}
                                        sx={{
                                            height: 180, // 이미지 높이 (원하는 값으로 조절)
                                            objectFit: 'cover',
                                        }}
                                        image={spot.image}
                                    />
                                    <CardContent sx={{ flexGrow: 1 }}>
                                        <Typography variant="h6">{spot.name}</Typography>
                                        <Typography variant="body2" color="text.secondary">
                                            {spot.location}
                                        </Typography>
                                    </CardContent>
                                    <CardActions>
                                        <IconButton onClick={() => toggleBookmark(spot.id)}>
                                            {spot.bookmarked ? (
                                                <Favorite sx={{ color: 'tomato' }} />
                                            ) : (
                                                <FavoriteBorder />
                                            )}
                                        </IconButton>
                                    </CardActions>
                                </Card>
                            </Grid>
                        ))}
                    </Grid>
                </Box>

                {/* 오른쪽 화살표 버튼 */}
                <IconButton
                    onClick={handleScrollRight}
                    sx={{
                        position: 'absolute',
                        right: '-48px',
                        top: '50%',
                        transform: 'translateY(-50%)',
                        backgroundColor: 'rgba(255, 255, 255, 0.7)',
                        '&:hover': { backgroundColor: 'rgba(255, 255, 255, 0.9)' },
                        boxShadow: 1,
                        zIndex: 2,
                    }}
                >
                    <ArrowForwardIosIcon />
                </IconButton>
            </Box>
        </Container>
    );
};

export default RecommendationGallery;
