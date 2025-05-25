import json
import os
from datetime import datetime

def transform_place(entry):
    return {
        "name": entry.get("place_name", ""),
        "category": entry.get("category_name", "").split("›")[-1].strip() or None,
        "tags": [],
        "description": "",
        "address": entry.get("address_name", ""),
        "region": " ".join(entry.get("address_name", "").split()[:2]) if entry.get("address_name") else "",
        "location": {
            "type": "Point",
            "coordinates": [float(entry.get("x", 0)), float(entry.get("y", 0))]
        },
        "image_url": None,
        "rating": 0.0,
        "review_count": 0,
        "place_url": entry.get("place_url", ""),
        "vector": [],
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }

def process_files_with_prefix(prefix, input_dir, output_dir):
    for i in range(20):  # 최대 20개까지 처리
        filename = f"cleaned_{prefix}_{i}.json"
        input_path = os.path.join(input_dir, filename)
        if not os.path.exists(input_path):
            continue

        with open(input_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        formatted = [transform_place(entry) for entry in raw_data]

        output_filename = f"transed_{prefix}_{i}.json"
        output_path = os.path.join(output_dir, output_filename)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(formatted, f, ensure_ascii=False, indent=2)

        print(f"[✔] {input_path} → {output_path} 변환 완료")

# 실행 예시
if __name__ == "__main__":
    process_files_with_prefix(
        prefix="culture",
        input_dir="C:/WhereWeGo/place_data/Preprocessing_data",
        output_dir="C:/WhereWeGo/place_data/Transformed_data"
    )
