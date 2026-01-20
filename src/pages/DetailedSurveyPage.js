import React, { useMemo, useState } from "react";
import styles from "./DetailedSurveyPage.module.scss";

/* ──────────────────────────────────────────────────────────────
   샘플 관광지 데이터 (public/image 경로에 이미지 넣어두면 표시돼요)
────────────────────────────────────────────────────────────── */
const SPOT_SAMPLES = [
  {
    id: "hdae",
    name: "해운대 해수욕장",
    category: "해변",
    region: "해운대구",
    address: "부산 해운대구 해운대해변로",
    image: "/image/haeundae.jpg",
    tags: ["바다", "산책", "야경"],
  },
  {
    id: "gwangalli",
    name: "광안리 해변",
    category: "해변",
    region: "수영구",
    address: "부산 수영구 광안해변로",
    image: "/image/gwangalli.jpg",
    tags: ["광안대교", "카페", "야경"],
  },
  {
    id: "gamcheon",
    name: "감천문화마을",
    category: "문화",
    region: "사하구",
    address: "부산 사하구 감내2로",
    image: "/image/gamcheon.jpg",
    tags: ["알록달록", "전망", "포토스팟"],
  },
  {
    id: "jagalchi",
    name: "자갈치시장",
    category: "음식",
    region: "중구",
    address: "부산 중구 자갈치해안로",
    image: "/image/jagalchi.jpg",
    tags: ["해산물", "시장", "현지맛집"],
  },
  {
    id: "taejongdae",
    name: "태종대",
    category: "자연",
    region: "영도구",
    address: "부산 영도구 전망로",
    image: "/image/taejongdae.jpg",
    tags: ["절벽", "바다열차", "등대"],
  },
  {
    id: "songdo",
    name: "송도해수욕장",
    category: "해변",
    region: "서구",
    address: "부산 서구 송도해변로",
    image: "/image/songdo.jpg",
    tags: ["케이블카", "스카이워크"],
  },
  {
    id: "yongdusan",
    name: "용두산공원",
    category: "자연",
    region: "중구",
    address: "부산 중구 용두산길",
    image: "/image/yongdusan.jpg",
    tags: ["부산타워", "전망"],
  },
  {
    id: "beomeosa",
    name: "범어사",
    category: "문화",
    region: "금정구",
    address: "부산 금정구 범어사로",
    image: "/image/beomeosa.jpg",
    tags: ["사찰", "산책"],
  },
];

/**
 * DetailedSurveyPage
 * - 단계형 선택(활동 → 활동성 → 시간대 → 계절 → 중요 요소 → 샘플 관광지 → 완료)
 * - 5 라운드 카드 비교 투표
 * - AI 개인화 추천 패널
 *
 * 서버 엔드포인트 (필요 시 경로만 바꾸세요):
 *  POST /select                 { step, value }
 *  GET  /recommendations        -> { status:'success', recommendations:{ rounds:[{primary,alternative}, ...] } }
 *  POST /vote                   { round_number, choice, item_name }
 *  GET  /ml-recommendations?k=10
 *  GET  /reset
 */
export default function DetailedSurveyPage() {
  // ──────────────────────────────────────────────────────────────
  // 상태
  const [selections, setSelections] = useState({
    activity: null, // 자연풍경/자연산림/관람및체험/...
    activity_level: null, // 높음/중간/낮음
    time: null, // 오전/오후/저녁
    season: null, // 봄/여름/가을/겨울
    preference: null, // 활동성/시간대
  });

  const [currentStep, setCurrentStep] = useState(
    "activity"
  ); // 'activity'|'activity_level'|'time'|'season'|'preference'|'spots'|'complete'|'recommend'
  const [loading, setLoading] = useState(false);

  // 샘플 관광지 선택
  const [selectedSpotIds, setSelectedSpotIds] = useState(new Set());
  const toggleSpot = (id) =>
    setSelectedSpotIds((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  const isSelectedSpot = (id) => selectedSpotIds.has(id);

  // 추천/투표 관련
  const [rounds, setRounds] = useState([]); // [{primary:{item,reason}, alternative:{item,reason}} ...]
  const [currentRound, setCurrentRound] = useState(1);
  const [userChoices, setUserChoices] = useState([]); // [{round, choice, item}]
  const totalRounds = 5;

  // ML 추천 관련
  const [mlOpen, setMlOpen] = useState(false);
  const [mlLoading, setMlLoading] = useState(false);
  const [mlResult, setMlResult] = useState(null); // { ml_recommendations:{recommendations:[]}, base_user_info, personalization_info, vote_summary }

  // 표시용 값
  const progressPercent = useMemo(
    () => Math.min(100, Math.round((currentRound / totalRounds) * 100)),
    [currentRound]
  );

  // ──────────────────────────────────────────────────────────────
  // 서버 연동 유틸
  const postJSON = async (url, body) => {
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    return res.json();
  };

  const getJSON = async (url) => {
    const res = await fetch(url);
    return res.json();
  };

  // ──────────────────────────────────────────────────────────────
  // 선택 처리
  const handleSelect = async (step, value) => {
    setSelections((prev) => ({ ...prev, [step]: value }));

    try {
      await postJSON("/select", { step, value });
    } catch {
      /* 서버 실패해도 로컬로 진행 */
    } finally {
      const next = inferNextStep(step);
      setCurrentStep(next);
    }
  };

  const inferNextStep = (step) => {
    // spots(샘플 관광지 선택) 단계를 포함
    const order = [
      "activity",
      "activity_level",
      "time",
      "season",
      "preference",
      "spots",
      "complete",
    ];
    const idx = order.indexOf(step);
    return order[idx + 1] || "complete";
  };

  // 완료 → 추천 시작
  const startRecommendations = async () => {
    setCurrentStep("recommend");
    setLoading(true);
    setRounds([]);
    setCurrentRound(1);
    setUserChoices([]);

    try {
      // 샘플 선택을 서버에 같이 보내고 싶다면 POST로 변경.
      // 예시:
      // const data = await postJSON("/recommendations", { selectedSpotIds: [...selectedSpotIds] });
      const data = await getJSON("/recommendations");
      if (data?.status === "success") {
        const r = data.recommendations?.rounds || [];
        setRounds(r.slice(0, totalRounds));
      } else {
        console.error("추천 실패:", data?.message);
      }
    } catch (e) {
      console.error("추천 요청 실패:", e);
    } finally {
      setLoading(false);
    }
  };

  // 현재 라운드
  const thisRound = rounds[currentRound - 1] || null;

  // 카드 선택 → 투표
  const onPick = (choice) => {
    submitVote(choice);
  };

  const submitVote = async (choice) => {
    if (!thisRound) return;
    const pickedItem =
      choice === "primary" ? thisRound.primary?.item : thisRound.alternative?.item;

    setUserChoices((prev) => [...prev, { round: currentRound, choice, item: pickedItem }]);

    try {
      await postJSON("/vote", {
        round_number: currentRound,
        choice,
        item_name: pickedItem?.name,
      });
    } catch (e) {
      console.error("투표 전송 실패:", e);
    } finally {
      setTimeout(() => {
        if (currentRound < totalRounds) setCurrentRound((n) => n + 1);
      }, 250);
    }
  };

  // 다시 시작
  const resetAll = async () => {
    setSelections({
      activity: null,
      activity_level: null,
      time: null,
      season: null,
      preference: null,
    });
    setSelectedSpotIds(new Set());
    setCurrentStep("activity");
    setRounds([]);
    setCurrentRound(1);
    setUserChoices([]);
    setMlOpen(false);
    setMlLoading(false);
    setMlResult(null);

    try {
      await getJSON("/reset");
    } catch (e) {
      console.warn("reset error:", e);
    }
  };

  // ML 추천
  const openMlRecommendation = async () => {
    setMlOpen(true);
    setMlLoading(true);
    setMlResult(null);

    try {
      const data = await getJSON("/ml-recommendations?k=10");
      setMlResult(data);
    } catch (e) {
      console.error("ML 추천 오류:", e);
      setMlResult({ error: "네트워크 오류가 발생했습니다." });
    } finally {
      setMlLoading(false);
    }
  };

  // ──────────────────────────────────────────────────────────────
  return (
    <div className={styles.pageBg}>
      <div className={styles.container}>
        <h1 className={styles.title}>관광 선호도 조사</h1>

        {/* 단계: 활동 */}
        {currentStep === "activity" && (
          <Step title="관심 있는 활동을 선택해주세요">
            <Grid className={styles.activityGrid}>
              {[
                "자연풍경",
                "자연산림",
                "관람및체험",
                "휴양",
                "테마거리",
                "예술감상",
                "공연관람",
                "트레킹",
              ].map((v) => (
                <button
                  key={v}
                  className={styles.selectionBtn}
                  onClick={() => handleSelect("activity", v)}
                >
                  {v}
                </button>
              ))}
            </Grid>
          </Step>
        )}

        {/* 단계: 활동성 */}
        {currentStep === "activity_level" && (
          <Step title="선호하는 활동성을 선택해주세요">
            <Grid className={styles.timeGrid}>
              {["높음", "중간", "낮음"].map((v) => (
                <button
                  key={v}
                  className={styles.selectionBtn}
                  onClick={() => handleSelect("activity_level", v)}
                >
                  {v}
                </button>
              ))}
            </Grid>
          </Step>
        )}

        {/* 단계: 시간대 */}
        {currentStep === "time" && (
          <Step title="선호하는 시간대를 선택해주세요">
            <Grid className={styles.timeGrid}>
              {["오전", "오후", "저녁"].map((v) => (
                <button
                  key={v}
                  className={styles.selectionBtn}
                  onClick={() => handleSelect("time", v)}
                >
                  {v}
                </button>
              ))}
            </Grid>
          </Step>
        )}

        {/* 단계: 계절 */}
        {currentStep === "season" && (
          <Step title="선호하는 계절을 선택해주세요">
            <Grid className={styles.seasonGrid}>
              {["봄", "여름", "가을", "겨울"].map((v) => (
                <button
                  key={v}
                  className={styles.selectionBtn}
                  onClick={() => handleSelect("season", v)}
                >
                  {v}
                </button>
              ))}
            </Grid>
          </Step>
        )}

        {/* 단계: 중요 요소 */}
        {currentStep === "preference" && (
          <Step title="중요하게 생각하는 요소를 선택해주세요">
            <Grid className={styles.preferenceGrid}>
              {["활동성", "시간대"].map((v) => (
                <button
                  key={v}
                  className={styles.selectionBtn}
                  onClick={() => handleSelect("preference", v)}
                >
                  {v}
                </button>
              ))}
            </Grid>
          </Step>
        )}

        {/* 단계: 샘플 관광지 선택 */}
        {currentStep === "spots" && (
          <div className={styles.step}>
            <div className={styles.stepTitle}>
              마음에 드는 <b>샘플 관광지</b>를 선택하세요 <span style={{ color: "#6b7280" }}>(복수 선택 가능)</span>
            </div>

            <div className={`${styles.grid} ${styles.spotGrid}`}>
              {SPOT_SAMPLES.map((spot) => (
                <div
                  key={spot.id}
                  className={`${styles.spotCard} ${
                    isSelectedSpot(spot.id) ? styles.spotCardActive : ""
                  }`}
                  onClick={() => toggleSpot(spot.id)}
                  role="button"
                  tabIndex={0}
                >
                  <div className={styles.spotThumb}>
                    <img src={spot.image} alt={spot.name} />
                  </div>
                  <div className={styles.spotBody}>
                    <div className={styles.spotTopRow}>
                      <span className={styles.spotCategory}>{spot.category}</span>
                      {isSelectedSpot(spot.id) && (
                        <span className={styles.spotPicked}>선택됨</span>
                      )}
                    </div>
                    <div className={styles.spotName}>{spot.name}</div>
                    <div className={styles.spotMeta}>
                      <span>{spot.region}</span>
                      <span className={styles.spotDot}>•</span>
                      <span className={styles.spotAddr}>{spot.address}</span>
                    </div>
                    <div className={styles.spotTags}>
                      {(spot.tags || []).slice(0, 3).map((t, i) => (
                        <span key={i} className={styles.spotTag}>
                          #{t}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              ))}
            </div>

            <div className={styles.spotActions}>
              <button
                className={styles.selectionBtn}
                onClick={() => setCurrentStep("complete")}
                disabled={selectedSpotIds.size === 0}
              >
                {selectedSpotIds.size > 0
                  ? `선택 완료 (${selectedSpotIds.size}개)`
                  : "선택 후 다음"}
              </button>
            </div>
          </div>
        )}

        {/* 완료 → 추천 시작 버튼 */}
        {currentStep === "complete" && (
          <div className={styles.step}>
            <div className={styles.completeMessage}>
              선택이 완료되었습니다! 두가지 관광지 중 하나를 선택해주세요.
            </div>
            <button
              className={styles.selectionBtn}
              onClick={startRecommendations}
              style={{ marginTop: 20 }}
            >
              심화 설문조사 하기
            </button>
          </div>
        )}

        {/* 추천/투표 단계 */}
        {currentStep === "recommend" && (
          <div className={styles.step}>
            <div className={styles.stepTitle}>
              {currentRound <= totalRounds
                ? `라운드 ${currentRound}/${totalRounds} - 관광지를 선택해주세요`
                : "🎉 모든 라운드 완료!"}
            </div>

            <div className={styles.progressBar}>
              <div
                className={styles.progressFill}
                style={{ width: `${progressPercent}%` }}
              />
            </div>

            {loading && (
              <div style={{ textAlign: "center" }}>
                <div className={styles.spinner} />
                <p style={{ marginTop: 20 }}>
                  맞춤형 관광지를 찾고 있습니다...
                </p>
              </div>
            )}

            {!loading && currentRound <= totalRounds && thisRound && (
              <>
                <div>
                  <Card
                    onPick={() => onPick("primary")}
                    header="🎯 맞춤 추천"
                    data={thisRound.primary}
                  />
                  <Card
                    onPick={() => onPick("alternative")}
                    header="🔄 대안 추천"
                    data={thisRound.alternative}
                  />
                </div>

                <div style={{ marginTop: 20 }}>
                  <div className={styles.tipPrimary}>
                    💡 원하시는 관광지를 클릭해주세요
                  </div>
                  <div className={styles.tipSecondary}>
                    카드를 클릭하면 자동으로 다음 라운드로 진행됩니다
                  </div>
                </div>
              </>
            )}

            {!loading && currentRound > totalRounds && (
              <div>
                <div className={styles.completeMessage}>
                  🎉 모든 라운드가 완료되었습니다!
                </div>

                <div style={{ margin: "20px 0" }}>
                  <h3 className={styles.selectedTitle}>선택하신 관광지들</h3>
                  {userChoices.map(({ round, item }) => (
                    <div
                      key={round}
                      className={styles.recoCard}
                      style={{ margin: "10px 0" }}
                    >
                      <div className={styles.recoHeader}>라운드 {round} 선택</div>
                      <div className={styles.placeName}>{item?.name}</div>
                      <div className={styles.placeInfo}>
                        <Info label="카테고리" value={item?.category} />
                        <Info label="지역" value={item?.region} />
                        <Info
                          label="만족도 점수"
                          value={`${item?.final_score?.toFixed?.(2)}점`}
                        />
                      </div>
                    </div>
                  ))}
                </div>

                <div className={styles.finalActions}>
                  <button className={styles.mlBtn} onClick={openMlRecommendation}>
                    🤖 AI 개인화 추천 받기
                  </button>
                  <button className={styles.resetBtn} onClick={resetAll}>
                    다시 시작하기
                  </button>
                </div>

                {mlOpen && (
                  <div className={styles.mlResult}>
                    <div className={styles.stepTitle}>🤖 AI 개인화 추천 결과</div>
                    {mlLoading && <div className={styles.spinner} />}
                    {!mlLoading && (
                      <>
                        {mlResult?.error ? (
                          <div className={styles.mlError}>
                            <h4>❌ 추천 오류</h4>
                            <p> {mlResult.error} </p>
                            <p className={styles.mlErrorSub}>
                              모델 파일이 없거나 서버 오류가 발생했을 수 있습니다.
                            </p>
                          </div>
                        ) : (
                          <MlRecommendationView data={mlResult} />
                        )}
                      </>
                    )}
                    <button
                      className={styles.resetBtn}
                      onClick={() => setMlOpen(false)}
                      style={{ marginTop: 20 }}
                    >
                      결과 닫기
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* 선택값 요약 */}
        <div
          className={`${styles.selectionPanel} ${
            hasAnySelection(selections) || selectedSpotIds.size > 0
              ? ""
              : styles.hidden
          }`}
        >
          <h3>선택하신 내용</h3>
          <SelectionRow label="활동:" value={selections.activity} />
          <SelectionRow label="활동성:" value={selections.activity_level} />
          <SelectionRow label="시간대:" value={selections.time} />
          <SelectionRow label="계절:" value={selections.season} />
          <SelectionRow label="선호도:" value={selections.preference} />

          {selectedSpotIds.size > 0 && (
            <>
              <hr
                style={{
                  border: 0,
                  borderTop: "1px dashed var(--line)",
                  margin: "12px 0",
                }}
              />
              <h3
                style={{
                  textAlign: "center",
                  marginBottom: 10,
                  fontWeight: 800,
                }}
              >
                샘플 선택
              </h3>
              {[...selectedSpotIds]
                .map((id) => SPOT_SAMPLES.find((s) => s.id === id))
                .map((spot) => (
                  <div key={spot.id} className={styles.selectionItem}>
                    <span className={styles.selectionLabel}>
                      {spot.category}
                    </span>
                    <span className={styles.selectionValue}>{spot.name}</span>
                  </div>
                ))}
            </>
          )}

          <button className={styles.resetBtn} onClick={resetAll}>
            다시 선택하기
          </button>
        </div>
      </div>
    </div>
  );
}

/* ──────────────────────────────────────────────────────────────
   하위 컴포넌트
────────────────────────────────────────────────────────────── */
function Step({ title, children }) {
  return (
    <div className={styles.step}>
      <div className={styles.stepTitle}>{title}</div>
      {children}
    </div>
  );
}

function Grid({ className = "", children }) {
  return <div className={`${styles.grid} ${className}`.trim()}>{children}</div>;
}

function Card({ header, data, onPick }) {
  const item = data?.item || {};
  return (
    <div className={styles.recoCard} onClick={onPick}>
      <div className={styles.recoHeader}>{header}</div>
      <div className={styles.placeName}>{item.name}</div>

      <div className={styles.placeInfo}>
        <Info label="카테고리" value={item.category} />
        <Info label="지역" value={item.region} />
        <Info
          label="만족도 점수"
          value={`${item?.final_score?.toFixed?.(2)}점`}
        />
        <Info
          label="방문자 수"
          value={`${item?.visitors_count?.toLocaleString?.() || 0}명`}
        />
        <Info label="주소" value={item.address} />
      </div>

      <div className={styles.recoReason}>{data?.reason}</div>
    </div>
  );
}

function Info({ label, value }) {
  return (
    <div className={styles.infoItem}>
      <span className={styles.infoLabel}>{label}:</span>
      <span className={styles.infoValue}>{value}</span>
    </div>
  );
}

function SelectionRow({ label, value }) {
  return (
    <div className={styles.selectionItem}>
      <span className={styles.selectionLabel}>{label}</span>
      <span className={styles.selectionValue}>{value ?? "-"}</span>
    </div>
  );
}

function MlRecommendationView({ data }) {
  if (!data) return null;
  if (data?.status !== "success") {
    return (
      <div className={styles.mlError}>
        <h4>❌ 추천 오류</h4>
        <p>{data?.message || "추천을 가져오는데 실패했습니다."}</p>
      </div>
    );
  }

  const recs = data.ml_recommendations?.recommendations || [];
  const userInfo = data.base_user_info || {};
  const modelInfo = data.personalization_info || {};
  const totalVotes = data.vote_summary?.total_votes || 0;

  return (
    <>
      <div className={styles.mlSummary}>
        <h4>🎯 개인화 추천 기준</h4>
        <div className={styles.mlGrid}>
          <div>
            <strong>선호 활동:</strong> {userInfo.preferred_category}
          </div>
          <div>
            <strong>활동성:</strong> {userInfo.activity_level}
          </div>
          <div>
            <strong>선호 시간:</strong> {userInfo.preferred_time}
          </div>
          <div>
            <strong>선호 계절:</strong> {userInfo.preferred_season}
          </div>
          <div>
            <strong>중요 요소:</strong> {userInfo.preference_type}
          </div>
        </div>
        <p className={styles.mlNote}>
          {modelInfo.model_type} 모델이 {totalVotes}번의 선택 패턴을 분석하여{" "}
          {recs.length}개의 맞춤형 관광지를 추천해드립니다.
        </p>
      </div>

      <div>
        {recs.map((item, idx) => (
          <div key={idx} className={styles.mlItem}>
            <div className={styles.mlItemHeader}>
              <h4>
                {idx + 1}. {item.name}
              </h4>
              <span className={styles.mlScore}>
                AI 점수: {(item.score * 100).toFixed(1)}%
              </span>
            </div>
            <Info
              label="카테고리"
              value={`${item.category} (${item.category_group})`}
            />
            <Info
              label="품질 점수"
              value={`${item.final_score?.toFixed?.(2)}점`}
            />
            <div className={styles.mlReason}>{item.reason}</div>
          </div>
        ))}
      </div>
    </>
  );
}

function hasAnySelection(obj) {
  return Object.values(obj).some((v) => v !== null);
}
