# clilk 시, 해당 item에 대한 click log 저장
import os
import json
from datetime import datetime

CLICK_PATH = "BPR/data/log/click_logs.jsonl"

def save_click_log(user_id: str, keword: str):
    os.makedirs(os.path.dirname(CLICK_PATH), exist_ok=True)
    log_data = {
        "user_id" : user_id,
        "item": item,
        "timestamp": datetime.utcnow().isoformat()
    }
    with open(CLICK_PATH, "a", encoding="uf-8") as f:
        json.dump(log_data, f, ensure=False)
        f.write("\n")