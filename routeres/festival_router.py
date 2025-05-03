import os
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any
import httpx
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
import json 

router = APIRouter(prefix="/festival", tags=["festival"])

SERVICE_KEY = "pFhO7c0hyxvss8UdPm2CVpsS9kTrr813vQyjbEYg8xx8kQEqFjxGqL3CFlHks2VrGrsjgSKlB7Y5l1ZM9B6lbw=="

class FestivalItem(BaseModel):
    contentid: int
    title: str
    eventstartdate: str
    eventenddate: Optional[str]
    firstimage: Optional[str]
    firstimage2: Optional[str]
    addr1: Optional[str]
    addr2: Optional[str]
    mapx: Optional[float]
    mapy: Optional[float]

class FestivalResponse(BaseModel):
    resultCode: str
    resultMsg: str
    numOfRows: int
    pageNo: int
    totalCount: int
    items: List[FestivalItem]

@router.get("", response_model=FestivalResponse)
async def list_festivals(
    pageNo: int = Query(1, ge=1),
    numOfRows: int = Query(100, ge=1, le=1000),
    arrange: str = Query("A", regex="^[ACDQR]$"),
):
    tz = timezone(timedelta(hours=9))
    today      = datetime.now(tz).strftime("%Y%m%d")
    two_months = (datetime.now(tz) + timedelta(days=60)).strftime("%Y%m%d")

    params: Dict[str, Any] = {
        "serviceKey":     SERVICE_KEY,
        "MobileOS":       "ETC",
        "MobileApp":      "WhereWeGoApp",
        "listYN":         "Y",
        "arrange":        arrange,
        "eventStartDate": today,
        "eventEndDate":   two_months,
        "pageNo":         pageNo,
        "numOfRows":      numOfRows,
        "_type":          "json",
        "areaCode":       6,
    }
    url = "http://apis.data.go.kr/B551011/KorService1/searchFestival1"

    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params)

    # ——— 디버깅 로그 ———
    print("[festival-debug] URL   :", resp.url)
    print("[festival-debug] STATUS:", resp.status_code)
    print("[festival-debug] BODY  :", resp.text[:300].replace("\n", " "))
    # ——————————————————

    if resp.status_code != 200:
        raise HTTPException(502, "API 호출 실패")

    try:
        data = resp.json()
    except json.JSONDecodeError as e:
        raise HTTPException(
            502,
            detail=f"JSON 파싱 실패: {e}\n응답바디:\n{resp.text[:300]}"
        )

    header = data.get("response", {}).get("header", {})
    body   = data.get("response", {}).get("body", {})
    items  = body.get("items", {}).get("item", [])

    if isinstance(items, dict):
        items = [items]

    def overlaps(it: dict) -> bool:
        start = it.get("eventstartdate")
        end   = it.get("eventenddate") or start
        return not (end < today or start > two_months)

    filtered = [it for it in items if overlaps(it)]

    festivals: List[FestivalItem] = []
    for it in filtered:
        festivals.append(FestivalItem(
            contentid     = int(it["contentid"]),
            title         = it["title"],
            eventstartdate= it["eventstartdate"],
            eventenddate  = it.get("eventenddate"),
            firstimage    = it.get("firstimage"),
            firstimage2   = it.get("firstimage2"),
            addr1         = it.get("addr1"),
            addr2         = it.get("addr2"),
            mapx          = float(it["mapx"]) if it.get("mapx") else None,
            mapy          = float(it["mapy"]) if it.get("mapy") else None,
        ))

    return FestivalResponse(
        resultCode = header.get("resultCode", ""),
        resultMsg  = header.get("resultMsg", ""),
        numOfRows  = body.get("numOfRows", numOfRows),
        pageNo     = body.get("pageNo", pageNo),
        totalCount = body.get("totalCount", 0),
        items      = festivals
    )
