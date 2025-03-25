import React from 'react';
import { Grid, Card, CardMedia, CardContent, Typography, CardActionArea } from '@mui/material';

const attractions = [
  {
    title: '해운대 해수욕장',
    image: '/image/HaeundaeBeach.jpg',
    description: '부산을 대표하는 아름다운 해변입니다.',
  },
  {
    title: '자갈치 시장',
    image: '/image/JagalchiMarket.jpg',
    description: '신선한 해산물과 활기찬 분위기를 느껴보세요.',
  },
  {
    title: '태종대 공원',
    image: '/image/Taejong-daeAmusementPark.jpg',
    description: '멋진 바다 전망과 자연을 만끽할 수 있는 곳입니다.',
  },
];

const AttractionsSection = () => {
  return (
    <Grid container spacing={4}>
      {attractions.map((attraction, index) => (
        <Grid item key={index} xs={12} sm={6} md={4}>
          <Card
            sx={{
              borderRadius: 2,
              boxShadow: 3,
              transition: 'transform 0.3s',
              '&:hover': { transform: 'scale(1.03)' },
            }}
          >
            <CardActionArea>
              <CardMedia
                component="img"
                height="200"
                image={attraction.image}
                alt={attraction.title}
              />
              <CardContent>
                <Typography gutterBottom variant="h5" component="div">
                  {attraction.title}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {attraction.description}
                </Typography>
              </CardContent>
            </CardActionArea>
          </Card>
        </Grid>
      ))}
    </Grid>
  );
};

export default AttractionsSection;
