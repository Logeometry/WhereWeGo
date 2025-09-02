# ncf_modular 패키지
"""
NCF Modular - 모듈화된 신경 협업 필터링 패키지 (시간대별, 계절별 필터링 및 선호도 지원)

주요 구성요소:
- config: 설정 및 시드 함수, 카테고리 규칙 정의, 시간대별 규칙, 계절별 규칙, 선호도 규칙
- models: SymmetricResidualCategoryNCF 모델 (시간대별, 계절별 필터링 및 선호도 지원)
- data_utils: 데이터 로딩 및 전처리 (시간대별, 계절별 및 선호도별 triplet 구조 지원)
- evaluation: 학습 및 평가 함수 (시간대별, 계절별 필터링 및 선호도 지원)
- utils: 유틸리티 함수
- main: 메인 실행 함수

새로운 triplet 구조: [user_id, category_group, activity_level, time_period, season, preference, pos_item_index, neg_item_index]
시간대별 필터링: 아침(0), 오후(1), 저녁(2)
계절별 필터링: 봄(0), 여름(1), 가을(2), 겨울(3)
선호도: 활동성 선호(0), 시간대 선호(1)

DataMaking.py와 완전 동기화됨:
- 모든 카테고리에 season_rules 추가
- 데이터 파일 경로 통일
- 계절별 필터링 로직 통합
"""

from .config import CONFIG, seed_everything, CATEGORY_RULES, TIME_RULES, SEASON_RULES, PREFERENCE_RULES
from .models import SymmetricResidualCategoryNCF
from .data_utils import (
    NCFDataset,
    load_data,
    create_dataloaders,
    analyze_data_sparsity,
    analyze_triplet_data,
    AdvancedFilteringUtils
)
from .evaluation import (
    train_epoch,
    validate_epoch,
    evaluate_comprehensive,
    recommend_with_preference_filtering,
    analyze_preference_based_recommendations,
    generate_preference_based_recommendations
)
from .utils import save_checkpoint, visualize_training_extended
from .main import main

__version__ = "4.0.0"
__author__ = "NCF Team"

__all__ = [
    'CONFIG',
    'CATEGORY_RULES',
    'TIME_RULES',
    'SEASON_RULES',
    'PREFERENCE_RULES',
    'seed_everything',
    'SymmetricResidualCategoryNCF',
    'NCFDataset',
    'load_data',
    'create_dataloaders',
    'analyze_data_sparsity',
    'analyze_triplet_data',
    'AdvancedFilteringUtils',
    'train_epoch',
    'validate_epoch',
    'evaluate_comprehensive',
    'recommend_with_preference_filtering',
    'analyze_preference_based_recommendations',
    'generate_preference_based_recommendations',
    'save_checkpoint',
    'visualize_training_extended',
    'main'
] 
