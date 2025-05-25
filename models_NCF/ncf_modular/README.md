# NCF Modular - 모듈화된 신경 협업 필터링

## 개요
Practical Residual NCF v5의 모듈화된 버전입니다. 코드의 가독성, 유지보수성, 재사용성을 향상시키기 위해 기능별로 모듈을 분리했습니다.

## 프로젝트 구조
```
WhereWeGo/
├── ncf_modular/                 # NCF 패키지
│   ├── __init__.py             # 패키지 초기화
│   ├── config.py               # 설정 및 시드 함수
│   ├── models.py               # SymmetricResidualCategoryNCF 모델 클래스
│   ├── data_utils.py           # 데이터 로딩, 전처리, 데이터셋 클래스
│   ├── evaluation.py           # 학습, 검증, 평가 함수들
│   ├── utils.py                # 체크포인트 저장, 시각화 유틸리티
│   ├── main.py                 # 메인 학습 스크립트
│   └── README.md               # 이 파일
├── data/                       # 데이터 파일들
│   ├── exported_vector_full.json    # MongoDB 벡터 데이터
│   └── improved_implicit.json       # 사용자-아이템 상호작용 데이터
├── checkpoints/                # 모델 체크포인트 저장소
├── run_ncf_modular.py          # 실행 진입점
└── setup_data.py               # 데이터 파일 정리 스크립트
```

## 설정 및 실행

### 1. 데이터 파일 정리 (최초 1회)
```bash
python setup_data.py
```
이 스크립트는:
- `data/` 폴더를 생성합니다
- `exported_vector_full.json`과 `improved_implicit.json`을 `data/` 폴더로 이동시킵니다
- 파일 위치를 자동으로 확인합니다

### 2. 모델 학습 실행
```bash
# 기본 실행
python run_ncf_modular.py

# 하이퍼파라미터 조정
python run_ncf_modular.py --epochs 100 --batch_size 256 --lr 1e-4

# 도움말 보기
python run_ncf_modular.py --help
```

## 모듈 설명

### config.py
- `CONFIG`: 모든 하이퍼파라미터 설정
- `seed_everything()`: 재현성을 위한 랜덤 시드 고정
- **새로 추가**: 데이터 파일 경로 설정

### models.py
- `SymmetricResidualCategoryNCF`: 메인 모델 클래스
  - GMF + MLP 하이브리드 구조
  - Projection layer를 통한 사전학습 벡터 활용
  - 카테고리 정보 융합

### data_utils.py
- `NCFDataset`: PyTorch 데이터셋 클래스
- `get_data_file_path()`: **새로 추가** - 유연한 파일 경로 탐색
- `load_vector_data()`: MongoDB 벡터 데이터 로딩
- `analyze_interaction_data()`: 상호작용 데이터 분석
- `create_mappings()`: 사용자/아이템 매핑 생성
- `load_data()`: 전체 데이터 로딩 파이프라인
- `create_dataloaders()`: 학습/검증/테스트 데이터로더 생성
- `load_pretrained_vectors()`: 사전학습 벡터 모델 로딩
- `analyze_data_sparsity()`: 데이터 희소성 분석

### evaluation.py
- `train_epoch()`: 한 에폭 학습
- `validate_epoch()`: 검증 손실 계산
- `evaluate_comprehensive()`: 종합 평가 (HR, Recall, NDCG, MAP, AUC)
- `calculate_ndcg()`: NDCG 메트릭 계산
- `calculate_map()`: MAP 메트릭 계산

### utils.py
- `save_checkpoint()`: 모델 체크포인트 저장
- `visualize_training_extended()`: 10개 서브플롯 학습 시각화

### main.py
- `main()`: 전체 학습 파이프라인 실행
- 모든 모듈을 import하여 통합 실행

## 데이터 파일 관리

### 자동 파일 탐색
시스템이 다음 순서로 데이터 파일을 찾습니다:
1. `./data/` 폴더 (권장)
2. 현재 디렉토리
3. 상위 디렉토리

### 수동 설정
`ncf_modular/config.py`에서 경로를 직접 수정할 수 있습니다:
```python
CONFIG = {
    # ...
    'data_dir': './your_custom_data_path/',
    'vector_file': 'your_vector_file.json',
    'interaction_file': 'your_interaction_file.json'
}
```

## 장점

### 1. 가독성 향상
- 기능별로 모듈이 분리되어 코드 이해가 쉬움
- 각 모듈의 역할이 명확함

### 2. 유지보수성
- 특정 기능 수정시 해당 모듈만 수정하면 됨
- 버그 추적과 디버깅이 용이함

### 3. 재사용성
- 개별 모듈을 다른 프로젝트에서 재사용 가능
- 모델, 데이터 처리, 평가 함수 등을 독립적으로 사용

### 4. 협업 효율성
- 여러 개발자가 동시에 다른 모듈 작업 가능
- 코드 충돌 최소화

### 5. 테스트 용이성
- 각 모듈을 독립적으로 테스트 가능
- 단위 테스트 작성이 쉬움

### 6. 데이터 관리 개선
- 데이터 파일들이 별도 폴더로 정리됨
- 유연한 파일 경로 탐색으로 다양한 환경 지원

## 의존성
- torch
- numpy
- matplotlib
- tqdm
- sklearn (AUC 계산용)

## 출력
- 체크포인트: `./checkpoints/best_model_v5_modular.pth`
- 시각화: `./checkpoints/training_results_modular_YYYYMMDD_HHMMSS.png`

## 문제 해결

### 데이터 파일을 찾을 수 없는 경우
1. `python setup_data.py` 실행
2. 수동으로 파일을 `data/` 폴더에 복사
3. `config.py`에서 경로 확인

### Import 오류가 발생하는 경우
- `run_ncf_modular.py`를 루트 디렉토리에서 실행하세요
- `ncf_modular` 폴더가 올바른 위치에 있는지 확인하세요 