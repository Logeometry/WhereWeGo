# improved_triplets.py - 추천 시스템에 적합한 현실적 데이터 생성
# 현재 학습에 사용하는 데이터는 이 파일로부터 만들어짐
import json
import random
import numpy as np
from collections import defaultdict, Counter
from tqdm import tqdm


def generate_realistic_triplets(
    input_path="places_filtered.json",
    output_path="improved_implicit.json",
    seed=44
):
    """현실적인 사용자 행동 패턴을 모방한 triplet 생성"""
    random.seed(seed)
    np.random.seed(seed)

    with open(input_path, "r", encoding="utf-8") as f:
        places = json.load(f)

    item_id_map = {str(i): place["_id"] for i, place in enumerate(places)}
    item_category_map = {int(k): place["category_group"] for k, place in enumerate(places)}
    category_items = defaultdict(list)
    for item_id, cat in item_category_map.items():
        category_items[cat].append(item_id)

    num_items = len(item_id_map)
    category_list = list(category_items.keys())

    # 1. Power-law 분포로 사용자 활동도 생성
    def generate_user_activity_levels(num_users_target=3000):
        """Power-law 분포를 따르는 사용자 활동도 생성"""
        # Zipf 분포 (alpha=1.2, 추천 시스템에서 일반적)
        alpha = 1.2
        activities = np.random.zipf(alpha, num_users_target)
        
        # 최소/최대 활동도 제한 (5~100개)
        activities = np.clip(activities, 5, 100)
        
        # 정렬하여 Power-law 분포 보장
        activities = np.sort(activities)[::-1]
        
        print(f"사용자 활동도 분포:")
        print(f"  평균: {np.mean(activities):.2f}")
        print(f"  중앙값: {np.median(activities):.2f}")
        print(f"  최소: {min(activities)}, 최대: {max(activities)}")
        print(f"  표준편차: {np.std(activities):.2f}")
        
        return activities

    # 2. Long-tail 분포로 아이템 인기도 목표 설정
    def generate_item_popularity_targets(num_items):
        """Long-tail 분포를 따르는 아이템 인기도 목표"""
        # Pareto 분포 (80-20 법칙)
        alpha = 1.16  # 80-20 법칙에 해당하는 alpha 값
        popularity = np.random.pareto(alpha, num_items) + 1
        
        # 정규화하여 합리적인 범위로 조정
        popularity = popularity / popularity.sum() * num_items * 50  # 평균 50
        popularity = np.clip(popularity, 10, 500)  # 최소 10, 최대 500
        
        # 내림차순 정렬하여 Long-tail 보장
        popularity = np.sort(popularity)[::-1]
        
        print(f"아이템 인기도 목표:")
        print(f"  평균: {np.mean(popularity):.2f}")
        print(f"  상위 20% 아이템 비율: {sum(popularity[:int(len(popularity)*0.2)])/sum(popularity)*100:.1f}%")
        
        return popularity

    # 3. 다양한 사용자 선호도 패턴 정의
    def generate_user_preference_profiles(num_users, category_list):
        """현실적인 사용자 선호도 프로필 생성"""
        profiles = []
        
        for i in range(num_users):
            profile_type = random.choices(
                ['specialist', 'explorer', 'mainstream', 'niche'],
                weights=[0.15, 0.25, 0.45, 0.15]  # 더 현실적인 분포
            )[0]
            
            if profile_type == 'specialist':
                # 1-2개 카테고리에만 집중
                num_cats = random.randint(1, 2)
                preferred_cats = random.sample(category_list, num_cats)
                cat_weights = {cat: random.uniform(0.8, 1.0) if cat in preferred_cats 
                              else random.uniform(0.01, 0.1) for cat in category_list}
                
            elif profile_type == 'explorer':
                # 많은 카테고리를 탐험하지만 선호도 차이 있음
                num_main_cats = random.randint(3, 5)
                main_cats = random.sample(category_list, num_main_cats)
                cat_weights = {cat: random.uniform(0.6, 0.9) if cat in main_cats
                              else random.uniform(0.1, 0.4) for cat in category_list}
                
            elif profile_type == 'mainstream':
                # 인기 있는 카테고리 선호
                cat_weights = {cat: random.uniform(0.3, 0.8) for cat in category_list}
                
            else:  # niche
                # 특정 카테고리에 매우 강한 선호
                niche_cat = random.choice(category_list)
                cat_weights = {cat: random.uniform(0.9, 1.0) if cat == niche_cat
                              else random.uniform(0.01, 0.2) for cat in category_list}
            
            profiles.append({
                'type': profile_type,
                'category_weights': cat_weights
            })
        
        return profiles

    # 사용자 활동도 및 프로필 생성
    user_activities = generate_user_activity_levels(3000)
    item_popularity_targets = generate_item_popularity_targets(num_items)
    user_profiles = generate_user_preference_profiles(len(user_activities), category_list)

    # 실제 triplet 생성
    triplets = []
    item_popularity_actual = Counter()
    user_id = 0

    print("\n현실적인 Triplet 생성 중...")
    
    for activity_level, user_profile in tqdm(zip(user_activities, user_profiles), 
                                            total=len(user_activities), 
                                            desc="사용자별 데이터 생성"):
        
        # 4. 사용자별 아이템 선호도 계산
        item_scores = {}
        for item_id in range(num_items):
            category = item_category_map[item_id]
            category_weight = user_profile['category_weights'][category]
            
            # 아이템 고유 점수 (인기도 + 랜덤성)
            popularity_bonus = item_popularity_targets[item_id] / max(item_popularity_targets) * 0.3
            random_factor = random.uniform(0.1, 0.4)
            
            item_scores[item_id] = category_weight * 0.6 + popularity_bonus + random_factor

        # 상위 점수 아이템들 중에서 선택 (확률적)
        sorted_items = sorted(item_scores.items(), key=lambda x: x[1], reverse=True)
        
        # 5. 현실적인 positive sampling
        num_positives = min(activity_level, len(sorted_items))
        
        # 상위 아이템들에 대한 가중 확률 생성
        top_candidates = sorted_items[:min(num_positives * 3, len(sorted_items))]
        items, scores = zip(*top_candidates)
        
        # 소프트맥스로 확률 변환 (temperature=2.0으로 다양성 확보)
        scores = np.array(scores)
        probs = np.exp(scores / 2.0)
        probs = probs / probs.sum()
        
        # 중복 없이 sampling
        selected_indices = np.random.choice(
            len(top_candidates), 
            size=num_positives, 
            replace=False, 
            p=probs
        )
        
        positive_items = [items[i] for i in selected_indices]
        
        # 6. 개선된 negative sampling
        for pos_item in positive_items:
            # 같은 카테고리 내에서 negative 선택 (더 현실적)
            pos_category = item_category_map[pos_item]
            same_cat_items = category_items[pos_category]
            
            # 50% 확률로 같은 카테고리에서, 50% 확률로 전체에서 선택
            if random.random() < 0.5 and len(same_cat_items) > 1:
                neg_candidates = [i for i in same_cat_items if i != pos_item]
            else:
                neg_candidates = [i for i in range(num_items) if i != pos_item]
            
            # 인기도 역가중치로 negative sampling (unpopular items 선호)
            neg_weights = []
            for neg_item in neg_candidates:
                current_popularity = item_popularity_actual[neg_item]
                weight = 1.0 / (1.0 + current_popularity * 0.1)  # 인기도 페널티
                neg_weights.append(weight)
            
            if neg_weights:
                neg_weights = np.array(neg_weights)
                neg_weights = neg_weights / neg_weights.sum()
                
                neg_item = np.random.choice(neg_candidates, p=neg_weights)
                
                triplets.append([user_id, pos_item, int(neg_item)])
                item_popularity_actual[pos_item] += 1

        user_id += 1

    # 7. 결과 검증 및 저장
    print(f"\n=== 생성 결과 검증 ===")
    
    # 사용자별 상호작용 분포
    user_interactions = defaultdict(set)
    for triplet in triplets:
        user, pos_item, neg_item = triplet
        user_interactions[user].add(pos_item)
    
    interaction_counts = [len(items) for items in user_interactions.values()]
    print(f"사용자별 상호작용 분포:")
    print(f"  평균: {np.mean(interaction_counts):.2f}")
    print(f"  표준편차: {np.std(interaction_counts):.2f}")
    print(f"  최소-최대: {min(interaction_counts)}-{max(interaction_counts)}")
    
    # 아이템별 인기도 분포
    final_popularity = list(item_popularity_actual.values())
    print(f"아이템별 인기도 분포:")
    print(f"  평균: {np.mean(final_popularity):.2f}")
    print(f"  표준편차: {np.std(final_popularity):.2f}")
    print(f"  상위 20% 아이템 비율: {sum(sorted(final_popularity, reverse=True)[:int(len(final_popularity)*0.2)])/sum(final_popularity)*100:.1f}%")

    # 메타데이터 구성
    metadata = {
        "generation_method": "realistic_power_law",
        "num_users": user_id,
        "num_items": num_items,
        "total_triplets": len(triplets),
        "user_activity_distribution": {
            "mean": float(np.mean(interaction_counts)),
            "std": float(np.std(interaction_counts)),
            "min": int(min(interaction_counts)),
            "max": int(max(interaction_counts))
        },
        "item_popularity_distribution": {
            "mean": float(np.mean(final_popularity)),
            "std": float(np.std(final_popularity)),
            "top_20_percent_ratio": float(sum(sorted(final_popularity, reverse=True)[:int(len(final_popularity)*0.2)])/sum(final_popularity))
        }
    }

    # 결과 저장
    output_data = {
        "triplets": triplets,
        "metadata": metadata,
        "item_id_map": item_id_map,
        "user_profiles": [{'type': p['type']} for p in user_profiles]  # 타입만 저장
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print(f"\n개선된 Triplet 생성 완료: {output_path}")
    print(f"   총 {len(triplets)}개 triplet, {user_id}명 사용자, {num_items}개 아이템")


if __name__ == "__main__":
    generate_realistic_triplets(
        input_path="places_filtered.json",
        output_path="improved_implicit.json",
        seed=44
    ) 