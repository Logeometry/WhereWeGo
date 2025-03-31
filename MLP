import torch
import torch.nn as nn
import numpy as np
import pandas as pd
import folium
import requests
import json
from datetime import datetime
import webbrowser
import os
from torch.utils.data import TensorDataset, DataLoader

serviceKey = 'API key'
base_url = 'https://api.odcloud.kr/api/15096728/v1/uddi:a7cfe5da-2d11-4416-b67f-aff99ee63bbe'
busan_center = [35.1796, 129.0756]


class AccessibilityMLP(nn.Module):
    def __init__(self):
        super(AccessibilityMLP, self).__init__()
        self.layer1 = nn.Linear(4, 8)
        self.layer2 = nn.Linear(8, 4)
        self.layer3 = nn.Linear(4, 1)
        self.relu = nn.ReLU()

        self.init_weights()

    def init_weights(self):
        with torch.no_grad():
            # 첫 번째 층: 각 특성의 기본 중요도 설정
            self.layer1.weight.data = torch.tensor([
                [0.4, 0.3, 0.2, 0.1],  # 물품보관함 중심
                [0.3, 0.4, 0.2, 0.1],  # 유아거치대 중심
                [0.2, 0.2, 0.4, 0.2],  # 휠체어 중심
                [0.1, 0.2, 0.3, 0.4],  # 점자유도로 중심
                [0.25, 0.25, 0.25, 0.25],  # 균등 가중치
                [0.3, 0.3, 0.2, 0.2],  # 보관/거치대 중심
                [0.2, 0.2, 0.3, 0.3],  # 이동/안내 중심
                [0.4, 0.2, 0.2, 0.2]  # 물품보관함 특화
            ])
            self.layer1.bias.data = torch.zeros(8)

            # 두 번째 층: 특성 조합의 가중치
            self.layer2.weight.data = torch.tensor([
                [0.3, 0.2, 0.2, 0.1, 0.1, 0.05, 0.025, 0.025],  # 물품보관함 관련
                [0.2, 0.3, 0.1, 0.2, 0.1, 0.05, 0.025, 0.025],  # 유아거치대 관련
                [0.2, 0.1, 0.3, 0.2, 0.1, 0.05, 0.025, 0.025],  # 휠체어 관련
                [0.1, 0.2, 0.2, 0.3, 0.1, 0.05, 0.025, 0.025]  # 점자유도로 관련
            ])
            self.layer2.bias.data = torch.zeros(4)

            # 마지막 층: 최종 점수 계산
            self.layer3.weight.data = torch.tensor([[0.3, 0.3, 0.2, 0.2]])
            self.layer3.bias.data = torch.tensor([0.0])

    def forward(self, x):
        x = self.relu(self.layer1(x))
        x = self.relu(self.layer2(x))
        x = self.layer3(x)
        # 점수를 0-100 범위로 조정
        return torch.clamp(x * 100, min=0, max=100)


def fetch_tourism_data():
    try:
        headers = {
            'Authorization': f'Infuser {serviceKey}'
        }
        params = {
            'page': 1,
            'perPage': 1000
        }

        response = requests.get(base_url, params=params, headers=headers)

        print("API 응답 상태 코드:", response.status_code)
        print("API 응답 내용:", response.text[:500])
        print("요청 헤더:", headers)

        if response.status_code == 200:
            data = response.json()
            print("데이터 구조:", data.keys())

            df = pd.DataFrame(data['data'])

            column_mapping = {
                '업체명': 'MAIN_TITLE',
                '도로명상세': 'ADDR1',
                '위도': 'LAT',
                '경도': 'LNG',
                '물품보관함유무': 'BAGGAGE_KEEPING_YN',
                '유아거치대유무': 'BABY_CARRIAGE_YN',
                '휠체어이동가능여부': 'WHEELCHAIR_YN',
                '점자유도로유무': 'BRAILLE_BLOCK_YN'
            }

            df = df.rename(columns=column_mapping)

            columns = [
                'MAIN_TITLE', 'ADDR1', 'LAT', 'LNG',
                'BAGGAGE_KEEPING_YN', 'BABY_CARRIAGE_YN',
                'WHEELCHAIR_YN', 'BRAILLE_BLOCK_YN'
            ]

            df = df[columns]
            return df

        else:
            print(f"API 요청 실패: {response.status_code}")
            print(f"에러 메시지: {response.text}")
            return None

    except Exception as e:
        print(f"에러 발생: {str(e)}")
        return None


def prepare_data(df):
    feature_columns = [
        'BAGGAGE_KEEPING_YN', 'BABY_CARRIAGE_YN',
        'WHEELCHAIR_YN', 'BRAILLE_BLOCK_YN'
    ]

    # Y/N을 1/0으로 변환
    for col in feature_columns:
        df[col] = (df[col] == 'Y').astype(float)

    features = torch.FloatTensor(df[feature_columns].values)
    return features


def train_model(df):
    # 하이퍼파라미터 설정
    batch_size = 32
    learning_rate = 0.01
    epochs = 100

    # 데이터 준비
    features = prepare_data(df)

    weights = torch.tensor([0.3, 0.3, 0.2, 0.2])  # 물품보관함, 유아거치대, 휠체어, 점자유도로의 중요도
    targets = (features * weights.unsqueeze(0)).sum(dim=1).unsqueeze(1)

    dataset = TensorDataset(features, targets)
    data_loader = DataLoader(dataset=dataset, batch_size=batch_size, shuffle=True)

    model = AccessibilityMLP()
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)

    # 학습 과정
    for epoch in range(epochs):
        total_loss = 0
        for batch_features, batch_targets in data_loader:
            outputs = model(batch_features)
            loss = criterion(outputs, batch_targets)

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            total_loss += loss.item()

        if (epoch + 1) % 10 == 0:
            print(f'Epoch [{epoch + 1}/{epochs}], Loss: {total_loss / len(data_loader):.4f}')

    return model


def calculate_accessibility_score(features):
    # 각 시설별로 새로운 MLP 모델 생성
    model = AccessibilityMLP()

    # 특성을 텐서로 변환하고 점수 계산
    with torch.no_grad():
        score = model(features)
    return float(score.item())


def create_accessibility_map():
    df = fetch_tourism_data()

    if df is not None:
        # Y/N을 1/0으로 변환
        for col in ['BAGGAGE_KEEPING_YN', 'BABY_CARRIAGE_YN',
                    'WHEELCHAIR_YN', 'BRAILLE_BLOCK_YN']:
            df[col] = (df[col] == 'Y').astype(float)

        # 지도 생성
        m = folium.Map(location=busan_center, zoom_start=12)
        accessible_count = 0
        total_count = len(df)

        try:
            # 각 시설별로 개별 처리
            for idx, row in df.iterrows():
                if pd.isna(row['LAT']) or pd.isna(row['LNG']):
                    continue

                # 현재 시설의 특성을 텐서로 변환
                features = torch.FloatTensor([[
                    float(row['BAGGAGE_KEEPING_YN']),
                    float(row['BABY_CARRIAGE_YN']),
                    float(row['WHEELCHAIR_YN']),
                    float(row['BRAILLE_BLOCK_YN'])
                ]])

                # 개별 MLP로 접근성 점수 계산
                score = calculate_accessibility_score(features)

                # 디버깅을 위한 출력
                print(f"\n시설명: {row['MAIN_TITLE']}")
                print(f"특성: {features.numpy()}")
                print(f"계산된 점수: {score:.1f}")

                if score >= 30:
                    accessible_count += 1
                    popup_text = f"""
                    <div style="width:200px">
                        <h4>{row['MAIN_TITLE']}</h4>
                        <p><b>접근성 점수:</b> {score:.1f}/100점</p>
                        <p><b>주소:</b> {row['ADDR1']}</p>
                        <hr>
                        <p><b>시설 현황:</b></p>
                        <ul>
                            <li>물품보관함: {'✓' if row['BAGGAGE_KEEPING_YN'] >= 0.5 else '✗'}</li>
                            <li>유아거치대: {'✓' if row['BABY_CARRIAGE_YN'] >= 0.5 else '✗'}</li>
                            <li>휠체어이동: {'✓' if row['WHEELCHAIR_YN'] >= 0.5 else '✗'}</li>
                            <li>점자유도로: {'✓' if row['BRAILLE_BLOCK_YN'] >= 0.5 else '✗'}</li>
                        </ul>
                    </div>
                    """

                    folium.Marker(
                        [float(row['LAT']), float(row['LNG'])],
                        popup=folium.Popup(popup_text, max_width=300),
                        icon=folium.Icon(color='red', icon='info-sign'),
                        tooltip=f"{row['MAIN_TITLE']} (점수: {score:.1f})"
                    ).add_to(m)

            # 범례 추가
            legend_html = '''
            <div style="position: fixed; 
                        bottom: 50px; right: 50px; 
                        border:2px solid grey; z-index:9999; 
                        background-color:white;
                        padding: 10px;
                        font-size:14px;">
                <p><i class="fa fa-circle" style="color:red"></i> 접근성 우수 </p>
            </div>
            '''
            m.get_root().html.add_child(folium.Element(legend_html))

            # 분석 결과 출력
            print("\n===== 부산 관광지 접근성 분석 결과 =====")
            print(f"\n전체 관광지 수: {total_count}개")
            print(f"접근성 우수 관광지 수: {accessible_count}개")
            print(f"접근성 우수 비율: {(accessible_count / total_count * 100):.1f}%")

            # 지도 저장 및 열기
            map_file = 'busan_accommodation_butt.html'
            abs_path = os.path.abspath(map_file)
            m.save(map_file)
            webbrowser.open('file://' + abs_path)

            return {
                'total_locations': total_count,
                'accessible_locations': accessible_count,
                'accessibility_ratio': (accessible_count / total_count * 100)
            }

        except Exception as e:
            print(f"오류 발생: {str(e)}")
            return None


if __name__ == "__main__":
    result = create_accessibility_map()
    if result:
        print("\n지도가 생성되었습니다.")
