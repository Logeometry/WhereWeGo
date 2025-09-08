from typing import List
import json
from schemas import Tourism, LogData
from db import places_col, user_data_col, user_log_col 

def load_logs_data_from_json(file_path: str) -> List[dict]:
    """JSON 파일에서 로그 데이터를 로드합니다."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

async def load_location_data_from_db() -> List[Tourism]:
    results: List[Tourism] = []
    cursor = places_col.find({})
    async for doc in cursor:
        doc['_id'] = str(doc['_id'])
        results.append(Tourism(**doc))
    return results

async def load_logs_data_from_db() -> List[LogData]:
    results: List[LogData] = []
    cursor = user_log_col.find({})
    async for doc in cursor:
        results.append(LogData(**doc))
    return results

# async def load_logs_data_from_db() -> List[LogData]:
#     results: List[LogData] = []
#     cursor = user_log_col.find({}) 
#     async for doc in cursor:
#         results.append(LogData(**doc))
#     return results

