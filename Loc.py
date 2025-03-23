import requests
import pandas as pd
import urllib.parse
import webbrowser
import os

def get_busan_attractions(service_key):
    # API 엔드포인트 URL
    url = 'http://apis.data.go.kr/6260000/AttractionService/getAttractionKr'

    # URL 디코딩된 서비스키로 변환
    decoded_key = urllib.parse.unquote(service_key)

    # 요청 파라미터
    params = {
        'serviceKey': decoded_key,  # 디코딩된 API 키 사용
        'pageNo': '1',
        'numOfRows': '100',
        'resultType': 'json'
    }

    try:
        # API 호출
        response = requests.get(url, params=params)

        # 응답 내용 확인을 위한 출력
        print("응답 상태 코드:", response.status_code)
        print("응답 헤더:", response.headers)
        print("응답 내용:", response.text[:500])  # 처음 500자만 출력

        # 응답 확인
        if response.status_code == 200:
            try:
                data = response.json()
                # 데이터를 DataFrame으로 변환
                items = data['getAttractionKr']['item']
                df = pd.DataFrame(items)
                return df
            except ValueError as json_error:
                print(f"JSON 파싱 에러: {str(json_error)}")
                return None
        else:
            print(f"에러 발생: {response.status_code}")
            print(response.text)
            return None

    except Exception as e:
        print(f"예외 발생: {str(e)}")
        return None

# API 키
service_key = 'API key'

# 함수 호출
df = get_busan_attractions(service_key)

if df is not None:
    # 데이터 출력
    print("가져온 관광지 수:", len(df))
    print("\n관광지 정보:")
    print(df[['MAIN_TITLE', 'ADDR1', 'LAT', 'LNG']].head())

    # 지도 시각화
    import folium

    # 부산 중심 좌표
    busan_center = [35.1796, 129.0756]

    # 지도 생성
    m = folium.Map(location=busan_center, zoom_start=12)

    # 관광지 마커 추가
    for idx, row in df.iterrows():
        folium.Marker(
            [float(row['LAT']), float(row['LNG'])],
            popup=row['MAIN_TITLE']
        ).add_to(m)

    # 지도 파일 경로 설정
    map_file = 'busan_attractions.html'
    abs_path = os.path.abspath(map_file)

    # 지도 저장
    m.save(map_file)

    # 웹 브라우저에서 지도 열기
    webbrowser.open('file://' + abs_path)
    print(f"\n지도가 웹 브라우저에서 열렸습니다. 파일 위치: {abs_path}")
