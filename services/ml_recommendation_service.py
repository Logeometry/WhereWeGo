import torch
import torch.nn as nn
import numpy as np
from typing import List, Dict, Optional
from bson import ObjectId
import os
import json
import sys
import random

# NCF 모델 관련 임포트
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
model_dir = os.path.join(parent_dir, 'model')
if os.path.exists(model_dir):
    sys.path.insert(0, model_dir)
    try:
        from ncf_inner.models import SymmetricResidualCategoryNCF
        from ncf_inner.config import CONFIG
        from ncf_inner.data_utils import load_data
        NCF_AVAILABLE = True
        print("✅ NCF 모델 모듈 로드 성공")
    except ImportError as e:
        print(f"⚠️ NCF 모델 임포트 실패: {e}")
        NCF_AVAILABLE = False
        SymmetricResidualCategoryNCF = None
        CONFIG = None
        load_data = None
else:
    print("⚠️ model 디렉토리를 찾을 수 없습니다.")
    NCF_AVAILABLE = False
    SymmetricResidualCategoryNCF = None
    CONFIG = None
    load_data = None

class MLRecommendationService:
    def __init__(self):
        self.model = None
        self.model_data = None
        self.tourism_data = None
        self.user_mapping = {}
        self.item_mapping = {}
        self.reverse_item_mapping = {}
        self.is_loaded = False
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
    async def load_model(self, ckpt_path: str = None, mapping_path: str = None):
        """NCF 모델을 로드하고 전역 변수에 저장 (1.localserver.py와 동일한 방식)"""
        if not NCF_AVAILABLE:
            print("❌ NCF 모듈을 사용할 수 없습니다.")
            return False
        
        if self.model is not None:
            print("✅ NCF 모델이 이미 로드되어 있습니다.")
            return True
        
        try:
            print("🔄 NCF 모델 로딩 중...")
            
            # 모델 파일 경로 찾기 (1.localserver.py와 호환)
            if ckpt_path is None:
                MODEL_PATH = "model_epoch_5.pth"
                possible_paths = [
                    MODEL_PATH,
                    os.path.join(current_dir, MODEL_PATH),
                    os.path.join(current_dir, 'checkpoints', MODEL_PATH),
                    os.path.join(current_dir, '..', MODEL_PATH),
                    os.path.join(parent_dir, 'model', MODEL_PATH),
                    os.path.join(parent_dir, 'model', 'ncf_inner', MODEL_PATH),
                    'C:/Users/user/Desktop/새 폴더 (2)/.vscode/WhereWeGo-backend/model/model_epoch_5.pth',
                    'best_model_v5_modular.pth',
                    os.path.join(parent_dir, 'model', 'best_model_v5_modular.pth')
                ]
            else:
                possible_paths = [ckpt_path]
            
            model_file_path = None
            for path in possible_paths:
                if os.path.exists(path):
                    model_file_path = path
                    break
            
            if not model_file_path:
                print(f"❌ 모델 파일을 찾을 수 없습니다")
                return False
            
            # 데이터 로딩 (사용자/아이템 수 확인용)
            try:
                if load_data:
                    self.model_data = load_data()
                    n_users = self.model_data['n_users']
                    n_items = self.model_data['n_items']
                    print(f"📊 데이터 로드 완료: 사용자 {n_users}명, 아이템 {n_items}개")
                else:
                    raise Exception("load_data 함수를 사용할 수 없습니다")
            except Exception as e:
                print(f"⚠️ 데이터 로딩 실패: {e}")
                # 관광지 데이터 기반으로 아이템 수 추정
                try:
                    tourism_data = await self.load_tourism_data()
                    if tourism_data and 'groups' in tourism_data:
                        n_items = sum(len(group.get('items', [])) for group in tourism_data['groups'])
                        print(f"📍 관광지 데이터 기반 아이템 수: {n_items}개")
                    else:
                        n_items = 1000
                        print(f"📊 기본 아이템 수 사용: {n_items}개")
                except:
                    n_items = 1000
                    print(f"📊 기본 아이템 수 사용: {n_items}개")
                
                # 사용자 수는 에러 내용에서 추정된 현재 크기 사용
                n_users = 7384  # 오류 메시지에서 보이는 현재 모델 크기
                print(f"📊 추정 사용자 수: {n_users}명")
                
                # 기본 데이터 구조 생성
                self.model_data = {
                    'n_users': n_users,
                    'n_items': n_items,
                    'item_id_to_model_idx': {i: i for i in range(n_items)},
                    'user_id_to_idx': {}  # 빈 매핑으로 시작
                }
            
            # 모델 초기화
            if CONFIG:
                config = CONFIG
            else:
                config = {
                    "embedding_dim": 128,
                    "mlp_layers": [256, 256],
                    "dropout": 0.3
                }
            
            self.model = SymmetricResidualCategoryNCF(
                n_users=n_users,
                n_items=n_items,
                config=config
            ).to(self.device)
            
            # 모델 로드 (크기 불일치 처리 - 1.localserver.py와 동일)
            checkpoint = torch.load(model_file_path, map_location=self.device)
            
            # 체크포인트 형식 확인
            if isinstance(checkpoint, dict) and 'model_state_dict' in checkpoint:
                saved_state_dict = checkpoint['model_state_dict']
                epoch = checkpoint.get('epoch', 'Unknown')
                print(f"📦 체크포인트 발견 (에폭: {epoch})")
            else:
                saved_state_dict = checkpoint
                epoch = 'Unknown'
                print(f"📦 모델 state_dict 발견")
            
            # 크기 호환성 검사 및 조정
            print("🔍 모델 크기 호환성 검사...")
            current_state_dict = self.model.state_dict()
            compatible_state_dict = {}
            size_mismatches = []
            missing_keys = []
            
            for key in current_state_dict.keys():
                if key in saved_state_dict:
                    saved_shape = saved_state_dict[key].shape
                    current_shape = current_state_dict[key].shape
                    
                    if saved_shape == current_shape:
                        compatible_state_dict[key] = saved_state_dict[key]
                        print(f"✅ {key}: {current_shape} - 호환됨")
                    else:
                        print(f"⚠️ {key}: 저장된 크기 {saved_shape} -> 현재 크기 {current_shape}")
                        size_mismatches.append((key, saved_shape, current_shape))
                        
                        # 크기 조정 로직
                        if len(saved_shape) == 2 and len(current_shape) == 2:
                            current_tensor = current_state_dict[key].clone()
                            min_dim0 = min(saved_shape[0], current_shape[0])
                            min_dim1 = min(saved_shape[1], current_shape[1])
                            current_tensor[:min_dim0, :min_dim1] = saved_state_dict[key][:min_dim0, :min_dim1]
                            compatible_state_dict[key] = current_tensor
                            print(f"🔧 {key}: 크기 조정 완료 ({min_dim0}x{min_dim1} 복사)")
                        elif len(saved_shape) == 1 and len(current_shape) == 1:
                            current_tensor = current_state_dict[key].clone()
                            min_dim = min(saved_shape[0], current_shape[0])
                            current_tensor[:min_dim] = saved_state_dict[key][:min_dim]
                            compatible_state_dict[key] = current_tensor
                            print(f"🔧 {key}: 1D 크기 조정 완료 ({min_dim} 복사)")
                        else:
                            compatible_state_dict[key] = current_state_dict[key]
                            print(f"🔧 {key}: 기본값 사용 (형태 불일치)")
                else:
                    missing_keys.append(key)
                    compatible_state_dict[key] = current_state_dict[key]
                    
                    if key in ["user_time_period.weight", "user_season.weight", "user_preference.weight"]:
                        print(f"➕ {key}: 새로운 컨텍스트 레이어, 랜덤 초기화 사용")
                    else:
                        print(f"➕ {key}: 새로운 레이어, 기본값 사용")
            
            # 호환성 조정된 state_dict 로드
            try:
                self.model.load_state_dict(compatible_state_dict, strict=False)
                print(f"✅ 모델 로드 완료 (크기 조정 적용)")
                
                if size_mismatches:
                    print(f"📊 크기 조정된 레이어: {len(size_mismatches)}개")
                if missing_keys:
                    print(f"📊 새로 초기화된 레이어: {len(missing_keys)}개")
                    
                print(f"🎯 최종 모델 크기: 사용자 {n_users}명, 아이템 {n_items}개")
                    
            except Exception as load_error:
                print(f"❌ 모델 로드 실패: {load_error}")
                return False
            
            self.model.eval()  # 추론 모드로 전환
            self.is_loaded = True
            
            print(f"🎯 디바이스: {self.device}")
            print(f"📂 모델 파일: {model_file_path}")
            return True
            
        except Exception as e:
            print(f"❌ NCF 모델 로딩 실패: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def load_tourism_data(self):
        """관광지 데이터 로드 (1.localserver.py와 동일)"""
        try:
            # 현재 디렉토리에서 찾고, 없으면 상위 디렉토리에서 찾기
            file_paths = [
                'sort3Wpreference.json',
                os.path.join(parent_dir, 'model', 'sort3Wpreference.json'),
                'C:/Users/user/Desktop/새 폴더 (2)/.vscode/WhereWeGo-backend/model/sort3Wpreference.json'
            ]
            
            for file_path in file_paths:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        self.tourism_data = data
                        return data
                except FileNotFoundError:
                    continue
            
            print("관광지 데이터 파일을 찾을 수 없습니다.")
            return None
        except Exception as e:
            print(f"데이터 로드 오류: {e}")
            return None

    def get_tourism_data_in_tester_format(self):
        """tester.py 형식으로 관광지 데이터를 변환"""
        if not self.tourism_data:
            return {}
        
        # tester.py 형식으로 변환: {index: {name, category, category_group, ...}}
        tourism_dict = {}
        for group in self.tourism_data.get('groups', []):
            for item in group.get('items', []):
                if 'index' in item and 'name' in item:
                    tourism_dict[item['index']] = {
                        'name': item['name'],
                        'category': item.get('category', ''),
                        'category_group': item.get('category_group', ''),
                        'popular_score': item.get('popular_score', 0),
                        'visitors_count': item.get('visitors_count', 0),
                        'final_score': item.get('final_score', 0)
                    }
        return tourism_dict

    def recommend_with_vote_context(self, user_vote_schemas, top_k=10):
        """vote_schema 컨텍스트를 기반으로 한 추천 (1.localserver.py와 동일)"""
        print(f"🎯 Vote schema 기반 컨텍스트 추천 시작")
        
        if not self.model or not self.model_data:
            print("❌ 모델이나 데이터가 로드되지 않았습니다.")
            return []
        
        # vote_schema에서 사용자 컨텍스트 정보 추출 (첫 번째 스키마 사용)
        if not user_vote_schemas or len(user_vote_schemas[0]) < 6:
            print("❌ vote_schema 형식이 올바르지 않습니다.")
            return []
        
        first_schema = user_vote_schemas[0]
        user_context = {
            'category_group': first_schema[1],    # category_group (str)
            'activity_level': first_schema[2],    # activity_level (int: 0-2)
            'time_period': first_schema[3],       # time_period (int: 0-2) 
            'season': first_schema[4],           # season (int: 0-3)
            'preference': first_schema[5]        # preference (int: 0-1)
        }
        
        print(f"📊 추출된 사용자 컨텍스트: {user_context}")
        
        # 선택된 아이템들 (positive items) 추출 - 중복 제거
        selected_items = set()
        for schema in user_vote_schemas:
            if len(schema) >= 7:  # pos_item_index가 7번째 인덱스
                selected_items.add(schema[6])  # pos_item_index
        
        selected_items = list(selected_items)
        print(f"🚫 제외할 아이템들: {selected_items} (총 {len(selected_items)}개)")
        
        # 가상 사용자 ID 설정 (일관성을 위해 고정값 사용)
        virtual_user_id = 10001
        user_idx = 0  # 첫 번째 사용자 인덱스 사용
        
        print(f"🎭 가상 사용자 ID: {virtual_user_id}, 모델 인덱스: {user_idx}")
        
        # 모든 아이템에 대한 예측 점수 계산
        all_item_indices = list(self.model_data['item_id_to_model_idx'].values()) if 'item_id_to_model_idx' in self.model_data else list(range(self.model_data['n_items']))
        
        with torch.no_grad():
            # 사용자와 모든 아이템 조합 생성
            user_tensor = torch.tensor([user_idx] * len(all_item_indices), device=self.device)
            items_tensor = torch.tensor(all_item_indices, device=self.device)
            
            # 컨텍스트 정보를 포함하여 예측 수행
            try:
                # 모든 컨텍스트 키가 있는지 확인
                if all(key in user_context for key in ['category_group', 'activity_level', 'time_period', 'season', 'preference']):
                    category_groups = [user_context['category_group']] * len(all_item_indices)
                    activity_levels = [user_context['activity_level']] * len(all_item_indices)
                    time_periods = [user_context['time_period']] * len(all_item_indices)
                    seasons = [user_context['season']] * len(all_item_indices)
                    preferences = [user_context['preference']] * len(all_item_indices)
                    
                    # 컨텍스트를 포함한 예측 시도
                    predictions = torch.sigmoid(
                        self.model(user_tensor, items_tensor, category_groups, activity_levels, time_periods, seasons, preferences)
                    )
                    print("✅ 컨텍스트 포함 예측 성공")
                else:
                    # 기본 예측
                    predictions = torch.sigmoid(self.model(user_tensor, items_tensor))
                    print("⚠️ 컨텍스트 불완전, 기본 예측 사용")
                    
            except Exception as context_error:
                print(f"⚠️ 컨텍스트 포함 예측 실패: {context_error}")
                print("🔄 기본 예측으로 대체")
                # 기본 예측으로 대체
                predictions = torch.sigmoid(self.model(user_tensor, items_tensor))
            
            predictions_np = predictions.cpu().numpy()
            
            # 선택된 아이템들의 점수를 -1.0으로 설정하여 제외
            for item_id in selected_items:
                if 'item_id_to_model_idx' in self.model_data and item_id in self.model_data['item_id_to_model_idx']:
                    model_idx = self.model_data['item_id_to_model_idx'][item_id]
                    if model_idx in all_item_indices:
                        idx_pos = all_item_indices.index(model_idx)
                        predictions_np[idx_pos] = -1.0
                elif item_id < len(all_item_indices):  # 직접 인덱스로 사용
                    if item_id < len(predictions_np):
                        predictions_np[item_id] = -1.0
            
            # 상위 k개 아이템 선택
            top_indices = np.argsort(predictions_np)[::-1][:top_k]
            top_items = [all_item_indices[idx] for idx in top_indices]
            
            # 추천 결과 생성
            tourism_dict = self.get_tourism_data_in_tester_format()
            recommendations = []
            for i, item_idx in enumerate(top_items):
                score = predictions_np[all_item_indices.index(item_idx)]
                
                # 점수가 음수인 경우 제외
                if score < 0:
                    continue
                    
                # 관광지 정보 가져오기
                if item_idx in tourism_dict:
                    item_info = tourism_dict[item_idx]
                    item_name = item_info['name']
                    category_info = f"{item_info['category']} ({item_info['category_group']})"
                    final_score = item_info.get('final_score', 0)
                else:
                    item_name = f"관광지_{item_idx}"
                    category_info = "알 수 없음"
                    final_score = 0
                
                recommendations.append({
                    'rank': i + 1,
                    'item_id': item_idx,
                    'item_name': item_name,
                    'category': category_info,
                    'score': float(score),
                    'final_score': final_score,
                    'reason': f"Vote schema 컨텍스트 기반 ML 예측 (점수: {score:.4f})"
                })
        
        print(f"✅ 추천 완료: {len(recommendations)}개 관광지 추천")
        return recommendations

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
        """설문조사 결과를 survey_log 컬렉션에 저장 (8요소 구조화된 형태)"""
        from services.db_handler import survey_log_collection
        from datetime import datetime, timezone
        from schemas import Survey_log
        
        try:
            for pref in survey_preferences:
                # 8요소 구조화된 설문조사 로그 생성
                survey_log_data = Survey_log(
                    user_id=str(pref.get("user_id", user_id)),
                    category_group=str(pref.get("category_group", "")),
                    activity_level_idx=int(pref.get("activity_level_idx", 0)),
                    time_period=int(pref.get("time_period", 0)),
                    season=int(pref.get("season", 0)),
                    preference=int(pref.get("preference", 0)),
                    pos_item_index=int(pref.get("pos_item_index", 0)),
                    neg_item_index=int(pref.get("neg_item_index", 0)),
                    timestamp=datetime.now(timezone.utc)
                )
                # 별도의 survey_log 컬렉션에 저장
                await survey_log_collection.insert_one(survey_log_data.dict())
                
                print(f"✅ 설문조사 로그 저장: 사용자={user_id}, 카테고리={pref.get('category_group')}, "
                      f"활동성={pref.get('activity_level_idx')}, 시간대={pref.get('time_period')}, "
                      f"계절={pref.get('season')}, 선호도={pref.get('preference')}, "
                      f"긍정={pref.get('pos_item_index')}, 부정={pref.get('neg_item_index')}")
            return True
        except Exception as e:
            print(f"설문조사 로그 저장 실패: {e}")
            return False
    
    async def get_survey_logs(self, user_id: str) -> List[Dict]:
        """사용자의 설문조사 로그 가져오기 (8요소 구조화된 형태)"""
        from services.db_handler import survey_log_collection
        
        try:
            logs_cursor = survey_log_collection.find({"user_id": user_id}).sort("timestamp", -1)
            survey_logs = []
            async for log in logs_cursor:
                survey_logs.append({
                    "user_id": log.get("user_id"),
                    "category_group": log.get("category_group"),
                    "activity_level_idx": log.get("activity_level_idx"),
                    "time_period": log.get("time_period"),
                    "season": log.get("season"),
                    "preference": log.get("preference"),
                    "pos_item_index": log.get("pos_item_index"),
                    "neg_item_index": log.get("neg_item_index"),
                    "timestamp": log.get("timestamp")
                })
            return survey_logs
        except Exception as e:
            print(f"설문조사 로그 조회 실패: {e}")
            return []

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
        """ML 모델 기반 추천 (vote_schema 지원)"""
        if not self.is_loaded:
            print("ML 모델이 로드되지 않았습니다.")
            # 모델 로딩 시도
            if not await self.load_model():
                return []
        
        try:
            # 관광지 데이터 로딩
            if not self.tourism_data:
                await self.load_tourism_data()
            
            # survey_preferences가 vote_schema 형식인지 확인
            if survey_preferences and len(survey_preferences) > 0:
                first_pref = survey_preferences[0]
                
                # vote_schema 형식 감지 (8개 필드)
                if (isinstance(first_pref, dict) and 
                    all(key in first_pref for key in ["user_id", "category_group", "activity_level_idx", 
                                                     "time_period", "season", "preference", 
                                                     "pos_item_index", "neg_item_index"])):
                    
                    print("🎯 Vote schema 형식 감지 - 컨텍스트 기반 추천 수행")
                    
                    # vote_schema를 리스트 형식으로 변환
                    vote_schemas = []
                    for pref in survey_preferences:
                        schema = [
                            pref["user_id"],
                            pref["category_group"],
                            pref["activity_level_idx"],
                            pref["time_period"],
                            pref["season"],
                            pref["preference"],
                            pref["pos_item_index"],
                            pref["neg_item_index"]
                        ]
                        vote_schemas.append(schema)
                    
                    # vote_schema 기반 추천 수행
                    recommendations = self.recommend_with_vote_context(vote_schemas, top_k=count)
                    
                    # 형식 변환
                    formatted_recommendations = []
                    for rec in recommendations:
                        formatted_recommendations.append({
                            "place_id": str(rec['item_id']),
                            "score": rec['score'],
                            "model_score": rec['score'],
                            "name": rec.get('item_name', ''),
                            "category": rec.get('category', ''),
                            "reason": rec.get('reason', '')
                        })
                    
                    return formatted_recommendations
            
            # 기존 방식 (vote_schema가 아닌 경우)
            print("🔄 기본 추천 방식 사용")
            
            if save_to_logs and survey_preferences:
                await self.save_survey_to_user_logs(user_id, survey_preferences)
            
            # 사용자 매핑 확인
            if user_id in self.user_mapping:
                user_idx = self.user_mapping[user_id]
            else:
                user_idx = 0  # 기본 사용자 인덱스
                self.user_mapping[user_id] = user_idx
            
            recommendations = []
            
            # 간단한 추천 (아이템 매핑이 없는 경우 기본 추천)
            if not self.item_mapping:
                print("⚠️ 아이템 매핑이 없어 기본 추천을 제공합니다.")
                # 관광지 데이터에서 상위 아이템들 반환
                tourism_dict = self.get_tourism_data_in_tester_format()
                sorted_items = sorted(tourism_dict.items(), 
                                    key=lambda x: x[1].get('final_score', 0), 
                                    reverse=True)
                
                for i, (item_id, item_info) in enumerate(sorted_items[:count]):
                    recommendations.append({
                        "place_id": str(item_id),
                        "score": 0.8 - (i * 0.01),  # 점진적 점수 감소
                        "model_score": 0.8 - (i * 0.01),
                        "name": item_info.get('name', ''),
                        "category": item_info.get('category_group', ''),
                        "reason": "기본 추천 (final_score 기준)"
                    })
                
                return recommendations
            
            # 모델 기반 추천
            with torch.no_grad():
                for item_id, item_idx in self.item_mapping.items():
                    if exclude_places and item_id in exclude_places:
                        continue
                    
                    user_tensor = torch.tensor([user_idx], dtype=torch.long, device=self.device)
                    item_tensor = torch.tensor([item_idx], dtype=torch.long, device=self.device)
                    
                    try:
                        model_score = torch.sigmoid(self.model(user_tensor, item_tensor)).item()
                    except Exception as model_error:
                        print(f"모델 예측 오류: {model_error}")
                        model_score = 0.5  # 기본 점수
                    
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
