// src/components/Header.js
import React, { useState, useEffect, useRef, useContext } from 'react';
import {
  AppBar, Toolbar, Typography, IconButton, Box, Drawer, List, ListItem,
  ListItemIcon, ListItemText, Divider, Avatar, TextField, InputAdornment, Button, Image
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
import CloseIcon from '@mui/icons-material/Close';
import { useNavigate, useLocation } from 'react-router-dom';
import './Header.scss';
import { SearchContext } from '../SearchContext';
import logoImage from '../assets/Logo.png';

const Header = ({ onSelectCategory = () => { } }) => {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  const { recentSearches, updateSearches, removeSearch, clearAllSearches } = useContext(SearchContext);

  const handleRemoveSearch = (index) => {
    removeSearch(index);
  };

  const handleSpotSelect = (spot) => {
    updateSearches(spot);
    navigate(`/search?query=${encodeURIComponent(spot)}`);
    setIsDropdownOpen(false);
  };

  const handleSearchChange = (e) => {
    setSearchTerm(e.target.value);
  };

  const performSearch = () => {
    if (searchTerm.trim()) {
      updateSearches(searchTerm.trim());
      navigate(`/search?query=${encodeURIComponent(searchTerm.trim())}`);
      setSearchTerm('');
      setIsDropdownOpen(false);
    }
  };

  const handleClearAll = () => {
    clearAllSearches();
  };

  const toggleDrawer = (open) => (event) => {
    if (event && event.type === 'keydown' && (event.key === 'Tab' || event.key === 'Shift')) return;
    setDrawerOpen(open);
  };

  useEffect(() => {
    setIsDropdownOpen(false);
  }, [location.pathname]);

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

  const liveKeywords = [
    '해운대', '광안리', '감천문화마을', '태종대', '자갈치시장',
    '부산타워', '부산시민공원', '이기대공원', '송정해수욕장', '영도다리'
  ];

  const renderSearchDropdown = () => {
    if (!isDropdownOpen) return null;
    console.log('[Header] Rendering 통합된 검색 드롭다운. Recent searches:', recentSearches, 'Live keywords:', liveKeywords);

    return (
      <Box sx={{
        position: 'absolute',
        top: '40px',
        width: '600px',
        backgroundColor: '#fff',
        border: '1px solid #ccc',
        borderRadius: 1,
        boxShadow: 2,
        zIndex: 1000,
        color: '#000',
        maxHeight: '400px',
        overflowY: 'auto',
      }}>
        {recentSearches.length > 0 && (
          <Box sx={{ p: 1, borderBottom: '1px solid #eee' }}>
            <Typography fontWeight="bold" fontSize={14} mb={1}>최근 검색어</Typography>
            {recentSearches.map((spot, i) => (
              <Box
                key={`recent-${i}-${spot}`}
                onMouseDown={(e) => e.preventDefault()}
                onClick={() => handleSpotSelect(spot)}
                sx={{ px: 2, py: 1, display: 'flex', alignItems: 'center', cursor: 'pointer', '&:hover': { backgroundColor: '#f0f0f0' } }}
              >
                <SearchIcon fontSize="small" sx={{ mr: 1 }} />
                <Typography variant="body2" sx={{ flexGrow: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{spot}</Typography>
                <IconButton size="small" onClick={(e) => { e.stopPropagation(); handleRemoveSearch(i); }} sx={{ ml: 1 }}>
                  <CloseIcon fontSize="small" />
                </IconButton>
              </Box>
            ))}
            <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 1 }}>
              <Button onClick={handleClearAll} size="small">전체삭제</Button>
            </Box>
          </Box>
        )}

        {liveKeywords.length > 0 && (
          <Box sx={{ p: 1 }}>
            <Typography fontWeight="bold" fontSize={14} mb={1}>실시간 인기 검색어</Typography>
            {liveKeywords.map((keyword, index) => (
              <Box
                key={`live-${index}-${keyword}`}
                onClick={() => handleSpotSelect(keyword)}
                sx={{ px: 2, py: 1, display: 'flex', alignItems: 'center', cursor: 'pointer', '&:hover': { backgroundColor: '#f0f0f0' } }}
              >
                <Typography variant="body2" sx={{ width: 20 }}>{index + 1}</Typography>
                <Typography variant="body2" sx={{ flexGrow: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', ml: 1 }}>{keyword}</Typography>
                <Typography variant="body2" sx={{ color: index % 2 === 0 ? 'red' : 'blue', ml: 1 }}>
                  {index % 2 === 0 ? '▲' : '▼'}
                </Typography>
              </Box>
            ))}
          </Box>
        )}

        {recentSearches.length === 0 && liveKeywords.length === 0 && (
          <Box sx={{ p: 2, color: '#777', textAlign: 'center' }}>
            검색 기록 또는 실시간 인기 검색어가 없습니다.
          </Box>
        )}
      </Box>
    );
  };

  return (
    <>
      <AppBar position="fixed" className="header" sx={{ backgroundColor: '#fff', color: '#000' }}>
        <Toolbar className="header__toolbar">
          <Box className="header__left" sx={{ display: 'flex', alignItems: 'center' }}>
            <IconButton edge="start" className="header__icon-button" onClick={toggleDrawer(true)} sx={{ color: '#000' }}>
              <MenuIcon />
            </IconButton>
            <Box
              onClick={() => navigate('/')}
              sx={{ display: 'flex', alignItems: 'center', cursor: 'pointer', ml: 1 }} // 햄버거 버튼과의 간격 추가
            >
              <img src={logoImage} alt="Where We Go 로고" style={{ marginRight: '8px', height: '30px' }} />
              <Typography
                variant="h4"
                className="header__logo"
                sx={{ fontFamily: 'Jua', color: '#000' }}
              >
                Where We Go
              </Typography>
            </Box>
          </Box>

          <Box className="header__center" sx={{ flex: 1, display: 'flex', justifyContent: 'center', position: 'relative' }}>
            <TextField
              placeholder="관광지를 검색해보세요"
              variant="outlined"
              size="small"
              className="header__search"
              value={searchTerm}
              onChange={handleSearchChange}
              onFocus={() => { console.log('[Header] Search focused.'); setIsDropdownOpen(true); }}
              onBlur={() => setTimeout(() => { console.log('[Header] Search blur triggered.'); setIsDropdownOpen(false); }, 200)}
              onKeyDown={(e) => e.key === 'Enter' && performSearch()}
              autoComplete="off"
              InputProps={{
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton onClick={performSearch} sx={{ color: '#000' }}>
                      <SearchIcon />
                    </IconButton>
                  </InputAdornment>
                ),
              }}
              sx={{
                width: '300px',
                backgroundColor: '#fff',
                borderRadius: 1,
                '& .MuiOutlinedInput-root': {
                  '& fieldset': {
                    borderColor: '#ccc',
                  },
                  '&:hover fieldset': {
                    borderColor: '#aaa',
                  },
                  '&.Mui-focused fieldset': {
                    borderColor: theme => theme.palette.primary.main,
                  },
                },
                '& .MuiInputBase-input': {
                  color: '#000',
                }
              }}
            />
            {renderSearchDropdown()} {/* 조건 제거 */}
          </Box>

          <Box className="header__right">
            <IconButton className="header__icon-button" sx={{ color: '#000' }}><PublicIcon /></IconButton>
            <IconButton className="header__icon-button" onClick={() => navigate('/wishlist')} sx={{ color: '#000' }}><FavoriteBorderIcon /></IconButton>
            <IconButton className="header__icon-button" sx={{ color: '#000' }}><PersonOutlineIcon /></IconButton>
          </Box>
        </Toolbar>
      </AppBar>

      <Drawer anchor="left" open={drawerOpen} onClose={toggleDrawer(false)}>
        <Box sx={{ width: 250, color: '#000' }} role="presentation" onKeyDown={toggleDrawer(false)}>
          <Box sx={{ display: 'flex', alignItems: 'center', padding: '16px' }}>
            <Avatar sx={{ marginRight: '8px', backgroundColor: '#ccc' }} />
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
                  setDrawerOpen(false);
                  onSelectCategory(item.label);
                  navigate('/category');
                }}
                sx={{ px: 2, py: 1, cursor: 'pointer', '&:hover': { backgroundColor: '#f0f0f0' } }}
              >
                <ListItemIcon sx={{ color: '#000' }}>{item.icon}</ListItemIcon>
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
                sx={{ px: 2, py: 1, cursor: 'pointer', '&:hover': { backgroundColor: '#f0f0f0' } }}
              >
                <ListItemIcon sx={{ color: '#000' }}>{item.icon}</ListItemIcon>
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