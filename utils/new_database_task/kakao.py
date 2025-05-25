import os
import requests
import time
import json
from dotenv import load_dotenv
"""
카카오 API 키를 환경 변수에 저장하고, 해당 키를 사용하여 카카오 API에 요청을 보내 지리 정보를 수집합니다.
최대 10페이지까지 수집 가능하도록 설정해뒀고, 각 페이지에는 최대 15개의 데이터가 포함됩니다.
마지막 페이지에 도달하면 즉시 다음 페이지로 넘어갑니다.
그리드는 부산 지역을 기준으로 1Km 단위로 생성합니다.
AT4는 관광명소 카테고리입니다.
FD6는 음식점 카테고리입니다.
SW8은 지하철역 입니다.
CE7은 카페 카테고리입니다.
CT1은 문화시설 카테고리입니다.
"""

# 1. 환경 변수 로드
load_dotenv()
API_KEY = os.getenv("KAKAO_REST_API_KEY")
headers = {"Authorization": f"KakaoAK {API_KEY}"}


# 2. 카카오 API 요청
def search_kakao_category(x, y, radius=1000, page=1):
    url = "https://dapi.kakao.com/v2/local/search/category.json"
    params = {
        "category_group_code": "CT1",
        "x": x,
        "y": y,
        "radius": radius,
        "page": page,
        "size": 15
    }
    res = requests.get(url, headers=headers, params=params)

    if res.status_code != 200:
        print(f"[ERROR] 요청 실패 | status: {res.status_code} | reason: {res.reason}")
        print(res.text)
        return {"documents": []}
    else:
        data = res.json()
        print(f"[INFO] x:{x}, y:{y}, page:{page} → {len(data.get('documents', []))}개 수신됨")
        return data


# 3. 그리드 생성기
def generate_grid(lat_start, lat_end, lon_start, lon_end, step=0.01):
    lat = lat_start
    while lat <= lat_end:
        lon = lon_start
        while lon <= lon_end:
            yield round(lon, 5), round(lat, 5)
            lon += step
        lat += step


# 4. 수집 후 1000개 단위 저장
def collect_and_save_places():
    collected = {}
    chunk_index = 0
    chunk_data = []

    for x, y in generate_grid(35.05, 35.30, 128.90, 129.25, step=0.01):
        for page in range(1, 46):
            data = search_kakao_category(x, y, page=page)
            docs = data.get("documents", [])
            if not docs:
                break

            for doc in docs:
                key = (doc["place_name"], doc["address_name"])
                if key not in collected:
                    collected[key] = True
                    chunk_data.append(doc)

                    # 1000개마다 파일 저장
                    if len(chunk_data) == 1000:
                        filename = f"culture_{chunk_index}.json"
                        with open(filename, "w", encoding="utf-8") as f:
                            json.dump(chunk_data, f, ensure_ascii=False, indent=2)
                        print(f"[SAVE] {filename} 저장 완료")
                        chunk_index += 1
                        chunk_data = []

            if data.get("meta", {}).get("is_end", False):
                break

            time.sleep(0.3)

    # 남은 데이터 저장
    if chunk_data:
        filename = f"culture_{chunk_index}.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(chunk_data, f, ensure_ascii=False, indent=2)
        print(f"[SAVE] {filename} 저장 완료")

# 실행
if __name__ == "__main__":
    collect_and_save_places()
