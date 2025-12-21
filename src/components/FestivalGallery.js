// src/components/FestivalGallery.jsx
import React, { useEffect, useState } from 'react';
import {
  Grid, Card, CardActionArea, CardContent, CardMedia, Typography,
  Box, Stack, Chip, IconButton, Skeleton, Alert, Tooltip
} from '@mui/material';
import FavoriteBorderIcon from '@mui/icons-material/FavoriteBorder';
import ShareIcon from '@mui/icons-material/Share';
import PlaceIcon from '@mui/icons-material/Place';
import CalendarMonthIcon from '@mui/icons-material/CalendarMonth';
import axios from 'axios';

const API_PREFIX =
  process.env.REACT_APP_API_PREFIX ||
  (typeof import.meta !== "undefined" && import.meta.env && import.meta.env.VITE_API_PREFIX) ||
  "";

function parseDate(yyyymmdd) {
  // "20251024" → "2025.10.24"
  if (!yyyymmdd || String(yyyymmdd).length !== 8) return yyyymmdd || '미정';
  const s = String(yyyymmdd);
  return `${s.slice(0,4)}.${s.slice(4,6)}.${s.slice(6,8)}`;
}

function formatRange(start, end) {
  return `${parseDate(start)} ~ ${parseDate(end)}`;
}

export default function FestivalGallery() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState(null);

  useEffect(() => {
    (async () => {
      try {
        const url = `${API_PREFIX}/api/v1/festival`;
        const res = await axios.get(url);
        const list = res?.data?.festivals ?? [];
        setData(Array.isArray(list) ? list : []);
      } catch (e) {
        setErr(e);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  if (loading) {
    return (
      <Grid container spacing={3}>
        {Array.from({ length: 6 }).map((_, i) => (
          <Grid item xs={12} sm={6} md={4} lg={3} key={`sk-${i}`}>
            <Card sx={{ borderRadius: 3, overflow: 'hidden' }}>
              <Skeleton variant="rectangular" height={200} />
              <Box p={2}>
                <Skeleton variant="text" />
                <Skeleton variant="text" width="60%" />
              </Box>
            </Card>
          </Grid>
        ))}
      </Grid>
    );
  }

  if (err) return <Alert severity="error">축제 목록을 불러오지 못했습니다.</Alert>;
  if (!data.length) return <Alert severity="info">현재 표시할 축제 정보가 없습니다.</Alert>;

  return (
    <Grid container spacing={3}>
      {data.map((f, idx) => {
        const {
          id,
          title = '무제',
          address = '',
          start_date,
          end_date,
          image,
          thumbnail,
          poster,
          link, // 상세 링크가 있으면 사용
        } = f || {};

        const imgSrc = image || thumbnail || poster || '/images/placeholders/festival.jpg';

        return (
          <Grid item xs={12} sm={6} md={4} lg={3} key={id ?? `${title}-${idx}`}>
            <Card
              elevation={0}
              sx={{
                height: '100%',
                borderRadius: 3,
                overflow: 'hidden',
                boxShadow: (theme) => `0 1px 3px rgba(0,0,0,0.12)`,
                transition: 'transform .18s ease, box-shadow .18s ease',
                '&:hover': {
                  transform: 'translateY(-2px)',
                  boxShadow: (theme) => `0 8px 24px rgba(0,0,0,0.18)`,
                },
              }}
            >
              <CardActionArea
                component={link ? 'a' : 'div'}
                href={link || undefined}
                target={link ? '_blank' : undefined}
                rel={link ? 'noreferrer' : undefined}
                sx={{ alignItems: 'stretch' }}
              >
                {/* 이미지 영역: 16:9 비율 고정 + 오버레이 */}
                <Box sx={{ position: 'relative' }}>
                  <CardMedia
                    component="img"
                    image={imgSrc}
                    alt={title}
                    loading="lazy"
                    sx={{
                      aspectRatio: '16 / 9',        // 최신 브라우저용
                      width: '100%',
                      objectFit: 'cover',
                      display: 'block',
                    }}
                    onError={(e) => { e.currentTarget.src = '/images/placeholders/festival.jpg'; }}
                  />
                  {/* 그라데이션 오버레이 + 타이틀 */}
                  <Box
                    sx={{
                      position: 'absolute',
                      inset: 0,
                      background:
                        'linear-gradient(180deg, rgba(0,0,0,0) 40%, rgba(0,0,0,0.6) 100%)',
                      display: 'flex',
                      alignItems: 'flex-end',
                      p: 2,
                    }}
                  >
                    <Typography
                      variant="subtitle1"
                      sx={{
                        color: '#fff',
                        fontWeight: 700,
                        textShadow: '0 1px 2px rgba(0,0,0,0.6)',
                        overflow: 'hidden',
                        whiteSpace: 'nowrap',
                        textOverflow: 'ellipsis',
                        width: '100%',
                      }}
                      title={title}
                    >
                      {title}
                    </Typography>
                  </Box>

                  {/* 우상단 액션버튼 */}
                  <Stack
                    direction="row"
                    spacing={1}
                    sx={{ position: 'absolute', top: 8, right: 8 }}
                  >
                    <Tooltip title="좋아요">
                      <IconButton
                        size="small"
                        sx={{
                          bgcolor: 'rgba(255,255,255,0.9)',
                          '&:hover': { bgcolor: 'rgba(255,255,255,1)' },
                        }}
                        aria-label="좋아요"
                      >
                        <FavoriteBorderIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="공유">
                      <IconButton
                        size="small"
                        sx={{
                          bgcolor: 'rgba(255,255,255,0.9)',
                          '&:hover': { bgcolor: 'rgba(255,255,255,1)' },
                        }}
                        aria-label="공유"
                      >
                        <ShareIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  </Stack>
                </Box>

                {/* 본문 */}
                <CardContent sx={{ pt: 1.5 }}>
                  <Stack spacing={1}>
                    {/* 주소 */}
                    {address && (
                      <Stack direction="row" spacing={0.5} alignItems="center">
                        <PlaceIcon fontSize="small" />
                        <Typography
                          variant="body2"
                          color="text.secondary"
                          sx={{
                            overflow: 'hidden',
                            whiteSpace: 'nowrap',
                            textOverflow: 'ellipsis',
                          }}
                          title={address}
                        >
                          {address}
                        </Typography>
                      </Stack>
                    )}

                    {/* 날짜 칩 */}
                    <Stack direction="row" spacing={1} flexWrap="wrap">
                      <Chip
                        size="small"
                        icon={<CalendarMonthIcon />}
                        label={formatRange(start_date, end_date)}
                        sx={{
                          fontWeight: 600,
                          bgcolor: (theme) => theme.palette.grey[100],
                        }}
                      />
                    </Stack>
                  </Stack>
                </CardContent>
              </CardActionArea>
            </Card>
          </Grid>
        );
      })}
    </Grid>
  );
}
