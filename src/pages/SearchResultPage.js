// src/pages/SearchResultPage.js
import React from 'react';
import { Container, Typography } from '@mui/material';
import { useLocation } from 'react-router-dom';
import TouristList from '../components/TouristList';

const SearchResultPage = () => {
  // URL 쿼리에서 "query" 파라미터 추출 (검색어)
  const location = useLocation();
  const params = new URLSearchParams(location.search);
  const query = params.get('query') || '';

  // 예시 관광지 데이터 (실제 데이터는 API나 별도 파일에서 관리)
  const touristData = [
    {
      title: '해운대',
      location: '부산 해운대구',
      description: '부산을 대표하는 아름다운 해변 관광지입니다.',
      image: '/image/haeundae.jpg',
      tags: ['해변', '여름', '바다'],
    },
    {
      title: '광안리',
      location: '부산 수영구',
      description: '야경과 함께 즐기는 부산의 대표 해변입니다.',
      image: '/image/gwangalli.jpg',
      tags: ['해변', '야경', '부산'],
    },
    {
      title: '감천문화마을',
      location: '부산 사하구',
      description: '알록달록한 집들이 모여있는 문화 예술 마을입니다.',
      image: '/image/gamcheon.jpg',
      tags: ['문화', '마을', '예술'],
    },
    {
      title: '태종대',
      location: '부산 영도구',
      description: '절경과 함께 즐기는 부산의 해안 절벽 명소입니다.',
      image: '/image/taejongdae.jpg',
      tags: ['자연', '해안', '부산'],
    },
    // 필요한 만큼 샘플 데이터를 추가
  ];

  // 검색어(query)를 소문자로 변환 후 제목, 위치, 설명에서 포함하는 항목 필터링
  const filteredResults = touristData.filter(item =>
    item.title.toLowerCase().includes(query.toLowerCase()) ||
    item.location.toLowerCase().includes(query.toLowerCase()) ||
    item.description.toLowerCase().includes(query.toLowerCase())
  );

  return (
    <Container maxWidth="md" sx={{ py: 6 }}>
      <Typography variant="h4" gutterBottom>
        "{query}" 검색 결과
      </Typography>
      {filteredResults.length > 0 ? (
       
        <TouristList 
          items={filteredResults} 
          totalCount={filteredResults.length} 
          currentPage={1} 
          itemsPerPage={filteredResults.length} 
        />
      ) : (
        <Typography variant="body1">
          검색 결과가 없습니다.
        </Typography>
      )}
    </Container>
  );
};

export default SearchResultPage;