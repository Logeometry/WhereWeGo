import React, { useState } from 'react';
import {
  AppBar,
  Toolbar,
  Typography,
  IconButton,
  Box,
  Drawer,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Divider,
  Avatar,
  TextField,
  InputAdornment,
} from '@mui/material';
import MenuIcon from '@mui/icons-material/Menu';
import SearchIcon from '@mui/icons-material/Search';
import PersonOutlineIcon from '@mui/icons-material/PersonOutline';
import FavoriteBorderIcon from '@mui/icons-material/FavoriteBorder';
import PublicIcon from '@mui/icons-material/Public';

// Drawer 아이콘 예시
import BeachAccessIcon from '@mui/icons-material/BeachAccess';   // 해변
import MuseumIcon from '@mui/icons-material/Museum';             // 역사/문화
import RestaurantIcon from '@mui/icons-material/Restaurant';     // 맛집
import HotelIcon from '@mui/icons-material/Hotel';               // 숙박
import EventIcon from '@mui/icons-material/Event';               // 이벤트
import MapIcon from '@mui/icons-material/Map';                   // 지도
import LocalActivityIcon from '@mui/icons-material/LocalActivity'; // 체험
import StarBorderIcon from '@mui/icons-material/StarBorder';     // 주요 서비스 예시

import './Header.scss';

const Header = () => {
  // Drawer 열림/닫힘 상태
  const [drawerOpen, setDrawerOpen] = useState(false);

  // Drawer 토글 함수
  const toggleDrawer = (open) => (event) => {
    // Tab, Shift 등의 키 이벤트로 인한 Drawer 닫힘 방지
    if (
      event &&
      event.type === 'keydown' &&
      (event.key === 'Tab' || event.key === 'Shift')
    ) {
      return;
    }
    setDrawerOpen(open);
  };

  // 카테고리 예시 목록
  const categoryList = [
    { label: '자연/해변', icon: <BeachAccessIcon /> },
    { label: '역사/문화', icon: <MuseumIcon /> },
    { label: '맛집/레스토랑', icon: <RestaurantIcon /> },
    { label: '숙박', icon: <HotelIcon /> },
    { label: '이벤트', icon: <EventIcon /> },
    { label: '지도/투어', icon: <MapIcon /> },
    { label: '체험', icon: <LocalActivityIcon /> },
  ];

  // 주요 서비스 예시
  const serviceList = [
    { label: '추천 코스', icon: <StarBorderIcon /> },
    { label: '인기 맛집', icon: <StarBorderIcon /> },
    { label: '숙박 예약', icon: <StarBorderIcon /> },
    { label: '할인 티켓', icon: <StarBorderIcon /> },
  ];

  // ListItem 공통 hover 스타일
  const hoverStyle = {
    '&:hover': {
      backgroundColor: '#e0f7fa', // 마우스 오버 시 변화할 배경색 (예시)
      transition: 'background-color 0.3s ease',
    },
  };

  // Drawer 내부 컨텐츠
  const drawerContent = (
    <Box
      sx={{ width: 250 }}
      role="presentation"
      onKeyDown={toggleDrawer(false)}
    >
      {/* 상단 로그인 영역 */}
      <Box sx={{ display: 'flex', alignItems: 'center', padding: '16px' }}>
        <Avatar sx={{ marginRight: '8px' }} />
        <Typography variant="body1">로그인</Typography>
      </Box>
      <Divider />

      {/* 카테고리 영역 */}
      <Typography variant="subtitle1" sx={{ p: 2 }}>
        카테고리
      </Typography>
      <List>
        {categoryList.map((item) => (
          <ListItem
            button
            key={item.label}
            onClick={toggleDrawer(false)}
            sx={hoverStyle}
          >
            <ListItemIcon>{item.icon}</ListItemIcon>
            <ListItemText primary={item.label} />
          </ListItem>
        ))}
      </List>
      <Divider />

      {/* 주요 서비스 영역 */}
      <Typography variant="subtitle1" sx={{ p: 2 }}>
        주요 서비스
      </Typography>
      <List>
        {serviceList.map((item) => (
          <ListItem
            button
            key={item.label}
            onClick={toggleDrawer(false)}
            sx={hoverStyle}
          >
            <ListItemIcon>{item.icon}</ListItemIcon>
            <ListItemText primary={item.label} />
          </ListItem>
        ))}
      </List>
    </Box>
  );

  return (
    <>
      <AppBar position="fixed" className="header">
        <Toolbar className="header__toolbar">
          {/* 왼쪽 영역: 햄버거 메뉴 + 로고 */}
          <Box className="header__left" sx={{ display: 'flex', alignItems: 'center' }}>
            <IconButton
              edge="start"
              className="header__icon-button"
              onClick={toggleDrawer(true)}
            >
              <MenuIcon />
            </IconButton>
            <Typography variant="h6" className="header__logo">
              부산 투어
            </Typography>
          </Box>

          {/* 중앙 영역: 검색창 */}
          <Box className="header__center" sx={{ flex: 1, display: 'flex', justifyContent: 'center' }}>
            <TextField
              placeholder="관광지를 검색해보세요"
              variant="outlined"
              size="small"
              className="header__search"
              InputProps={{
                endAdornment: (
                  <InputAdornment position="end">
                    <SearchIcon />
                  </InputAdornment>
                ),
              }}
            />
          </Box>

          {/* 오른쪽 영역: 아이콘 메뉴 (지도/즐겨찾기/로그인 등) */}
          <Box className="header__right">
            <IconButton className="header__icon-button">
              <PublicIcon />
            </IconButton>
            <IconButton className="header__icon-button">
              <FavoriteBorderIcon />
            </IconButton>
            <IconButton className="header__icon-button">
              <PersonOutlineIcon />
            </IconButton>
          </Box>
        </Toolbar>
      </AppBar>

      {/* 왼쪽에서 열리는 Drawer */}
      <Drawer anchor="left" open={drawerOpen} onClose={toggleDrawer(false)}>
        {drawerContent}
      </Drawer>
    </>
  );
};

export default Header;
