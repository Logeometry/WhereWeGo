# data_utils.py
# 데이터 처리 유틸리티 모듈

import torch
import json
import random
import numpy as np
import os
from torch.utils.data import Dataset, DataLoader

class NCFDataset(Dataset):
    """
    신경 협업 필터링 데이터셋
    
    학습을 위한 사용자-아이템 상호작용 데이터를 처리하며 부정 샘플링을 지원합니다.
    긍정 및 부정 샘플 생성을 모두 지원합니다.
    
    Args:
        interactions (dict): 사용자-아이템 상호작용 {user_id: [item_ids]}
        user_id_to_idx (dict): 사용자 ID에서 인덱스로의 매핑
        item_id_to_model_idx (dict): 아이템 ID에서 모델 인덱스로의 매핑
        negative_sampling (bool): 부정 샘플 생성 여부
    """
    
    def __init__(self, interactions, user_id_to_idx, item_id_to_model_idx, negative_sampling=True):
        self.user_id_to_idx = user_id_to_idx
        self.item_id_to_model_idx = item_id_to_model_idx
        self.samples = []
        
        # 긍정 샘플 생성
        for user_id, item_list in interactions.items():
            if user_id in user_id_to_idx:
                for item_id in item_list:
                    if item_id in item_id_to_model_idx:
                        user_idx = user_id_to_idx[user_id]
                        model_idx = item_id_to_model_idx[item_id]
                        self.samples.append((user_idx, model_idx, 1.0))
        
        # 부정 샘플 생성
        if negative_sampling:
            self._generate_negative_samples()
    
    def _generate_negative_samples(self):
        """설정된 비율로 부정 샘플 생성"""
        from .config import CONFIG  # 상대 import로 수정
        
        all_model_indices = list(self.item_id_to_model_idx.values())
        negative_samples = []
        
        for user_idx, pos_model_idx, _ in self.samples:
            for _ in range(CONFIG['negative_ratio']):
                neg_model_idx = random.choice(all_model_indices)
                negative_samples.append((user_idx, neg_model_idx, 0.0))
        
        self.samples.extend(negative_samples)
        random.shuffle(self.samples)
    
    def __getitem__(self, idx):
        return self.samples[idx]
    
    def __len__(self):
        return len(self.samples)

def get_data_file_path(filename):
    """데이터 파일의 전체 경로를 반환"""
    from .config import CONFIG
    
    # 여러 위치에서 파일을 찾아봄
    possible_paths = [
        os.path.join(CONFIG['data_dir'], filename),  # ./data/ 폴더
        filename,  # 현재 디렉토리
        os.path.join('..', filename),  # 상위 디렉토리
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    # 파일을 찾지 못한 경우
    raise FileNotFoundError(f"데이터 파일을 찾을 수 없습니다: {filename}\n"
                          f"다음 위치들을 확인했습니다: {possible_paths}")

def load_vector_data():
    """MongoDB 내보내기 형식의 사전학습 벡터 데이터 로딩"""
    from .config import CONFIG
    
    vector_file_path = get_data_file_path(CONFIG['vector_file'])
    print(f"벡터 파일 로딩: {vector_file_path}")
    
    with open(vector_file_path, 'r', encoding='utf-8') as f:
        vector_array = json.load(f)
    
    # index 필드를 기준으로 정렬하여 순서 보장
    vector_array.sort(key=lambda x: x['index'])
    
    # 인덱스 기반 매핑 생성
    index_to_model_idx = {}  # MongoDB index -> 모델 임베딩 인덱스
    vectors = []
    
    for model_idx, item_data in enumerate(vector_array):
        mongodb_index = item_data['index']
        vector_full = item_data['vector_full']
        
        index_to_model_idx[mongodb_index] = model_idx
        vectors.append(vector_full)
    
    print(f"벡터 데이터 로딩 완료: {len(vectors)}개 아이템")
    
    return {
        'vectors': vectors,
        'index_to_model_idx': index_to_model_idx,
        'n_items': len(vectors)
    }

def analyze_interaction_data():
    """improved_implicit.json의 triplet 형식 상호작용 데이터 분석"""
    from .config import CONFIG
    
    interaction_file_path = get_data_file_path(CONFIG['interaction_file'])
    print(f"상호작용 파일 로딩: {interaction_file_path}")
    
    with open(interaction_file_path, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)
    
    # triplets 키에서 데이터 추출
    if 'triplets' in raw_data:
        triplets = raw_data['triplets']
        
        # triplets를 user-item 상호작용 딕셔너리로 변환
        interactions = {}
        all_users = set()
        all_items = set()
        
        for triplet in triplets:
            if len(triplet) >= 2:  # user_id, item_id 최소 2개 원소 필요
                user_id = str(triplet[0])  # 문자열로 통일
                item_id = triplet[1]       # 원본 타입 유지
                
                all_users.add(user_id)
                all_items.add(item_id)
                
                if user_id not in interactions:
                    interactions[user_id] = []
                interactions[user_id].append(item_id)
        
        print(f"상호작용 데이터 로딩 완료: {len(interactions)}명 사용자, {len(all_items)}개 아이템")
        
    else:
        raise ValueError("'triplets' 키를 찾을 수 없습니다. 데이터 형식을 확인해주세요.")
    
    # 사용자 ID 분석
    user_sample_keys = list(interactions.keys())[:5]
    user_is_index_based = all(key.isdigit() for key in user_sample_keys)
    
    # 아이템 ID 분석
    interaction_item_sample = list(all_items)[:5]
    interaction_item_is_index_based = all(str(item).isdigit() for item in interaction_item_sample)
    
    return {
        'interactions': interactions,
        'user_is_index_based': user_is_index_based,
        'interaction_item_is_index_based': interaction_item_is_index_based
    }

def create_mappings(interaction_data, vector_data):
    """모델 학습을 위한 사용자 및 아이템 매핑 생성"""
    interactions = interaction_data['interactions']
    index_to_model_idx = vector_data['index_to_model_idx']
    
    # 사용자 매핑 생성
    if interaction_data['user_is_index_based']:
        user_id_to_idx = {}
        max_user_idx = -1
        
        for user_id in interactions.keys():
            user_idx = int(user_id)
            user_id_to_idx[user_id] = user_idx
            max_user_idx = max(max_user_idx, user_idx)
        
        n_users = max_user_idx + 1
    else:
        user_ids = sorted(set(interactions.keys()))
        user_id_to_idx = {uid: idx for idx, uid in enumerate(user_ids)}
        n_users = len(user_ids)
    
    # 아이템 매핑 생성 (interaction item_id -> MongoDB index -> model_idx)
    item_id_to_model_idx = {}
    matched_items = 0
    missing_items = 0
    
    # 정상적인 딕셔너리 구조 처리 {user_id: [item_id1, item_id2, ...]}
    for user_id, item_list in interactions.items():
        for item_id in item_list:
            if item_id not in item_id_to_model_idx:
                # item_id를 MongoDB index로 변환
                if interaction_data['interaction_item_is_index_based']:
                    mongodb_index = int(item_id)
                else:
                    # 문자열 ID의 경우 추가 매핑 로직 필요
                    try:
                        mongodb_index = int(item_id)
                    except:
                        missing_items += 1
                        continue
                
                # MongoDB index를 모델 인덱스로 변환
                if mongodb_index in index_to_model_idx:
                    model_idx = index_to_model_idx[mongodb_index]
                    item_id_to_model_idx[item_id] = model_idx
                    matched_items += 1
                else:
                    missing_items += 1
    
    print(f"매핑 생성 완료: {n_users}명 사용자, {matched_items}개 아이템 매칭")
    
    return {
        'user_id_to_idx': user_id_to_idx,
        'item_id_to_model_idx': item_id_to_model_idx,
        'n_users': n_users,
        'n_items': vector_data['n_items']
    }

def load_data():
    """
    전체 데이터 로딩 파이프라인
    
    Returns:
        dict: 상호작용, 벡터, 매핑, 데이터셋 크기를 포함하는 딕셔너리
    """
    # 1. 몽고DB 벡터 데이터 로딩
    vector_data = load_vector_data()
    
    # 2. 상호작용 데이터 분석
    interaction_data = analyze_interaction_data()
    
    # 3. 매핑 생성
    mapping_data = create_mappings(interaction_data, vector_data)
    
    return {
        'interactions': interaction_data['interactions'],
        'vectors': vector_data['vectors'],
        'user_id_to_idx': mapping_data['user_id_to_idx'],
        'item_id_to_model_idx': mapping_data['item_id_to_model_idx'],
        'n_users': mapping_data['n_users'],
        'n_items': mapping_data['n_items']
    }

def create_dataloaders(data, config):
    """70:20:10 분할로 학습/검증/테스트 데이터로더 생성"""
    # 학습/검증/테스트 분할 (70:20:10)
    interactions = data['interactions']
    train_interactions = {}
    val_interactions = {}
    test_interactions = {}
    
    total_interactions = 0
    train_interactions_count = 0
    val_interactions_count = 0
    test_interactions_count = 0
    
    for user_id, items in interactions.items():
        total_interactions += len(items)
        
        # 70:20:10 분할
        n_train = int(len(items) * 0.7)
        n_val = int(len(items) * 0.2)
        
        train_interactions[user_id] = items[:n_train]
        val_interactions[user_id] = items[n_train:n_train+n_val]
        test_interactions[user_id] = items[n_train+n_val:]
        
        train_interactions_count += len(train_interactions[user_id])
        val_interactions_count += len(val_interactions[user_id])
        test_interactions_count += len(test_interactions[user_id])
    
    # 데이터셋 생성
    train_dataset = NCFDataset(train_interactions, data['user_id_to_idx'], data['item_id_to_model_idx'])
    val_dataset = NCFDataset(val_interactions, data['user_id_to_idx'], data['item_id_to_model_idx'], negative_sampling=False)
    test_dataset = NCFDataset(test_interactions, data['user_id_to_idx'], data['item_id_to_model_idx'], negative_sampling=False)
    
    print(f"데이터 분할 완료: 학습 {len(train_dataset):,}, 검증 {len(val_dataset):,}, 테스트 {len(test_dataset):,}")
    
    # 데이터로더 생성
    train_loader = DataLoader(train_dataset, batch_size=config['batch_size'], 
                             shuffle=True, num_workers=config['num_workers'])
    val_loader = DataLoader(val_dataset, batch_size=config['batch_size'], 
                           shuffle=False, num_workers=config['num_workers'])
    test_loader = DataLoader(test_dataset, batch_size=config['batch_size'], 
                            shuffle=False, num_workers=config['num_workers'])
    
    return {
        'train_loader': train_loader,
        'val_loader': val_loader, 
        'test_loader': test_loader,
        'train_interactions': train_interactions,
        'val_interactions': val_interactions,
        'test_interactions': test_interactions
    }

def load_pretrained_vectors(model, vectors):
    """
    모델 임베딩에 사전학습 벡터 로드
    
    Args:
        model: NCF 모델
        vectors: 사전학습 벡터 리스트
    """
    # 벡터가 이미 올바른 순서로 정렬되어 있음
    vectors_tensor = torch.FloatTensor(vectors)
    
    # 모델 임베딩 크기와 맞는지 확인
    expected_size = model.item_vector_full.num_embeddings
    actual_size = vectors_tensor.size(0)
    
    if expected_size != actual_size:
        print(f"크기 불일치: 모델={expected_size}, 벡터={actual_size}")
        # 크기 조정 (필요시)
        if actual_size < expected_size:
            # 부족한 부분은 랜덤 벡터로 채움
            additional_vectors = torch.randn(expected_size - actual_size, 264) * 0.1
            vectors_tensor = torch.cat([vectors_tensor, additional_vectors], dim=0)
        else:
            # 초과하는 부분은 자름
            vectors_tensor = vectors_tensor[:expected_size]
    
    # 모델에 로드
    model.item_vector_full.weight.data.copy_(vectors_tensor)
    # Fine-tuning 허용 (낮은 LR로 업데이트)
    model.item_vector_full.weight.requires_grad = True
    
    print(f"사전학습 벡터 로딩 완료: {vectors_tensor.size(0)}개")

def analyze_data_sparsity(interactions, n_users, n_items):
    """
    데이터 희소성 메트릭 분석
    
    Args:
        interactions (dict): 사용자-아이템 상호작용
        n_users (int): 전체 사용자 수
        n_items (int): 전체 아이템 수
        
    Returns:
        dict: 희소성 분석 결과
    """
    total_possible_interactions = n_users * n_items
    actual_interactions = sum(len(items) for items in interactions.values())
    sparsity = (1 - actual_interactions / total_possible_interactions) * 100
    
    print(f"데이터 희소성: {sparsity:.2f}% (사용자 {n_users:,}명, 아이템 {n_items:,}개)")
    
    return {
        'sparsity': sparsity,
        'density': 100-sparsity,
        'total_interactions': actual_interactions,
        'avg_per_user': actual_interactions / len(interactions)
    } 