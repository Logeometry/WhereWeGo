# evaluation.py
# 평가 함수 모듈

import torch
import torch.nn.functional as F
import numpy as np
from tqdm import tqdm
from .data_utils import AdvancedFilteringUtils


def validate_epoch(model, dataloader, device):
    """과적합 감지를 위한 검증 손실 계산 - 계절별 필터링 지원"""
    model.eval()
    total_loss = 0

    with torch.no_grad():
        for batch in tqdm(dataloader, desc="Validating"):
            if len(batch) == 8:  # 최신 구조: (users, items, labels, category_groups, activity_levels, time_periods, seasons, preferences)
                users, items, labels, category_groups, activity_levels, time_periods, seasons, preferences = batch
                users, items, labels = users.to(device), items.to(device), labels.to(device)

                # 문자열 리스트를 텐서로 변환하지 않고 그대로 전달
                predictions = model(users, items, category_groups, activity_levels, time_periods, seasons, preferences)
            elif len(batch) == 7:  # 새로운 구조: (users, items, labels, category_groups, activity_levels, time_periods, preferences)
                users, items, labels, category_groups, activity_levels, time_periods, preferences = batch
                users, items, labels = users.to(device), items.to(device), labels.to(device)

                # 기본 계절 (봄) 사용
                seasons = [0] * len(users)
                predictions = model(users, items, category_groups, activity_levels, time_periods, seasons, preferences)
            elif len(batch) == 6:  # 기존 구조: (users, items, labels, category_groups, activity_levels, time_periods)
                users, items, labels, category_groups, activity_levels, time_periods = batch
                users, items, labels = users.to(device), items.to(device), labels.to(device)

                # 기본 선호도 (시간대 선호) 및 계절 (봄) 사용
                preferences = [1] * len(users)
                seasons = [0] * len(users)
                predictions = model(users, items, category_groups, activity_levels, time_periods, seasons, preferences)
            elif len(batch) == 5:  # 기존 구조: (users, items, labels, category_groups, activity_levels)
                users, items, labels, category_groups, activity_levels = batch
                users, items, labels = users.to(device), items.to(device), labels.to(device)

                # 기본 시간대 (오후) 및 선호도 (시간대 선호) 및 계절 (봄) 사용
                time_periods = [1] * len(users)
                preferences = [1] * len(users)
                seasons = [0] * len(users)
                predictions = model(users, items, category_groups, activity_levels, time_periods, seasons, preferences)
            else:  # 레거시 구조: (users, items, labels)
                users, items, labels = batch
                users, items, labels = users.to(device), items.to(device), labels.to(device)
                predictions = model(users, items)

            loss = F.binary_cross_entropy_with_logits(predictions, labels)
            total_loss += loss.item()

    return total_loss / len(dataloader)


def train_epoch(model, dataloader, optimizer, device):
    """한 에폭 모델 학습 - 계절별 필터링 지원"""
    model.train()
    total_loss = 0

    for batch in tqdm(dataloader, desc="Training"):
        if len(batch) == 8:  # 최신 구조: (users, items, labels, category_groups, activity_levels, time_periods, seasons, preferences)
            users, items, labels, category_groups, activity_levels, time_periods, seasons, preferences = batch
            users, items, labels = users.to(device), items.to(device), labels.to(device)

            optimizer.zero_grad()
            predictions = model(users, items, category_groups, activity_levels, time_periods, seasons, preferences)
        elif len(batch) == 7:  # 새로운 구조: (users, items, labels, category_groups, activity_levels, time_periods, preferences)
            users, items, labels, category_groups, activity_levels, time_periods, preferences = batch
            users, items, labels = users.to(device), items.to(device), labels.to(device)

            # 기본 계절 (봄) 사용
            seasons = [0] * len(users)
            optimizer.zero_grad()
            predictions = model(users, items, category_groups, activity_levels, time_periods, seasons, preferences)
        elif len(batch) == 6:  # 기존 구조: (users, items, labels, category_groups, activity_levels, time_periods)
            users, items, labels, category_groups, activity_levels, time_periods = batch
            users, items, labels = users.to(device), items.to(device), labels.to(device)

            # 기본 선호도 (시간대 선호) 및 계절 (봄) 사용
            preferences = [1] * len(users)
            seasons = [0] * len(users)
            optimizer.zero_grad()
            predictions = model(users, items, category_groups, activity_levels, time_periods, seasons, preferences)
        elif len(batch) == 5:  # 기존 구조: (users, items, labels, category_groups, activity_levels)
            users, items, labels, category_groups, activity_levels = batch
            users, items, labels = users.to(device), items.to(device), labels.to(device)

            # 기본 시간대 (오후) 및 선호도 (시간대 선호) 및 계절 (봄) 사용
            time_periods = [1] * len(users)
            preferences = [1] * len(users)
            seasons = [0] * len(users)
            optimizer.zero_grad()
            predictions = model(users, items, category_groups, activity_levels, time_periods, seasons, preferences)
        else:  # 레거시 구조: (users, items, labels)
            users, items, labels = batch
            users, items, labels = users.to(device), items.to(device), labels.to(device)

            optimizer.zero_grad()
            predictions = model(users, items)

        loss = F.binary_cross_entropy_with_logits(predictions, labels)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        optimizer.step()

        total_loss += loss.item()

    return total_loss / len(dataloader)


def calculate_ndcg(y_true, y_score, k=10):
    """NDCG@K 메트릭 계산"""

    def dcg_at_k(r, k):
        r = np.asarray(r, dtype=float)[:k]
        return np.sum(r / np.log2(np.arange(2, r.size + 2)))

    indices = np.argsort(y_score)[::-1]
    ranked_true = y_true[indices]
    dcg = dcg_at_k(ranked_true, k)
    idcg = dcg_at_k(sorted(y_true, reverse=True), k)

    return dcg / idcg if idcg > 0 else 0


def calculate_map(y_true, y_score, k=10):
    """MAP@K (평균 정밀도) 메트릭 계산"""
    indices = np.argsort(y_score)[::-1][:k]
    ranked_true = y_true[indices]

    precisions = []
    num_hits = 0

    for i, hit in enumerate(ranked_true):
        if hit:
            num_hits += 1
            precision_at_i = num_hits / (i + 1)
            precisions.append(precision_at_i)

    return np.mean(precisions) if precisions else 0.0


def evaluate_comprehensive(model, test_triplets, user_id_to_idx, item_id_to_model_idx, device, k_list=[5, 10, 20]):
    """
    다중 메트릭을 사용한 종합 평가 - 계절별 필터링 지원

    주어진 k 값들에 대해 HR, Precision, Recall, NDCG, MAP, AUC를 계산합니다.

    Args:
        model: 학습된 모델
        test_triplets: 평가용 triplet 데이터
        user_id_to_idx: 사용자 ID에서 인덱스로의 매핑
        item_id_to_model_idx: 아이템 ID에서 모델 인덱스로의 매핑
        device: 연산 장치
        k_list: 평가할 k 값들의 리스트

    Returns:
        dict: 계산된 모든 메트릭을 포함하는 딕셔너리
    """
    model.eval()

    # triplet에서 유저별 positive 아이템 수집
    user_positive_items = {}
    all_item_indices = list(item_id_to_model_idx.values())

    for triplet in test_triplets:
        if len(triplet) >= 3:
            user_id = str(triplet[0])
            if len(triplet) == 8:  # 최신 구조 (계절 포함)
                pos_item = triplet[6]
            elif len(triplet) == 7:  # 새로운 구조 (선호도 포함)
                pos_item = triplet[5]
            elif len(triplet) == 6:  # 기존 구조 (시간대 포함)
                pos_item = triplet[4]
            elif len(triplet) == 5:  # 기존 구조
                pos_item = triplet[3]
            else:  # 레거시 구조
                pos_item = triplet[1]

            if user_id in user_id_to_idx and pos_item in item_id_to_model_idx:
                user_idx = user_id_to_idx[user_id]
                model_idx = item_id_to_model_idx[pos_item]

                if user_idx not in user_positive_items:
                    user_positive_items[user_idx] = set()
                user_positive_items[user_idx].add(model_idx)

    # 메트릭 초기화
    metrics = {}
    for k in k_list:
        metrics[f'HR@{k}'] = []
        metrics[f'Precision@{k}'] = []
        metrics[f'Recall@{k}'] = []
        metrics[f'NDCG@{k}'] = []
        metrics[f'MAP@{k}'] = []

    metrics['AUC'] = []

    with torch.no_grad():
        for user_idx in tqdm(user_positive_items.keys(), desc="Evaluating"):
            positive_items = user_positive_items[user_idx]

            # 해당 유저와 모든 아이템 조합 생성
            user_tensor = torch.tensor([user_idx] * len(all_item_indices), device=device)
            items_tensor = torch.tensor(all_item_indices, device=device)

            # 기본 예측 (카테고리 그룹과 활동성 레벨, 시간대, 계절 없이)
            predictions = torch.sigmoid(model(user_tensor, items_tensor))
            predictions_np = predictions.cpu().numpy()

            # Ground truth 배열 생성
            y_true = np.array([1 if item_idx in positive_items else 0 for item_idx in all_item_indices])

            # AUC 계산
            try:
                from sklearn.metrics import roc_auc_score
                auc = roc_auc_score(y_true, predictions_np)
                metrics['AUC'].append(auc)
            except:
                pass

            # 상위 K개 아이템 인덱스 획득
            top_indices = np.argsort(predictions_np)[::-1]

            # 각 K에 대해 메트릭 계산
            for k in k_list:
                top_k_indices = top_indices[:k]
                top_k_items = set([all_item_indices[idx] for idx in top_k_indices])

                # HR@K
                hit = 1 if len(top_k_items & positive_items) > 0 else 0
                metrics[f'HR@{k}'].append(hit)

                # Precision@K
                precision = len(top_k_items & positive_items) / k
                metrics[f'Precision@{k}'].append(precision)

                # Recall@K
                recall = len(top_k_items & positive_items) / len(positive_items)
                metrics[f'Recall@{k}'].append(recall)

                # NDCG@K
                y_true_k = y_true[top_k_indices]
                y_score_k = predictions_np[top_k_indices]
                ndcg = calculate_ndcg(y_true_k, y_score_k, k)
                metrics[f'NDCG@{k}'].append(ndcg)

                # MAP@K
                map_score = calculate_map(y_true_k, y_score_k, k)
                metrics[f'MAP@{k}'].append(map_score)

    # 평균 계산
    final_metrics = {}
    for metric_name, values in metrics.items():
        if values:
            avg_value = np.mean(values)
            final_metrics[metric_name] = avg_value

    return final_metrics


def recommend_with_preference_filtering(model, user_id, user_context, all_items, device,
                                        config, visitor_data=None, top_k=10):
    """
    선호도별 필터링을 적용한 추천 시스템 - 계절 고려

    Args:
        model: 학습된 모델
        user_id: 사용자 ID
        user_context: 사용자 컨텍스트 (시간, 계절, 날씨, 위치, 활동성, 선호도 등)
        all_items: 모든 아이템 리스트
        device: 연산 장치
        config: 설정
        visitor_data: 방문자 수 데이터
        top_k: 추천 개수

    Returns:
        필터링된 추천 아이템 리스트
    """
    # 고급 필터링 유틸리티 초기화
    filtering_utils = AdvancedFilteringUtils(config)

    # 선호도별 필터링 적용
    if all(key in user_context for key in ['preference', 'activity_level', 'time_period', 'season', 'category_group']):
        preference = user_context['preference']
        activity_level = user_context['activity_level']
        time_period = user_context['time_period']
        season = user_context['season']
        category_group = user_context['category_group']

        filtered_items = filtering_utils.filter_by_preference(
            all_items, preference, activity_level, time_period, season, category_group
        )
    else:
        filtered_items = all_items

    if not filtered_items:
        print("선호도별 필터링 후 추천 가능한 아이템이 없습니다.")
        return []

    # 모델 예측 수행
    model.eval()
    with torch.no_grad():
        # 필터링된 아이템에 대해서만 예측
        item_indices = [item.index for item in filtered_items]
        user_tensor = torch.tensor([user_id] * len(item_indices), device=device)
        items_tensor = torch.tensor(item_indices, device=device)

        # 컨텍스트 정보가 있으면 추가
        if all(key in user_context for key in ['category_group', 'activity_level', 'time_period', 'season', 'preference']):
            category_groups = [user_context['category_group']] * len(item_indices)
            activity_levels = [user_context['activity_level']] * len(item_indices)
            time_periods = [user_context['time_period']] * len(item_indices)
            seasons = [user_context['season']] * len(item_indices)
            preferences = [user_context['preference']] * len(item_indices)
            predictions = torch.sigmoid(
                model(user_tensor, items_tensor, category_groups, activity_levels, time_periods, seasons, preferences))
        else:
            predictions = torch.sigmoid(model(user_tensor, items_tensor))

        predictions_np = predictions.cpu().numpy()

    # 상위 K개 아이템 선택
    top_indices = np.argsort(predictions_np)[::-1][:top_k]
    recommended_items = [filtered_items[i] for i in top_indices]

    return recommended_items


def analyze_preference_based_recommendations(recommended_items, user_context, visitor_data=None):
    """
    선호도별 추천 품질 분석 - 계절 고려

    Args:
        recommended_items: 추천된 아이템 리스트
        user_context: 사용자 컨텍스트
        visitor_data: 방문자 수 데이터

    Returns:
        분석 결과 딕셔너리
    """
    analysis = {
        'total_recommended': len(recommended_items),
        'category_distribution': {},
        'preference_compliance': 0,
        'average_popularity': 0,
        'diversity_score': 0
    }

    if not recommended_items:
        return analysis

    # 카테고리 분포 분석
    categories = [item.category_group for item in recommended_items if hasattr(item, 'category_group')]
    category_counts = {}
    for category in categories:
        category_counts[category] = category_counts.get(category, 0) + 1

    analysis['category_distribution'] = category_counts

    # 평균 인기도 계산
    if visitor_data:
        popularities = [visitor_data.get(item.name, 0) for item in recommended_items if hasattr(item, 'name')]
        if popularities:
            analysis['average_popularity'] = sum(popularities) / len(popularities)

    # 선호도 준수도 계산
    if 'preference' in user_context:
        preference = user_context['preference']
        preference_compliance_count = 0
        for item in recommended_items:
            # 선호도별 선호 카테고리 확인
            if hasattr(item, 'category_group') and 'category_group' in user_context:
                if item.category_group == user_context['category_group']:
                    preference_compliance_count += 1

        analysis['preference_compliance'] = preference_compliance_count / len(
            recommended_items) if recommended_items else 0

    # 다양성 점수 계산 (카테고리 수 / 전체 아이템 수)
    analysis['diversity_score'] = len(category_counts) / len(recommended_items) if recommended_items else 0

    return analysis


def generate_preference_based_recommendations(model, user_id, user_context, all_items, device,
                                              config, visitor_data=None, top_k=10):
    """
    선호도별 추천 생성 및 분석 - 계절 고려

    Args:
        model: 학습된 모델
        user_id: 사용자 ID
        user_context: 사용자 컨텍스트
        all_items: 모든 아이템 리스트
        device: 연산 장치
        config: 설정
        visitor_data: 방문자 수 데이터
        top_k: 추천 개수

    Returns:
        추천 결과와 분석 정보
    """
    # 선호도별 추천 수행
    recommended_items = recommend_with_preference_filtering(
        model, user_id, user_context, all_items, device, config, visitor_data, top_k
    )

    # 추천 품질 분석
    quality_analysis = analyze_preference_based_recommendations(recommended_items, user_context, visitor_data)

    # 결과 출력
    print(f"\n=== 선호도별 추천 결과 ===")
    print(f"사용자 ID: {user_id}")
    print(f"컨텍스트: {user_context}")
    print(f"추천 아이템 수: {quality_analysis['total_recommended']}")
    print(f"카테고리 분포: {quality_analysis['category_distribution']}")
    print(f"선호도 준수도: {quality_analysis['preference_compliance']:.2f}")
    print(f"평균 인기도: {quality_analysis['average_popularity']:.2f}")
    print(f"다양성 점수: {quality_analysis['diversity_score']:.2f}")

    # 선호도 타입 표시
    preference_type = "활동성 선호" if user_context.get('preference', 1) == 0 else "시간대 선호"
    print(f"사용자 선호도: {preference_type}")

    print(f"\n=== 상위 {top_k}개 추천 아이템 ===")
    for i, item in enumerate(recommended_items, 1):
        popularity = visitor_data.get(item.name, 0) if visitor_data and hasattr(item, 'name') else 0
        print(f"{i:2d}. {item.name} ({item.category_group}) - 인기도: {popularity}")

    return {
        'recommended_items': recommended_items,
        'quality_analysis': quality_analysis
    }