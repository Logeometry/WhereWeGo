# WhereWeGo - 부산 여행 플래너

> React 기반 부산 관광지 추천 및 여행 일정 관리 프론트엔드 애플리케이션

---

## 📁 프로젝트 구조

```
src/
├── 🏠 루트: 앱 초기화 및 전역 설정
├── 📦 assets: 정적 리소스
├── 🧩 components: 재사용 가능한 UI 컴포넌트
│   └── survey: 설문조사 전용 컴포넌트
├── 🌐 contexts: 전역 상태 관리
├── 📊 data: 정적 데이터 및 설정
├── 🪝 hooks: 커스텀 훅
├── 📄 pages: 페이지 컴포넌트
│   └── SurveyForm: 설문 폼 전용
├── 🔌 api: 백엔드 API 통신
└── 🛠️ utils: 유틸리티 함수
```

---

## 🛠️ 기술 스택

| 분류 | 기술 |
|------|------|
| 프레임워크 | React 18 + Create React App |
| UI 라이브러리 | Material-UI (MUI) v6 |
| 라우팅 | React Router DOM v7 |
| 스타일링 | SCSS + Emotion |
| 상태관리 | React Context API |
| HTTP 통신 | Axios + Fetch API |
| 지도 | Tmap API, Google Maps API |
| 드래그앤드롭 | react-beautiful-dnd |

---

# 📘 TypeScript 도입 가이드

## 1. 도입 목적

- **타입 안전성**: 런타임 에러를 컴파일 타임에 발견
- **개발 생산성**: IDE 자동완성 및 리팩토링 지원 강화
- **코드 문서화**: 타입 정의가 곧 문서 역할
- **유지보수성**: 대규모 코드베이스에서 변경 영향 파악 용이

---

## 2. 설치 방법

```bash
# TypeScript 및 타입 정의 설치
npm install --save-dev typescript @types/react @types/react-dom @types/node

# 추가 라이브러리 타입 (필요 시)
npm install --save-dev @types/react-beautiful-dnd
```

```bash
# tsconfig.json 생성 (CRA 자동 생성)
npx tsc --init
```

> **참고**: Create React App은 `.ts`/`.tsx` 파일을 자동 인식하므로 별도 설정 없이 점진적 도입 가능

---

## 3. 마이그레이션 우선순위

### 🔴 1단계: 핵심 영역 (즉시 권장)

| 파일/폴더 | 변환 대상 | 효과 | 난이도 |
|-----------|----------|------|--------|
| `src/api/` | `category.js` → `category.ts` | 백엔드 응답 타입 안전성 | ⭐ 낮음 |
| `src/api/` | `nearby.js` → `nearby.ts` | API 호출 타입 체크 | ⭐ 낮음 |
| `src/contexts/` | `ItineraryContext.js` → `.tsx` | 전역 상태 타입 안전성 | ⭐ 낮음 |
| `src/contexts/` | `WishlistContext.js` → `.tsx` | 전역 상태 타입 안전성 | ⭐ 낮음 |

### 🟡 2단계: 데이터 레이어

| 파일/폴더 | 변환 대상 | 효과 | 난이도 |
|-----------|----------|------|--------|
| `src/data/` | `touristData.js` → `.ts` | 관광지 데이터 구조 명확화 | ⭐ 낮음 |
| `src/data/` | `categoriesData.js` → `.tsx` | 카테고리 타입 정의 | ⭐ 낮음 |

### 🟢 3단계: 복잡한 페이지

| 파일 | 효과 | 난이도 |
|------|------|--------|
| `TravelPlanPage.js` | 일정 데이터 타입 안전성 | ⭐⭐ 중간 |
| `TouristSpotRecommendPage.js` | 추천 데이터 타입 체크 | ⭐⭐ 중간 |
| `SurveyPage.js` | 설문 상태 타입 안전성 | ⭐⭐ 중간 |

### 🔵 4단계: UI 컴포넌트 (선택)

| 파일 | 효과 | 난이도 |
|------|------|--------|
| `Header.js` | Props 타입 체크 | ⭐ 낮음 |
| `Footer.js` | Props 타입 체크 | ⭐ 낮음 |
| 기타 단순 컴포넌트 | 선택적 적용 | ⭐ 낮음 |

---

## 4. 핵심 타입 정의 (예시)

### 4.1 관광지 (Place) 타입

```typescript
// src/types/place.ts

/** 좌표 타입 */
interface GeoLocation {
  type: 'Point';
  coordinates: [number, number]; // [longitude, latitude]
}

/** 관광지 기본 정보 */
interface Place {
  _id: string;
  name: string;
  description: string;
  location: GeoLocation;
  estimated_duration: number;
  subcategory: string;
  parentCategory: string;
  image?: string;
  rating?: number;
  reviewCount?: number;
  phone?: string;
  website?: string;
  entranceFee?: string;
  hours?: string;
  facilities?: string[];
  tags?: string[];
}

/** 프론트엔드용 관광지 (좌표 변환 후) */
interface TouristSpot {
  id: string;
  name: string;
  description: string;
  duration: number;
  locX: number; // longitude
  locY: number; // latitude
  category?: string;
  image?: string;
}

export type { GeoLocation, Place, TouristSpot };
```

### 4.2 여행 일정 타입

```typescript
// src/types/itinerary.ts

import type { TouristSpot } from './place';

/** 일별 일정 */
interface DailySchedule {
  day: number;
  date: string; // YYYY-MM-DD
  places: TouristSpot[];
  isFirstDay: boolean;
  isLastDay: boolean;
}

/** 여행 계획 전체 */
interface TravelPlan {
  departureCity: string;
  otherCity?: string;
  travelDuration: number;
  travelStartDate: string;
  startingPoint: string;
  dailySchedule: DailySchedule[];
  travelTips?: string;
}

/** 설문 결과 state */
interface SurveyState {
  mode: 'simple' | 'detailed';
  departureCity: string;
  otherCity?: string;
  travelDuration: number;
  travelStartDate: string;
  startingPoint: string;
  preferences: Record<string, boolean>;
  surveyAttractions?: string[];
  detailed?: DetailedSurveyAnswers;
}

interface DetailedSurveyAnswers {
  travelType?: string;
  budgetLevel?: string;
  duration?: number;
  activities?: string[];
  stayImportance?: string;
  popularity?: string;
  companion?: string;
}

export type { DailySchedule, TravelPlan, SurveyState, DetailedSurveyAnswers };
```

### 4.3 API 응답 타입

```typescript
// src/types/api.ts

import type { Place, DailySchedule } from './index';

/** 혼잡도 응답 */
interface CrowdingResponse {
  success: boolean;
  message: string;
}

/** 장소 목록 응답 */
interface PlacesResponse {
  places: Place[];
  total: number;
}

/** 일정 생성 요청 */
interface GenerateItineraryRequest {
  departureCity: string;
  otherCity?: string;
  travelDuration: number;
  travelStartDate: string;
  startingPoint: string;
  preferences: Record<string, boolean>;
  surveyAttractions: string[];
}

/** 일정 생성 응답 */
interface GenerateItineraryResponse {
  dailySchedule: DailySchedule[];
  travelTips: string;
}

export type {
  CrowdingResponse,
  PlacesResponse,
  GenerateItineraryRequest,
  GenerateItineraryResponse,
};
```

### 4.4 Context 타입

```typescript
// src/types/context.ts

import type { TouristSpot } from './place';

/** Itinerary Context */
interface ItineraryContextValue {
  selectedSpots: TouristSpot[];
  addSpot: (spot: TouristSpot) => void;
  removeSpot: (id: string) => void;
  clearAll: () => void;
  setSelectedSpots: React.Dispatch<React.SetStateAction<TouristSpot[]>>;
}

/** Wishlist Context */
interface WishlistContextValue {
  wishlistItems: Place[];
  wishlistIds: string[];
  addToWishlist: (itemId: string) => void;
  removeFromWishlist: (itemId: string) => void;
  isWishlisted: (itemId: string) => boolean;
}

/** Search Context */
interface SearchContextValue {
  recentSearches: string[];
  updateSearches: (query: string) => void;
  removeSearch: (index: number) => void;
  clearAllSearches: () => void;
}

export type { ItineraryContextValue, WishlistContextValue, SearchContextValue };
```

---

## 5. 파일별 변환 가이드

### 5.1 `src/api/category.ts` 변환 예시

```typescript
// src/api/category.ts
import type { Place, CrowdingResponse, PlacesResponse } from '../types';

const API_BASE = process.env.REACT_APP_API_PREFIX || '';
const API_V1 = `${API_BASE}/api/v1`;

async function req<T>(url: string, opts: RequestInit = {}): Promise<T> {
  const res = await fetch(url, {
    credentials: opts.credentials ?? 'omit',
    headers: { 'Content-Type': 'application/json', ...opts.headers },
    ...opts,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => '');
    const err = new Error(`HTTP ${res.status}`) as Error & { status: number; body: string };
    err.status = res.status;
    err.body = text;
    throw err;
  }
  return res.json();
}

export async function getPlacesBySubCategory(label: string): Promise<Place[]> {
  const enc = encodeURIComponent(label);
  try {
    return await req<Place[]>(`${API_V1}/places/subcategory/${enc}`);
  } catch (e) {
    console.warn('getPlacesBySubCategory error:', e);
    return [];
  }
}

export async function getPlaceById(id: string): Promise<Place | null> {
  const enc = encodeURIComponent(id);
  try {
    return await req<Place>(`${API_V1}/places/${enc}`);
  } catch (e) {
    console.error('getPlaceById error:', e);
    return null;
  }
}

export async function getAttractionCrowdingByName(placeName: string): Promise<CrowdingResponse> {
  const enc = encodeURIComponent(placeName);
  try {
    return await req<CrowdingResponse>(`${API_V1}/crowding/attraction/${enc}`);
  } catch (e) {
    console.warn('getAttractionCrowdingByName error:', e);
    return { success: false, message: '혼잡도 정보를 불러올 수 없습니다.' };
  }
}
```

### 5.2 `src/contexts/ItineraryContext.tsx` 변환 예시

```typescript
// src/contexts/ItineraryContext.tsx
import React, { createContext, useContext, useMemo, useState, ReactNode } from 'react';
import type { TouristSpot, ItineraryContextValue } from '../types';

const ItineraryContext = createContext<ItineraryContextValue | null>(null);

interface ItineraryProviderProps {
  children: ReactNode;
}

export function ItineraryProvider({ children }: ItineraryProviderProps) {
  const [selectedSpots, setSelectedSpots] = useState<TouristSpot[]>([]);

  const addSpot = (spot: TouristSpot) => {
    setSelectedSpots((prev) => 
      prev.some((s) => s.id === spot.id) ? prev : [...prev, spot]
    );
  };

  const removeSpot = (id: string) => {
    setSelectedSpots((prev) => prev.filter((s) => s.id !== id));
  };

  const clearAll = () => setSelectedSpots([]);

  const value = useMemo<ItineraryContextValue>(
    () => ({ selectedSpots, addSpot, removeSpot, clearAll, setSelectedSpots }),
    [selectedSpots]
  );

  return (
    <ItineraryContext.Provider value={value}>
      {children}
    </ItineraryContext.Provider>
  );
}

export function useItinerary(): ItineraryContextValue {
  const ctx = useContext(ItineraryContext);
  if (!ctx) {
    throw new Error('useItinerary must be used within ItineraryProvider');
  }
  return ctx;
}
```

---

## 6. tsconfig.json 권장 설정

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "lib": ["DOM", "DOM.Iterable", "ES2020"],
    "allowJs": true,
    "skipLibCheck": true,
    "esModuleInterop": true,
    "allowSyntheticDefaultImports": true,
    "strict": true,
    "forceConsistentCasingInFileNames": true,
    "noFallthroughCasesInSwitch": true,
    "module": "ESNext",
    "moduleResolution": "node",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "baseUrl": "src",
    "paths": {
      "@/*": ["./*"],
      "@components/*": ["components/*"],
      "@pages/*": ["pages/*"],
      "@contexts/*": ["contexts/*"],
      "@api/*": ["api/*"],
      "@types/*": ["types/*"],
      "@utils/*": ["utils/*"],
      "@data/*": ["data/*"]
    }
  },
  "include": ["src"],
  "exclude": ["node_modules", "build"]
}
```

---

## 7. 마이그레이션 체크리스트

### 1단계: 기반 설정
- [ ] TypeScript 및 타입 패키지 설치
- [ ] `tsconfig.json` 생성 및 설정
- [ ] `src/types/` 폴더 생성
- [ ] 핵심 타입 정의 파일 작성 (`place.ts`, `itinerary.ts`, `api.ts`, `context.ts`)
- [ ] `src/types/index.ts` 배럴 파일 생성

### 2단계: API 레이어 변환
- [ ] `src/api/category.js` → `category.ts`
- [ ] `src/api/nearby.js` → `nearby.ts`

### 3단계: Context 변환
- [ ] `src/contexts/ItineraryContext.js` → `.tsx`
- [ ] `src/contexts/WishlistContext.js` → `.tsx`
- [ ] `src/SearchContext.js` → `.tsx`

### 4단계: 데이터 레이어 변환
- [ ] `src/data/touristData.js` → `.ts`
- [ ] `src/data/categoriesData.js` → `.tsx`
- [ ] `src/data/surveyAttractions.js` → `.ts`

### 5단계: 페이지 변환
- [ ] `TravelPlanPage.js` → `.tsx`
- [ ] `TouristSpotRecommendPage.js` → `.tsx`
- [ ] `SurveyPage.js` → `.tsx`

### 6단계: 컴포넌트 변환 (선택)
- [ ] `Header.js` → `.tsx`
- [ ] 기타 컴포넌트

---

## 8. 주의사항

1. **점진적 도입**: 전체 변환보다 파일 단위로 점진적 변환 권장
2. **strict 모드**: 초기에는 `strict: false`로 시작 후 점진적으로 활성화 가능
3. **any 사용 최소화**: 임시로 `any` 사용 시 `// TODO: 타입 정의 필요` 주석 추가
4. **테스트**: 각 파일 변환 후 기능 테스트 필수
5. **타입 가드**: 백엔드 응답은 런타임 검증 함께 고려

---

## 9. 참고 자료

- [TypeScript 공식 문서](https://www.typescriptlang.org/docs/)
- [React TypeScript Cheatsheet](https://react-typescript-cheatsheet.netlify.app/)
- [CRA + TypeScript](https://create-react-app.dev/docs/adding-typescript/)
