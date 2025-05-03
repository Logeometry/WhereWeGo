import { useState, useEffect } from 'react';
import { surveyAttractions } from '../data/surveyAttractions';

export const useSurveyAttractions = () => {
  const [attractions, setAttractions] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    setTimeout(() => {
      try {
        const groupedData = {};
        surveyAttractions.forEach(attraction => { // 수정: surveyAttractions 사용
          attraction.themes.forEach(theme => {
            if (!groupedData[theme]) {
              groupedData[theme] = [];
            }
            groupedData[theme].push(attraction);
          });
        });
        setAttractions(groupedData);
        setLoading(false);
      } catch (err) {
        setError(err);
        setLoading(false);
      }
    }, 500); // 가짜 로딩 시간
  }, []);

  return { attractions, loading, error };
};