from fastapi import APIRouter, Request
from pydantic import BaseModel
from datetime import datetime
import json
import os

router = APIRouter()

LOG_PATH = "BPR/data/logs/click_logs.jsonl"  # 한 줄씩 저장

class ClickLog(BaseModel):
    user_id: str
    place_id: str
    timestamp: str  # ISO format preferred

@router.post("/log/click")
async def log_click(log: ClickLog):
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        json.dump(log.dict(), f, ensure_ascii=False)
        f.write("\n")
    return {"status": "success"}
