import requests
import json
import time
from pydantic import BaseModel
from typing import Optional

class LocationData(BaseModel):
    content_id: str
    name: str
    address: str
    tel: Optional[str]
    image_url: Optional[str]
    map_x: Optional[float]
    map_y: Optional[float]
    area_code: Optional[int]
    sigungu_code: Optional[int]
    cat1: Optional[str]
    cat2: Optional[str]
    cat3: Optional[str]
    content_type_id: Optional[int]


def fetch_tourist_data(params):
    url = "https://apis.data.go.kr/B551011/KorService1/areaBasedList1"
    try:
        res = requests.get(url, params=params, timeout=10)
        if res.status_code != 200:
            return [], 0

        data = res.json()
        header = data.get('response', {}).get('header', {})
        body = data.get('response', {}).get('body', {})

        if header.get('resultCode') != '0000':
            return [], 0

        return body.get('items', {}).get('item', []), body.get('totalCount', 0)

    except requests.exceptions.RequestException:
        return [], 0

def to_location_data(item: dict) -> LocationData:
    return LocationData(
        content_id=str(item.get("contentid", "")),
        name=item.get("title", "제목 없음"),
        address=(item.get("addr1") or "") + " " + (item.get("addr2") or ""),
        tel=item.get("tel"),
        image_url=item.get("firstimage"),
        map_x=float(item["mapx"]) if item.get("mapx") else None,
        map_y=float(item["mapy"]) if item.get("mapy") else None,
        area_code=int(item["areacode"]) if item.get("areacode") else None,
        sigungu_code=int(item["sigungucode"]) if item.get("sigungucode") else None,
        cat1=item.get("cat1"),
        cat2=item.get("cat2"),
        cat3=item.get("cat3"),
        content_type_id=int(item["contenttypeid"]) if item.get("contenttypeid") else None
    )


def main():
    SERVICE_KEY = "pFhO7c0hyxvss8UdPm2CVpsS9kTrr813vQyjbEYg8xx8kQEqFjxGqL3CFlHks2VrGrsjgSKlB7Y5l1ZM9B6lbw=="
    area_code = '6'
    all_results = []

    for idx, sigungu in enumerate(range(1, 17), 1):
        print(f"\n 수집 중: ({idx}/16) 시군구 코드 {sigungu}")

        page = 1
        total_pages = 1

        while page <= total_pages:
            time.sleep(0.3)

            params = {
                'serviceKey': SERVICE_KEY,
                'MobileApp': 'AppTest',
                'MobileOS': 'ETC',
                'listYN': 'Y',
                'arrange': 'A',
                'areaCode': area_code,
                'sigunguCode': str(sigungu),
                '_type': 'json',
                'numOfRows': '100',
                'pageNo': str(page)
            }

            items, total_count = fetch_tourist_data(params)

            if page == 1:
                total_pages = (total_count // 100) + (1 if total_count % 100 else 0)

            if items:
                all_results.extend(items)

            print(f" - {page}/{total_pages} 페이지")

            page += 1

    converted = [to_location_data(item).dict() for item in all_results]

    with open("tourist_spots_all.json", "w", encoding="utf-8") as f:
        json.dump(converted, f, ensure_ascii=False, indent=2)
        print(f"\n 저장 완료: 총 {len(converted)}건")


if __name__ == "__main__":
    main()
