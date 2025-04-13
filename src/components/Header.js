// src/components/Header.js
import React, { useState } from 'react';
import {
  AppBar, Toolbar, Typography, IconButton, Box, Drawer, List, ListItem,
  ListItemIcon, ListItemText, Divider, Avatar, TextField, InputAdornment
} from '@mui/material';
import MenuIcon from '@mui/icons-material/Menu';
import SearchIcon from '@mui/icons-material/Search';
import PersonOutlineIcon from '@mui/icons-material/PersonOutline';
import FavoriteBorderIcon from '@mui/icons-material/FavoriteBorder';
import PublicIcon from '@mui/icons-material/Public';
import TerrainIcon from '@mui/icons-material/Terrain';
import AccountBalanceIcon from '@mui/icons-material/AccountBalance';
import LocationOnIcon from '@mui/icons-material/LocationOn';
import EmojiEventsIcon from '@mui/icons-material/EmojiEvents';
import CelebrationIcon from '@mui/icons-material/Celebration';
import CottageIcon from '@mui/icons-material/Cottage';
import ParkIcon from '@mui/icons-material/Park';
import StarBorderIcon from '@mui/icons-material/StarBorder';
import { useNavigate } from 'react-router-dom';
import './Header.scss';

const Header = ({ onSelectCategory = () => {} }) => {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [filteredSpots, setFilteredSpots] = useState([]);
  const [isFocused, setIsFocused] = useState(false);
  const [recentSearches, setRecentSearches] = useState(() => {
    const saved = localStorage.getItem('recentSearches');
    return saved ? JSON.parse(saved) : ['해운대', '광안리', '감천문화마을'];
  });
  const navigate = useNavigate();

  

  const handleSearchChange = (e) => {
  setSearchTerm(e.target.value);
};

  const performSearch = () => {
    if (searchTerm.trim()) {
      setRecentSearches(prev => {
      const updated = [searchTerm, ...prev.filter(s => s !== searchTerm)].slice(0, 5);
      localStorage.setItem('recentSearches', JSON.stringify(updated));
      return updated;
    });
    }
  };

  const handleSpotSelect = (spot) => {
    setRecentSearches(prev => {
      const updated = [spot, ...prev.filter(s => s !== spot)].slice(0, 5);
      localStorage.setItem('recentSearches', JSON.stringify(updated));
      return updated;
    });
    navigate(`/search?query=${encodeURIComponent(spot)}`);
  };

  const toggleDrawer = (open) => (event) => {
    if (event && event.type === 'keydown' && (event.key === 'Tab' || event.key === 'Shift')) return;
    setDrawerOpen(open);
  };

  const categoryList = [
    { label: '자연/해변', icon: <TerrainIcon /> },
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

  return (
    <>
      <AppBar position="fixed" className="header">
        <Toolbar className="header__toolbar">
          <Box className="header__left" sx={{ display: 'flex', alignItems: 'center' , color: '#000' }}>
            <IconButton edge="start" className="header__icon-button" onClick={toggleDrawer(true)}>
              <MenuIcon />
            </IconButton>
            <Typography
              variant="h4"
              className="header__logo"
              onClick={() => navigate('/')}
              sx={{ cursor: 'pointer', fontFamily: 'Jua', color: '#fff' , color: '#000' }}
            >
              부산 투어
            </Typography>
          </Box>
          <Box className="header__center" sx={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', position: 'relative' , color: '#000' }}>
            <TextField
              placeholder="관광지를 검색해보세요"
              variant="outlined"
              size="small"
              className="header__search"
              value={searchTerm}
              onChange={handleSearchChange}
              onFocus={() => setIsFocused(true)}
              onBlur={() => setTimeout(() => setIsFocused(false), 200)}
              onKeyDown={(e) => e.key === 'Enter' && performSearch()}
              InputProps={{
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton onClick={performSearch}>
                      <SearchIcon />
                    </IconButton>
                  </InputAdornment>
                ),
              }}
              sx={{ width: '300px', backgroundColor: '#fff', borderRadius: 1 , color: '#000' }}
            />
            {isFocused && (
              <Box sx={{ position: 'absolute', top: '40px', width: '300px', backgroundColor: '#fff', border: '1px solid #ccc', borderRadius: 1, boxShadow: 2, zIndex: 1000 , color: '#000' }}>
                {searchTerm ? (
                  <Box
                    onMouseDown={(e) => e.preventDefault()}
                    onClick={() => handleSpotSelect(searchTerm)}
                    sx={{ px: 2, py: 1, cursor: 'pointer', color: '#000', '&:hover': { backgroundColor: '#f0f0f0' } }}
                  >
                    "{searchTerm} 검색"
                  </Box>
                ) : (!searchTerm && recentSearches.length > 0) ? (
                  recentSearches.map((spot, i) => (
                    <Box
                      key={i}
                      onMouseDown={(e) => e.preventDefault()}
                      onClick={() => handleSpotSelect(spot)}
                      sx={{ px: 2, py: 1, cursor: 'pointer', color: '#000', '&:hover': { backgroundColor: '#f0f0f0' } }}

                    >
                      {spot}
                    </Box>
                  ))
                ) : null}
              </Box>
            )}
          </Box>
          <Box className="header__right">
            <IconButton className="header__icon-button"><PublicIcon /></IconButton>
            <IconButton className="header__icon-button" onClick={() => navigate('/wishlist')}><FavoriteBorderIcon /></IconButton>
            <IconButton className="header__icon-button"><PersonOutlineIcon /></IconButton>
          </Box>
        </Toolbar>
      </AppBar>

      <Drawer anchor="left" open={drawerOpen} onClose={toggleDrawer(false)}>
        <Box sx={{ width: 250 , color: '#000' }} role="presentation" onKeyDown={toggleDrawer(false)}>
          <Box sx={{ display: 'flex', alignItems: 'center', padding: '16px' , color: '#000' }}>
            <Avatar sx={{ marginRight: '8px' , color: '#000' }} />
            <Typography variant="body1">로그인</Typography>
          </Box>
          <Divider />
          <Typography variant="subtitle1" sx={{ p: 2 , color: '#000' }}>카테고리</Typography>
          <List>
            {categoryList.map((item) => (
              <ListItem
                button
                key={item.label}
                onClick={() => {
                  setDrawerOpen(false);
                  onSelectCategory(item.label);
                  navigate('/category');
                }}
                sx={{ px: 2, py: 1, cursor: 'pointer', color: '#000', '&:hover': { backgroundColor: '#f0f0f0' } }}

              >
                <ListItemIcon>{item.icon}</ListItemIcon>
                <ListItemText primary={item.label} />
              </ListItem>
            ))}
          </List>
          <Divider />
          <Typography variant="subtitle1" sx={{ p: 2 , color: '#000' }}>주요 서비스</Typography>
          <List>
            {serviceList.map((item) => (
              <ListItem button key={item.label} onClick={toggleDrawer(false)} sx={{ px: 2, py: 1, cursor: 'pointer', color: '#000', '&:hover': { backgroundColor: '#f0f0f0' } }}
>
                <ListItemIcon>{item.icon}</ListItemIcon>
                <ListItemText primary={item.label} />
              </ListItem>
            ))}
          </List>
        </Box>
      </Drawer>
    </>
  );
};

export default Header;
