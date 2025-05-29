# models.py
# 모델 정의 모듈

import torch
import torch.nn as nn
import torch.nn.functional as F


class SymmetricResidualCategoryNCF(nn.Module):
    """
    대칭적 잔차 카테고리 인식 신경 협업 필터링 모델

    다음 요소들을 결합한 하이브리드 추천 모델:
    - GMF (일반화된 행렬 분해) 브랜치 (Hadamard 곱)
    - MLP (다층 퍼셉트론) 브랜치 (비선형 상호작용)
    - 최종 레이어에서 카테고리 정보 융합
    - projection layer를 통한 사전학습 아이템 임베딩

    Args:
        n_users (int): 사용자 수
        n_items (int): 아이템 수
        config (dict): 모델 하이퍼파라미터 설정 딕셔너리
    """

    def __init__(self, n_users, n_items, config):
        super().__init__()
        self.config = config

        # 아이템 벡터 (264차원: 256 사전학습 + 8 카테고리)
        self.item_vector_full = nn.Embedding(n_items, 264)
        # projection layer 복원 - 256차원 → 128차원 특성 변환
        self.item_projection = nn.Sequential(
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Dropout(0.3)
        )

        # 사용자 임베딩 (128차원으로 복원)
        self.user_embedding_gmf = nn.Embedding(n_users, 256)
        self.user_embedding_mlp = nn.Embedding(n_users, 256)
        self.user_category_preference = nn.Embedding(n_users, 8)

        # GMF 브랜치 (Hadamard 내적 + FC) - 128차원 입력
        self.gmf_projection = nn.Sequential(
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Dropout(0.3)
        )

        # MLP 브랜치 (순수 MLP - 카테고리 없음) - 256차원 입력 (128+128)
        self.mlp_main = nn.Sequential(
            nn.Linear(256, 256),  # 128+128 입력
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(256, 256),
            nn.ReLU(),
            nn.Dropout(0.3)
        )

        self.mlp_projection = nn.Sequential(
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Dropout(0.3)
        )

        # 최종 융합 (128+128+8+8 = 272차원)
        self.final_fusion = nn.Sequential(
            nn.Linear(272, 128),
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

    def forward(self, user_ids, item_ids):
        # 1. 아이템 벡터 분리
        vector_full = self.item_vector_full(item_ids)
        item_pretrained = vector_full[:, :256]  # 256차원 사전학습 벡터
        item_category = vector_full[:, 256:]
        # projection layer를 통한 특성 변환 (256 → 128)
        item_projected = self.item_projection(item_pretrained)

        # 2. 사용자 임베딩 (128차원)
        user_gmf = self.user_embedding_gmf(user_ids)
        user_mlp = self.user_embedding_mlp(user_ids)
        user_category_pref = self.user_category_preference(user_ids)

        # 3. GMF 브랜치 (Hadamard 내적 + FC) - 128차원
        gmf_output = (user_gmf * item_projected)  # [B,128]
        gmf_output = self.gmf_projection(gmf_output)  # [B,128]

        # 4. MLP 브랜치 (순수 MLP) - 256차원 입력
        mlp_input = torch.cat([user_mlp, item_projected], dim=1)  # [B,256]
        mlp_output = self.mlp_projection(self.mlp_main(mlp_input))  # [B,128]

        # 5. 최종 융합 (GMF + MLP + 카테고리)
        final_input = torch.cat([
            gmf_output,  # [B, 128]
            mlp_output,  # [B, 128]
            user_category_pref,  # [B, 8]
            item_category  # [B, 8]
        ], dim=1)  # [B, 272]

        prediction = self.final_fusion(final_input).squeeze()

        return prediction
