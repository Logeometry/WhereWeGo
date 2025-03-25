import React from 'react';
import { Box, Typography, Container, Link } from '@mui/material';
import './Footer.scss';

const Footer = () => {
  return (
    <Box className="footer">
      <Container maxWidth="lg">
        <Typography variant="body1" align="center" className="footer__text">
          부산 투어 마켓 © {new Date().getFullYear()} 모든 권리 보유.
        </Typography>
        <Typography variant="body2" align="center" className="footer__links">
          <Link href="#" color="inherit" className="footer__link">이용 약관</Link>
          <Link href="#" color="inherit" className="footer__link">개인정보 처리방침</Link>
          <Link href="#" color="inherit" className="footer__link">고객 센터</Link>
        </Typography>
      </Container>
    </Box>
  );
};

export default Footer;
