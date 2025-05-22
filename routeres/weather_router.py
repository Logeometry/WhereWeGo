# backend/app/routers/weather_router.py

from datetime import datetime, timezone, timedelta
from typing import List
import httpx
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

router = APIRouter(prefix="/weather", tags=["weather"])
SERVICE_KEY = "pFhO7c0hyxvss8UdPm2CVpsS9kTrr813vQyjbEYg8xx8kQEqFjxGqL3CFlHks2VrGrsjgSKlB7Y5l1ZM9B6lbw%3D%3D"
REGION_INFO = {
    "강서구":   {"nx": 95,  "ny": 76},
    "금정구":   {"nx": 98,  "ny": 77},
    "기장군":   {"nx":100,  "ny": 77},
    "남구":     {"nx": 98,  "ny": 75},
    "동구":     {"nx": 97,  "ny": 75},
    "동래구":   {"nx": 98,  "ny": 76},
    "부산진구": {"nx": 97,  "ny": 75},
    "북구":     {"nx": 97,  "ny": 76},
    "사상구":   {"nx": 96,  "ny": 75},
    "사하구":   {"nx": 96,  "ny": 74},
    "서구":     {"nx": 97,  "ny": 74},
    "수영구":   {"nx": 99,  "ny": 75},
    "연제구":   {"nx": 98,  "ny": 76},
    "영도구":   {"nx": 97,  "ny": 74},
    "중구":     {"nx": 97,  "ny": 74},
    "해운대구": {"nx": 99,  "ny": 76},
}

class ForecastItem(BaseModel):
    time: str    = Field(..., description="HHMM")
    category: str
    value: str

class ForecastResponse(BaseModel):
    region: str
    date:   str  = Field(..., description="YYYYMMDD")
    forecasts: List[ForecastItem]

@router.get("", response_model=ForecastResponse)
async def forecast(
    region: str = Query(..., description="구·군명"),
    date:   str = Query(datetime.now(timezone(timedelta(hours=9))).strftime("%Y%m%d"))
):
    if region not in REGION_INFO:
        raise HTTPException(400, "지원하지 않는 지역입니다.")
    nx, ny = REGION_INFO[region]["nx"], REGION_INFO[region]["ny"]

    now = datetime.now(timezone(timedelta(hours=9)))
    slots = ["0200","0500","0800","1100","1400","1700","2000","2300"]
    hhmm = now.strftime("%H%M")
    base_time = max((s for s in slots if s <= hhmm), default=slots[0])
    base_date = now.strftime("%Y%m%d")

    url = (
        "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst"
        f"?serviceKey={SERVICE_KEY}&numOfRows=1000&pageNo=1&dataType=JSON"
        f"&base_date={base_date}&base_time={base_time}&nx={nx}&ny={ny}"
    )
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
    if resp.status_code != 200:
        raise HTTPException(502, "API 호출 실패")

    data = resp.json().get("response", {}) \
                  .get("body", {}) \
                  .get("items", {}) \
                  .get("item", [])

    forecasts = [
        ForecastItem(time=i["fcstTime"], category=i["category"], value=i["fcstValue"])
        for i in sorted(data, key=lambda x: x["fcstTime"])
        if i.get("fcstDate") == date
    ]
    return ForecastResponse(region=region, date=date, forecasts=forecasts)
