#!/usr/bin/env python3
# run_ncf_modular.py
# NCF 모듈화 버전 실행 스크립트

import sys
import os
import argparse

# 현재 디렉토리를 Python 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# ncf_modular 패키지에서 main 함수 import
try:
    from ncf_modular import main, CONFIG
except ImportError as e:
    print(f"Import 오류: {e}")
    print("ncf_modular 패키지를 찾을 수 없습니다. 현재 디렉토리를 확인해주세요.")
    sys.exit(1)

if __name__ == "__main__":
    # 명령행 인수 처리
    parser = argparse.ArgumentParser(description="NCF Modular 학습 실행")
    parser.add_argument('--epochs', type=int, default=None, help='학습 에폭 수')
    parser.add_argument('--batch_size', type=int, default=None, help='배치 크기')
    parser.add_argument('--lr', type=float, default=None, help='학습률')
    args = parser.parse_args()
    
    # 설정 업데이트 (None이 아닌 경우만)
    if args.epochs is not None:
        CONFIG['epochs'] = args.epochs
        print(f"에폭 수 설정: {args.epochs}")
    if args.batch_size is not None:
        CONFIG['batch_size'] = args.batch_size
        print(f"배치 크기 설정: {args.batch_size}")
    if args.lr is not None:
        CONFIG['learning_rate'] = args.lr
        print(f"학습률 설정: {args.lr}")
    
    # 메인 함수 실행
    main() 