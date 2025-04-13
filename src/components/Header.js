// src/components/Header.js
import React, { useState } from 'react';
import { AppBar, Toolbar, Typography, IconButton, Box, Drawer, List, ListItem, ListItemIcon, ListItemText, Divider, Avatar, TextField, InputAdornment } from '@mui/material';
import MenuIcon from '@mui/icons-material/Menu';
import SearchIcon from '@mui/icons-material/Search';
import PersonOutlineIcon from '@mui/icons-material/PersonOutline';
import FavoriteBorderIcon from '@mui/icons-material/FavoriteBorder';
import PublicIcon from '@mui/icons-material/Public';
// 카테고리 아이콘
import BeachAccessIcon from '@mui/icons-material/BeachAccess';
import MuseumIcon from '@mui/icons-material/Museum';
import RestaurantIcon from '@mui/icons-material/Restaurant';
import HotelIcon from '@mui/icons-material/Hotel';
import EventIcon from '@mui/icons-material/Event';
import MapIcon from '@mui/icons-material/Map';
import LocalActivityIcon from '@mui/icons-material/LocalActivity';
import StarBorderIcon from '@mui/icons-material/StarBorder';
import { useNavigate } from 'react-router-dom';
import TerrainIcon from '@mui/icons-material/Terrain';
import AccountBalanceIcon from '@mui/icons-material/AccountBalance';
import LocationOnIcon from '@mui/icons-material/LocationOn';
import EmojiEventsIcon from '@mui/icons-material/EmojiEvents';
import CelebrationIcon from '@mui/icons-material/Celebration';
import CottageIcon from '@mui/icons-material/Cottage';
import ParkIcon from '@mui/icons-material/Park';
import './Header.scss';

const Header = ({ onSelectCategory = () => { } }) => {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const navigate = useNavigate();

  const toggleDrawer = (open) => (event) => {
    if (event && event.type === 'keydown' && (event.key === 'Tab' || event.key === 'Shift')) return;
    setDrawerOpen(open);
  };

  //  대분류 데이터
  const categoryList = [
    { label: '자연/해변', icon: <TerrainIcon /> },           // 또는 <WavesIcon />
    { label: '역사/문화유산', icon: <AccountBalanceIcon /> },
    { label: '랜드마크', icon: <LocationOnIcon /> },
    { label: '체험 관광', icon: <EmojiEventsIcon /> },
    { label: '축제/이벤트', icon: <CelebrationIcon /> },
    { label: '전통 마을', icon: <CottageIcon /> },
    { label: '공원/정원', icon: <ParkIcon /> },
  ];
  const serviceList = [
    { label: '추천 코스', icon: <StarBorderIcon /> },
    { label: '인기 맛집', icon: <StarBorderIcon /> },
    { label: '숙박 예약', icon: <StarBorderIcon /> },
    { label: '할인 티켓', icon: <StarBorderIcon /> },
  ];

  const hoverStyle = {
    '&:hover': {
      backgroundColor: '#e0f7fa',
      transition: 'background-color 0.3s ease',
    },
  };

  // Drawer 내부 컨텐츠
  const drawerContent = (
    <Box sx={{ width: 250 }} role="presentation" onKeyDown={toggleDrawer(false)}>
      <Box sx={{ display: 'flex', alignItems: 'center', padding: '16px' }}>
        <Avatar sx={{ marginRight: '8px' }} />
        <Typography variant="body1">로그인</Typography>
      </Box>
      <Divider />
      <Typography variant="subtitle1" sx={{ p: 2 }}>카테고리</Typography>
      <List>
        {categoryList.map((item) => (
          <ListItem
            button
            key={item.label}
            onClick={() => {
              // Drawer 닫기
              setDrawerOpen(false);
              // 부모로부터 받은 콜백으로 선택된 대분류 전달
              onSelectCategory(item.label);
              // 카테고리 상세 페이지로 이동
              navigate('/category');
            }}
            sx={hoverStyle}
          >
            <ListItemIcon>{item.icon}</ListItemIcon>
            <ListItemText primary={item.label} />
          </ListItem>
        ))}
      </List>
      <Divider />
      <Typography variant="subtitle1" sx={{ p: 2 }}>주요 서비스</Typography>
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
          <Box className="header__left" sx={{ display: 'flex', alignItems: 'center' }}>
            <IconButton edge="start" className="header__icon-button" onClick={toggleDrawer(true)}>
              <MenuIcon />
            </IconButton>
            <Typography
              variant="h4"
              className="header__logo"
              onClick={() => navigate('/')}
              sx={{ fontFamily: 'Jua' }}
            >
              부산 투어
            </Typography>
          </Box>
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
          <Box className="header__right">
            <IconButton className="header__icon-button"><PublicIcon /></IconButton>
            <IconButton
              className="header__icon-button"
              onClick={() => navigate('/wishlist')}
            >
              <FavoriteBorderIcon />
            </IconButton>
            <IconButton className="header__icon-button"><PersonOutlineIcon /></IconButton>
          </Box>
        </Toolbar>
      </AppBar>
      <Drawer anchor="left" open={drawerOpen} onClose={toggleDrawer(false)}>
        {drawerContent}
      </Drawer>
    </>
  );
};

export default Header;
