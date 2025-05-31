# clilk 시, 해당 item에 대한 click log 저장
import os
import json
from datetime import datetime
import uuid
from schemas import User_log

CLICK_PATH = "data/click_logs.json"

def save_click_log(user_id: str, target_id: str):
    os.makedirs(os.path.dirname(CLICK_PATH), exist_ok=True)
    log_data = {
        "user_id" : user_id,
        "event": "click",
        "taget_id": target_id,
        "timestamp": datetime.utcnow().isoformat()
    }
    with open(CLICK_PATH, "a", encoding="utf-8") as f:
        json.dump(log_data, f, ensure_ascii=False)
        f.write("\n")