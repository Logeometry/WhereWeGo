import { useState, useEffect } from 'react';
import styles from './SurveyPage.module.scss';

// 로딩 메시지와 부산 관련 사실 데이터
const loadingMessages = [
  "부산 여행 선호도를 분석하고 있습니다...",
  "부산의 명소들을 검색하고 있습니다...",
  "당신에게 가장 적합한 부산 여행지를 찾고 있습니다...",
  "맞춤형 부산 여행 추천을 생성하고 있습니다...",
  "거의 완료되었습니다. 조금만 더 기다려주세요..."
];

const facts = [
  "해운대 해수욕장은 부산에서 가장 유명한 해변으로, 연간 약 1천만 명이 방문합니다.",
  "감천문화마을은 색색의 집들이 산비탈에 늘어선 예술 마을로, '한국의 마추픽추'라 불립니다.",
  "부산 국제영화제는 아시아에서 가장 큰 영화제 중 하나로, 매년 10월에 개최됩니다.",
  "태종대는 부산의 남동쪽 끝에 위치한 해안 절벽으로, 수려한 자연 경관을 자랑합니다.",
  "광안대교는 밤에 화려한 조명으로 빛나는 부산의 랜드마크입니다.",
  "자갈치 시장은 한국 최대의 수산물 시장으로, 신선한 해산물을 맛볼 수 있습니다."
];

// 여행지 데이터
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
    imageUrl: '/image/GwanganriBeach.jpg',
    category: "해변" // Beach
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
    imageUrl: '/image/Taejongdae.jpg',
    category: "자연" // Nature
  }
];

export default function TravelSurvey() {
  // 상태 관리
  const [stage, setStage] = useState('start'); // 'start', 'survey', 'loading', 'results'
  const [preferences, setPreferences] = useState({});
  const [currentAttractionIndex, setCurrentAttractionIndex] = useState(0);
  const [loadingMessageIndex, setLoadingMessageIndex] = useState(0);
  const [factIndex, setFactIndex] = useState(0);
  const [loadingProgress, setLoadingProgress] = useState(0);

  const totalAttractions = surveyAttractions.length;
  const completedCount = Object.keys(preferences).length;

  // 로딩 메시지와 사실 관련 효과
  useEffect(() => {
    if (stage === 'loading') {
      // 로딩 메시지 변경
      const messageInterval = setInterval(() => {
        setLoadingMessageIndex((prev) => (prev + 1) % loadingMessages.length);
      }, 2000);

      // 사실 정보 변경
      const factInterval = setInterval(() => {
        setFactIndex((prev) => (prev + 1) % facts.length);
      }, 4000);

      // 프로그레스 바 업데이트
      const progressInterval = setInterval(() => {
        setLoadingProgress((prev) => {
          const newProgress = prev + 5;
          return newProgress <= 100 ? newProgress : 100;
        });
      }, 500);

      // 로딩 완료 (약 10초 후)
      const loadingTimer = setTimeout(() => {
        setStage('results');
        clearInterval(messageInterval);
        clearInterval(factInterval);
        clearInterval(progressInterval);
      }, 10000);

      return () => {
        clearInterval(messageInterval);
        clearInterval(factInterval);
        clearInterval(progressInterval);
        clearTimeout(loadingTimer);
      };
    }
  }, [stage]);

  // 선호도 선택 핸들러
  const handlePreference = (preference) => {
    const currentAttraction = surveyAttractions[currentAttractionIndex];
    setPreferences(prev => ({ ...prev, [currentAttraction.id]: preference }));

    if (currentAttractionIndex < totalAttractions - 1) {
      // 다음 설문으로 이동
      setCurrentAttractionIndex(prevIndex => prevIndex + 1);
    } else {
      // 모든 설문이 완료되면 로딩 화면으로 전환
      console.log("마지막 설문 완료, 로딩 화면으로 전환");
      setStage('loading');
      setLoadingProgress(0);
    }
  };

  // 설문 시작 핸들러
  const handleStartSurvey = () => {
    setStage('survey');
    setCurrentAttractionIndex(0);
    setPreferences({});
  };

  // 설문 재시작 핸들러
  const handleRestartSurvey = () => {
    setStage('start');
    setCurrentAttractionIndex(0);
    setPreferences({});
  };

  // 현재 표시해야 할 명소 정보
  const currentAttraction = stage === 'survey' 
    ? surveyAttractions[currentAttractionIndex]
    : null;

  // 결과 분석 함수
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

  // 추천 여행지 생성 함수
  const getRecommendations = () => {
    const results = getResults();
    const topCategory = results.length > 0 ? results[0].category : null;
    
    if (!topCategory) return [];
    
    // 상위 카테고리에 해당하는 여행지 추천
    return surveyAttractions
      .filter(attraction => attraction.category === topCategory)
      .map(attraction => ({
        ...attraction,
        reason: `${topCategory} 카테고리에서 당신의 선호도가 가장 높았습니다.`
      }));
  };

  // 콘솔에 현재 상태 기록
  console.log("현재 상태:", { 
    stage, 
    currentAttractionIndex,
    completedCount 
  });

  return (
    <div className={styles.container}>
      <div className={styles.contentWrapper}>
        {stage === 'start' && (
          // 설문 시작 전 화면
          <div className={styles.startScreen}>
            <h1 className={styles.startTitle}>부산 여행 스타일 찾기</h1>
            <p className={styles.startButtonText}>부산의 관광 명소에 대한 몇 가지 질문에 답하고 맞춤형 여행 추천을 받아보세요.</p>
            <button
              onClick={handleStartSurvey}
              className={styles.startButton}
            >
              설문 시작하기
            </button>
          </div>
        )}

        {stage === 'loading' && (
          // 로딩 화면
          <div className={styles.loadingScreen}>
            <h2 className={styles.loadingTitle}>분석 중...</h2>
            
            <div className={styles.loadingProgressContainer}>
              <div 
                className={styles.loadingProgressBar}
                style={{ width: `${loadingProgress}%` }}
              ></div>
            </div>
            
            <p className={styles.loadingMessage}>
              {loadingMessages[loadingMessageIndex]}
            </p>
            
            <div className={styles.factBox}>
              <h3 className={styles.factTitle}>알고 계셨나요?</h3>
              <p className={styles.factText}>{facts[factIndex]}</p>
            </div>
          </div>
        )}

        {stage === 'results' && (
          // 설문 완료 후 결과 화면
          <div className={styles.resultsScreen}>
            <h2 className={styles.resultsTitle}>당신의 여행 선호도 분석 결과</h2>

            <div className={styles.resultsList}>
              <h3 className={styles.resultsSubtitle}>선호하는 여행 카테고리:</h3>
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

            {/* 추천 여행지 섹션 */}
            <div className={styles.recommendationsSection}>
              <h3 className={styles.recommendationsTitle}>당신을 위한 맞춤 추천 여행지</h3>
              <div className={styles.recommendationsList}>
                {getRecommendations().map(recommendation => (
                  <div key={recommendation.id} className={styles.recommendationCard}>
                    <img 
                      src={recommendation.imageUrl} 
                      alt={recommendation.name}
                      className={styles.recommendationImage}
                    />
                    <div className={styles.recommendationContent}>
                      <h4 className={styles.recommendationName}>{recommendation.name}</h4>
                      <p className={styles.recommendationDescription}>{recommendation.description}</p>
                      <p className={styles.recommendationReason}>{recommendation.reason}</p>
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
                설문 다시 하기
              </button>
            </div>
          </div>
        )}

        {stage === 'survey' && (
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