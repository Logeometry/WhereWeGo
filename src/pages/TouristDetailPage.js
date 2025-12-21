// src/pages/TouristDetailPage.js
import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft, MapPin, Clock, Phone, Globe, Navigation, Star, Heart,
  Camera, DollarSign, Coffee, ChevronDown, Share2, Play, Wifi, X, Users,
} from 'lucide-react';
import { useWishlist } from '../contexts/WishlistContext';
import { getPlaceById, getAttractionCrowdingByName } from '../api/category';
import './TouristDetailPage.scss';

// BASE 도메인 (/api/v1 는 개별 호출에서 붙임)
const RAW_BASE =
  process.env.REACT_APP_API_PREFIX ||
  (typeof import.meta !== 'undefined' &&
    import.meta.env &&
    (import.meta.env.VITE_API_PREFIX || import.meta.env.VITE_API_BASE_URL)) ||
  window.location.origin;

const API_BASE = RAW_BASE.replace(/\/$/, '');
const API_V1 = `${API_BASE}/api/v1`;

// 샘플 데이터(폴백)
const busanSampleData = [
  {
    _id: 'busan-beach-001',
    name: '해운대 해수욕장',
    category: '해변/바다',
    description:
      '부산의 대표적인 해수욕장으로, 아름다운 백사장과 맑은 바다로 유명합니다. 다양한 수상 스포츠와 해변 활동을 즐길 수 있으며, 주변에는 맛집과 카페들이 즐비해 있어 관광객들에게 인기가 높습니다.',
    address: '부산광역시 해운대구 해운대해변로 264',
    region: '해운대구',
    rating: 4.5,
    reviewCount: 15420,
    hours: '24시간 개방',
    phone: '051-749-4062',
    website: 'www.haeundae.go.kr',
    entranceFee: '무료',
    tags: ['해변', '수상스포츠', '일몰', '카페', '맛집', '야경'],
  },
];

const TouristDetailPage = () => {
  const { id: touristId } = useParams();
  const navigate = useNavigate();
  const { isWishlisted, addToWishlist, removeFromWishlist } = useWishlist();

  const [touristData, setTouristData] = useState(null);
  const [loading, setLoading]   = useState(true);
  const [error, setError]       = useState(null);
  const [isScrolled, setIsScrolled] = useState(false);
  const [imageLoaded, setImageLoaded] = useState(false);
  const [weatherData, setWeatherData] = useState(null);

  // 혼잡도(이름 기반)
  const [crowdingLoading, setCrowdingLoading] = useState(false);
  const [crowdingResp, setCrowdingResp] = useState(null); // { success, message }

  const [showSpecialOffer, setShowSpecialOffer] = useState(true);
  const [expandedCards, setExpandedCards] = useState({
    crowding: false, features: false, reviews: false, details: false,
  });

  useEffect(() => {
    const onScroll = () => setIsScrolled(window.scrollY > 100);
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  // 날씨 (CORS 문제 회피 위해 credentials: 'omit')
  const fetchWeatherData = async (region) => {
    try {
      const url = `${API_V1}/weather?region=${encodeURIComponent(region)}`;
      const res = await fetch(url, {
        method: 'GET',
        credentials: 'omit',
        headers: { 'Content-Type': 'application/json' },
      });

      if (res.ok) {
        const data = await res.json();
        const tempData = Array.isArray(data?.forecasts)
          ? data.forecasts.find((item) => item.category === 'TMP')
          : null;

        setWeatherData({
          temperature: tempData?.value ?? '24',
          region: data?.region ?? region,
        });
      } else {
        setWeatherData({ temperature: '24', region });
      }
    } catch (err) {
      console.error('날씨 데이터 로딩 오류:', err);
      setWeatherData({ temperature: '24', region: region || '부산' });
    }
  };

  // 혼잡도(관광지 이름 기반)
  const fetchCrowdingByName = async (placeName) => {
    if (!placeName) return;
    setCrowdingLoading(true);
    try {
      const json = await getAttractionCrowdingByName(placeName);
      // 기대응답: { success: true/false, message: "혼잡도: 92.51%" | "혼잡도 정보 없음" }
      setCrowdingResp(json);
    } catch {
      setCrowdingResp({ success: false, message: '혼잡도 정보를 불러올 수 없습니다.' });
    } finally {
      setCrowdingLoading(false);
    }
  };

  // 상세 데이터
  useEffect(() => {
    const load = async () => {
      if (!touristId) {
        setError('관광지 ID가 없습니다.');
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        setError(null);

        const data = await getPlaceById(touristId);

        if (data) {
          setTouristData(data);

          const address = data.address || '';
          const regionMatch = address.match(/([가-힣]+구)/);
          const region = regionMatch ? regionMatch[1] : '해운대구';
          fetchWeatherData(region);

          // ← 좌표기반 호출 제거, **이름 기반**으로 변경
          fetchCrowdingByName(data.name);

          setTimeout(() => setImageLoaded(true), 500);
        } else {
          // 404 등으로 null이면 샘플 사용
          const sample =
            busanSampleData.find(s => s._id === touristId) || busanSampleData[0];
          setTouristData(sample);
          fetchWeatherData('해운대구');

          // 샘플도 **이름 기반**으로 호출
          fetchCrowdingByName(sample.name);

          setTimeout(() => setImageLoaded(true), 500);
        }
      } catch (err) {
        console.error('관광지 데이터 로딩 오류:', err);
        setError('관광지 정보를 불러오는 중 오류가 발생했습니다.');
        const sample =
          busanSampleData.find(s => s._id === touristId) || busanSampleData[0];
        setTouristData(sample);
        fetchWeatherData('해운대구');
        fetchCrowdingByName(sample.name);
        setTimeout(() => setImageLoaded(true), 500);
      } finally {
        setLoading(false);
      }
    };

    load();
  }, [touristId]); // eslint-disable-line react-hooks/exhaustive-deps

  const toggleCard = (key) => setExpandedCards(prev => ({ ...prev, [key]: !prev[key] }));

  const parseCrowdingPercent = (msg) => {
    // "혼잡도: 92.51%" 같은 문자열에서 숫자만 추출
    if (!msg) return null;
    const m = msg.match(/([\d.]+)\s*%/);
    if (!m) return null;
    const v = parseFloat(m[1]);
    if (Number.isNaN(v)) return null;
    return v;
  };

  const getCrowdingLevelClassFromMessage = (msg) => {
    const v = parseCrowdingPercent(msg);
    if (v == null) return 'no-info';    // "혼잡도 정보 없음" 등
    if (v >= 80) return 'very-crowded';
    if (v >= 60) return 'crowded';
    if (v >= 40) return 'normal';
    if (v >= 20) return 'comfortable';
    return 'empty';
  };

  // 로딩
  if (loading) {
    return (
      <div className="tourist-detail-page loading">
        <div className="floating-header floating-header--scrolled">
          <div className="header-content">
            <button className="back-button" onClick={() => navigate(-1)}>
              <ArrowLeft size={20} />
              <span className="back-text">목록으로 돌아가기</span>
            </button>
          </div>
        </div>
        <div className="loading-content">
          <div className="loading-spinner"></div>
          <h2>관광지 정보를 불러오는 중...</h2>
        </div>
      </div>
    );
  }

  // 데이터 없음
  if (!touristData) {
    return (
      <div className="tourist-detail-page not-found">
        <div className="floating-header floating-header--scrolled">
          <div className="header-content">
            <button className="back-button" onClick={() => navigate(-1)}>
              <ArrowLeft size={20} />
              <span className="back-text">목록으로 돌아가기</span>
            </button>
          </div>
        </div>
        <div className="not-found-content">
          <h2>요청하신 관광지 정보를 찾을 수 없습니다.</h2>
          {error && <p className="error-message">{error}</p>}
          <button className="cta-button" onClick={() => navigate('/')}>홈으로 돌아가기</button>
        </div>
      </div>
    );
  }

  const handleWishlistToggle = () => {
    const placeId = touristData.id || touristData._id;
    if (isWishlisted(placeId)) removeFromWishlist(placeId);
    else addToWishlist(placeId);
  };

  const handleShare = async () => {
    if (navigator.share) {
      try {
        await navigator.share({
          title: touristData.name,
          text: touristData.description,
          url: window.location.href,
        });
      } catch {}
    } else {
      try {
        await navigator.clipboard.writeText(window.location.href);
        alert('링크가 복사되었습니다!');
      } catch {}
    }
  };

  const handleNaverMap = () => {
    const url = `https://map.naver.com/v5/search/${encodeURIComponent(touristData.name)}`;
    const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    if (isMobile) {
      if (window.confirm(`네이버 지도에서 "${touristData.name}" 검색으로 이동할까요?`)) {
        window.open(url, '_blank');
      }
    } else {
      window.open(url, '_blank');
    }
  };

  const infoItems = [
    { icon: MapPin, label: '주소', value: touristData.address || touristData.region || '정보 없음' },
    { icon: Clock, label: '운영시간', value: touristData.hours || '정보 없음' },
    { icon: Phone, label: '전화번호', value: touristData.phone || '정보 없음' },
    {
      icon: Globe,
      label: '웹사이트',
      value: touristData.website
        ? <a href={`http://${touristData.website}`} target="_blank" rel="noopener noreferrer">{touristData.website}</a>
        : '정보 없음',
    },
    { icon: DollarSign, label: '입장료', value: touristData.entranceFee || '정보 없음' },
  ];

  return (
    <div className="tourist-detail-page">
      {/* Floating Header */}
      <div className={`floating-header ${isScrolled ? 'floating-header--scrolled' : 'floating-header--transparent'}`}>
        <div className="header-content">
          <button className="back-button" onClick={() => navigate(-1)}>
            <ArrowLeft size={20} />
            <span className="back-text">목록으로 돌아가기</span>
          </button>
          {isScrolled && (
            <div className="header-title animate-fade-in-up">
              <h1>{touristData.name}</h1>
              <div className="rating-badge">
                <Star className="star-icon w-4 h-4" />
                <span>{touristData.rating || 'N/A'}</span>
              </div>
            </div>
          )}
          <div className="header-actions">
            <button onClick={handleShare} className="action-button">
              <Share2 size={20} />
            </button>
            <button
              onClick={handleWishlistToggle}
              className={`action-button ${isWishlisted(touristData.id || touristData._id) ? 'action-button--liked' : ''}`}
            >
              <Heart size={20} className="heart-icon" fill={isWishlisted(touristData.id || touristData._id) ? '#dc3545' : 'none'} />
            </button>
          </div>
        </div>
      </div>

      {/* Hero */}
      <div className="hero-section">
        <div
          className={`hero-background ${imageLoaded ? 'loaded' : ''}`}
          style={{ backgroundImage: `url(https://images.unsplash.com/photo-1520637736862-4d197d17c280?w=1200&h=600&fit=crop)` }}
          onLoad={() => setImageLoaded(true)}
        />
        <div className="hero-overlay" />

        {/* Weather */}
        <div className="weather-widget">
          <div className="weather-content">
            <div className="weather-icon">☀️</div>
            <div className="weather-info">
              <div className="weather-temp">{weatherData?.temperature || '24'}°</div>
              <div className="weather-location">{weatherData?.region || '부산'}</div>
            </div>
          </div>
        </div>

        {/* Floating Actions */}
        <div className="floating-actions">
          <button className="floating-button"><Camera size={20} /></button>
          <button className="floating-button"><Play size={20} /></button>
        </div>

        {/* Hero Content */}
        <div className="hero-content">
          <div className="content-wrapper">
            <h1 className="hero-title animate-fade-in-up">{touristData.name}</h1>
            <div className="hero-meta animate-fade-in-up">
              <div className="meta-item">
                <MapPin size={20} />
                <span>{touristData.address || touristData.region || '정보 없음'}</span>
              </div>
              <div className="rating-info">
                <Star className="star-icon w-5 h-5" />
                <span className="rating-score">{touristData.rating || 'N/A'}</span>
                <span className="review-count">{(touristData.review_count || touristData.reviewCount || 0).toLocaleString()}</span>
              </div>
            </div>
            <div className="tags-container animate-fade-in-up">
              <span className="category-tag">{touristData.category}</span>
              {touristData.tags?.slice(0, 4).map((tag, i) => (
                <span key={i} className="tag">{tag}</span>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Main */}
      <div className="main-content">
        <div className="content-grid">
          <div className="animate-fade-in-up" style={{ animationDelay: '0.2s' }}>
            {/* Crowding (이름 기반 메시지 그대로 표기) */}
            <div className={`content-card crowding-card ${expandedCards.crowding ? 'expanded' : 'collapsed'}`}>
              <h2 className="card-title accordion-header" onClick={() => toggleCard('crowding')}>
                <div className="title-content">
                  <div className="title-icon title-icon--red"><Users className="text-white" size={20} /></div>
                  실시간 혼잡도
                </div>
                <ChevronDown className={`accordion-icon ${expandedCards.crowding ? 'rotated' : ''}`} size={24} />
              </h2>
              <div className="accordion-content">
                {crowdingLoading ? (
                  <div className="crowding-loading">
                    <div className="loading-spinner"></div>
                    <p>혼잡도 정보를 불러오는 중...</p>
                  </div>
                ) : (
                  <div className="crowding-content">
                    <div className={`crowding-level level-${getCrowdingLevelClassFromMessage(crowdingResp?.message)}`}>
                      <span className="level-label">현재 상태</span>
                      <span className="level-value">
                        {crowdingResp?.message ?? '혼잡도 정보를 불러올 수 없습니다.'}
                      </span>
                    </div>
                    <div className="crowding-description">
                      <p>장소명 기반으로 단순화된 혼잡도 메시지를 표시합니다.</p>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Features */}
            <div className={`content-card features-card ${expandedCards.features ? 'expanded' : 'collapsed'}`}>
              <h2 className="card-title accordion-header" onClick={() => toggleCard('features')}>
                <div className="title-content">
                  <div className="title-icon title-icon--green"><Coffee className="text-white" size={20} /></div>
                  편의시설
                </div>
                <ChevronDown className={`accordion-icon ${expandedCards.features ? 'rotated' : ''}`} size={24} />
              </h2>
              <div className="accordion-content">
                <div className="features-grid">
                  <div className="feature-item"><div className="feature-icon feature-icon--wifi"><Wifi size={20} /></div><span>WiFi 무료</span></div>
                  <div className="feature-item"><div className="feature-icon feature-icon--parking"><Navigation size={20} /></div><span>주차 가능</span></div>
                  <div className="feature-item"><div className="feature-icon feature-icon--cafe"><Coffee size={20} /></div><span>카페 근처</span></div>
                  <div className="feature-item"><div className="feature-icon feature-icon--family"><Heart size={20} /></div><span>가족 친화적</span></div>
                </div>
              </div>
            </div>

            {/* Reviews */}
            <div className={`content-card reviews-card ${expandedCards.reviews ? 'expanded' : 'collapsed'}`}>
              <h2 className="card-title accordion-header" onClick={() => toggleCard('reviews')}>
                <div className="title-content">
                  <div className="title-icon title-icon--purple"><Star className="text-white" size={20} /></div>
                  리뷰 요약
                </div>
                <ChevronDown className={`accordion-icon ${expandedCards.reviews ? 'rotated' : ''}`} size={24} />
              </h2>
              <div className="accordion-content">
                <div className="reviews-summary">
                  <div className="rating-display">
                    <div className="rating-number">{touristData.rating}</div>
                    <div className="rating-stars">
                      {[...Array(5)].map((_, i) => (
                        <Star key={i} size={16} className={i < Math.floor(touristData.rating) ? 'star-filled' : 'star-empty'} />
                      ))}
                    </div>
                    <div className="review-count-text">
                      {(touristData.review_count || touristData.reviewCount || 0).toLocaleString()}개의 리뷰
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Sidebar */}
          <div className="sidebar animate-slide-in-right" style={{ animationDelay: '0.4s' }}>
            <div className={`content-card sticky-card info-card ${expandedCards.details ? 'expanded' : 'collapsed'}`}>
              <h2 className="card-title accordion-header" onClick={() => toggleCard('details')}>
                <div className="title-content">상세 정보</div>
                <ChevronDown className={`accordion-icon ${expandedCards.details ? 'rotated' : ''}`} size={24} />
              </h2>
              <div className="accordion-content">
                <div className="info-list">
                  {infoItems.map((item, i) => (
                    <div key={i} className="info-item">
                      <item.icon className="info-icon" size={20} />
                      <div className="info-content">
                        <p className="info-label">{item.label}</p>
                        <p className="info-value">{item.value}</p>
                      </div>
                    </div>
                  ))}
                </div>
                <button className="map-button" onClick={handleNaverMap}>
                  <Navigation size={20} />
                  네이버 지도로 보기
                </button>
              </div>
            </div>

            {/* Special Offer */}
            <div className={`special-offer-container ${!showSpecialOffer ? 'hidden' : ''}`}>
              <div className="content-card special-offer-card">
                <button className="close-button" onClick={() => setShowSpecialOffer(false)} aria-label="특별 혜택 닫기">
                  <X size={16} />
                </button>
                <div className="offer-badge">특별 혜택</div>
                <h3 className="offer-title">지금 예약하면 20% 할인!</h3>
                <p className="offer-description">이 관광지 근처 숙소 예약 시 특별 할인 혜택을 받을 수 있습니다.</p>
                <button className="offer-button">예약하기</button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TouristDetailPage;
