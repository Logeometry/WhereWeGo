import React from 'react';
import './TourCardList.scss';

const tours = [
  {
    title: '해운대 해수욕장',
    image: '/image/HaeundaeBeach.jpg',
  },
  {
    title: '자갈치 시장',
    image: '/image/JagalchiMarket.jpg',
  },
  {
    title: '태종대 공원',
    image: '/image/Taejong-daeAmusementPark.jpg',
  },
];

const TourCardList = () => {
  return (
    <div className="tour-grid">
      {tours.map((tour, index) => (
        <div className="tour-thumbnail" key={index}>
          <img src={tour.image} alt={tour.title} />
          <div className="tour-title">{tour.title}</div>
        </div>
      ))}
    </div>
  );
};

export default TourCardList;
