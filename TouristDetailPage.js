import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  MapPin,
  Clock,
  Phone,
  Globe,
  Navigation,
  Star,
  Heart,
  Camera,
  DollarSign,
  Coffee,
  Bed,
  ChevronRight,
  Share2,
  Play,
  Wifi,
} from 'lucide-react';
import { useWishlist } from '../contexts/WishlistContext';
import './TouristDetailPage.scss';

// Sample data for demonstration (백엔드 Tourism 스키마 구조에 맞춰 수정)
const busanSampleData = [
  {
    _id: "busan-beach-001",
    id: "busan-beach-001", // Tourism 스키마의 id 필드
    name: "해운대 해수욕장",
    category: "해변/바다",
    category_group: "관광명소",
    description: "부산의 대표적인 해수욕장으로, 아름다운 백사장과 맑은 바다로 유명합니다. 다양한 수상 스포츠와 해변 활동을 즐길 수 있으며, 주변에는 맛집과 카페들이 즐비해 있어 관광객들에게 인기가 높습니다.",
    address: "부산광역시 해운대구 해운대해변로 264",
    region: "해운대구",
    location: {
      type: "Point",
      coordinates: [129.1604, 35.1587] // [lng, lat] 형식
    },
    rating: 4.5,
    review_count: 15420, // 백엔드 스키마에 맞춘 필드명
    reviewCount: 15420, // 프론트엔드 호환성을 위해 두 필드 모두 제공
    visitors_count: 50000,
    // 백엔드에는 없지만 프론트엔드에서 사용하는 필드들 (선택사항)
    hours: "24시간 개방",
    phone: "051-749-4062",
    website: "www.haeundae.go.kr",
    entranceFee: "무료",
    tags: ["해변", "수상스포츠", "일몰", "카페", "맛집", "야경"],
    created_at: "2024-01-01T00:00:00Z",
    updated_at: "2024-01-01T00:00:00Z",
    vector_version: 1
  }
];

const TouristDetailPage = () => {
  const { id: touristId } = useParams();
  const navigate = useNavigate();
  const { isWishlisted, addToWishlist, removeFromWishlist } = useWishlist();

  // Sample data fallback
  const touristData = busanSampleData.find(item => item._id === touristId) || busanSampleData[0];

  const [isScrolled, setIsScrolled] = useState(false);
  const [imageLoaded, setImageLoaded] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      const scrollTop = window.scrollY;
      setIsScrolled(scrollTop > 100);
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  useEffect(() => {
    console.log('TouristDetailPage 렌더링 시작');
    console.log('URL에서 가져온 touristId:', touristId);
    if (!touristData) {
      console.log('touristData를 찾을 수 없습니다!');
    } else {
      console.log('찾은 touristData:', touristData);
    }
    // Set image as loaded after a delay to simulate loading
    setTimeout(() => setImageLoaded(true), 500);
  }, [touristId, touristData]);

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
          <button className="cta-button" onClick={() => navigate('/')}>홈으로 돌아가기</button>
        </div>
      </div>
    );
  }

  const handleWishlistToggle = () => {
    if (isWishlisted(touristData._id)) {
      removeFromWishlist(touristData._id);
    } else {
      addToWishlist(touristData._id);
    }
  };

  const handleShare = async () => {
    if (navigator.share) {
      try {
        await navigator.share({
          title: touristData.name,
          text: touristData.description,
          url: window.location.href,
        });
      } catch (err) {
        console.log('Error sharing:', err);
      }
    } else {
      try {
        await navigator.clipboard.writeText(window.location.href);
        alert('링크가 복사되었습니다!');
      } catch (err) {
        console.log('Error copying to clipboard:', err);
      }
    }
  };

  const infoItems = [
    { icon: MapPin, label: "주소", value: touristData.address || touristData.region || '정보 없음' },
    { icon: Clock, label: "운영시간", value: touristData.hours || '정보 없음' },
    { icon: Phone, label: "전화번호", value: touristData.phone || '정보 없음' },
    { icon: Globe, label: "웹사이트", value: touristData.website ? <a href={`http://${touristData.website}`} target="_blank" rel="noopener noreferrer">{touristData.website}</a> : '정보 없음' },
    { icon: DollarSign, label: "입장료", value: touristData.entranceFee || '정보 없음' }
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
              className={`action-button ${isWishlisted(touristData._id) ? 'action-button--liked' : ''}`}
            >
              <Heart
                size={20}
                className="heart-icon"
                fill={isWishlisted(touristData._id) ? '#dc3545' : 'none'}
              />
            </button>
          </div>
        </div>
      </div>

      {/* Hero Section */}
      <div className="hero-section">
        <div
          className={`hero-background ${imageLoaded ? 'loaded' : ''}`}
          style={{ backgroundImage: `url(https://images.unsplash.com/photo-1520637736862-4d197d17c280?w=1200&h=600&fit=crop)` }}
          onLoad={() => setImageLoaded(true)}
        />
        <div className="hero-overlay" />

        {/* Weather Widget */}
        <div className="weather-widget">
          <div className="weather-content">
            <div className="weather-icon">☀️</div>
            <div className="weather-info">
              <div className="weather-temp">24°</div>
              <div className="weather-location">부산</div>
            </div>
          </div>
        </div>

        {/* Floating Actions */}
        <div className="floating-actions">
          <button className="floating-button">
            <Camera size={20} />
          </button>
          <button className="floating-button">
            <Play size={20} />
          </button>
        </div>

        {/* Hero Content */}
        <div className="hero-content">
          <div className="content-wrapper">
            <div className="tags-container">
              <span className="category-tag">
                {touristData.category}
              </span>
              {touristData.tags?.slice(0, 4).map((tag, index) => (
                <span key={index} className="tag">
                  {tag}
                </span>
              ))}
            </div>
            <h1 className="hero-title animate-fade-in-up">
              {touristData.name}
            </h1>
            <div className="hero-meta animate-fade-in-up">
              <div className="meta-item">
                <MapPin size={20} />
                <span>{touristData.address || touristData.region || '정보 없음'}</span>
              </div>
              <div className="rating-info">
                <Star className="star-icon w-5 h-5" />
                <span className="rating-score">{touristData.rating || 'N/A'}</span>
                <span className="review-count">({(touristData.review_count || touristData.reviewCount || 0).toLocaleString()})</span>
              </div>
            </div>
            <button className="cta-button animate-fade-in-up">
              <Navigation size={20} />
              길찾기
            </button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="main-content">
        <div className="content-grid">
          <div className="animate-fade-in-up" style={{ animationDelay: '0.2s' }}>
            {/* Description Card */}
            <div className="content-card description-card">
              <h2 className="card-title">
                <div className="title-icon title-icon--blue">
                  <MapPin className="text-white" size={20} />
                </div>
                관광지 소개
              </h2>
              <p className="description-text">{touristData.description || '설명이 없습니다.'}</p>
            </div>

            {/* Features Grid */}
            <div className="content-card features-card">
              <h2 className="card-title">
                <div className="title-icon title-icon--green">
                  <Coffee className="text-white" size={20} />
                </div>
                편의시설
              </h2>
              <div className="features-grid">
                <div className="feature-item">
                  <div className="feature-icon feature-icon--wifi">
                    <Wifi size={20} />
                  </div>
                  <span>WiFi 무료</span>
                </div>
                <div className="feature-item">
                  <div className="feature-icon feature-icon--parking">
                    <Navigation size={20} />
                  </div>
                  <span>주차 가능</span>
                </div>
                <div className="feature-item">
                  <div className="feature-icon feature-icon--cafe">
                    <Coffee size={20} />
                  </div>
                  <span>카페 근처</span>
                </div>
                <div className="feature-item">
                  <div className="feature-icon feature-icon--family">
                    <Heart size={20} />
                  </div>
                  <span>가족 친화적</span>
                </div>
              </div>
            </div>

            {/* Reviews Card */}
            <div className="content-card reviews-card">
              <h2 className="card-title">
                <div className="title-icon title-icon--purple">
                  <Star className="text-white" size={20} />
                </div>
                리뷰 요약
              </h2>
              <div className="reviews-summary">
                <div className="rating-display">
                  <div className="rating-number">{touristData.rating}</div>
                  <div className="rating-stars">
                    {[...Array(5)].map((_, i) => (
                      <Star 
                        key={i} 
                        size={16} 
                        className={i < Math.floor(touristData.rating) ? 'star-filled' : 'star-empty'} 
                      />
                    ))}
                  </div>
                  <div className="review-count-text">
                    {(touristData.review_count || touristData.reviewCount || 0).toLocaleString()}개의 리뷰
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Sidebar */}
          <div className="sidebar animate-slide-in-right" style={{ animationDelay: '0.4s' }}>
            <div className="content-card sticky-card info-card">
              <h2 className="card-title">상세 정보</h2>
              <div className="info-list">
                {infoItems.map((item, index) => (
                  <div key={index} className="info-item">
                    <item.icon className="info-icon" size={20} />
                    <div className="info-content">
                      <p className="info-label">{item.label}</p>
                      <p className="info-value">{item.value}</p>
                    </div>
                  </div>
                ))}
              </div>
              <button className="map-button">
                <Navigation size={20} />
                네이버 지도로 보기
              </button>
            </div>

            {/* Special Offer Card */}
            <div className="content-card special-offer-card">
              <div className="offer-badge">특별 혜택</div>
              <h3 className="offer-title">지금 예약하면 20% 할인!</h3>
              <p className="offer-description">
                이 관광지 근처 숙소 예약 시 특별 할인 혜택을 받을 수 있습니다.
              </p>
              <button className="offer-button">
                예약하기
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TouristDetailPage;