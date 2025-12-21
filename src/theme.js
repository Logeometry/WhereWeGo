import { createTheme } from '@mui/material/styles';

const theme = createTheme({
  palette: {
    primary: {
      main: '#ff1150', // 모든 primary 색상이 이 색상으로 통일됩니다.
    },
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none', // 대문자 변환 해제
          borderRadius: 30, // 둥근 모서리
          fontWeight: 'bold',
          transition: '0.3s',
        },
        containedPrimary: {
          backgroundColor: '#ff1150',
          color: '#fff',
          '&:hover': {
            backgroundColor: '#ff6f61',
          },
        },
        outlinedPrimary: {
          borderColor: '#ff1150',
          color: '#ff1150',
          '&:hover': {
            borderColor: '#ff6f61',
            color: '#ff6f61',
          },
        },
        textPrimary: {
          color: '#ff1150',
          '&:hover': {
            backgroundColor: 'rgba(255, 17, 80, 0.08)',
          },
        },
      },
    },
  },
});

export default theme;
