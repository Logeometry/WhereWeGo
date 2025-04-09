//
import React, { useState } from 'react';
import './SurveyForm.scss';

const travelTypes = ['자연 및 아웃도어', '문화 및 역사', '도시 관광', '휴양 및 힐링', '모험 및 액티비티'];
const climates = ['따뜻하고 습한 열대 기후', '따뜻하고 건조한 기후', '온화한 사계절 기후', '서늘하거나 추운 기후'];
const durations = ['1-3일', '4-7일', '8-14일', '15일 이상'];
const companions = ['혼자 여행', '커플/부부', '가족(아이 포함)', '친구들과', '단체/투어'];
const activities = ['등산', '수영/해변', '쇼핑', '역사 탐방', '현지 음식', '사진 촬영', '캠핑', '축제/이벤트', '예술/박물관', '스포츠', '야생동물 관찰', '휴식', '나이트라이프'];

const SurveyForm = () => {
  const [selectedTags, setSelectedTags] = useState([]);

  const toggleTag = (tag) => {
    setSelectedTags((prev) =>
      prev.includes(tag) ? prev.filter((t) => t !== tag) : [...prev, tag]
    );
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    alert('설문이 제출되었습니다! 맞춤형 여행지를 분석 중입니다.');
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
          {travelTypes.map((type, i) => (
            <label key={i} className="option-item">
              <input type="radio" name="travel-type" value={type} />
              {type}
            </label>
          ))}
        </div>
        <div className="question-block">
          <h3>2. 예산 범위는 어떻게 되시나요?</h3>
          <input type="range" min="1" max="5" defaultValue="3" className="slider" />
          <div className="slider-values">
            <span>저예산</span>
            <span>중간</span>
            <span>고예산</span>
          </div>
        </div>

        <div className="question-block">
          <h3>3. 선호하는 여행 기간은?</h3>
          {durations.map((d, i) => (
            <label key={i} className="option-item">
              <input type="radio" name="duration" value={d} />
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
                <input type="radio" id={`star${val}`} name="rating" value={val} />
                <label htmlFor={`star${val}`}>{val}</label>
              </React.Fragment>
            ))}
          </div>
        </div>

        <div className="question-block">
          <h3>6. 얼마나 인기있는 관광지를 선호하시나요?</h3>
          <input type="range" min="1" max="5" defaultValue="3" className="slider" />
          <div className="slider-values">
            <span>한적한 곳</span>
            <span>적당히 붐비는 곳</span>
            <span>인기 관광지</span>
          </div>
        </div>

        <div className="question-block">
          <h3>7. 여행 동반자는?</h3>
          {companions.map((c, i) => (
            <label key={i} className="option-item">
              <input type="radio" name="companion" value={c} />
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
};

export default SurveyForm;
