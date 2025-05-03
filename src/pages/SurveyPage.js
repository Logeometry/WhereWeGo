import { useState, useEffect } from 'react';
// MUI 컴포넌트 import 제거 또는 주석 처리 (스타일 관련이므로)
// import Button from '@mui/material/Button';
// import ThumbUpIcon from '@mui/icons-material/ThumbUp';
// import ThumbDownIcon from '@mui/icons-material/ThumbDown';
// import HelpOutlineIcon from '@mui/icons-material/HelpOutline';
// import Typography from '@mui/material/Typography';
// import Box from '@mui/material/Box';
// import Container from '@mui/material/Container';
// import Paper from '@mui/material/Paper';
// import LinearProgress from '@mui/material/LinearProgress';
import styles from './SurveyPage.module.scss';
// Sample attraction data - replace with your actual data
const surveyAttractions = [
  {
    id: 1,
    name: "해운대",
    description: "넓은 백사장과 푸른 바다가 아름다운 부산의 대표 해수욕장",
    imageUrl: '/image/HaeundaeBeach.jpg',
    category: "해변" // Beach
  },
  {
    id: 2,
    name: '광안리',
    description: "광안대교 야경과 트렌디한 카페, 맛집이 어우러진 활기찬 해변",
    imageUrl: '/image/GwanganriBeach.jpg', // 사용자 제공 데이터와 다르게 수정 (실제 이미지 경로를 반영해야 함)
    category: "해변" // Beach (필요시 '야경', '도시' 등으로 세분화 가능)
  },
  {
    id: 3,
    name: '감천문화마을',
    description: "형형색색의 집들이 계단식으로 늘어선 아름다운 문화 예술 마을",
    imageUrl: '/image/Gamcheon.jpg',
    category: "문화" // Culture
  },
  {
    id: 4,
    name: '태종대',
    description: "기암절벽과 푸른 바다가 어우러진 부산의 아름다운 자연 공원",
    imageUrl: '/image/Taejongdae.jpg', // 사용자 제공 데이터와 다르게 수정 (실제 이미지 경로를 반영해야 함)
    category: "자연" // Nature
  }
];


export default function TravelSurvey() {
  const [preferences, setPreferences] = useState({});
  const [currentAttractionIndex, setCurrentAttractionIndex] = useState(0);
  const [surveyStarted, setSurveyStarted] = useState(false);
  const [showResults, setShowResults] = useState(false);

  const totalAttractions = surveyAttractions.length;
  const completedCount = Object.keys(preferences).length;

  const handlePreference = (preference) => {
    const currentAttraction = surveyAttractions[currentAttractionIndex];
    setPreferences(prev => ({ ...prev, [currentAttraction.id]: preference }));

    if (currentAttractionIndex < totalAttractions - 1) {
      setCurrentAttractionIndex(prevIndex => prevIndex + 1);
    } else {
      setShowResults(true);
    }
  };

  const handleStartSurvey = () => {
    setSurveyStarted(true);
    setCurrentAttractionIndex(0);
    setPreferences({});
    setShowResults(false);
  };

  const handleRestartSurvey = () => {
    setShowResults(false);
    setCurrentAttractionIndex(0);
    setPreferences({});
    setSurveyStarted(false); // 시작 화면으로 돌아가도록 수정
  };

    const currentAttraction = surveyStarted && !showResults
      ? surveyAttractions[currentAttractionIndex]
      : null;

  const getResults = () => {
    const categoryCounts = {};

    Object.entries(preferences).forEach(([attractionId, preference]) => {
      const attraction = surveyAttractions.find(a => a.id === parseInt(attractionId, 10));
      if (!attraction) return;

      if (!categoryCounts[attraction.category]) {
        categoryCounts[attraction.category] = { like: 0, neutral: 0, dislike: 0 };
      }

      categoryCounts[attraction.category][preference]++;
    });

    const categoryScores = Object.entries(categoryCounts).map(([category, counts]) => {
      const score = counts.like * 1 + counts.neutral * 0 + counts.dislike * -1;
      return { category, score };
    });

    return categoryScores.sort((a, b) => b.score - a.score);
  };

  return (
    // Tailwind 클래스 대신 SCSS Modules 클래스 적용
    <div className={styles.container}>
      <div className={styles.contentWrapper}>
        {!surveyStarted ? (
          // 설문 시작 전 화면
          <div className={styles.startScreen}>
            <h1 className={styles.startTitle}>Discover Your Travel Style</h1>
            <p className={styles.startButtonText}>Answer a few quick questions about tourist attractions to get personalized travel recommendations.</p>
            <button
              onClick={handleStartSurvey}
              className={styles.startButton}
            >
              Start Survey
            </button>
          </div>
        ) : showResults ? (
          // 설문 완료 후 결과 화면
          <div className={styles.resultsScreen}>
            <h2 className={styles.resultsTitle}>Your Travel Preferences</h2>

            <div className={styles.resultsList}>
              <h3 className={styles.resultsSubtitle}>Your top travel categories:</h3>
              <div className={styles.categoryScores}>
                {getResults().map((result, index) => (
                  <div key={result.category} className={styles.categoryItem}>
                    <div className={styles.categoryRank}>
                      {index + 1}
                    </div>
                    <div className={styles.categoryInfo}>
                      <div className={styles.categoryName}>{result.category}</div>
                      <div className={styles.scoreBarContainer}>
                        <div
                          className={styles.scoreBar}
                          style={{ width: `${Math.max(0, Math.min(100, (result.score / totalAttractions) * 100 + 50))}%` }}
                        ></div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className={styles.resultsFooter}>
              <button
                onClick={handleRestartSurvey}
                className={styles.restartButton}
              >
                Retake Survey
              </button>
            </div>
          </div>
        ) : (
          // 설문 진행 중 화면
          <div className={styles.surveyScreen}>
            {/* Progress bar */}
            <div className={styles.progressBarContainer}>
              <div
                className={styles.progressBar}
                style={{ width: `${(completedCount / totalAttractions) * 100}%` }}
              ></div>
            </div>

            <div className={styles.questionCounter}>
              {currentAttractionIndex + 1} / {totalAttractions}
            </div>

            {/* Attraction card */}
            {currentAttraction && (
              <div className={styles.attractionCard}>
                <img
                  src={currentAttraction.imageUrl}
                  alt={currentAttraction.name}
                  className={styles.attractionImage}
                />
                <div className={styles.attractionOverlay}>
                  <div className={styles.attractionText}>
                    <h2 className={styles.attractionName}>{currentAttraction.name}</h2>
                    <p className={styles.attractionDescription}>{currentAttraction.description}</p>
                  </div>
                </div>
              </div>
            )}

            {/* Preference buttons */}
            <div className={styles.preferenceButtons}>
              <button
                onClick={() => handlePreference('like')}
                className={`${styles.preferenceButton} ${styles.likeButton}`}
              >
                <span className={styles.buttonIcon}>👍</span>
                <span className={styles.buttonText}>좋아요</span>
              </button>

              <button
                onClick={() => handlePreference('neutral')}
                className={`${styles.preferenceButton} ${styles.neutralButton}`}
              >
                 <span className={styles.buttonIcon}>🤔</span>
                 <span className={styles.buttonText}>모르겠어요</span>
              </button>

              <button
                onClick={() => handlePreference('dislike')}
                className={`${styles.preferenceButton} ${styles.dislikeButton}`}
              >
                <span className={styles.buttonIcon}>👎</span>
                <span className={styles.buttonText}>싫어요</span>
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}