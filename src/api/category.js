// src/api/category.js

// 1) BASE 도메인 (반드시 .env의 REACT_APP_API_PREFIX를 쓰는 구성)
//    없으면 빈 문자열("")이 되어 상대경로 호출을 피할 수 없음 → 반드시 .env 세팅 권장
const RAW_BASE =
  process.env.REACT_APP_API_PREFIX ||
  (typeof import.meta !== 'undefined' &&
    import.meta.env &&
    (import.meta.env.VITE_API_PREFIX || import.meta.env.VITE_API_BASE_URL)) ||
  '';

const API_BASE = RAW_BASE.replace(/\/$/, '');
const API_V1 = `${API_BASE}/api/v1`;

// 공통 fetch (기본은 credentials: 'omit'으로 CORS 이슈 최소화)
async function req(url, opts = {}) {
  const res = await fetch(url, {
    credentials: opts.credentials ?? 'omit',
    headers: { 'Content-Type': 'application/json', ...(opts.headers || {}) },
    ...opts,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => '');
    const err = new Error(`HTTP ${res.status}`);
    err.status = res.status;
    err.body = text;
    throw err;
  }
  return res.json();
}

// 여러 후보 URL을 순서대로 시도
async function tryFirst(urls, opts) {
  let lastErr = null;
  for (const u of urls) {
    try {
      return await req(u, opts);
    } catch (e) {
      lastErr = e;
      // 404 포함 모든 에러는 다음 후보로 진행
    }
  }
  throw lastErr || new Error('No endpoints matched');
}

/** [GET] 서브카테고리별 장소 */
export async function getPlacesBySubCategory(label) {
  const enc = encodeURIComponent(label);
  const urls = [
    `${API_V1}/places/subcategory/${enc}`,
    `${API_BASE}/places/subcategory/${enc}`,
    `${API_V1}/place/subcategory/${enc}`,
    `${API_BASE}/place/subcategory/${enc}`,
  ];
  try {
    return await tryFirst(urls);
  } catch (e) {
    console.warn('getPlacesBySubCategory error:', e);
    if (e.status === 404) return [];
    throw e;
  }
}

/** [GET] 전체 장소 (페이지네이션) */
export async function getAllPlaces(page = 1, limit = 100) {
  const qs = `?page=${page}&limit=${limit}`;
  const urls = [
    `${API_V1}/places${qs}`,
    `${API_BASE}/places${qs}`,
  ];
  try {
    return await tryFirst(urls);
  } catch (e) {
    console.warn('getAllPlaces error:', e);
    if (e.status === 404) return { places: [], total: 0 };
    throw e;
  }
}

/** [GET] 장소 상세 */
export async function getPlaceById(id) {
  const enc = encodeURIComponent(id);
  const urls = [
    `${API_V1}/places/${enc}`,
    `${API_BASE}/places/${enc}`,
    `${API_V1}/place/${enc}`,
    `${API_BASE}/place/${enc}`,
  ];
  try {
    return await tryFirst(urls);
  } catch (e) {
    console.error('getPlaceById error:', e);
    // 404 등 상세 못 찾으면 null 반환 → 페이지에서 샘플로 대체
    return null;
  }
}

/** [GET] 관광지 혼잡도(이름 기반) 
 * 백엔드 스펙:
 *   GET /api/v1/crowding/attraction/:placeName
 * 반환: { success: true|false, message: "혼잡도: 92.51%" | "혼잡도 정보 없음" }
 */
export async function getAttractionCrowdingByName(placeName) {
  const enc = encodeURIComponent(placeName);
  const url = `${API_V1}/crowding/attraction/${enc}`;

  try {
    return await req(url, { credentials: 'omit' });
  } catch (e) {
    console.warn('getAttractionCrowdingByName error:', e);
    // 실패 시에도 UI 일관성을 위해 표준 형태로 반환
    return { success: false, message: '혼잡도 정보를 불러올 수 없습니다.' };
  }
}
