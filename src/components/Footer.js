import React from 'react';
import { Box, Typography, Container, Link, Stack, useMediaQuery, useTheme } from '@mui/material';
import './Footer.scss';

const Footer = () => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));

  return (
    <Box 
      component="footer"
      className="footer"
      sx={{
        width: '100%',
        maxWidth: '100%',
        backgroundColor: '#2c3e50',
        color: '#ecf0f1',
        py: { xs: 3, sm: 4, md: 5 },
        px: { xs: 1.5, sm: 3, md: 4 },  // 모바일: 12px로 통일
        mt: 'auto',
        overflowX: 'hidden'
      }}
    >
      <Container 
        maxWidth="lg"
        disableGutters
        sx={{
          px: { xs: 0, sm: 0, md: 0 }
        }}
      >
        <Stack
          spacing={{ xs: 2, sm: 2.5, md: 3 }}
          alignItems="center"
        >
          <Typography 
            variant="body1" 
            align="center" 
            className="footer__text"
            sx={{
              fontSize: { xs: '0.875rem', sm: '1rem', md: '1.125rem' },
              fontWeight: 500,
              letterSpacing: '0.5px'
            }}
          >
            부산 투어 마켓 © {new Date().getFullYear()} 모든 권리 보유.
          </Typography>
          
          <Stack
            direction={{ xs: 'column', sm: 'row' }}
            spacing={{ xs: 1.5, sm: 3, md: 4 }}
            alignItems="center"
            justifyContent="center"
            className="footer__links"
          >
            <Link 
              href="#" 
              color="inherit" 
              underline="hover"
              className="footer__link"
              sx={{
                fontSize: { xs: '0.813rem', sm: '0.875rem', md: '0.938rem' },
                transition: 'color 0.2s ease',
                '&:hover': {
                  color: '#3498db'
                }
              }}
            >
              이용 약관
            </Link>
            <Link 
              href="#" 
              color="inherit" 
              underline="hover"
              className="footer__link"
              sx={{
                fontSize: { xs: '0.813rem', sm: '0.875rem', md: '0.938rem' },
                transition: 'color 0.2s ease',
                '&:hover': {
                  color: '#3498db'
                }
              }}
            >
              개인정보 처리방침
            </Link>
            <Link 
              href="#" 
              color="inherit" 
              underline="hover"
              className="footer__link"
              sx={{
                fontSize: { xs: '0.813rem', sm: '0.875rem', md: '0.938rem' },
                transition: 'color 0.2s ease',
                '&:hover': {
                  color: '#3498db'
                }
              }}
            >
              고객 센터
            </Link>
          </Stack>
          
          <Typography 
            variant="caption" 
            align="center"
            sx={{
              fontSize: { xs: '0.688rem', sm: '0.75rem', md: '0.813rem' },
              opacity: 0.8,
              mt: { xs: 1, sm: 1.5 }
            }}
          >
            부산광역시 | 대표: WhereWeGo | 사업자등록번호: 000-00-00000
          </Typography>
        </Stack>
      </Container>
    </Box>
  );
};

export default Footer;
