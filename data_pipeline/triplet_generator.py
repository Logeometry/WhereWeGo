# triplet_generator.py (item 중심 + 성향 기반 + 하한 보장)
# bpr 데이터 생성 파일
import json
import random
import numpy as np
import time
from collections import defaultdict
from tqdm import tqdm
from typing import List, Dict

def load_place_data(path: str):
    with open(path, "r", encoding="utf-8") as f:
        places = json.load(f)
    items = [i for i in range(len(places))]
    item_categories = {i: place.get("category_group", "기타") for i, place in enumerate(places)}
    category_to_items = defaultdict(list)
    for i, cat in item_categories.items():
        if cat != "기타":
            category_to_items[cat].append(i)
    return items, item_categories, category_to_items

def generate_user_preferences(
    category_to_items: Dict[str, List[int]],
    num_positive: int,
    user_type: str
) -> List[int]:
    categories = list(category_to_items.keys())

    if user_type == "random":
        pool = sum(category_to_items.values(), [])
    elif user_type == "single":
        selected = random.choice(categories)
        pool = category_to_items[selected]
    elif user_type == "double":
        selected = random.sample(categories, 2)
        pool = category_to_items[selected[0]] + category_to_items[selected[1]]
    elif user_type == "triple":
        selected = random.sample(categories, 3)
        pool = sum([category_to_items[c] for c in selected], [])
    else:
        pool = sum(category_to_items.values(), [])

    return random.sample(pool, min(num_positive, len(pool)))

def generate_triplets(
    input_path="places_filtered.json",
    output_path="please.json",
    num_positive_per_user=15,
    neg_ratio=2,

    pos_lower=20,
    seed=None
):
    if seed is None:
        seed = int(time.time()) % (2**32 - 1)
    print(f"\U0001f9ea 사용된 랜덤 시드: {seed}")
    random.seed(seed)
    np.random.seed(seed)

    items, item_categories, category_to_items = load_place_data(input_path)
    item_pos_count = defaultdict(int)
    item_neg_count = defaultdict(int)
    triplets = []

    user_type_distribution = [
        ("random", 0.2),
        ("single", 0.3),
        ("double", 0.3),
        ("triple", 0.2)
    ]

    user_id = 0
    unmet_items = set(items)

    print("\nTriplet 생성 중... (하한 조건 달성까지 반복)")
    with tqdm() as pbar:
        while unmet_items:
            user_type = random.choices(
                [ut[0] for ut in user_type_distribution],
                weights=[ut[1] for ut in user_type_distribution],
                k=1
            )[0]

            positives = generate_user_preferences(category_to_items, num_positive_per_user, user_type)
            for pos in positives:
                neg_candidates = [i for i in items if i != pos]
                weights = np.array([1 / (1 + item_neg_count[i]) for i in neg_candidates], dtype=np.float64)
                weights /= weights.sum()
                negs = np.random.choice(neg_candidates, size=neg_ratio, replace=False, p=weights)

                for neg in negs:
                    triplets.append([user_id, pos, int(neg)])
                    item_neg_count[neg] += 1

                item_pos_count[pos] += 1
            
            user_id += 1

            unmet_items = {i for i in items if item_pos_count[i] < pos_lower}
            pbar.set_description(f"생성 사용자 수: {user_id} / 미달 item: {len(unmet_items)}")
            pbar.update(1)

    metadata = {
        "num_users": user_id,
        "num_businesses": len(items),
        "positive_per_user": num_positive_per_user,
        "neg_ratio": neg_ratio,
        "pos_lower": pos_lower,
        "seed": seed
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({
            "triplets": triplets,
            "metadata": metadata
        }, f, indent=2, ensure_ascii=False)

    print(f"\nTriplet 생성 완료: {output_path}")
    print(f"총 사용자 수: {user_id}")
    print(f"총 triplet 수: {len(triplets)}")

if __name__ == "__main__":
    generate_triplets()