from typing import Tuple, Protocol

class TravelTimeEstimator(Protocol):
    def estimate(self,
                 origin: Tuple[float, float],
                 dest:   Tuple[float, float],
                 mode:   str = "walk"
                 ) -> float:
        """
        origin → dest 예상 이동 시간(분)을 반환
        """
        ...

class DistanceBasedEstimator:
    def estimate(self,
                 origin: Tuple[float, float],
                 dest:   Tuple[float, float],
                 mode:   str = "walk"
                 ) -> float:
        # Haversine 등으로 실제 거리를 계산하고,
        # 평균 속도로 시간을 환산한 뒤 분 단위로 반환
        from math import radians, sin, cos, sqrt, atan2
        lat1, lon1 = origin
        lat2, lon2 = dest
        # 지구 반지름(km)
        R = 6371.0
        dlat = radians(lat2 - lat1)
        dlon = radians(lon2 - lon1)
        a = sin(dlat/2)**2 + cos(radians(lat1))*cos(radians(lat2))*sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        distance_km = R * c
        # 속도 (km/h
        speed = 5.0 if mode == "walk" else 40.0
        # 시간(분)으로 변환
        return (distance_km / speed) * 60
