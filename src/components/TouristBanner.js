import React from 'react';
import './TouristBanner.scss';

const attractions = [
  {
    title: "해운대 해수욕장",
    image: "image/HaeundaeBeach.jpg",
    description: "부산을 대표하는 해변",
    rating: 4.5,
    reviews: 120
  },
  {
    title: "자갈치 시장",
    image: "JagalchiMarket.jpg",
    description: "신선한 해산물 시장",
    rating: 4.0,
    reviews: 90
  },
  {
    title: "태종대 공원",
    image: "Taejong-daeAmusementPark.jpge",
    description: "자연과 바다가 어우러진 명소",
    rating: 4.7,
    reviews: 150
  }
];

const TouristBanner = () => {
  return (
    <section className="tourist-banner" id="tourist-info">
      <div className="banner-header">
        <h2>부산 인기 관광지 BEST 3</h2>
        <a href="/more" className="more-link">더 많은 부산 관광지 보기</a>
      </div>
      <div className="card-container">
        {attractions.map((attraction, index) => (
          <div key={index} className="card">
            <img src={attraction.image} alt={attraction.title} />
            <div className="card-content">
              <h3>{attraction.title}</h3>
              <p>{attraction.description}</p>
              <div className="card-meta">
                <span>⭐ {attraction.rating}</span>
                <span>({attraction.reviews} 리뷰)</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
};

export default TouristBanner;
