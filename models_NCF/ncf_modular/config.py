# config.py
# 설정 파일

import torch
import random
import numpy as np

def seed_everything(seed=42):
    """재현성을 위한 랜덤 시드 고정"""
    random.seed(seed)
    np.random.seed(seed) 
    torch.manual_seed(seed)
    torch.cuda.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False

# 설정 - 최적화된 성능 파라미터
CONFIG = {
    'user_dim': 128,              
    'item_dim': 128,             
    'category_dim': 8,
    'branch_dim': 256,
    'projection_dim': 128,       
    'learning_rate': 8e-5,       
    'item_lr': 2e-5,              # 사전학습 아이템 벡터용 낮은 학습률
    'batch_size': 512,
    'epochs': 200,
    'weight_decay': 5e-5,
    'train_ratio': 0.8,
    'negative_ratio': 2,          
    'eval_k': [5, 10, 20],
    'eval_every': 5,
    'patience': 4,                
    'device': 'cuda' if torch.cuda.is_available() else 'cpu',
    'num_workers': 2,
    'save_dir': './checkpoints/',
    'seed': 42,
    
    # 데이터 파일 경로 설정
    'data_dir': './data/',
    'vector_file': 'exported_vector_full.json',
    'interaction_file': 'improved_implicit.json'
} 