# 가상환경 및 의존성 설치 가이드

## 빠른 시작

### 1. 기본 환경 요구사항
- **Python**: 3.8 이상 (3.9+ 권장)
- **CUDA**: PyTorch GPU 사용 시 (선택사항)
- **MongoDB**: 로컬 또는 Atlas 클라우드

### 2. 가상환경 생성 (권장)
```bash
# conda 사용
conda create -n wherewego python=3.9
conda activate wherewego

# 또는 venv 사용
python -m venv wherewego
# Windows
wherewego\Scripts\activate
# Linux/Mac
source wherewego/bin/activate
```

### 3. 의존성 설치

#### 기본 설치 (CPU 버전)
```bash
pip install -r requirements.txt
```

#### GPU 지원 설치 (CUDA 사용 시)
```bash
# CUDA 11.8 기준
pip install torch>=2.1.0+cu118 torchvision>=0.16.0+cu118 --index-url https://download.pytorch.org/whl/cu118
pip install -r requirements.txt
```

#### 개발 환경 설치 (모든 의존성)
```bash
# 주석 처리된 선택적 의존성도 모두 설치
pip install -r requirements.txt
pip install Pillow opencv-python efficientnet-pytorch imagehash
pip install selenium webdriver-manager
pip install plotly networkx
```

## 환경 설정

### 1. MongoDB 설정

#### 로컬 MongoDB
```bash
# MongoDB 설치 및 실행
# Windows (chocolatey)
choco install mongodb

# macOS (homebrew)
brew install mongodb-community

# Ubuntu
sudo apt install mongodb
```

#### MongoDB Atlas (클라우드)
1. [MongoDB Atlas](https://www.mongodb.com/atlas) 계정 생성
2. 클러스터 생성
3. 연결 문자열 복사

### 2. 환경 변수 설정
```bash
# .env 파일 생성
cp .env.example .env

# .env 파일 편집
MONGO_ATLAS_URL=mongodb+srv://username:password@cluster.mongodb.net/tourism_recommendation
MONGO_DB=tourism_recommendation
```

### 3. 설치 확인
```bash
# PyTorch GPU 확인
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"

# MongoDB 연결 확인
python utils/dbconfig.py

# 전체 환경 확인
python -c "
import torch, numpy, pandas, sklearn, matplotlib
print('모든 라이브러리 정상 설치됨')
"
```

## 패키지별 용도

### 핵심 머신러닝
- **torch**: 딥러닝 프레임워크 (NCF 모델)
- **scikit-learn**: 전통적 ML 알고리즘 (평가 메트릭)
- **numpy**: 수치 연산

### 데이터 처리
- **pandas**: 데이터 조작 및 분석
- **matplotlib/seaborn**: 시각화

### 데이터베이스
- **pymongo**: MongoDB 연결
- **python-dotenv**: 환경 변수 관리

### 유틸리티
- **tqdm**: 진행률 표시
- **requests**: HTTP 요청
- **geopy**: 지리 정보 처리

## 문제 해결

### PyTorch 설치 오류
```bash
# 기존 PyTorch 제거 후 재설치
pip uninstall torch torchvision
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
```

### MongoDB 연결 오류
```bash
# 연결 테스트
python utils/dbconfig.py

# 방화벽 확인 (Atlas 사용 시)
# IP 화이트리스트에 현재 IP 추가
```

### 메모리 부족 오류
```bash
# 배치 크기 줄이기
# config.py에서 batch_size 값 감소
```

## 버전 호환성

| 라이브러리 | 최소 버전 | 권장 버전 | 비고 |
|-----------|----------|----------|------|
| Python | 3.8 | 3.9+ | 타입 힌트 지원 |
| PyTorch | 2.0 | 2.1+ | 최신 기능 활용 |
| NumPy | 1.20 | 1.24+ | 성능 개선 |
| MongoDB | 4.4 | 6.0+ | Atlas 호환성 |

## 다음 단계
설치가 완료되면 [README.md](README.md)의 실행 방법을 참고하여 프로젝트를 시작하세요! 
