from typing import List
from schemas import Tourism, LogData
from db import places_col, user_data_col, user_log_col 

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

