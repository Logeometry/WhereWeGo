# data_utils.py
# 데이터 처리 유틸리티 모듈

import torch
import json
import random
import numpy as np
import os
from torch.utils.data import Dataset, DataLoader
from datetime import datetime, timedelta
import math


class AdvancedFilteringUtils:
    """고급 필터링 유틸리티 클래스 - 선호도 및 계절 지원"""

    def __init__(self, config):
        self.config = config
        self.category_rules = config.get('category_rules', {})
        self.time_rules = config.get('time_rules', {})
        self.season_rules = config.get('season_rules', {})
        self.preference_rules = config.get('preference_rules', {})

    def get_time_period(self, hour):
        """시간대별 구분"""
        if 6 <= hour < 12:
            return "아침"
        elif 12 <= hour < 18:
            return "오후"
        else:
            return "저녁"

    def get_time_period_index(self, time_period):
        """시간대를 인덱스로 변환"""
        time_mapping = {
            "아침": 0,
            "오후": 1,
            "저녁": 2
        }
        return time_mapping.get(time_period, 0)

    def get_season_name(self, season_idx):
        """계절 인덱스를 이름으로 변환"""
        season_mapping = {
            0: "봄",
            1: "여름",
            2: "가을",
            3: "겨울"
        }
        return season_mapping.get(season_idx, "봄")

    def get_activity_level_name(self, activity_level):
        """활동성 레벨을 이름으로 변환"""
        activity_mapping = {
            0: "high_activity",
            1: "medium_activity",
            2: "low_activity"
        }
        return activity_mapping.get(activity_level, "medium_activity")

    def get_time_period_name(self, time_period):
        """시간대를 이름으로 변환"""
        time_mapping = {
            0: "morning",
            1: "afternoon",
            2: "evening"
        }
        return time_mapping.get(time_period, "afternoon")

    def filter_by_preference(self, items, user_preference, user_activity_level, user_time_period, user_season,
                             category_group):
        """선호도에 따른 필터링 (활동성 vs 시간대) - 계절 고려"""
        if user_preference == 0:  # 활동성 선호
            return self.filter_by_activity_preference(items, user_activity_level, category_group)
        else:  # 시간대 선호
            return self.filter_by_time_preference(items, user_time_period, user_season, category_group)

    def filter_by_activity_preference(self, items, user_activity_level, category_group):
        """활동성 선호 사용자를 위한 필터링"""
        activity_level_name = self.get_activity_level_name(user_activity_level)

        if 'activity_preference' not in self.preference_rules:
            return items

        activity_prefs = self.preference_rules['activity_preference'].get(activity_level_name, {})
        preferred_categories = activity_prefs.get(category_group, [])

        if not preferred_categories:
            return items

        # 선호 카테고리에 속하는 아이템만 필터링
        filtered_items = []
        for item in items:
            if hasattr(item, 'category') and item.category in preferred_categories:
                filtered_items.append(item)

        return filtered_items if filtered_items else items

    def filter_by_time_preference(self, items, user_time_period, user_season, category_group):
        """시간대별 선호도에 따른 필터링 - 계절 고려"""
        time_period_name = self.get_time_period_name(user_time_period)
        season_name = self.get_season_name(user_season)

        if 'time_preference' not in self.preference_rules:
            return items

        time_prefs = self.preference_rules['time_preference'].get(time_period_name, {})
        preferred_categories = time_prefs.get(category_group, [])

        # 계절별 필터링 추가 - CATEGORY_RULES에서 season_rules 사용
        if category_group in self.category_rules and 'season_rules' in self.category_rules[category_group]:
            season_categories = self.category_rules[category_group]['season_rules'].get(user_season, [])
        else:
            season_categories = self.season_rules.get(season_name, {}).get(category_group, [])

        if not preferred_categories:
            preferred_categories = season_categories

        if not preferred_categories:
            return items

        # 선호 카테고리에 속하는 아이템만 필터링
        filtered_items = []
        for item in items:
            if hasattr(item, 'category') and item.category in preferred_categories:
                filtered_items.append(item)

        return filtered_items if filtered_items else items


class NCFDataset(Dataset):
    """
    신경 협업 필터링 데이터셋 - 시간대별, 계절별 및 선호도별 필터링 지원

    새로운 구조: [user_id, category_group, activity_level, time_period, season, preference, pos_item_index, neg_item_index]
    기존 구조: [user_id, category_group, activity_level, time_period, pos_item_index, neg_item_index]

    Args:
        triplets (list): triplet 데이터 리스트
        user_id_to_idx (dict): 사용자 ID에서 인덱스로의 매핑
        item_id_to_model_idx (dict): 아이템 ID에서 모델 인덱스로의 매핑
        negative_sampling (bool): 부정 샘플 생성 여부 (기본값: False, triplet에 이미 포함됨)
    """

    def __init__(self, triplets, user_id_to_idx, item_id_to_model_idx, negative_sampling=False):
        self.user_id_to_idx = user_id_to_idx
        self.item_id_to_model_idx = item_id_to_model_idx
        self.samples = []

        # 새로운 triplet 구조 처리
        for triplet in triplets:
            if len(triplet) == 8:  # 최신 구조: [user_id, category_group, activity_level, time_period, season, preference, pos_item_index, neg_item_index]
                user_id, category_group, activity_level, time_period, season, preference, pos_item_index, neg_item_index = triplet

                # 유저와 아이템이 매핑에 있는지 확인
                if (str(user_id) in user_id_to_idx and
                        pos_item_index in item_id_to_model_idx and
                        neg_item_index in item_id_to_model_idx):
                    user_idx = user_id_to_idx[str(user_id)]
                    pos_model_idx = item_id_to_model_idx[pos_item_index]
                    neg_model_idx = item_id_to_model_idx[neg_item_index]

                    # 긍정 샘플
                    self.samples.append(
                        (user_idx, pos_model_idx, 1.0, category_group, activity_level, time_period, season, preference))
                    # 부정 샘플
                    self.samples.append(
                        (user_idx, neg_model_idx, 0.0, category_group, activity_level, time_period, season, preference))

            elif len(
                    triplet) == 7:  # 새로운 구조: [user_id, category_group, activity_level, time_period, preference, pos_item_index, neg_item_index]
                user_id, category_group, activity_level, time_period, preference, pos_item_index, neg_item_index = triplet

                if (str(user_id) in user_id_to_idx and
                        pos_item_index in item_id_to_model_idx and
                        neg_item_index in item_id_to_model_idx):
                    user_idx = user_id_to_idx[str(user_id)]
                    pos_model_idx = item_id_to_model_idx[pos_item_index]
                    neg_model_idx = item_id_to_model_idx[neg_item_index]

                    # 긍정 샘플 (기본 계절: 봄)
                    self.samples.append(
                        (user_idx, pos_model_idx, 1.0, category_group, activity_level, time_period, 0, preference))
                    # 부정 샘플
                    self.samples.append(
                        (user_idx, neg_model_idx, 0.0, category_group, activity_level, time_period, 0, preference))

            elif len(
                    triplet) == 6:  # 기존 구조: [user_id, category_group, activity_level, time_period, pos_item_index, neg_item_index]
                user_id, category_group, activity_level, time_period, pos_item_index, neg_item_index = triplet

                if (str(user_id) in user_id_to_idx and
                        pos_item_index in item_id_to_model_idx and
                        neg_item_index in item_id_to_model_idx):
                    user_idx = user_id_to_idx[str(user_id)]
                    pos_model_idx = item_id_to_model_idx[pos_item_index]
                    neg_model_idx = item_id_to_model_idx[neg_item_index]

                    # 긍정 샘플 (기본 선호도: 시간대 선호, 기본 계절: 봄)
                    self.samples.append(
                        (user_idx, pos_model_idx, 1.0, category_group, activity_level, time_period, 0, 1))
                    # 부정 샘플
                    self.samples.append(
                        (user_idx, neg_model_idx, 0.0, category_group, activity_level, time_period, 0, 1))

            elif len(triplet) == 5:  # 기존 구조: [user_id, category_group, activity_level, pos_item_index, neg_item_index]
                user_id, category_group, activity_level, pos_item_index, neg_item_index = triplet

                if (str(user_id) in user_id_to_idx and
                        pos_item_index in item_id_to_model_idx and
                        neg_item_index in item_id_to_model_idx):
                    user_idx = user_id_to_idx[str(user_id)]
                    pos_model_idx = item_id_to_model_idx[pos_item_index]
                    neg_model_idx = item_id_to_model_idx[neg_item_index]

                    # 긍정 샘플 (기본 시간대: 오후, 기본 선호도: 시간대 선호, 기본 계절: 봄)
                    self.samples.append((user_idx, pos_model_idx, 1.0, category_group, activity_level, 1, 0, 1))
                    # 부정 샘플
                    self.samples.append((user_idx, neg_model_idx, 0.0, category_group, activity_level, 1, 0, 1))

            elif len(triplet) == 3:  # 기존 구조: [user_id, pos_item_index, neg_item_index]
                user_id, pos_item_index, neg_item_index = triplet

                if (str(user_id) in user_id_to_idx and
                        pos_item_index in item_id_to_model_idx and
                        neg_item_index in item_id_to_model_idx):
                    user_idx = user_id_to_idx[str(user_id)]
                    pos_model_idx = item_id_to_model_idx[pos_item_index]
                    neg_model_idx = item_id_to_model_idx[neg_item_index]

                    # 긍정 샘플 (기본값)
                    self.samples.append((user_idx, pos_model_idx, 1.0, "unknown", 1, 1, 0, 1))
                    # 부정 샘플
                    self.samples.append((user_idx, neg_model_idx, 0.0, "unknown", 1, 1, 0, 1))

        random.shuffle(self.samples)

    def __getitem__(self, idx):
        return self.samples[idx]

    def __len__(self):
        return len(self.samples)


def convert_triplets_to_new_format(triplets):
    """기존 triplet 데이터를 새로운 8개 요소 구조로 변환"""
    converted_triplets = []

    for triplet in triplets:
        if len(triplet) == 8:  # 이미 최신 구조
            converted_triplets.append(triplet)
        elif len(triplet) == 7:  # 선호도 포함 구조
            user_id, category_group, activity_level, time_period, preference, pos_item_index, neg_item_index = triplet
            # 기본 계절: 봄 (0)
            season = 0
            converted_triplets.append(
                [user_id, category_group, activity_level, time_period, season, preference, pos_item_index,
                 neg_item_index])
        elif len(triplet) == 6:  # 시간대 포함 구조
            user_id, category_group, activity_level, time_period, pos_item_index, neg_item_index = triplet
            # 기본 선호도: 시간대 선호 (1), 기본 계절: 봄 (0)
            preference = 1
            season = 0
            converted_triplets.append(
                [user_id, category_group, activity_level, time_period, season, preference, pos_item_index,
                 neg_item_index])
        elif len(triplet) == 5:  # 기존 구조
            user_id, category_group, activity_level, pos_item_index, neg_item_index = triplet
            # 기본 시간대: 오후 (1), 기본 선호도: 시간대 선호 (1), 기본 계절: 봄 (0)
            time_period = 1
            preference = 1
            season = 0
            converted_triplets.append(
                [user_id, category_group, activity_level, time_period, season, preference, pos_item_index,
                 neg_item_index])
        elif len(triplet) == 3:  # 레거시 구조
            user_id, pos_item_index, neg_item_index = triplet
            # 기본값들
            category_group = "자연풍경"
            activity_level = 1
            time_period = 1
            season = 0
            preference = 1
            converted_triplets.append(
                [user_id, category_group, activity_level, time_period, season, preference, pos_item_index,
                 neg_item_index])
        else:
            # 알 수 없는 구조는 건너뛰기
            continue

    print(f"데이터 변환 완료: {len(converted_triplets)}개 triplet을 새로운 구조로 변환")
    return converted_triplets


def get_data_file_path(filename):
    """데이터 파일의 전체 경로를 반환"""
    from .config import CONFIG

    # 여러 위치에서 파일을 찾아봄
    possible_paths = [
        os.path.join(CONFIG['data_dir'], filename),  # ./data/ 폴더
        filename,  # 현재 디렉토리
        os.path.join('..', filename),  # 상위 디렉토리
    ]

    for path in possible_paths:
        if os.path.exists(path):
            return path

    # 파일을 찾지 못한 경우
    raise FileNotFoundError(f"데이터 파일을 찾을 수 없습니다: {filename}\n"
                            f"다음 위치들을 확인했습니다: {possible_paths}")


def analyze_triplet_data():
    """시간대별, 계절별 및 선호도별 triplet 형식 데이터 분석"""
    from .config import CONFIG

    interaction_file_path = get_data_file_path(CONFIG['interaction_file'])
    print(f"Triplet 파일 로딩: {interaction_file_path}")

    with open(interaction_file_path, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)

    # triplets 키에서 데이터 추출
    if 'triplets' in raw_data:
        triplets = raw_data['triplets']

        # 기존 데이터를 새로운 구조로 변환
        converted_triplets = convert_triplets_to_new_format(triplets)
        triplets = converted_triplets

        # triplet 구조 분석
        structure_info = {
            'total_triplets': len(triplets),
            'newest_structure_count': 0,  # 8개 요소 (계절 포함)
            'new_structure_count': 0,  # 7개 요소 (선호도 포함)
            'old_structure_count': 0,  # 6개 요소 (시간대 포함)
            'legacy_structure_count': 0,  # 5개 요소
            'invalid_count': 0
        }

        all_users = set()
        all_items = set()
        category_groups = set()
        activity_levels = set()
        time_periods = set()
        seasons = set()
        preferences = set()

        for triplet in triplets:
            if len(triplet) == 8:  # 최신 구조 (계절 포함)
                structure_info['newest_structure_count'] += 1
                user_id, category_group, activity_level, time_period, season, preference, pos_item_index, neg_item_index = triplet

                all_users.add(str(user_id))
                all_items.add(pos_item_index)
                all_items.add(neg_item_index)
                category_groups.add(category_group)
                activity_levels.add(activity_level)
                time_periods.add(time_period)
                seasons.add(season)
                preferences.add(preference)

            elif len(triplet) == 7:  # 새로운 구조 (선호도 포함)
                structure_info['new_structure_count'] += 1
                user_id, category_group, activity_level, time_period, preference, pos_item_index, neg_item_index = triplet

                all_users.add(str(user_id))
                all_items.add(pos_item_index)
                all_items.add(neg_item_index)
                category_groups.add(category_group)
                activity_levels.add(activity_level)
                time_periods.add(time_period)
                preferences.add(preference)

            elif len(triplet) == 6:  # 기존 구조 (시간대 포함)
                structure_info['old_structure_count'] += 1
                user_id, category_group, activity_level, time_period, pos_item_index, neg_item_index = triplet

                all_users.add(str(user_id))
                all_items.add(pos_item_index)
                all_items.add(neg_item_index)
                category_groups.add(category_group)
                activity_levels.add(activity_level)
                time_periods.add(time_period)

            elif len(triplet) == 5:  # 기존 구조
                structure_info['legacy_structure_count'] += 1
                user_id, category_group, activity_level, pos_item_index, neg_item_index = triplet

                all_users.add(str(user_id))
                all_items.add(pos_item_index)
                all_items.add(neg_item_index)
                category_groups.add(category_group)
                activity_levels.add(activity_level)

            elif len(triplet) == 3:  # 레거시 구조
                structure_info['legacy_structure_count'] += 1
                user_id, pos_item_index, neg_item_index = triplet

                all_users.add(str(user_id))
                all_items.add(pos_item_index)
                all_items.add(neg_item_index)

            else:
                structure_info['invalid_count'] += 1

        print(f"Triplet 구조 분석:")
        print(f"  총 triplets: {structure_info['total_triplets']}")
        print(f"  최신 구조 (8개 요소, 계절 포함): {structure_info['newest_structure_count']}")
        print(f"  새로운 구조 (7개 요소, 선호도 포함): {structure_info['new_structure_count']}")
        print(f"  기존 구조 (6개 요소, 시간대 포함): {structure_info['old_structure_count']}")
        print(f"  레거시 구조 (5개 요소): {structure_info['legacy_structure_count']}")
        print(f"  잘못된 구조: {structure_info['invalid_count']}")
        print(f"  고유 사용자: {len(all_users)}명")
        print(f"  고유 아이템: {len(all_items)}개")
        print(f"  카테고리 그룹: {sorted(category_groups)}")
        print(f"  활동성 레벨: {sorted(activity_levels)}")
        print(f"  시간대: {sorted(time_periods)}")
        print(f"  계절: {sorted(seasons)}")
        print(f"  선호도: {sorted(preferences)}")

        return {
            'triplets': triplets,
            'structure_info': structure_info,
            'all_users': all_users,
            'all_items': all_items,
            'category_groups': category_groups,
            'activity_levels': activity_levels,
            'time_periods': time_periods,
            'seasons': seasons,
            'preferences': preferences
        }

    else:
        raise ValueError("'triplets' 키를 찾을 수 없습니다. 데이터 형식을 확인해주세요.")


def create_mappings(triplet_data):
    """모델 학습을 위한 사용자 및 아이템 매핑 생성"""
    all_users = triplet_data['all_users']
    all_items = triplet_data['all_items']

    # 사용자 매핑 생성 - 숫자 기준으로 정렬하여 연속적인 인덱스 사용
    user_id_to_idx = {}
    # 숫자 기준으로 정렬 (문자열 정렬이 아닌)
    sorted_user_ids = sorted(all_users, key=lambda x: int(x))

    for idx, user_id in enumerate(sorted_user_ids):
        user_id_to_idx[user_id] = idx

    n_users = len(user_id_to_idx)

    # 아이템 매핑 생성 (item_index -> model_idx)
    item_id_to_model_idx = {}
    for idx, item_id in enumerate(sorted(all_items)):
        item_id_to_model_idx[item_id] = idx

    n_items = len(all_items)
    print(f"매핑 생성 완료: {n_users}명 사용자, {n_items}개 아이템")

    # 사용자 ID 분포 확인
    user_ids_list = [int(uid) for uid in all_users]
    if user_ids_list:
        print(f"사용자 ID 범위: {min(user_ids_list)} ~ {max(user_ids_list)}")
        print(f"고유 사용자 ID: {user_ids_list}")
        print(f"실제 사용자 수: {len(user_ids_list)}명")
    else:
        print("경고: 사용자 데이터가 없습니다.")
        print("데이터 파일의 triplet 구조를 확인해주세요.")
        print(
            "예상 구조: [user_id, category_group, activity_level, time_period, season, preference, pos_item_index, neg_item_index]")

    return {
        'user_id_to_idx': user_id_to_idx,
        'item_id_to_model_idx': item_id_to_model_idx,
        'n_users': n_users,
        'n_items': n_items
    }


def load_data():
    """
    전체 데이터 로딩 파이프라인 - 시간대별, 계절별 필터링 지원

    Returns:
        dict: triplets, 매핑, 데이터셋 크기를 포함하는 딕셔너리
    """
    # 1. triplet 데이터 분석
    triplet_data = analyze_triplet_data()

    # 2. 매핑 생성
    mapping_data = create_mappings(triplet_data)

    # 3. user_item_interactions 생성
    user_item_interactions = {}
    for triplet in triplet_data['triplets']:
        if len(triplet) >= 8:  # 최신 구조: [user_id, category_group, activity_level, time_period, season, preference, pos_item_index, neg_item_index]
            user_id = str(triplet[0])
            pos_item_index = triplet[6]  # pos_item_index
            neg_item_index = triplet[7]  # neg_item_index

            if user_id not in user_item_interactions:
                user_item_interactions[user_id] = []
            user_item_interactions[user_id].append(pos_item_index)
            user_item_interactions[user_id].append(neg_item_index)

        elif len(
                triplet) >= 7:  # 새로운 구조: [user_id, category_group, activity_level, time_period, preference, pos_item_index, neg_item_index]
            user_id = str(triplet[0])
            pos_item_index = triplet[5]  # pos_item_index
            neg_item_index = triplet[6]  # neg_item_index

            if user_id not in user_item_interactions:
                user_item_interactions[user_id] = []
            user_item_interactions[user_id].append(pos_item_index)
            user_item_interactions[user_id].append(neg_item_index)

        elif len(
                triplet) >= 6:  # 기존 구조: [user_id, category_group, activity_level, time_period, pos_item_index, neg_item_index]
            user_id = str(triplet[0])
            pos_item_index = triplet[4]  # pos_item_index
            neg_item_index = triplet[5]  # neg_item_index

            if user_id not in user_item_interactions:
                user_item_interactions[user_id] = []
            user_item_interactions[user_id].append(pos_item_index)
            user_item_interactions[user_id].append(neg_item_index)

        elif len(triplet) >= 5:  # 기존 구조: [user_id, category_group, activity_level, pos_item_index, neg_item_index]
            user_id = str(triplet[0])
            pos_item_index = triplet[3]  # pos_item_index
            neg_item_index = triplet[4]  # neg_item_index

            if user_id not in user_item_interactions:
                user_item_interactions[user_id] = []
            user_item_interactions[user_id].append(pos_item_index)
            user_item_interactions[user_id].append(neg_item_index)

        elif len(triplet) >= 3:  # 레거시 구조: [user_id, pos_item_index, neg_item_index]
            user_id = str(triplet[0])
            pos_item_index = triplet[1]  # pos_item_index
            neg_item_index = triplet[2]  # neg_item_index

            if user_id not in user_item_interactions:
                user_item_interactions[user_id] = []
            user_item_interactions[user_id].append(pos_item_index)
            user_item_interactions[user_id].append(neg_item_index)

    # 중복 제거
    for user_id in user_item_interactions:
        user_item_interactions[user_id] = list(set(user_item_interactions[user_id]))

    return {
        'triplets': triplet_data['triplets'],
        'user_id_to_idx': mapping_data['user_id_to_idx'],
        'item_id_to_model_idx': mapping_data['item_id_to_model_idx'],
        'n_users': mapping_data['n_users'],
        'n_items': mapping_data['n_items'],
        'category_groups': triplet_data['category_groups'],
        'activity_levels': triplet_data['activity_levels'],
        'time_periods': triplet_data['time_periods'],
        'seasons': triplet_data['seasons'],
        'user_item_interactions': user_item_interactions  # 추가된 키
    }


def create_dataloaders(data, config):
    """70:20:10 분할로 학습/검증/테스트 데이터로더 생성 (Uniform Random)"""
    # 학습/검증/테스트 분할 (70:20:10)
    triplets = data['triplets']

    # uniform random하게 섞어서 분할
    random.shuffle(triplets)
    n_total = len(triplets)
    n_train = int(n_total * 0.7)
    n_val = int(n_total * 0.2)

    train_triplets = triplets[:n_train]
    val_triplets = triplets[n_train:n_train + n_val]
    test_triplets = triplets[n_train + n_val:]

    print(f"데이터 분할 완료: 학습 {len(train_triplets):,}, 검증 {len(val_triplets):,}, 테스트 {len(test_triplets):,}")

    # 데이터셋 생성
    train_dataset = NCFDataset(train_triplets, data['user_id_to_idx'], data['item_id_to_model_idx'])
    val_dataset = NCFDataset(val_triplets, data['user_id_to_idx'], data['item_id_to_model_idx'])
    test_dataset = NCFDataset(test_triplets, data['user_id_to_idx'], data['item_id_to_model_idx'])

    # 데이터로더 생성
    train_loader = DataLoader(train_dataset, batch_size=config['batch_size'],
                              shuffle=True, num_workers=config['num_workers'])
    val_loader = DataLoader(val_dataset, batch_size=config['batch_size'],
                            shuffle=False, num_workers=config['num_workers'])
    test_loader = DataLoader(test_dataset, batch_size=config['batch_size'],
                             shuffle=False, num_workers=config['num_workers'])

    return {
        'train_loader': train_loader,
        'val_loader': val_loader,
        'test_loader': test_loader,
        'train_triplets': train_triplets,
        'val_triplets': val_triplets,
        'test_triplets': test_triplets
    }


def analyze_data_sparsity(triplets, n_users, n_items):
    """
    데이터 희소성 메트릭 분석 - triplet 기반

    Args:
        triplets (list): triplet 데이터 리스트
        n_users (int): 전체 사용자 수
        n_items (int): 전체 아이템 수

    Returns:
        dict: 희소성 분석 결과
    """
    # 유저-아이템 상호작용 수집
    interactions = set()
    for triplet in triplets:
        if len(triplet) >= 3:
            user_id = triplet[0]
            if len(triplet) == 8:  # 최신 구조
                pos_item = triplet[6]
                neg_item = triplet[7]
            elif len(triplet) == 7:  # 새로운 구조
                pos_item = triplet[5]
                neg_item = triplet[6]
            elif len(triplet) == 6:  # 기존 구조
                pos_item = triplet[4]
                neg_item = triplet[5]
            elif len(triplet) == 5:  # 기존 구조
                pos_item = triplet[3]
                neg_item = triplet[4]
            else:  # 레거시 구조
                pos_item = triplet[1]
                neg_item = triplet[2]

            interactions.add((user_id, pos_item))
            interactions.add((user_id, neg_item))

    total_possible_interactions = n_users * n_items
    actual_interactions = len(interactions)
    sparsity = (1 - actual_interactions / total_possible_interactions) * 100

    print(f"데이터 희소성: {sparsity:.2f}% (사용자 {n_users:,}명, 아이템 {n_items:,}개)")

    return {
        'sparsity': sparsity,
        'density': 100 - sparsity,
        'total_interactions': actual_interactions,
        'avg_per_user': actual_interactions / n_users if n_users > 0 else 0
    } 
