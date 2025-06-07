import os
import re
import json
import requests
from math import radians, sin, cos, sqrt, atan2
from typing import Tuple
from requests.exceptions import HTTPError, RequestException

class TravelTimeService:
    def __init__(self, app_key: str = None):
        self.app_key  = app_key or os.getenv("APP_KEY")
        self.walk_url = "https://apis.openapi.sk.com/tmap/routes/pedestrian"

    def estimate_time(
        self,
        origin: Tuple[float, float],
        dest:   Tuple[float, float],
        mode:   str = "drive"
    ) -> float:
        if mode == "walk":
            return self._get_walk_time(origin, dest)
        return self._get_drive_time(origin, dest)

    def _get_drive_time(self, origin, dest) -> float:
        lat1, lon1 = origin
        lat2, lon2 = dest
        R = 6371.0
        dlat = radians(lat2 - lat1)
        dlon = radians(lon2 - lon1)
        a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        dist_km = R * c
        return (dist_km / 40.0) * 60  # 시속 40km 기준, 분 단위 반환

    def _get_walk_time(self, origin, dest) -> float:
        qs = {"version": "1"}
        data = {
            "startX":       f"{origin[1]}",
            "startY":       f"{origin[0]}",
            "endX":         f"{dest[1]}",
            "endY":         f"{dest[0]}",
            "startName":    "start",
            "endName":      "end",
            "reqCoordType": "WGS84GEO",
            "resCoordType": "WGS84GEO",
            "searchOption": "0"
        }
        headers = {
            "appKey":       os.getenv("APP_KEY"),
            "Accept":       "application/json",
            "Content-Type": "application/x-www-form-urlencoded"
        }

        try:
            resp = requests.post(
                self.walk_url,
                params=qs,
                data=data,
                headers=headers,
                timeout=5
            )
        except RequestException as e:
            raise RuntimeError(f"네트워크 오류: {e}")

        # “지원 불가 구간” 코드만 fallback
        if resp.status_code == 400:
            try:
                err = resp.json().get("error", {})
            except ValueError:
                err = {}
            if err.get("code") == "3102":
                return self._fallback_walk_time(origin, dest)
            # 그 외 400 에러는 그대로 예외
            raise RuntimeError(f"TMAP API 오류 {resp.status_code}: {resp.text}")

        # 인증 실패 등 다른 HTTP 오류
        try:
            resp.raise_for_status()
        except HTTPError:
            raise RuntimeError(f"TMAP API 오류 {resp.status_code}: {resp.text}")

        text = resp.text

        # JSON 파싱 (strict=False → 제어문자 제거)
        try:
            result = json.loads(text, strict=False)
        except json.JSONDecodeError:
            cleaned = re.sub(r'[\x00-\x1f]+', '', text)
            result = json.loads(cleaned)

        features = result.get("features", [])

        # SP 노드에 totalTime(초)이 있으면 우선 사용
        total_sec = None
        for f in features:
            props = f.get("properties", {})
            if props.get("pointType") == "SP" and "totalTime" in props:
                total_sec = props["totalTime"]
                break

        # 없으면 모든 LineString 세그먼트의 time 합산
        if total_sec is None:
            total_sec = sum(
                seg.get("properties", {}).get("time", 0)
                for seg in features
                if seg.get("geometry", {}).get("type") == "LineString"
            )

        return total_sec / 60.0  # 분 단위 반환

    def _fallback_walk_time(self, origin, dest) -> float:
        lat1, lon1 = origin
        lat2, lon2 = dest
        R = 6371.0
        dlat = radians(lat2 - lat1)
        dlon = radians(lon2 - lon1)
        a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        dist_km = R * c
        return (dist_km / 5.0) * 60  # 시속 5km 기준, 분 단위 반환

