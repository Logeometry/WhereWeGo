from typing import List, Dict, Optional
import json
import os
import sys
from schemas import Tourism, LogData
from services.db_handler import tourism_collection, user_log_collection

# 상위 디렉토리를 Python 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

def load_logs_data_from_json(file_path: str) -> List[dict]:
    """JSON 파일에서 로그 데이터를 로드합니다."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def load_tourism_data_from_json() -> Optional[Dict]:
    """관광지 데이터를 JSON 파일에서 로드 (1.localserver.py와 동일)"""
    try:
        # 여러 경로에서 데이터 파일 찾기
        file_paths = [
            'sort3Wpreference.json',
            os.path.join(parent_dir, 'model', 'sort3Wpreference.json'),
            os.path.join(parent_dir, 'model', 'ncf_inner', 'sort3Wpreference.json'),
            'C:/Users/user/Desktop/새 폴더 (2)/.vscode/WhereWeGo-backend/model/sort3Wpreference.json'
        ]
        
        for file_path in file_paths:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    print(f"✅ 관광지 데이터 로드 성공: {file_path}")
                    return data
            except FileNotFoundError:
                continue
        
        print("❌ 관광지 데이터 파일을 찾을 수 없습니다.")
        return None
    except Exception as e:
        print(f"관광지 데이터 로드 오류: {e}")
        return None

def get_tourism_data_in_tester_format(tourism_data: Optional[Dict] = None) -> Dict:
    """tester.py 형식으로 관광지 데이터를 변환 (1.localserver.py와 동일)"""
    if not tourism_data:
        tourism_data = load_tourism_data_from_json()
    
    if not tourism_data:
        return {}
    
    # tester.py 형식으로 변환: {index: {name, category, category_group, ...}}
    tourism_dict = {}
    for group in tourism_data.get('groups', []):
        for item in group.get('items', []):
            if 'index' in item and 'name' in item:
                tourism_dict[item['index']] = {
                    'name': item['name'],
                    'category': item.get('category', ''),
                    'category_group': item.get('category_group', ''),
                    'popular_score': item.get('popular_score', 0),
                    'visitors_count': item.get('visitors_count', 0),
                    'final_score': item.get('final_score', 0)
                }
    return tourism_dict

async def load_location_data_from_db() -> List[Tourism]:
    """MongoDB에서 관광지 데이터를 로드"""
    results: List[Tourism] = []
    cursor = tourism_collection.find({})
    async for doc in cursor:
        doc['_id'] = str(doc['_id'])
        results.append(Tourism(**doc))
    return results

async def load_logs_data_from_db() -> List[LogData]:
    """MongoDB에서 로그 데이터를 로드"""
    results: List[LogData] = []
    cursor = user_log_collection.find({})
    async for doc in cursor:
        results.append(LogData(**doc))
    return results

async def get_random_places_from_db(count: int = 10) -> List[Dict]:
    """MongoDB에서 랜덤한 관광지들을 가져오기"""
    try:
        pipeline = [
            {"$sample": {"size": count}},
            {"$project": {
                "_id": 1,
                "name": 1,
                "category": 1,
                "category_group": 1,
                "address": 1,
                "location": 1,
                "final_score": 1,
                "visitors_count": 1
            }}
        ]
        
        places_cursor = tourism_collection.aggregate(pipeline)
        places = await places_cursor.to_list(length=count)
        
        # ObjectId를 문자열로 변환
        for place in places:
            place['_id'] = str(place['_id'])
        
        return places
    except Exception as e:
        print(f"랜덤 관광지 로드 오류: {e}")
        return []

async def get_places_by_category(category_group: str, limit: int = 50) -> List[Dict]:
    """카테고리별로 관광지들을 가져오기"""
    try:
        cursor = tourism_collection.find(
            {"category_group": category_group}
        ).limit(limit)
        
        places = await cursor.to_list(length=limit)
        
        # ObjectId를 문자열로 변환
        for place in places:
            place['_id'] = str(place['_id'])
        
        return places
    except Exception as e:
        print(f"카테고리별 관광지 로드 오류: {e}")
        return []

async def get_places_by_final_score(min_score: float = 2.0, limit: int = 50) -> List[Dict]:
    """final_score 기준으로 관광지들을 가져오기"""
    try:
        cursor = tourism_collection.find(
            {"final_score": {"$gte": min_score}}
        ).sort("final_score", -1).limit(limit)
        
        places = await cursor.to_list(length=limit)
        
        # ObjectId를 문자열로 변환
        for place in places:
            place['_id'] = str(place['_id'])
        
        return places
    except Exception as e:
        print(f"점수별 관광지 로드 오류: {e}")
        return []

