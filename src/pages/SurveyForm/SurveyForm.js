// src/pages/SurveyForm.jsx
import React, { useState } from 'react';
import './SurveyForm.scss';

const travelTypes = ['자연 및 아웃도어', '문화 및 역사', '도시 관광', '휴양 및 힐링', '모험 및 액티비티'];
const durations   = ['1-3일', '4-7일', '8-14일', '15일 이상'];
const companions  = ['혼자 여행', '커플/부부', '가족(아이 포함)', '친구들과', '단체/투어'];
const activities  = ['등산', '수영/해변', '쇼핑', '역사 탐방', '현지 음식', '사진 촬영', '캠핑', '축제/이벤트', '예술/박물관', '스포츠', '야생동물 관찰', '휴식', '나이트라이프'];

export default function SurveyForm({ defaultValues = {}, onSubmit }) {
  const [travelType, setTravelType] = useState(defaultValues.travelType || '');
  const [budgetLevel, setBudgetLevel] = useState(defaultValues.budgetLevel || 3);     // 1~5
  const [duration, setDuration] = useState(defaultValues.duration || '');
  const [selectedTags, setSelectedTags] = useState(defaultValues.activities || []);
  const [stayImportance, setStayImportance] = useState(defaultValues.stayImportance || 3); // 1~5
  const [popularity, setPopularity] = useState(defaultValues.popularity || 3);        // 1~5
  const [companion, setCompanion] = useState(defaultValues.companion || '');

  const toggleTag = (tag) => {
    setSelectedTags((prev) => prev.includes(tag) ? prev.filter((t) => t !== tag) : [...prev, tag]);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const data = {
      travelType,
      budgetLevel: Number(budgetLevel),
      duration,
      activities: selectedTags,
      stayImportance: Number(stayImportance),
      popularity: Number(popularity),
      companion,
    };
    if (typeof onSubmit === 'function') onSubmit(data);
  };

  return (
    <div className="survey-container">
      <header className="survey-header">
        <div className="logo">유저 선호도 설문 조사</div>
      </header>

      <form className="survey-form" onSubmit={handleSubmit}>
        <div className="form-header">
          <h1>나만의 맞춤형 여행지 추천</h1>
          <p>아래 설문에 답하시면 당신의 취향에 맞는 여행지를 추천해 드립니다!</p>
        </div>

        <div className="question-block">
          <h3>1. 어떤 유형의 여행을 선호하시나요?</h3>
          {travelTypes.map((type) => (
            <label key={type} className="option-item">
              <input
                type="radio"
                name="travel-type"
                value={type}
                checked={travelType === type}
                onChange={() => setTravelType(type)}
              />
              {type}
            </label>
          ))}
        </div>

        <div className="question-block">
          <h3>2. 예산 범위는 어떻게 되시나요?</h3>
          <input
            type="range"
            min="1"
            max="5"
            value={budgetLevel}
            onChange={(e) => setBudgetLevel(e.target.value)}
            className="slider"
          />
          <div className="slider-values">
            <span>저예산</span>
            <span>중간</span>
            <span>고예산</span>
          </div>
        </div>

        <div className="question-block">
          <h3>3. 선호하는 여행 기간은?</h3>
          {durations.map((d) => (
            <label key={d} className="option-item">
              <input
                type="radio"
                name="duration"
                value={d}
                checked={duration === d}
                onChange={() => setDuration(d)}
              />
              {d}
            </label>
          ))}
        </div>

        <div className="question-block">
          <h3>4. 다음 중 관심 있는 활동을 모두 선택해주세요.</h3>
          <div className="tags-container">
            {activities.map((tag) => (
              <span
                key={tag}
                className={`tag ${selectedTags.includes(tag) ? 'selected' : ''}`}
                onClick={() => toggleTag(tag)}
              >
                {tag}
              </span>
            ))}
          </div>
        </div>

        <div className="question-block">
          <h3>5. 숙박 시설의 중요도는?</h3>
          <div className="rating">
            {[5, 4, 3, 2, 1].map((val) => (
              <React.Fragment key={val}>
                <input
                  type="radio"
                  id={`star${val}`}
                  name="rating"
                  value={val}
                  checked={stayImportance === val}
                  onChange={() => setStayImportance(val)}
                />
                <label htmlFor={`star${val}`}>{val}</label>
              </React.Fragment>
            ))}
          </div>
        </div>

        <div className="question-block">
          <h3>6. 얼마나 인기있는 관광지를 선호하시나요?</h3>
          <input
            type="range"
            min="1"
            max="5"
            value={popularity}
            onChange={(e) => setPopularity(e.target.value)}
            className="slider"
          />
          <div className="slider-values">
            <span>한적한 곳</span>
            <span>적당히 붐비는 곳</span>
            <span>인기 관광지</span>
          </div>
        </div>

        <div className="question-block">
          <h3>7. 여행 동반자는?</h3>
          {companions.map((c) => (
            <label key={c} className="option-item">
              <input
                type="radio"
                name="companion"
                value={c}
                checked={companion === c}
                onChange={() => setCompanion(c)}
              />
              {c}
            </label>
          ))}
        </div>

        <div className="btn-container">
          <button type="submit" className="submit-btn">
            맞춤 여행지 추천받기
          </button>
        </div>
      </form>
    </div>
  );
}
