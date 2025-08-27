# services/ml_recommendation_service.py
"""
ML 모델 기반 추천 서비스
체크포인트를 로드하여 개인화된 추천 제공
"""

import torch
import numpy as np
from typing import List, Dict, Optional
from bson import ObjectId
import os

# 모델 import
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'model'))
from model.models import SymmetricResidualCategoryNCF

class MLRecommendationService:
    def __init__(self):
        self.model = None
        self.user_mapping = {}  # 사용자 ID → 모델 인덱스
        self.item_mapping = {}  # 아이템 ID → 모델 인덱스
        self.reverse_item_mapping = {}  # 모델 인덱스 → 아이템 ID
        self.is_loaded = False
        
    async def load_model(self, ckpt_path: str):
        """체크포인트에서 모델 로드"""
        try:
            # 체크포인트 정보 확인
            ckpt = torch.load(ckpt_path, map_location="cpu")
            print("체크포인트 키들:", list(ckpt.keys()))
            
            # 체크포인트에서 사용자/아이템 수 추출
            user_embedding = ckpt.get('user_embedding_gmf.weight', None)
            item_embedding = ckpt.get('item_embedding_gmf.weight', None)
            
            if user_embedding is not None and item_embedding is not None:
                n_users = user_embedding.shape[0]
                n_items = item_embedding.shape[0]
                print(f"체크포인트에서 추출: n_users={n_users}, n_items={n_items}")
            else:
                # 기본값 설정
                n_users = 7434  # 체크포인트에서 확인된 값
                n_items = 1000  # 예시 값
                print(f"기본값 사용: n_users={n_users}, n_items={n_items}")
            
            # 모델 설정
            config = {
                "embedding_dim": 128,  # 체크포인트와 일치
                "mlp_layers": [256, 256],
                "dropout": 0.3
            }
            
            # 모델 초기화
            self.model = SymmetricResidualCategoryNCF(n_users, n_items, config)
            
            # 체크포인트 로드 (strict=False로 호환성 유지)
            self.model.load_state_dict(ckpt, strict=False)
            self.model.eval()
            
            # 매핑 초기화 (실제로는 DB에서 가져와야 함)
            await self._initialize_mappings()
            
            self.is_loaded = True
            print("ML 모델 로드 완료!")
            
        except Exception as e:
            print(f"모델 로드 실패: {e}")
            self.is_loaded = False
    
    async def _initialize_mappings(self):
        """사용자/아이템 ID 매핑 초기화"""
        # 실제로는 DB에서 사용자/아이템 목록을 가져와서 매핑해야 함
        # 임시로 더미 매핑 생성
        from services.db_handler import tourism_collection
        
        # 테스트 사용자 정보 하드코딩
        self.test_users = {
            "test123": {
                "user_idx": 123,  # 모델에서 사용할 인덱스
                "name": "테스트 사용자",
                "preferences": {
                    "categories": ["관광지", "문화시설", "자연"],
                    "regions": ["해운대구", "중구", "동래구"],
                    "rating_threshold": 4.0,
                    "max_travel_time": 60
                },
                "history": [
                    "681891fa77e67d6ebadae3dd",  # 부산역
                    "681891fa77e67d6ebadae3de",  # 해운대해수욕장
                    "681891fa77e67d6ebadae3df"   # 광안대교
                ]
            },
            "test_user_123": {
                "user_idx": 456,
                "name": "테스트 사용자 2",
                "preferences": {
                    "categories": ["음식점", "카페", "쇼핑"],
                    "regions": ["서구", "부산진구"],
                    "rating_threshold": 3.5,
                    "max_travel_time": 30
                },
                "history": [
                    "681891fa77e67d6ebadae3e0",  # 자갈치시장
                    "681891fa77e67d6ebadae3e1"   # 국제시장
                ]
            }
        }
        
        # 아이템 매핑 (관광지 ID → 모델 인덱스)
        places_cursor = tourism_collection.find({}, {"_id": 1})
        item_count = 0
        async for place in places_cursor:
            self.item_mapping[str(place["_id"])] = item_count
            self.reverse_item_mapping[item_count] = str(place["_id"])
            item_count += 1
            if item_count >= 1000:  # 모델의 n_items 제한
                break
        
        print(f"아이템 매핑 생성 완료: {len(self.item_mapping)}개")
        print(f"테스트 사용자 등록: {list(self.test_users.keys())}")
    
    async def get_recommendations(self, user_id: str, count: int = 10, 
                                exclude_places: List[str] = None) -> List[Dict]:
        """ML 모델 기반 추천"""
        if not self.is_loaded:
            print("ML 모델이 로드되지 않았습니다. 인기도 기반으로 폴백합니다.")
            return []
        
        try:
            # 테스트 사용자 정보 확인
            if user_id in self.test_users:
                user_info = self.test_users[user_id]
                user_idx = user_info["user_idx"]
                print(f"테스트 사용자 '{user_id}' 정보: {user_info['name']}")
                print(f"선호 카테고리: {user_info['preferences']['categories']}")
                print(f"방문 이력: {len(user_info['history'])}개 장소")
            else:
                # 일반 사용자는 해시 기반
                user_idx = hash(user_id) % 7434
                print(f"일반 사용자 '{user_id}' (인덱스: {user_idx})")
            
            # 추천 점수 계산
            recommendations = []
            
            with torch.no_grad():
                for item_id, item_idx in self.item_mapping.items():
                    # 제외할 장소 스킵
                    if exclude_places and item_id in exclude_places:
                        continue
                    
                    # 모델 예측
                    user_tensor = torch.tensor([user_idx], dtype=torch.long)
                    item_tensor = torch.tensor([item_idx], dtype=torch.long)
                    
                    score = self.model(user_tensor, item_tensor).item()
                    
                    recommendations.append({
                        "place_id": item_id,
                        "score": score
                    })
            
            # 점수 순으로 정렬하고 상위 count개 반환
            recommendations.sort(key=lambda x: x["score"], reverse=True)
            return recommendations[:count]
            
        except Exception as e:
            print(f"ML 추천 오류: {e}")
            return []
    
    async def get_similar_places(self, place_id: str, count: int = 5) -> List[Dict]:
        """유사한 장소 추천"""
        if not self.is_loaded:
            return []
        
        try:
            # 임시 구현: 랜덤 추천
            from services.db_handler import tourism_collection
            
            pipeline = [
                {"$match": {"_id": {"$ne": ObjectId(place_id)}}},
                {"$sample": {"size": count}}
            ]
            
            places_cursor = tourism_collection.aggregate(pipeline)
            places = await places_cursor.to_list(length=count)
            
            return [
                {
                    "place_id": str(place["_id"]),
                    "name": place.get("name", ""),
                    "similarity_score": np.random.uniform(0.5, 0.9)
                }
                for place in places
            ]
            
        except Exception as e:
            print(f"유사 장소 추천 오류: {e}")
            return []

# 전역 인스턴스
ml_recommendation_service = MLRecommendationService()
