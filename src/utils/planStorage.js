// src/utils/planStorage.js
// 로컬 스토리지에 여행 코스를 저장/불러오기 (React 요소 제거한 "순수 데이터"만 저장)

const STORAGE_KEY = "tripPlans";

// 내부 유틸: 전체 목록 읽기/쓰기
function readAll() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch (e) {
    console.error("planStorage readAll parse error:", e);
    return [];
  }
}

function writeAll(arr) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(arr));
  } catch (e) {
    console.error("planStorage writeAll stringify error:", e);
  }
}

// React 요소, 함수 등 비직렬화 값 제거
function sanitizeDays(days) {
  if (!Array.isArray(days)) return [];
  return days.map((day) => ({
    date: day?.date ?? "",
    dayName: day?.dayName ?? "",
    // places에서 필요한 필드만 남김
    places: Array.isArray(day?.places)
      ? day.places.map((p) => ({
          id: String(p?.id ?? ""),
          name: String(p?.name ?? ""),
          placeId: p?.placeId ?? null,
          time: p?.time ?? "",
          // icon 등 React 요소/함수/객체는 저장하지 않음
        }))
      : [],
  }));
}

export function listPlans() {
  // 최신순 정렬
  return readAll().sort((a, b) => (b.createdAt || 0) - (a.createdAt || 0));
}

export function savePlan({ title, days, cover = null }) {
  const all = readAll();
  const id = `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
  const entry = {
    id,
    title: String(title || "내 여행 코스"),
    days: sanitizeDays(days),
    cover,
    createdAt: Date.now(),
  };
  all.push(entry);
  writeAll(all);
  return id;
}

export function getPlan(id) {
  return readAll().find((p) => p.id === id) || null;
}

export function deletePlan(id) {
  const next = readAll().filter((p) => p.id !== id);
  writeAll(next);
}
