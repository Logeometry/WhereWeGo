import random
from datetime import datetime, timedelta, time, date
from typing import List, Dict
from .travel_time_estimator import TravelTimeService

class ItineraryService:
    def __init__(self, estimator: TravelTimeService, alpha: float = 0.5):
        self.estimator = estimator
        self.alpha = alpha

    def generate_ranked_course(
        self,
        candidates: List[Dict],
        day: date,
        origin: Dict,
        dest: Dict,
        start_time: time,
        end_time: time,
        avg_stay: int = 60
    ) -> List[Dict]:
        day_start = datetime.combine(day, start_time)
        day_end   = datetime.combine(day, end_time)

        # 식사 시간 블록
        lunch_start = datetime.combine(day, time(12, 0))
        lunch_end   = lunch_start + timedelta(hours=1)
        dinner_start = datetime.combine(day, time(18, 0))
        dinner_end   = dinner_start + timedelta(hours=1)

        time_blocks = []
        if day_start < lunch_start:
            time_blocks.append((day_start, min(lunch_start, day_end)))
        if lunch_end < dinner_start and lunch_end < day_end:
            time_blocks.append((lunch_end, min(dinner_start, day_end)))
        if dinner_end < day_end:
            time_blocks.append((dinner_end, day_end))

        # 방문 여부 플래그 초기화
        for place in candidates:
            place['_used'] = False

        result = []
        prev_coord = origin['coords']
        result.append({'place_id': origin['place_id'], 'type': 'origin', 'time': day_start})

        # 각 시간 블록마다 가장 점수 낮은(place) 선택
        for block_start, block_end in time_blocks:
            best = None
            best_score = float('inf')

            for place in candidates:
                if place['_used']:
                    continue
                coord = place['coords']
                # walk 모드로 거리 기반 시간 추정 
                # 추후 이동 수단 추가 구현 시, drive 모드로 자건거 혹은 자동차를 추가가능
                travel_min = self.estimator.estimate_time(prev_coord, coord, mode="walk")
                est_start = block_start + timedelta(minutes=travel_min)
                est_end   = est_start + timedelta(minutes=avg_stay)
                if est_end > block_end:
                    continue

                # α·travel + (1-α)·(1-rec_score)
                rec = place.get('rec_score', 0.0)
                score = self.alpha * travel_min + (1 - self.alpha) * (1 - rec)
                if score < best_score:
                    best_score = score
                    best = (place, travel_min)

            if best:
                place, travel_min = best
                visit_start = block_start + timedelta(minutes=travel_min)
                visit_end   = visit_start + timedelta(minutes=avg_stay)

                result.append({
                    'place_id':    place['place_id'],
                    'start_time':  visit_start,
                    'end_time':    visit_end,
                    'travel_time': travel_min
                })
                place['_used'] = True
                prev_coord = place['coords']

        # 식사 삽입
        if day_start <= lunch_start <= day_end:
            result.append({
                'place_id':   '점심',
                'start_time': lunch_start,
                'end_time':   lunch_end,
                'type':       'meal'
            })
        if day_start <= dinner_start <= day_end:
            result.append({
                'place_id':   '저녁',
                'start_time': dinner_start,
                'end_time':   dinner_end,
                'type':       'meal'
            })

        # 도착지
        result.append({'place_id': dest['place_id'], 'type': 'destination', 'time': day_end})

        # 시간순 정렬
        result.sort(key=lambda x: x.get('start_time') or x.get('time'))
        return result

    def generate_multi_day_course(
        self,
        candidates: List[Dict],
        origin: Dict,
        dest: Dict,
        start_dt: datetime,
        end_dt: datetime,
        avg_stay: int = 60
    ) -> List[Dict]:
        itinerary = []
        used_places = set()
        current_day = start_dt.date()
        last_day    = end_dt.date()

        while current_day <= last_day:
            st = start_dt.time() if current_day == start_dt.date() else time(9, 0)
            et = end_dt.time()   if current_day == last_day           else time(18, 0)

            day_candidates = [c for c in candidates if c['place_id'] not in used_places]
            day_plan = self.generate_ranked_course(
                candidates=day_candidates,
                day=current_day,
                origin=origin,
                dest=dest,
                start_time=st,
                end_time=et,
                avg_stay=avg_stay
            )

            # 이번 날 방문지 기록
            for item in day_plan:
                if 'start_time' in item:
                    used_places.add(item['place_id'])

            itinerary.append({'date': current_day, 'plan': day_plan})
            current_day += timedelta(days=1)

        return itinerary
