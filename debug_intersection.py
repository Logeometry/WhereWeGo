#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append('.')

from routeres.survey_router import get_intersection_based_recommendations, load_tourism_data, get_category_rules

def test_intersection():
    print("🔍 교집합 기반 추천 디버깅 테스트")
    print("=" * 50)
    
    # 테스트 데이터: 자연풍경, 높음, 오전, 여름, 활동성
    user_schema = [12345, '자연풍경', 0, 0, 1, 0]
    print(f"사용자 스키마: {user_schema}")
    print(f"  - 카테고리: 자연풍경")
    print(f"  - 활동성: 높음 (0)")
    print(f"  - 시간대: 오전 (0)")
    print(f"  - 계절: 여름 (1)")
    print(f"  - 선호도: 활동성 (0)")
    print()
    
    # 관광지 데이터 로드
    print("📊 관광지 데이터 로드 중...")
    tourism_data = load_tourism_data()
    if not tourism_data:
        print("❌ 관광지 데이터 로드 실패")
        return
    
    print("✅ 관광지 데이터 로드 성공")
    
    # 자연풍경 카테고리 아이템들 찾기
    natural_items = []
    for group in tourism_data.get('groups', []):
        if group.get('category_group') == '자연풍경':
            natural_items.extend(group.get('items', []))
    
    print(f"📋 자연풍경 카테고리 아이템 수: {len(natural_items)}")
    print("처음 10개 아이템:")
    for i, item in enumerate(natural_items[:10]):
        print(f"  {i+1:2d}. {item.get('name', 'Unknown')} - {item.get('category', 'Unknown')}")
    print()
    
    # 교집합 기반 추천 테스트
    print("🎯 교집합 기반 추천 테스트 시작...")
    print("-" * 30)
    
    filtered = get_intersection_based_recommendations(natural_items, user_schema)
    
    print("-" * 30)
    print(f"✅ 필터링 완료: {len(filtered)}개 아이템")
    print("필터링된 아이템들:")
    for i, item in enumerate(filtered[:10]):
        matched_keywords = item.get('matched_keywords', [])
        print(f"  {i+1:2d}. {item.get('name', 'Unknown')} - {item.get('category', 'Unknown')} - 키워드: {matched_keywords}")
    
    if len(filtered) == 0:
        print("⚠️ 필터링된 아이템이 없습니다!")
        print("원본 아이템들이 반환되었을 가능성이 있습니다.")
    
    print()
    print("🔍 카테고리 규칙 확인:")
    rules = get_category_rules()
    natural_rules = rules.get('자연풍경', {})
    print(f"자연풍경 규칙: {natural_rules}")
    
    if 'activity_rules' in natural_rules:
        high_activity = natural_rules['activity_rules'].get('high', [])
        print(f"높음 활동성 키워드: {high_activity}")

if __name__ == "__main__":
    test_intersection()
