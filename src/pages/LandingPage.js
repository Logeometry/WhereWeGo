import React from 'react';
import { Container } from '@mui/material';
import Header from '../components/Header';
import AiPlannerBanner from '../components/AiPlannerBanner'
import HeroSection from '../components/HeroSection';
import SidebarFilter from '../components/SidebarFilter';
import TourCardList from '../components/TourCardList';
import Footer from '../components/Footer';
import './LandingPage.scss';

const LandingPage = () => {
  return (
    <div className="landing-page">
      <Header />
      <AiPlannerBanner />
      <Container maxWidth="lg" className="landing-page__content">

        <div className="landing-page__cards">
          <TourCardList />
        </div>
      </Container>
      <Footer />
    </div>
  );
};

export default LandingPage;
