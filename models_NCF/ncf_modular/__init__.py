# ncf_modular 패키지
"""
NCF Modular - 모듈화된 신경 협업 필터링 패키지

주요 구성요소:
- config: 설정 및 시드 함수
- models: SymmetricResidualCategoryNCF 모델
- data_utils: 데이터 로딩 및 전처리
- evaluation: 학습 및 평가 함수
- utils: 유틸리티 함수
- main: 메인 실행 함수
"""

from .config import CONFIG, seed_everything
from .models import SymmetricResidualCategoryNCF
from .data_utils import (
    NCFDataset, 
    load_data, 
    create_dataloaders, 
    load_pretrained_vectors,
    analyze_data_sparsity
)
from .evaluation import (
    train_epoch, 
    validate_epoch, 
    evaluate_comprehensive
)
from .utils import save_checkpoint, visualize_training_extended
from .main import main

__version__ = "1.0.0"
__author__ = "NCF Team"

__all__ = [
    'CONFIG',
    'seed_everything', 
    'SymmetricResidualCategoryNCF',
    'NCFDataset',
    'load_data',
    'create_dataloaders',
    'load_pretrained_vectors',
    'analyze_data_sparsity',
    'train_epoch',
    'validate_epoch', 
    'evaluate_comprehensive',
    'save_checkpoint',
    'visualize_training_extended',
    'main'
] 