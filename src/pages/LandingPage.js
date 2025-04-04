import React from 'react';
import { Container } from '@mui/material';
import Header from '../components/Header';
import AiPlannerBanner from '../components/AiPlannerBanner'
import Footer from '../components/Footer';
import './LandingPage.scss';
import RecommendationGallery from '../components/RecommendationGallery';
import TravelNewsBanner from '../components/TravelNewsBanner';
const LandingPage = () => {
  return (
    <div className="landing-page">
      <Header />
      <AiPlannerBanner />
      <Container maxWidth="lg" className="landing-page__content">

        <div className="landing-page__cards">
          <RecommendationGallery />
        </div>
        
      </Container>
      <TravelNewsBanner />
      <Footer />
    </div>
  );
};

export default LandingPage;
