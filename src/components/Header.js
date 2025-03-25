import React from 'react';
import {
  AppBar,
  Toolbar,
  Typography,
  IconButton,
  Box,
  TextField,
  InputAdornment,
} from '@mui/material';
import MenuIcon from '@mui/icons-material/Menu';
import SearchIcon from '@mui/icons-material/Search';
import PersonOutlineIcon from '@mui/icons-material/PersonOutline';
import FavoriteBorderIcon from '@mui/icons-material/FavoriteBorder';
import PublicIcon from '@mui/icons-material/Public';

import './Header.scss';

const Header = () => {
  return (
    <AppBar position="fixed" className="header">
      <Toolbar className="header__toolbar">
        {/* 왼쪽 영역: 햄버거 메뉴 + 로고 */}
        <Box className="header__left">
          <IconButton edge="start" className="header__icon-button">
            <MenuIcon />
          </IconButton>
          <Typography variant="h6" className="header__logo">
            부산 투어
          </Typography>
        </Box>

        {/* 중앙 영역: 검색창 */}
        <Box className="header__center">
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
  );
};

export default Header;
