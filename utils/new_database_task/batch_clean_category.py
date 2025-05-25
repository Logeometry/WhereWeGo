import os
import json

def transform_place(entry):
    # category_name의 마지막 단어만 추출
    if "category_name" in entry and entry["category_name"]:
        parts = entry["category_name"].split("»")
        entry["category_name"] = parts[-1].strip()
    return entry

def process_files_with_prefix(prefix, input_dir, output_dir):
    os.makedirs(output_dir, exist_ok=True)

    for i in range(20):  # 최대 20개까지 처리
        filename = f"{prefix}_{i}.json"
        input_path = os.path.join(input_dir, filename)
        if not os.path.exists(input_path):
            continue

        with open(input_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        formatted = [transform_place(entry) for entry in raw_data]
        output_filename = f"cleaned_{prefix}_{i}.json"
        output_path = os.path.join(output_dir, output_filename)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(formatted, f, ensure_ascii=False, indent=2)

        print(f"[✔] {input_path} → {output_path} 변환 완료")

# 사용 예시 입출력 경로는 수정해서 사용
if __name__ == "__main__":
    process_files_with_prefix(
        prefix="restaurant",
        input_dir="C:\WhereWeGo\place_data",
        output_dir="C:\WhereWeGo\place_data\Preprocessing_data"
    )
