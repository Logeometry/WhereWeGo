#!/usr/bin/env python3
# run_ncf_modular.py
# NCF 모듈화 버전 실행 스크립트 - 계절별 필터링 지원

import sys
import os
import argparse

# 현재 디렉토리를 Python 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# ncf_inner 패키지에서 모든 핵심 모듈 import
try:
    from ncf_inner import (
        main,
        CONFIG, CATEGORY_RULES, TIME_RULES, SEASON_RULES, PREFERENCE_RULES,
        seed_everything,
        SymmetricResidualCategoryNCF,
        load_data, create_dataloaders, analyze_data_sparsity,
        train_epoch, validate_epoch, evaluate_comprehensive,
        recommend_with_preference_filtering, analyze_preference_based_recommendations, generate_preference_based_recommendations,
        save_checkpoint, visualize_training_extended
    )
except ImportError as e:
    print(f"Import 오류: {e}")
    print("ncf_inner 패키지를 찾을 수 없습니다. 현재 디렉토리를 확인해주세요.")
    sys.exit(1)

def print_season_rules():
    """계절별 필터링 규칙 출력"""
    print("\n=== 계절별 필터링 규칙 ===")
    for season, category_rules in SEASON_RULES.items():
        print(f"\n{season}:")
        for category, items in category_rules.items():
            print(f"  {category}: {items}")

def print_category_rules():
    """카테고리 규칙 및 시간대별, 계절별 규칙 출력"""
    print("\n=== 카테고리별 추천 규칙 ===")
    for category, rules in CATEGORY_RULES.items():
        print(f"\n{category}:")
        print(f"  카테고리 목록: {rules['categories']}")
        if 'exclude' in rules:
            print(f"  제외 대상: {rules['exclude']}")
        print(f"  활동성 규칙:")
        for activity, categories in rules['activity_rules'].items():
            activity_name = {0: "높음", 1: "중간", 2: "낮음"}[activity]
            print(f"    {activity_name}: {categories}")
        print(f"  시간대별 규칙:")
        for time_period, categories in rules['time_rules'].items():
            time_name = {0: "아침", 1: "오후", 2: "저녁"}[time_period]
            print(f"    {time_name}: {categories}")
        if 'season_rules' in rules:
            print(f"  계절별 규칙:")
            for season, categories in rules['season_rules'].items():
                season_name = {0: "봄", 1: "여름", 2: "가을", 3: "겨울"}[season]
                print(f"    {season_name}: {categories}")
        print(f"  상호작용 방식: {rules['interaction_ratio']['popular']*100}% 인기순, {rules['interaction_ratio']['random']*100}% 무작위")

def print_time_rules():
    """시간대별 필터링 규칙 출력"""
    print("\n=== 시간대별 필터링 규칙 ===")
    for time_period, category_rules in TIME_RULES.items():
        print(f"\n{time_period}:")
        for category, items in category_rules.items():
            print(f"  {category}: {items}")

def print_preference_rules():
    """선호도별 필터링 규칙 출력"""
    print("\n=== 선호도별 필터링 규칙 ===")
    for preference_type, rules in PREFERENCE_RULES.items():
        print(f"\n{preference_type}:")
        print(f"  설명: {rules['description']}")
        for activity_level, category_rules in rules.items():
            if activity_level != 'description':
                print(f"  {activity_level}:")
                for category, items in category_rules.items():
                    print(f"    {category}: {items}")

def print_training_info():
    """학습 정보 출력"""
    print("\n=== 계절별 필터링 학습 시스템 정보 ===")
    print(f"📊 데이터 파일: {CONFIG['interaction_file']}")
    print(f"🎯 Triplet 구조: [user_id, category_group, activity_level, time_period, season, preference, pos_item_index, neg_item_index]")
    print(f"⏰ 시간대: 0(아침), 1(오후), 2(저녁)")
    print(f"🌱 계절: 0(봄), 1(여름), 2(가을), 3(겨울)")
    print(f"🎭 선호도: 0(활동성), 1(시간대)")
    print(f"📈 학습 파라미터:")
    print(f"   - 에폭 수: {CONFIG['epochs']}")
    print(f"   - 배치 크기: {CONFIG['batch_size']}")
    print(f"   - 학습률: {CONFIG['learning_rate']}")
    print(f"   - 아이템 학습률: {CONFIG['item_lr']}")
    print(f"   - 디바이스: {CONFIG['device']}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="NCF Modular 학습 실행 (시간대/계절/선호도 필터링 지원)")
    parser.add_argument('--epochs', type=int, default=None, help='학습 에폭 수')
    parser.add_argument('--batch_size', type=int, default=None, help='배치 크기')
    parser.add_argument('--lr', type=float, default=None, help='학습률')
    parser.add_argument('--show_rules', action='store_true', help='카테고리 규칙 출력')
    parser.add_argument('--show_time_rules', action='store_true', help='시간대별 규칙 출력')
    parser.add_argument('--show_preference_rules', action='store_true', help='선호도별 규칙 출력')
    parser.add_argument('--show_season_rules', action='store_true', help='계절별 규칙 출력')
    parser.add_argument('--show_info', action='store_true', help='학습 시스템 정보 출력')
    args = parser.parse_args()

    # 규칙 출력 옵션
    if args.show_rules:
        print_category_rules()
        sys.exit(0)
    if args.show_time_rules:
        print_time_rules()
        sys.exit(0)
    if args.show_preference_rules:
        print_preference_rules()
        sys.exit(0)
    if args.show_season_rules:
        print_season_rules()
        sys.exit(0)
    if args.show_info:
        print_training_info()
        sys.exit(0)

    # CONFIG 업데이트
    if args.epochs is not None:
        CONFIG['epochs'] = args.epochs
        print(f"에폭 수 설정: {args.epochs}")
    if args.batch_size is not None:
        CONFIG['batch_size'] = args.batch_size
        print(f"배치 크기 설정: {args.batch_size}")
    if args.lr is not None:
        CONFIG['learning_rate'] = args.lr
        print(f"학습률 설정: {args.lr}")

    print(f"\n[INFO] 계절별 필터링 지원 NCF 학습 시작")
    print(f"[INFO] 데이터 파일: {CONFIG['interaction_file']}")
    print(f"[INFO] triplet 구조: [user_id, category_group, activity_level, time_period, season, preference, pos_item_index, neg_item_index]")
    print(f"[INFO] 시간대: 0(아침), 1(오후), 2(저녁) | 계절: 0(봄), 1(여름), 2(가을), 3(겨울) | 선호도: 0(활동성), 1(시간대)")

    # 전체 파이프라인 실행 (학습)
    main()