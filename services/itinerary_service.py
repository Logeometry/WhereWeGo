import random
from datetime import datetime, timedelta, time, date
from typing import List, Dict
from .travel_time_estimator import TravelTimeEstimator

class ItineraryService:
    def __init__(self, estimator: TravelTimeEstimator, alpha: float = 0.5):
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
            day_end = datetime.combine(day, end_time)

            lunch_start = datetime.combine(day, time(12, 0))
            lunch_end = lunch_start + timedelta(hours=1)

            dinner_start = datetime.combine(day, time(18, 0))
            dinner_end = dinner_start + timedelta(hours=1)

            time_blocks = []
            if day_start < lunch_start:
                time_blocks.append((day_start, min(lunch_start, day_end)))
            if lunch_end < dinner_start and lunch_end < day_end:
                time_blocks.append((lunch_end, min(dinner_start, day_end)))
            if dinner_end < day_end:
                time_blocks.append((dinner_end, day_end))

            for place in candidates:
                place['_used'] = False

            result = []
            prev_coord = origin['coords']
            result.append({'place_id': origin['place_id'], 'type': 'origin', 'time': day_start})

            for block_start, block_end in time_blocks:
                est = None
                best_score = float('inf')
                for place in candidates:
                    if place['_used']:
                        continue
                    coord = place['coords']
                    dist = self.estimator.estimate(prev_coord, coord)
                    est_start = block_start + timedelta(minutes=dist)
                    est_end = est_start + timedelta(minutes=avg_stay)
                    if est_end > block_end:
                        continue
                    score = self.alpha * dist + (1 - self.alpha) * (1 - place.get('rec_score', 0.0))
                    if score < best_score:
                        best_score = score
                        best = place

                if best:
                    travel = self.estimator.estimate(prev_coord, best['coords'])
                    visit_start = block_start + timedelta(minutes=travel)
                    visit_end = visit_start + timedelta(minutes=avg_stay)
                    result.append({
                        'place_id': best['place_id'],
                        'start_time': visit_start,
                        'end_time': visit_end,
                        'travel_time': travel
                    })
                    best['_used'] = True
                    prev_coord = best['coords']

            # 점심 추가
            if day_start <= lunch_start <= day_end:
                result.append({
                    'place_id': '점심',
                    'start_time': lunch_start,
                    'end_time': lunch_end,
                    'type': 'meal'
                })

            # 저녁 추가
            if day_start <= dinner_start <= day_end:
                result.append({
                    'place_id': '저녁',
                    'start_time': dinner_start,
                    'end_time': dinner_end,
                    'type': 'meal'
                })

            # 도착지 추가
            result.append({'place_id': dest['place_id'], 'type': 'destination', 'time': day_end})

            # 시간 순 정렬
            result.sort(key=lambda x: x.get('start_time') or x.get('time'))

            return result

        # for slot_start, slot_end in slots:
        #     best = None
        #     best_score = float('inf')
        #     for place in candidates:
        #         if place['_used']:
        #             continue
        #         coord = place['coords']
        #         dist = self.estimator.estimate(prev_coord, coord)
        #         rec = place.get('rec_score', 0.0)
        #         score = self.alpha * dist + (1 - self.alpha) * (1 - rec)
        #         est_start = slot_start + timedelta(minutes=dist)
        #         est_end   = est_start + timedelta(minutes=avg_stay)
        #         if est_end > slot_end:
        #             continue
        #         # if score < best_score:
        #             best_score = score
        #             best = place
        #     if not best:
        #         break

    def generate_multi_day_course(
        self,
        candidates: List[Dict],
        origin: Dict,
        dest: Dict,
        start_dt: datetime,
        end_dt: datetime,
        avg_stay: int = 60
    ) -> List[Dict]:
        """
        다중 날짜 일정 생성
        """
        itinerary = []
        used_places = set()
        current_day = start_dt.date()
        last_day    = end_dt.date()

        while current_day <= last_day:
            # 첫날 시작 시간, 마지막날 종료 시간 설정
            st = start_dt.time() if current_day == start_dt.date() else time(9, 0)
            et = end_dt.time()   if current_day == last_day           else time(18, 0)

            # 사용하지 않은 후보만 필터링
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

            # 이번 날 방문한 장소를 used_places에 추가 (origin/dest 제외)
            for item in day_plan:
                if 'start_time' in item:
                    used_places.add(item['place_id'])

            itinerary.append({'date': current_day, 'plan': day_plan})
            current_day += timedelta(days=1)

        return itinerary
