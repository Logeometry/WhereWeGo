# WhereWeGo - 여행지 추천 시스템

## 프로젝트 개요
WhereWeGo는 사용자의 선호도를 학습하여 개인화된 여행지를 추천하는 시스템입니다. 
BPR(Bayesian Personalized Ranking) 사전학습과 NCF(Neural Collaborative Filtering)를 결합한 하이브리드 접근법을 사용합니다.

## 시스템 아키텍처

### 1. 데이터 파이프라인 (`data_pipeline/`)
- **`triplet123.py`**: BPR 학습용 triplet 데이터셋 생성
- **`improved_triplets.py`**: NCF 학습용 고품질 데이터셋 생성  
- **`please.json`**: BPR 학습용 JSON 데이터

### 2. 모델 구현 (`models/`)
- **`create_vector_use_bpr.py`**: BPR 사전학습 모델
- **`ncf_modular/`**: 모듈화된 NCF 시스템
  - `models.py`: SymmetricResidualCategoryNCF 모델
  - `data_utils.py`: 데이터 로딩 및 전처리
  - `evaluation.py`: 모델 평가 메트릭
  - `config.py`: 하이퍼파라미터 설정
- **`run_ncf_modular.py`**: NCF 모델 실행 스크립트

### 3. 유틸리티 (`utils/`)
- **`visualization.py`**: 임베딩 시각화
- **`new_database_task/`**: 데이터베이스 구축 작업
- **`dbconfig.py`**: 데이터베이스 설정

## 실행 방법

### 1. 환경 설정
```bash
pip install -r requirements.txt
```

### 2. 데이터 준비
```bash
# BPR용 데이터 생성
python data_pipeline/triplet123.py

# NCF용 데이터 생성  
python data_pipeline/improved_triplets.py
```

### 3. 모델 학습
```bash
# BPR 사전학습
python models/create_vector_use_bpr.py

# NCF 학습
python models/run_ncf_modular.py
```

## 모델 성능
- **평가 메트릭**: HR@K, Recall@K, NDCG@K, MAP, AUC
- **데이터셋**: 실제 여행지 데이터 기반
- **사전학습 효과**: BPR 임베딩을 통한 성능 향상

## 기술 스택
- **Framework**: PyTorch
- **Database**: MongoDB
- **Visualization**: Matplotlib, t-SNE
- **Evaluation**: scikit-learn

## 프로젝트 구조
```
database/
├── data_pipeline/          # 데이터 생성 및 전처리
├── models/                 # 모델 구현 및 학습
│   └── ncf_modular/       # 모듈화된 NCF 시스템
├── utils/                  # 유틸리티 및 도구
└── docs/                   # 문서
```

## 개발팀
- 추천 시스템 연구팀

## 라이선스
MIT License
