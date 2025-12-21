// src/components/Header.jsx
import React, { useState, useEffect } from 'react';
import {
  AppBar, Toolbar, Typography, IconButton, Box, Drawer, List, Divider, Avatar,
  Button, ListItemButton, ListItemIcon, ListItemText
} from '@mui/material';
import MenuIcon from '@mui/icons-material/Menu';
import PersonOutlineIcon from '@mui/icons-material/PersonOutline';
import FavoriteBorderIcon from '@mui/icons-material/FavoriteBorder';
import StarBorderIcon from '@mui/icons-material/StarBorder';
import AddLocationIcon from '@mui/icons-material/AddLocation';

// 카테고리 아이콘
import PaletteIcon from '@mui/icons-material/Palette';
import MovieIcon from '@mui/icons-material/Movie';
import NatureIcon from '@mui/icons-material/Nature';
import DirectionsWalkIcon from '@mui/icons-material/DirectionsWalk';
import WavesIcon from '@mui/icons-material/Waves';
import AttractionsIcon from '@mui/icons-material/Attractions';
import ShoppingBagIcon from '@mui/icons-material/ShoppingBag';

import { useNavigate } from 'react-router-dom';
import './Header.scss';
import axios from 'axios';
import AddTouristSpotForm from './AddTouristSpotForm';

const API_BASE = process.env.REACT_APP_API_PREFIX;

const Header = ({ onSelectCategory = () => {} }) => {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [addTouristFormOpen, setAddTouristFormOpen] = useState(false);
  const [user, setUser] = useState(null);

  const navigate = useNavigate();

  const categoryList = [
    { label: '공연관람',   icon: <PaletteIcon /> },
    { label: '예술 감상', icon: <PaletteIcon /> },
    { label: '관람및체험', icon: <MovieIcon /> },
    { label: '자연산림',   icon: <NatureIcon /> },
    { label: '자연풍경',   icon: <WavesIcon /> },
    { label: '테마거리',   icon: <ShoppingBagIcon /> },
    { label: '트레킹',     icon: <DirectionsWalkIcon /> },
    { label: '휴양',       icon: <AttractionsIcon /> },
  ];

  // “관광지 추가”만 유지
  const serviceList = [
    { label: '관광지 추가', icon: <AddLocationIcon />, action: 'add-tourist' },
  ];

  // 사용자 정보
  useEffect(() => {
    const fetchUser = async () => {
      try {
        const { data } = await axios.get(`${API_BASE}/api/v1/me`, { withCredentials: true });
        setUser(data || null);
      } catch (error) {
        if (axios.isAxiosError(error) && error.response?.status === 401) {
          setUser(null);
        } else {
          console.error('사용자 정보 조회 실패:', error);
          setUser(null);
        }
      }
    };
    fetchUser();
  }, []);

  const handleGoogleLogin = () => { window.location.href = `${API_BASE}/api/v1/auth/google/login`; };
  const handleKakaoLogin  = () => { window.location.href = `${API_BASE}/api/v1/auth/kakao/login`;  };

  const handleLogout = async () => {
    try {
      await axios.post(`${API_BASE}/api/v1/logout`, {}, { withCredentials: true });
      setUser(null);
      alert('로그아웃되었습니다.');
      navigate('/');
    } catch (error) {
      console.error('로그아웃 실패:', error);
      alert('로그아웃 중 오류가 발생했습니다. 다시 시도해주세요.');
    }
  };

  const handleForceLogout = async () => {
    try {
      await axios.post(`${API_BASE}/api/v1/force-logout`, {}, { withCredentials: true });
      setUser(null);
      alert('강제 로그아웃 처리되었습니다.');
      navigate('/');
    } catch (error) {
      console.error('강제 로그아웃 실패:', error);
      alert('강제 로그아웃 중 오류가 발생했습니다.');
    }
  };

  const toggleDrawer = (open) => (event) => {
    if (event && event.type === 'keydown' && (event.key === 'Tab' || event.key === 'Shift')) return;
    setDrawerOpen(open);
  };

  return (
    <>
      <AppBar
        position="fixed"
        className="header"
        sx={{
          backgroundColor: '#fff',
          color: '#000',
          width: '100%',
          left: 0,
          right: 0,
          maxWidth: '100vw',
          boxSizing: 'border-box',
          borderBottom: '1px solid #eee'
        }}
      >
        <Toolbar
          className="header__toolbar"
          sx={{
            height: { xs: '70px', sm: '74px', md: '80px', lg: '100px' },
            minHeight: { xs: '70px', sm: '74px', md: '80px', lg: '100px' },
            px: { xs: 1.5, sm: 2, md: 3 },
            width: '100%',
            maxWidth: '100%',
            boxSizing: 'border-box'
          }}
        >
          {/* 왼쪽: 메뉴 + 로고 */}
          <Box
            className="header__left"
            sx={{
              display: 'flex', alignItems: 'center', height: '100%',
              gap: { xs: 0.5, sm: 1 }, flexShrink: 0, zIndex: 2
            }}
          >
            <IconButton edge="start" className="header__icon-button" onClick={toggleDrawer(true)} sx={{ color: '#000', p: { xs: 0.5, sm: 0.75, md: 1 } }}>
              <MenuIcon sx={{ fontSize: { xs: '1.4rem', sm: '1.5rem', md: '1.6rem' } }} />
            </IconButton>

            <Box onClick={() => navigate('/')} sx={{ display: 'flex', alignItems: 'center', cursor: 'pointer', height: '100%', width: { xs: '70px', sm: '90px', md: '110px', lg: '130px' }, flexShrink: 0 }}>
              <Box
                component="img"
                src="/WhereWeGo.PNG"
                alt="Where We Go 로고"
                sx={{ height: { xs: '38px', sm: '48px', md: '65px', lg: '80px' }, width: '100%', maxHeight: '100%', objectFit: 'contain' }}
              />
            </Box>
          </Box>

          {/* 중앙: (검색 제거로 비워둠) */}
          <Box sx={{ flex: 1 }} />

          {/* 오른쪽: 위시리스트 + 로그인/프로필 */}
          <Box
            className="header__right"
            sx={{
              display: 'flex', alignItems: 'center',
              gap: { xs: 0.3, sm: 0.5, md: 1 }, flexShrink: 0, ml: 'auto', zIndex: 2
            }}
          >
            <IconButton className="header__icon-button" onClick={() => navigate('/wishlist')} sx={{ color: '#000', p: { xs: 0.3, sm: 0.4, md: 0.6 } }}>
              <FavoriteBorderIcon sx={{ fontSize: { xs: '1.2rem', sm: '1.3rem', md: '1.4rem', lg: '1.5rem' } }} />
            </IconButton>

            {user ? (
              <IconButton className="header__icon-button" sx={{ color: '#000', p: { xs: 0.2, sm: 0.3, md: 0.4 } }} onClick={toggleDrawer(true)}>
                <Avatar src={user.picture} alt={user.name} sx={{ width: { xs: 24, sm: 28, md: 32, lg: 36 }, height: { xs: 24, sm: 28, md: 32, lg: 36 } }} />
              </IconButton>
            ) : (
              <IconButton className="header__icon-button" sx={{ color: '#000', p: { xs: 0.3, sm: 0.4, md: 0.6 } }} onClick={toggleDrawer(true)}>
                <PersonOutlineIcon sx={{ fontSize: { xs: '1.2rem', sm: '1.3rem', md: '1.4rem', lg: '1.5rem' } }} />
              </IconButton>
            )}
          </Box>
        </Toolbar>
      </AppBar>

      {/* 좌측 드로어 */}
      <Drawer anchor="left" open={drawerOpen} onClose={toggleDrawer(false)}>
        <Box sx={{ width: 280, color: '#000' }} role="presentation" onKeyDown={toggleDrawer(false)}>
          <Box sx={{ display: 'flex', alignItems: 'center', p: 2, gap: 1 }}>
            {user ? (
              <>
                <Avatar src={user.picture} alt={user.name} />
                <Typography variant="body1" noWrap>{user.name}</Typography>
                <Box sx={{ ml: 'auto', display: 'flex', gap: 1 }}>
                  <Button onClick={handleLogout} size="small" variant="outlined">로그아웃</Button>
                  <Button onClick={handleForceLogout} size="small" variant="text">강제</Button>
                </Box>
              </>
            ) : (
              <>
                <Avatar sx={{ backgroundColor: '#ccc' }} />
                <Typography variant="body1">로그인</Typography>
                <Box sx={{ ml: 'auto', display: 'flex', gap: 1 }}>
                  <Button onClick={handleGoogleLogin} size="small" variant="outlined">Google</Button>
                  <Button onClick={handleKakaoLogin} size="small" variant="outlined">Kakao</Button>
                </Box>
              </>
            )}
          </Box>

          <Divider />

          {/* 카테고리 */}
          <Typography variant="subtitle1" sx={{ p: 2 }}>카테고리</Typography>
          <List sx={{ pt: 0 }}>
            {categoryList.map((item) => (
              <ListItemButton
                key={item.label}
                onClick={() => {
                  setDrawerOpen(false);
                  onSelectCategory(item.label);
                  navigate(`/category/${encodeURIComponent(item.label)}`);
                }}
                sx={{ px: 2, py: 1, '&:hover': { backgroundColor: '#f5f5f5' } }}
              >
                <ListItemIcon sx={{ color: '#000', minWidth: 36 }}>{item.icon}</ListItemIcon>
                <ListItemText primary={item.label} />
              </ListItemButton>
            ))}
          </List>

          <Divider />

          {/* 주요 서비스 (관광지 추가만 표시) */}
          <Typography variant="subtitle1" sx={{ p: 2 }}>주요 서비스</Typography>
          <List sx={{ pt: 0 }}>
            {serviceList.map((item) => (
              <ListItemButton
                key={item.label}
                onClick={() => {
                  setDrawerOpen(false);
                  if (item.action === 'add-tourist') setAddTouristFormOpen(true);
                }}
                sx={{ px: 2, py: 1, '&:hover': { backgroundColor: '#f5f5f5' } }}
              >
                <ListItemIcon sx={{ color: '#000', minWidth: 36 }}>{item.icon}</ListItemIcon>
                <ListItemText primary={item.label} />
              </ListItemButton>
            ))}
          </List>
        </Box>
      </Drawer>

      {/* 관광지 추가 폼 */}
      <AddTouristSpotForm
        open={addTouristFormOpen}
        onClose={() => setAddTouristFormOpen(false)}
      />
    </>
  );
};

export default Header;
