import torch
import numpy as np
from typing import List, Dict, Optional
from bson import ObjectId
import os
import json
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'model'))
from model.ncf_inner.models import SymmetricResidualCategoryNCF

class MLRecommendationService:
    def __init__(self):
        self.model = None
        self.user_mapping = {}
        self.item_mapping = {}
        self.reverse_item_mapping = {}
        self.is_loaded = False
        
    async def load_model(self, ckpt_path: str, mapping_path: str = None):
        try:
            ckpt = torch.load(ckpt_path, map_location="cpu")
            
            if 'model_state_dict' in ckpt:
                model_state_dict = ckpt['model_state_dict']
                final_fusion_weight = model_state_dict.get('final_fusion.0.weight', None)
                
                config = {
                    "embedding_dim": 128,
                    "mlp_layers": [256, 256],
                    "dropout": 0.3
                }
                
                user_embedding = model_state_dict.get('user_embedding_gmf.weight', None)
                item_embedding = model_state_dict.get('item_embedding_gmf.weight', None)
                
                if user_embedding is not None and item_embedding is not None:
                    n_users = user_embedding.shape[0]
                    n_items = item_embedding.shape[0]
                else:
                    n_users = ckpt.get('n_users', 1000)
                    n_items = ckpt.get('n_items', 1000)
                
                if mapping_path and os.path.exists(mapping_path):
                    with open(mapping_path, 'r', encoding='utf-8') as f:
                        mappings = json.load(f)
                    self.user_mapping = mappings.get('user_mapping', {})
                    self.item_mapping = mappings.get('item_mapping', {})
                    self.reverse_item_mapping = {v: k for k, v in self.item_mapping.items()}
                else:
                    self.user_mapping = ckpt.get('user_mapping', {})
                    self.item_mapping = ckpt.get('item_mapping', {})
                    self.reverse_item_mapping = {v: k for k, v in self.item_mapping.items()}
            else:
                user_embedding = ckpt.get('user_embedding_gmf.weight', None)
                item_embedding = ckpt.get('item_embedding_gmf.weight', None)
                
                if user_embedding is not None and item_embedding is not None:
                    n_users = user_embedding.shape[0]
                    n_items = item_embedding.shape[0]
                else:
                    n_users = 7434
                    n_items = 1000
                
                config = {
                    "embedding_dim": 128,
                    "mlp_layers": [256, 256],
                    "dropout": 0.3
                }
                model_state_dict = ckpt
            
            # 모델 초기화
            self.model = SymmetricResidualCategoryNCF(n_users, n_items, config)
            
            if final_fusion_weight is not None and final_fusion_weight.shape[1] != 300:
                adjusted_weight = torch.zeros(128, 300)
                adjusted_weight[:, :291] = final_fusion_weight
                model_state_dict['final_fusion.0.weight'] = adjusted_weight
                
                if 'final_fusion.0.bias' in model_state_dict:
                    bias = model_state_dict['final_fusion.0.bias']
                    if bias.shape[0] != 128:
                        adjusted_bias = torch.zeros(128)
                        adjusted_bias[:bias.shape[0]] = bias
                        model_state_dict['final_fusion.0.bias'] = adjusted_bias
            
            self.model.load_state_dict(model_state_dict, strict=False)
            self.model.eval()
           
            if not self.user_mapping or not self.item_mapping:
                try:
                    await self._initialize_mappings()
                except Exception as e:
                    print(f"매핑 초기화 실패, 기본 매핑 사용: {e}")
                    # 기본 매핑으로 계속 진행
            
            self.is_loaded = True
            
        except Exception as e:
            print(f"ML 모델 로딩 실패: {e}")
            import traceback
            traceback.print_exc()
            self.is_loaded = False
    
    async def _initialize_mappings(self):
        """사용자/아이템 ID 매핑 초기화"""
        from services.db_handler import tourism_collection, user_log_collection
        
        # 아이템 매핑 (관광지 ID → 모델 인덱스)
        places_cursor = tourism_collection.find({}, {"_id": 1})
        item_count = 0
        async for place in places_cursor:
            self.item_mapping[str(place["_id"])] = item_count
            self.reverse_item_mapping[item_count] = str(place["_id"])
            item_count += 1
            if item_count >= 1000:
                break
        
        await self._initialize_user_mappings()
    
    async def _initialize_user_mappings(self):
        from services.db_handler import user_log_collection
        
        try:
            user_ids = await user_log_collection.distinct("user_id")
            user_count = 0
            
            for user_id in user_ids:
                if user_count >= 7434:
                    break
                self.user_mapping[user_id] = user_count
                user_count += 1
        except Exception as e:
            print(f"사용자 매핑 초기화 실패: {e}")
            # 빈 매핑으로 계속 진행
    
    async def get_user_logs(self, user_id: str) -> List[Dict]:
        from services.db_handler import user_log_collection
        
        logs_cursor = user_log_collection.find({"user_id": user_id})
        logs = []
        async for log in logs_cursor:
            logs.append({
                "event": log.get("event"),
                "target_id": log.get("target_id"),
                "timestamp": log.get("timestamp")
            })
        return logs
    
    async def save_survey_to_user_logs(self, user_id: str, survey_preferences: List[Dict]):
        """설문조사 결과를 유저 로그에 저장"""
        from services.db_handler import user_log_collection
        from datetime import datetime, timezone
        
        try:
            for pref in survey_preferences:
                log_data = {
                    "user_id": user_id,
                    "event": f"survey_{pref.get('responses', 'neutral')}",
                    "target_id": pref.get("content_id"),
                    "timestamp": datetime.now(timezone.utc)
                }
                await user_log_collection.insert_one(log_data)
            return True
        except Exception as e:
            return False
    
    async def get_user_behavior_logs(self, user_id: str) -> List[Dict]:
        """사용자의 모든 행동 로그 가져오기 (찜, 클릭, 방문 등)"""
        from services.db_handler import user_log_collection
        
        try:
            # 모든 사용자 행동 로그 가져오기
            logs_cursor = user_log_collection.find({
                "user_id": user_id
            }).sort("timestamp", -1)  # 최신순 정렬
            
            behavior_logs = []
            async for log in logs_cursor:
                event = log.get("event")
                target_id = log.get("target_id")
                timestamp = log.get("timestamp")
                
                # TODO: 추후 이벤트 타입별 가중치 부여 시스템 구현
                # 현재는 모든 이벤트에 동일한 가중치 적용

                weight = 1.0
                
                behavior_logs.append({
                    "content_id": target_id,
                    "event": event,
                    "weight": weight,
                    "timestamp": timestamp
                })
            
            return behavior_logs
        except Exception as e:
            print(f"사용자 행동 로그 조회 실패: {e}")
            return []
    
    async def get_recommendations(self, user_id: str, count: int = 10, 
                                exclude_places: List[str] = None,
                                survey_preferences: List[Dict] = None,
                                save_to_logs: bool = True) -> List[Dict]:
        """ML 모델 기반 추천 (실제 유저 로그와 설문조사 결과 포함)"""
        if not self.is_loaded:
            print("ML 모델이 로드되지 않았습니다.")
            return []
        
        try:
            if survey_preferences and save_to_logs:
                await self.save_survey_to_user_logs(user_id, survey_preferences)
            
            if user_id in self.user_mapping:
                user_idx = self.user_mapping[user_id]
            else:
                # 새로운 사용자: 임베딩 확장 및 기본값 설정
                new_user_idx = len(self.user_mapping)
                self.user_mapping[user_id] = new_user_idx
                
                # 모델 임베딩 확장
                if not self.expand_user_embeddings(new_user_idx):
                    print(f"사용자 임베딩 확장 실패, 기본 사용자(0) 사용")
                    user_idx = 0
                else:
                    user_idx = new_user_idx
            
            if save_to_logs:
                user_logs = await self.get_user_logs(user_id)
                behavior_logs = await self.get_user_behavior_logs(user_id)
            else:
                behavior_logs = []
            

            
            recommendations = []
            
            with torch.no_grad():
                for item_id, item_idx in self.item_mapping.items():
                    if exclude_places and item_id in exclude_places:
                        continue
                    
                    user_tensor = torch.tensor([user_idx], dtype=torch.long)
                    item_tensor = torch.tensor([item_idx], dtype=torch.long)
                    
                    model_score = self.model(user_tensor, item_tensor).item()
                    
                    recommendations.append({
                        "place_id": item_id,
                        "score": model_score
                    })
            
            recommendations.sort(key=lambda x: x["score"], reverse=True)
            return recommendations[:count]
            
        except Exception as e:
            print(f"ML 추천 오류: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def expand_user_embeddings(self, new_user_idx):
        """새로운 사용자 임베딩 확장 (기본값으로 초기화)"""
        try:
            # 기본값 설정
            default_activity = 1      # 중간 활동성
            default_time = 1          # 오후
            default_season = 1        # 여름  
            default_preference = 0    # 활동성 중심
            default_category = [0.125] * 8  # 모든 카테고리 동일 선호도
            
            # 1. 사용자 임베딩 확장
            self.model.user_embedding_gmf.weight.data = torch.cat([
                self.model.user_embedding_gmf.weight.data,
                torch.randn(1, 128)
            ], dim=0)
            
            self.model.user_embedding_mlp.weight.data = torch.cat([
                self.model.user_embedding_mlp.weight.data,
                torch.randn(1, 128)
            ], dim=0)
            
            # 2. 사용자 특성 임베딩 확장
            self.model.user_category_preference.weight.data = torch.cat([
                self.model.user_category_preference.weight.data,
                torch.randn(1, 8)
            ], dim=0)
            
            self.model.user_activity_level.weight.data = torch.cat([
                self.model.user_activity_level.weight.data,
                torch.randn(1, 3)
            ], dim=0)
            
            self.model.user_time_period.weight.data = torch.cat([
                self.model.user_time_period.weight.data,
                torch.randn(1, 3)
            ], dim=0)
            
            self.model.user_season.weight.data = torch.cat([
                self.model.user_season.weight.data,
                torch.randn(1, 4)
            ], dim=0)
            
            self.model.user_preference.weight.data = torch.cat([
                self.model.user_preference.weight.data,
                torch.randn(1, 2)
            ], dim=0)
            
            # 3. 기본값 설정
            self.set_default_embedding_values(new_user_idx, default_activity, default_time, default_season, default_preference, default_category)
            
            print(f"새로운 사용자 임베딩 확장 완료: user_idx={new_user_idx}")
            return True
            
        except Exception as e:
            print(f"사용자 임베딩 확장 실패: {e}")
            return False
    
    def set_default_embedding_values(self, user_idx, activity, time, season, preference, category):
        """새로운 사용자 임베딩에 기본값 설정"""
        try:
            # 활동성 레벨 (one-hot encoding)
            activity_embedding = torch.zeros(1, 3)
            activity_embedding[0, activity] = 1.0
            self.model.user_activity_level.weight.data[user_idx] = activity_embedding.squeeze()
            
            # 시간대 (one-hot encoding)
            time_embedding = torch.zeros(1, 3)
            time_embedding[0, time] = 1.0
            self.model.user_time_period.weight.data[user_idx] = time_embedding.squeeze()
            
            # 계절 (one-hot encoding)
            season_embedding = torch.zeros(1, 4)
            season_embedding[0, season] = 1.0
            self.model.user_season.weight.data[user_idx] = season_embedding.squeeze()
            
            # 선호도 (one-hot encoding)
            preference_embedding = torch.zeros(1, 2)
            preference_embedding[0, preference] = 1.0
            self.model.user_preference.weight.data[user_idx] = preference_embedding.squeeze()
            
            # 카테고리 선호도 (균등 분포)
            self.model.user_category_preference.weight.data[user_idx] = torch.tensor(category)
            
            print(f"사용자 {user_idx} 기본값 설정 완료")
            
        except Exception as e:
            print(f"기본값 설정 실패: {e}")

    async def get_similar_places(self, place_id: str, count: int = 5) -> List[Dict]:
        if not self.is_loaded:
            return []
        
        try:
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

ml_recommendation_service = MLRecommendationService()
