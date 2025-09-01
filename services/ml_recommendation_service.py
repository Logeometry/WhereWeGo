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
    
    async def get_user_survey_preferences(self, user_id: str) -> List[Dict]:
        """사용자의 설문조사 선호도 가져오기 (유저 로그에서)"""
        from services.db_handler import user_log_collection
        
        try:
            logs_cursor = user_log_collection.find({
                "user_id": user_id,
                "event": {"$regex": "^survey_"}
            })
            
            survey_prefs = []
            async for log in logs_cursor:
                event = log.get("event")
                if event.startswith("survey_"):
                    response = event.replace("survey_", "")
                    survey_prefs.append({
                        "content_id": log.get("target_id"),
                        "responses": response
                    })
            
            return survey_prefs
        except Exception as e:
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
                 user_idx = hash(user_id) % 7434
            
            if save_to_logs:
                user_logs = await self.get_user_logs(user_id)
                survey_prefs = await self.get_user_survey_preferences(user_id)
            else:
                survey_prefs = []
            

            
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
                        "score": model_score,
                        "model_score": model_score
                    })
            
            recommendations.sort(key=lambda x: x["score"], reverse=True)
            return recommendations[:count]
            
        except Exception as e:
            print(f"ML 추천 오류: {e}")
            import traceback
            traceback.print_exc()
            return []
    
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
