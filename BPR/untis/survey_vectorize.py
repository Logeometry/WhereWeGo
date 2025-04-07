import json
import os

TRAVEL_TYPE = ["자연 및 아웃도어", "문화 및 역사", "도시 관광", "휴양 및 힐링", "모험 및 액티비티"]
CLIMATE = ["따뜻하고 습한 열대 기후", "따뜻하고 건조한 기후", "온화한 사계절 기후", "서늘하거나 추운 기후"]
DURATION = ["1-3일", "4-7일", "8-14일", "15일 이상"]
COMPANION = ["혼자 여행", "커플/부부", "가족(아이 포함)", "친구들과", "단체/투어"]
BUDGET = [1, 2, 3, 4, 5]

def vectorize(d):
    v = []
    v += [1 if d["travel_type"] == t else 0 for t in TRAVEL_TYPE]
    v += [1 if d["climate"] == c else 0 for c in CLIMATE]
    v += [1 if int(d["budget"]) == b else 0 for b in BUDGET]
    v += [1 if d["duration"] == dur else 0 for dur in DURATION]
    v += [1 if d["companion"] == c else 0 for c in COMPANION]
    return v

def save_vectors(survey, out_path):
    result = {d["username"]: vectorize(d) for d in survey if "username" in d}
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, separators=(",", ": "))

if __name__ == "__main__":
    base = os.path.dirname(os.path.abspath(__file__))
    root = os.path.abspath(os.path.join(base, "../../.."))
    input_path = os.path.join(root, "backend", "data", "survey_results.json")
    output_path = os.path.join(root, "backend", "BPR", "data", "training", "survey_vectors.json")

    try:
        with open(input_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            save_vectors(data, output_path)
    except Exception as e:
        print("error:", e)
