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

        # 식사 시간
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

        used_places = set()
        result = []
        prev_coord = origin['coords']
        result.append({
            'place_id': origin['place_id'],
            'type': 'origin',
            'start_time': day_start,
            'end_time': day_start,
            'travel_time': 0
        })

        for block_start, block_end in time_blocks:
            best = None
            best_score = float('inf')

            for place in candidates:
                if place["place_id"] in used_places:
                    continue
                coord = place['coords']
                # walk 모드로 거리 기반 시간 추정
                start = origin['coords']
                end = dest['coords']
                print(f"[DEBUG] walk API input: start=({start[1]}, {start[0]}), end=({end[1]}, {end[0]})")

                travel_min = self.estimator.estimate_time(prev_coord, coord, mode="")
                est_start = block_start + timedelta(minutes=travel_min)
                est_end   = est_start + timedelta(minutes=avg_stay)
                print(f"[DEBUG] trying place: {place['place_id']} - travel_min: {travel_min}, est_start: {est_start}, est_end: {est_end}, block: {block_start} ~ {block_end}")

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
                    "type": "place",
                    'place_id':    place['place_id'],
                    'start_time':  visit_start,
                    'end_time':    visit_end,
                    'travel_time': round(travel_min)
                })
                prev_coord = place['coords']
                used_places.add(place["place_id"])

        # 식사 삽입
        if day_start <= lunch_start <= day_end:
            result.append({
                'place_id':   '점심',
                'start_time': lunch_start,
                'end_time':   lunch_end,
                'type':       'meal',
                'travel_time': 60                
            })
        if day_start <= dinner_start <= day_end:
            result.append({
                'place_id':   '저녁',
                'start_time': dinner_start,
                'end_time':   dinner_end,
                'type':       'meal',
                'travel_time': 60
            })

        # 도착지
        result.append({
            'place_id': dest['place_id'],
            'type': 'destination',
            'start_time': day_end,
            'end_time': day_end,
            'travel_time': 0
        })

        # 시간순 정렬
        result.sort(key=lambda x: x.get('start_time') or x.get('time'))
        return result

    async def generate_multi_day_course(
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
                if item['type'] == 'place':
                    used_places.add(item['place_id'])

            itinerary.append({'date': current_day, 'plan': day_plan})
            current_day += timedelta(days=1)

        return itinerary
