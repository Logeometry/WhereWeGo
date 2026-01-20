// src/components/AddTouristSpotForm.js
import React, { useState } from 'react';
import {
  Dialog, DialogTitle, DialogContent, DialogActions, TextField, Button, Box, Typography,
  FormControl, InputLabel, Select, MenuItem, Chip, Alert, CircularProgress, Paper,
  IconButton, Grid
} from '@mui/material';
import {
  CloudUpload as CloudUploadIcon,
  Close as CloseIcon,
  PhotoCamera as PhotoCameraIcon,
  Delete as DeleteIcon
} from '@mui/icons-material';

// ---- API BASE: 환경변수 우선, 없으면 Vite 변수들, 없으면 현재 origin ----
const RAW_BASE =
  process.env.REACT_APP_API_PREFIX ||
  (typeof import.meta !== 'undefined' &&
    import.meta.env &&
    (import.meta.env.VITE_API_PREFIX || import.meta.env.VITE_API_BASE_URL)) ||
  window.location.origin;

const API_BASE = RAW_BASE.replace(/\/$/, ''); // 끝 슬래시 제거
const API_V1 = `${API_BASE}/api/v1`;

// 여러 후보 URL을 순서대로 시도 (프록시 사용시 /api/v1 도 동작하게)
async function tryPost(urls, formData) {
  let lastErr = null;
  for (const url of urls) {
    try {
      const res = await fetch(url, {
        method: 'POST',
        // multipart/form-data는 Content-Type을 직접 설정하지 말 것!
        body: formData,
        credentials: 'include', // 세션 사용하는 백엔드라면 유지, 필요 없으면 'omit'
      });
      if (!res.ok) {
        // 응답을 텍스트/JSON 시도해서 의미있는 에러 표시
        let detail = '';
        try {
          const maybeJson = await res.json();
          detail = maybeJson?.detail || maybeJson?.message || '';
        } catch {
          try { detail = await res.text(); } catch {}
        }
        const err = new Error(`HTTP ${res.status}${detail ? `: ${detail}` : ''}`);
        err.status = res.status;
        throw err;
      }
      return await res.json();
    } catch (e) {
      lastErr = e;
    }
  }
  throw lastErr || new Error('업로드 엔드포인트를 찾지 못했습니다.');
}

const AddTouristSpotForm = ({ open, onClose }) => {
  const [formData, setFormData] = useState({
    name: '',
    category: '',
    description: '',
    address: '',
    userEmail: '',
    userName: ''
  });

  const [images, setImages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [dragActive, setDragActive] = useState(false);

  const categories = [
    '공연관람', '예술 감상', '관람및체험', '자연산림',
    '자연풍경', '테마거리', '트레킹', '휴양'
  ];

  const handleInputChange = (field) => (event) => {
    setFormData(prev => ({ ...prev, [field]: event.target.value }));
    setError('');
  };

  const handleImageUpload = (files) => {
    const fileArray = Array.from(files);
    const validFiles = fileArray.filter(file => {
      const isValidType = file.type.startsWith('image/');
      const isValidSize = file.size <= 10 * 1024 * 1024; // 10MB
      return isValidType && isValidSize;
    });

    if (validFiles.length !== fileArray.length) {
      setError('일부 파일이 유효하지 않습니다. 이미지 파일만 업로드 가능하며, 파일 크기는 10MB 이하여야 합니다.');
    }

    const newImages = validFiles.map(file => ({
      file,
      preview: URL.createObjectURL(file),
      id: Date.now() + Math.random()
    }));

    setImages(prev => [...prev, ...newImages].slice(0, 5)); // 최대 5개
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') setDragActive(true);
    else if (e.type === 'dragleave') setDragActive(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleImageUpload(e.dataTransfer.files);
    }
  };

  const removeImage = (imageId) => {
    setImages(prev => {
      const updated = prev.filter(img => img.id !== imageId);
      const removed = prev.find(img => img.id === imageId);
      if (removed) URL.revokeObjectURL(removed.preview);
      return updated;
    });
  };

  const handleSubmit = async () => {
    if (!formData.name.trim()) {
      setError('관광지 이름을 입력해주세요.');
      return;
    }
    if (images.length === 0) {
      setError('최소 1개의 이미지를 업로드해주세요.');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const fd = new FormData();
      fd.append('name', formData.name);
      fd.append('category', formData.category);
      fd.append('description', formData.description);
      fd.append('address', formData.address);
      fd.append('user_email', formData.userEmail);
      fd.append('user_name', formData.userName);
      images.forEach(img => fd.append('images', img.file));

      // 후보 엔드포인트 (환경/프록시 모두 대응)
      const urls = [
        `${API_V1}/tourist-requests/submit`,
        `${API_BASE}/api/v1/tourist-requests/submit`,
        `${window.location.origin.replace(/\/$/, '')}/api/v1/tourist-requests/submit`,
      ];

      const result = await tryPost(urls, fd);
      console.log('등록 성공:', result);
      setSuccess(true);

      // 2초 후 폼 리셋 및 닫기
      setTimeout(() => { handleClose(); }, 2000);
    } catch (err) {
      console.error('등록 오류:', err);
      setError(err.message || '등록 요청 중 오류가 발생했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    images.forEach(image => URL.revokeObjectURL(image.preview));
    setFormData({
      name: '',
      category: '',
      description: '',
      address: '',
      userEmail: '',
      userName: ''
    });
    setImages([]);
    setError('');
    setSuccess(false);
    setLoading(false);
    onClose();
  };

  if (success) {
    return (
      <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
        <DialogContent sx={{ textAlign: 'center', py: 4 }}>
          <Typography variant="h5" color="primary" gutterBottom>
            🎉 등록 요청 완료!
          </Typography>
          <Typography variant="body1" color="text.secondary">
            관광지 등록 요청이 성공적으로 제출되었습니다.
            <br />
            검토 후 승인되면 사이트에 표시됩니다.
          </Typography>
        </DialogContent>
      </Dialog>
    );
  }

  return (
    <Dialog
      open={open}
      onClose={handleClose}
      maxWidth="md"
      fullWidth
      PaperProps={{ sx: { borderRadius: 2 } }}
    >
      <DialogTitle sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', pb: 1 }}>
        <Typography variant="h5" component="span" fontWeight="bold">
          새로운 관광지 등록
        </Typography>
        <IconButton onClick={handleClose} size="small">
          <CloseIcon />
        </IconButton>
      </DialogTitle>

      <DialogContent dividers>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
          {error && (
            <Alert severity="error" onClose={() => setError('')}>
              {error}
            </Alert>
          )}

          {/* 이미지 업로드 */}
          <Box>
            <Typography variant="h6" gutterBottom>
              이미지 업로드 <Chip label="필수" size="small" color="error" />
            </Typography>

            <Paper
              sx={{
                border: `2px dashed ${dragActive ? '#1976d2' : '#ccc'}`,
                borderRadius: 2,
                p: 3,
                textAlign: 'center',
                backgroundColor: dragActive ? '#f3f7ff' : '#fafafa',
                cursor: 'pointer',
                transition: 'all 0.3s ease',
                '&:hover': { borderColor: '#1976d2', backgroundColor: '#f3f7ff' }
              }}
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
              onClick={() => document.getElementById('image-upload-input').click()}
            >
              <CloudUploadIcon sx={{ fontSize: 48, color: '#666', mb: 1 }} />
              <Typography variant="body1" gutterBottom>
                이미지를 드래그하여 업로드하거나 클릭하여 선택하세요
              </Typography>
              <Typography variant="caption" color="text.secondary">
                최대 5개, 각 파일 10MB 이하 (JPG, PNG, GIF)
              </Typography>
              <input
                id="image-upload-input"
                type="file"
                multiple
                accept="image/*"
                style={{ display: 'none' }}
                onChange={(e) => handleImageUpload(e.target.files)}
              />
            </Paper>

            {images.length > 0 && (
              <Grid container spacing={2} sx={{ mt: 2 }}>
                {images.map((image) => (
                  <Grid item xs={6} sm={4} md={3} key={image.id}>
                    <Paper sx={{ position: 'relative', borderRadius: 1, overflow: 'hidden' }}>
                      <img
                        src={image.preview}
                        alt="미리보기"
                        style={{ width: '100%', height: '120px', objectFit: 'cover' }}
                      />
                      <IconButton
                        sx={{
                          position: 'absolute',
                          top: 4,
                          right: 4,
                          backgroundColor: 'rgba(255,255,255,0.8)',
                          '&:hover': { backgroundColor: 'rgba(255,255,255,0.9)' }
                        }}
                        size="small"
                        onClick={(e) => {
                          e.stopPropagation();
                          removeImage(image.id);
                        }}
                      >
                        <DeleteIcon fontSize="small" />
                      </IconButton>
                    </Paper>
                  </Grid>
                ))}
              </Grid>
            )}
          </Box>

          {/* 기본 정보 */}
          <TextField
            label="관광지 이름"
            value={formData.name}
            onChange={handleInputChange('name')}
            required
            fullWidth
            placeholder="예: 해운대 해수욕장"
          />

          <FormControl fullWidth>
            <InputLabel>카테고리</InputLabel>
            <Select
              value={formData.category}
              onChange={handleInputChange('category')}
              label="카테고리"
            >
              {categories.map((category) => (
                <MenuItem key={category} value={category}>
                  {category}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <TextField
            label="상세 설명"
            value={formData.description}
            onChange={handleInputChange('description')}
            multiline
            rows={4}
            fullWidth
            placeholder="관광지에 대한 자세한 설명을 입력해주세요..."
          />

          <TextField
            label="주소"
            value={formData.address}
            onChange={handleInputChange('address')}
            fullWidth
            placeholder="예: 부산광역시 해운대구 해운대해변로 264"
          />

          {/* 사용자 정보 (선택) */}
          <Box>
            <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>
              연락처 정보 (선택사항)
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6}>
                <TextField
                  label="이름"
                  value={formData.userName}
                  onChange={handleInputChange('userName')}
                  fullWidth
                  placeholder="등록자 이름"
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  label="이메일"
                  type="email"
                  value={formData.userEmail}
                  onChange={handleInputChange('userEmail')}
                  fullWidth
                  placeholder="example@email.com"
                />
              </Grid>
            </Grid>
          </Box>
        </Box>
      </DialogContent>

      <DialogActions sx={{ p: 3, gap: 1 }}>
        <Button onClick={handleClose} variant="outlined" disabled={loading}>
          취소
        </Button>
        <Button
          onClick={handleSubmit}
          variant="contained"
          disabled={loading || !formData.name.trim() || images.length === 0}
          startIcon={loading ? <CircularProgress size={20} /> : <PhotoCameraIcon />}
        >
          {loading ? '등록 중...' : '등록 요청'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default AddTouristSpotForm;
