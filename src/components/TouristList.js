import React from 'react';
import { Box, Card, CardMedia, CardContent, Typography, Button } from '@mui/material';
import { useNavigate } from 'react-router-dom'; // useNavigate 훅 import

const TouristList = ({ items, totalCount, currentPage, itemsPerPage }) => {
  const navigate = useNavigate(); // useNavigate 훅 초기화

  const handleItemClick = (id) => {
    navigate(`/tourist/${id}`); // 클릭 시 해당 ID를 가진 상세 페이지로 이동
  };

  return (
    <Box sx={{ mt: 4 }}>
      {items.map((item) => (
        <Card
          key={item.title}
          sx={{ display: 'flex', mb: 2, cursor: 'pointer' }} // cursor: 'pointer' 추가
          onClick={() => handleItemClick(item.title.split(' ')[1])} // 클릭 이벤트 핸들러 추가 및 ID 추출
        >
          <CardMedia
            component="img"
            sx={{ width: 151, height: 151 }}
            image={item.image || "/api/placeholder/151/151"} // 이미지 없을 경우 기본 이미지
            alt={item.title}
          />
          <Box sx={{ display: 'flex', flexDirection: 'column', flexGrow: 1 }}>
            <CardContent sx={{ flex: '1 0 auto' }}>
              <Typography component="div" variant="h6">
                {item.title}
              </Typography>
              <Typography variant="subtitle1" color="text.secondary" component="div">
                {item.location}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {item.description.substring(0, 80)}...
              </Typography>
            </CardContent>
          </Box>
        </Card>
      ))}
      {/* totalCount, currentPage, itemsPerPage props는 필요에 따라 TouristList에서 활용할 수 있습니다. */}
    </Box>
  );
};

export default TouristList;