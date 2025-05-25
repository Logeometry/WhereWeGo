#!/usr/bin/env python3
# setup_data.py
# 데이터 파일 정리 스크립트

import os
import shutil

def setup_data_directory():
    """데이터 파일들을 data 폴더로 정리"""
    
    # data 폴더 생성
    data_dir = './data'
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        print(f"{data_dir} 폴더 생성 완료")
    else:
        print(f"{data_dir} 폴더가 이미 존재합니다")
    
    # 이동할 파일들 정의
    files_to_move = [
        'exported_vector_full.json',
        'improved_implicit.json'
    ]
    
    moved_files = []
    missing_files = []
    
    for filename in files_to_move:
        source_path = filename
        target_path = os.path.join(data_dir, filename)
        
        if os.path.exists(source_path):
            if not os.path.exists(target_path):
                shutil.move(source_path, target_path)
                moved_files.append(filename)
                print(f"{filename} → {target_path}")
            else:
                print(f"{filename}이 이미 data 폴더에 있습니다")
        else:
            missing_files.append(filename)
            print(f"{filename}을 찾을 수 없습니다")
    
    # 결과 요약
    print("\n" + "="*50)
    print("데이터 파일 정리 결과")
    print("="*50)
    
    if moved_files:
        print(f"이동 완료: {len(moved_files)}개 파일")
        for f in moved_files:
            print(f"   - {f}")
    
    if missing_files:
        print(f"누락된 파일: {len(missing_files)}개")
        for f in missing_files:
            print(f"   - {f}")
        print("\n누락된 파일들을 data 폴더에 직접 복사해주세요.")
    
    # 최종 data 폴더 내용 확인
    if os.path.exists(data_dir):
        data_files = os.listdir(data_dir)
        print(f"\ndata 폴더 내용 ({len(data_files)}개 파일):")
        for f in sorted(data_files):
            file_path = os.path.join(data_dir, f)
            file_size = os.path.getsize(file_path) / (1024*1024)  # MB
            print(f"   - {f} ({file_size:.1f} MB)")

if __name__ == "__main__":
    print("NCF Modular 데이터 파일 정리 시작")
    print("="*50)
    setup_data_directory()
    print("\n설정 완료! 이제 python run_ncf_modular.py를 실행하세요.") 