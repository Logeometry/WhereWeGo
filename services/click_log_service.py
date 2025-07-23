# clilk 시, 해당 item에 대한 click log 저장
from services.db_handler import user_log_collection
from datetime import datetime, timezone
from schemas import User_log

async def save_click_log(user_id: str, target_id: str):
    # click log를 DB에 저장
    # print(f"click log 저장 시작: {user_id}, {target_id}")
    if user_log_collection is None:
        # print("MongDB user_log 컬렉션 연결 실패")
        return False
    log_data = User_log(
        user_id=user_id,
        event="click",
        target_id=target_id,
        timestamp=datetime.now(timezone.utc)
    )
    try: 
        result = await user_log_collection.insert_one(log_data.dict())
        # print(f"click log 저장 성공: {result.inserted_id}")
        return True
    except Exception as e:
        # print(f"click log 저장 실패: {e}")
        return False

# CLICK_PATH = "data/click_logs.json"

# def save_click_log(user_id: str, target_id: str):
#     os.makedirs(os.path.dirname(CLICK_PATH), exist_ok=True)
#     log_data = {
#         "user_id" : user_id,
#         "event": "click",
#         "taget_id": target_id,
#         "timestamp": datetime.utcnow().isoformat()
#     }
#     with open(CLICK_PATH, "a", encoding="utf-8") as f:
#         json.dump(log_data, f, ensure_ascii=False)
#         f.write("\n")