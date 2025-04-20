import requests
import pandas as pd
import folium
from folium import IFrame
import webbrowser
import os

def get_all_busan_accommodation(service_key):
    url = 'https://api.odcloud.kr/api/15096728/v1/uddi:a7cfe5da-2d11-4416-b67f-aff99ee63bbe'
    all_data = []

    for page in range(1, 17):
        params = {
            'serviceKey': service_key,
            'page': page,
            'perPage': 100
        }

        try:
            response = requests.get(url, params=params)

            if response.status_code == 200:
                data = response.json()
                items = data['data']
                if not items:
                    break
                all_data.extend(items)  #
            else:
                print(f"에러 발생: {response.status_code}")
                break

        except Exception as e:
            print(f"예외 발생: {str(e)}")
            break

    return pd.DataFrame(all_data)  # 모든 데이터를 DataFrame으로 변환하여 반환

# API 키
service_key = 'API key'

# 데이터 가져오기
df = get_all_busan_accommodation(service_key)

if df is not None:
    # 부산 중심 좌표
    busan_center = [35.1796, 129.0756]

    # 지도 생성
    m = folium.Map(location=busan_center, zoom_start=12)


    for idx, row in df.iterrows():
        try:
            html = f"""
                <div style="width:200px; text-align:center;">
                    <h4 style="margin:3px;">{row['업체명']}</h4>
                    <p style="margin:3px;">{row.get('주소', '')}</p>
                    <a href="https://search.naver.com/search.naver?query={row['업체명']}" 
                       target="_blank" 
                       style="background-color:#FF4444;
                              color:white;
                              padding:8px 15px;
                              text-decoration:none;
                              border-radius:5px;
                              display:inline-block;
                              margin:5px;">
                        상세정보 보기
                    </a>
                </div>
            """

            iframe = IFrame(html=html, width=220, height=150)
            popup = folium.Popup(iframe)

            # 마커 생성
            folium.Marker(
                location=[float(row['위도']), float(row['경도'])],
                popup=popup,
                icon=folium.Icon(color='red', icon='info-sign')
            ).add_to(m)

        except (ValueError, KeyError) as e:
            print(f"마커 생성 중 오류 발생: {str(e)}")
            continue

    # 지도 파일 저장
    map_file = 'busan_accommodation_butt.html'
    abs_path = os.path.abspath(map_file)
    m.save(map_file)

    # 웹 브라우저에서 지도 열기
    webbrowser.open('file://' + abs_path)
    print(f"\n지도가 웹 브라우저에서 열렸습니다. 파일 위치: {abs_path}")
else:
    print("데이터를 가져오는데 실패했습니다.")
