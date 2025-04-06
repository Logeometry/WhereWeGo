import os
import json
from datetime import datetime

LOG_PATH = "BPR/data/logs/search_logs.jsonl"

def save_search_log(user_id: str, keyword: str):
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    log_data = {
        "user_id": user_id,
        "keyword": keyword,
        "timestamp": datetime.utcnow().isoformat()
    }
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        json.dump(log_data, f, ensure_ascii=False)
        f.write("\n")
