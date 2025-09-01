# models.py
# 모델 정의 모듈

import torch
import torch.nn as nn
import torch.nn.functional as F


class SymmetricResidualCategoryNCF(nn.Module):
    """
    대칭적 잔차 카테고리 인식 신경 협업 필터링 모델 - 시간대별, 계절별 필터링 지원

    다음 요소들을 결합한 하이브리드 추천 모델:
    - GMF (일반화된 행렬 분해) 브랜치 (Hadamard 곱)
    - MLP (다층 퍼셉트론) 브랜치 (단일 잔차 블록)
    - 카테고리 그룹 정보 융합
    - 활동성 레벨 정보 융합
    - 시간대별 정보 융합
    - 계절별 정보 융합
    - 단순한 임베딩 레이어 사용

    Args:
        n_users (int): 사용자 수
        n_items (int): 아이템 수
        config (dict): 모델 하이퍼파라미터 설정 딕셔너리
    """

    def __init__(self, n_users, n_items, config):
        super().__init__()
        self.config = config

        # 사용자 임베딩 (128차원)
        self.user_embedding_gmf = nn.Embedding(n_users, 128)
        self.user_embedding_mlp = nn.Embedding(n_users, 128)
        self.user_category_preference = nn.Embedding(n_users, 8)
        self.user_activity_level = nn.Embedding(n_users, 3)  # 활동성 레벨 임베딩 추가
        self.user_time_period = nn.Embedding(n_users, 3)  # 시간대별 임베딩 추가
        self.user_season = nn.Embedding(n_users, 4)  # 계절별 임베딩 추가
        self.user_preference = nn.Embedding(n_users, 2)  # 선호도 임베딩 추가 (0: 활동성 선호, 1: 시간대 선호)

        # 아이템 임베딩 (128차원)
        self.item_embedding_gmf = nn.Embedding(n_items, 128)
        self.item_embedding_mlp = nn.Embedding(n_items, 128)
        self.item_category = nn.Embedding(n_items, 8)

        # 카테고리 그룹 임베딩 (8개 카테고리 그룹)
        self.category_group_embedding = nn.Embedding(8, 16)  # 카테고리 그룹별 임베딩

        # GMF 브랜치 (Hadamard 내적 + FC) - 128차원 입력
        self.gmf_projection = nn.Sequential(
            nn.Linear(128, 128),
            nn.ReLU(),
            nn.Dropout(0.2)
        )

        # MLP 브랜치 - 단일 잔차 블록 (256차원 입력)
        self.mlp_residual_block = nn.Sequential(
            nn.Linear(256, 256),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(256, 256)  # 잔차연결을 위해 같은 차원 유지
        )
        self.mlp_activation = nn.ReLU()
        self.mlp_dropout = nn.Dropout(0.2)

        self.mlp_projection = nn.Sequential(
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Dropout(0.2)
        )

        # 최종 융합 레이어 - 동적 차원 계산
        # 128(GMF) + 128(MLP) + 8(user_cat) + 8(item_cat) + 3(activity) + 3(time) + 4(season) + 2(preference) + 16(category_group) = 300
        self.final_fusion = nn.Sequential(
            nn.Linear(300, 128),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(64, 1)
        )

        self._init_weights()

    def _init_weights(self):
        for module in self.modules():
            if isinstance(module, nn.Linear):
                nn.init.xavier_uniform_(module.weight)
                if module.bias is not None:
                    nn.init.constant_(module.bias, 0)
            elif isinstance(module, nn.Embedding):
                nn.init.normal_(module.weight, mean=0, std=0.1)

    def forward(self, user_ids, item_ids, category_groups=None, activity_levels=None, time_periods=None, seasons=None, preferences=None):
        # 1. 사용자 임베딩 (128차원)
        user_gmf = self.user_embedding_gmf(user_ids)
        user_mlp = self.user_embedding_mlp(user_ids)
        user_category_pref = self.user_category_preference(user_ids)
        user_activity = self.user_activity_level(user_ids)  # 활동성 레벨 임베딩
        user_time = self.user_time_period(user_ids)  # 시간대별 임베딩
        user_season = self.user_season(user_ids)  # 계절별 임베딩
        user_preference = self.user_preference(user_ids)  # 선호도 임베딩

        # 2. 아이템 임베딩 (128차원)
        item_gmf = self.item_embedding_gmf(item_ids)
        item_mlp = self.item_embedding_mlp(item_ids)
        item_category = self.item_category(item_ids)

        # 3. 카테고리 그룹 임베딩 (16차원)
        if category_groups is not None:
            # 카테고리 그룹을 인덱스로 변환
            category_group_indices = self._get_category_group_indices(category_groups, user_ids.device)
            category_group_emb = self.category_group_embedding(category_group_indices)
        else:
            # 기본값: 0번 인덱스 (자연풍경)
            category_group_emb = self.category_group_embedding(torch.zeros_like(user_ids))

        # 4. GMF 브랜치 (Hadamard 내적 + FC) - 128차원
        gmf_output = (user_gmf * item_gmf)  # [B,128]
        gmf_output = self.gmf_projection(gmf_output)  # [B,128]

        # 5. MLP 브랜치 (단일 잔차 블록) - 256차원 입력
        mlp_input = torch.cat([user_mlp, item_mlp], dim=1)  # [B,256]

        # 잔차연결: input + residual_block(input)
        residual_output = self.mlp_residual_block(mlp_input)  # [B,256]
        mlp_with_residual = mlp_input + residual_output  # [B,256] 잔차연결
        mlp_activated = self.mlp_activation(mlp_with_residual)  # [B,256]
        mlp_output = self.mlp_dropout(mlp_activated)  # [B,256]
        mlp_output = self.mlp_projection(mlp_output)  # [B,128]

        # 6. 최종 융합 (GMF + MLP + 카테고리 + 활동성 + 시간대 + 계절 + 선호도 + 카테고리그룹)
        final_input = torch.cat([
            gmf_output,  # [B, 128]
            mlp_output,  # [B, 128]
            user_category_pref,  # [B, 8]
            item_category,  # [B, 8]
            user_activity,  # [B, 3]
            user_time,  # [B, 3]
            user_season,  # [B, 4]
            user_preference,  # [B, 2]
            category_group_emb  # [B, 16]
        ], dim=1)  # [B, 300]

        # 디버깅: 차원 확인
        if final_input.size(1) != 300:
            print(f"Warning: Expected 300 dimensions, got {final_input.size(1)}")
            print(
                f"GMF: {gmf_output.size(1)}, MLP: {mlp_output.size(1)}, UserCat: {user_category_pref.size(1)}, ItemCat: {item_category.size(1)}, Activity: {user_activity.size(1)}, Time: {user_time.size(1)}, Season: {user_season.size(1)}, Preference: {user_preference.size(1)}, CategoryGroup: {category_group_emb.size(1)}")

        prediction = self.final_fusion(final_input).squeeze()

        return prediction

    def _get_category_group_indices(self, category_groups, device):
        """카테고리 그룹명을 인덱스로 변환 - 디바이스 처리 개선"""
        category_mapping = {
            "자연풍경": 0,
            "예술 감상": 1,
            "공연관람": 2,
            "관람및체험": 3,
            "트레킹": 4,
            "휴양": 5,
            "테마거리": 6,
            "자연산림": 7
        }

        indices = []
        for category in category_groups:
            if isinstance(category, str):
                indices.append(category_mapping.get(category, 0))
            else:
                indices.append(0)  # 기본값

        return torch.tensor(indices, dtype=torch.long, device=device)