# ncf_modular 패키지
"""
NCF Modular - 모듈화된 신경 협업 필터링 패키지 (활동성 레벨 지원)

주요 구성요소:
- config: 설정 및 시드 함수, 카테고리 규칙 정의
- models: SymmetricResidualCategoryNCF 모델 (활동성 레벨 지원)
- data_utils: 데이터 로딩 및 전처리 (새로운 triplet 구조 지원)
- evaluation: 학습 및 평가 함수 (활동성 레벨 지원)
- utils: 유틸리티 함수
- main: 메인 실행 함수

새로운 triplet 구조: [user_id, category_group, activity_level, pos_item_index, neg_item_index]
"""

from .config import CONFIG, seed_everything, CATEGORY_RULES
from .models import SymmetricResidualCategoryNCF
from .data_utils import (
    NCFDataset,
    load_data,
    create_dataloaders,
    analyze_data_sparsity,
    analyze_triplet_data
)
from .evaluation import (
    train_epoch,
    validate_epoch,
    evaluate_comprehensive
)
from .utils import save_checkpoint, visualize_training_extended
from .main import main

__version__ = "2.0.0"
__author__ = "NCF Team"

__all__ = [
    'CONFIG',
    'CATEGORY_RULES',
    'seed_everything',
    'SymmetricResidualCategoryNCF',
    'NCFDataset',
    'load_data',
    'create_dataloaders',
    'analyze_data_sparsity',
    'analyze_triplet_data',
    'train_epoch',
    'validate_epoch', 
    'evaluate_comprehensive',
    'save_checkpoint',
    'visualize_training_extended',
    'main'
] 
