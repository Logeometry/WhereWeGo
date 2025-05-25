import json
from pymongo import MongoClient

def insert_json_to_mongodb(json_file_path, db_name="place_db", collection_name="tourism"):
    # 1. MongoDB 연결
    client = MongoClient("mongodb://localhost:27017/")
    db = client[db_name]
    collection = db[collection_name]

    # 2. JSON 파일 로드
    with open(json_file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 3. 삽입
    if isinstance(data, list):
        collection.insert_many(data)
        print(f" {len(data)}개 문서 삽입 완료")
    elif isinstance(data, dict):
        collection.insert_one(data)
        print(" 1개 문서 삽입 완료")
    else:
        print(" 올바르지 않은 JSON 구조입니다.")

# 실행 예시
if __name__ == "__main__":
    insert_json_to_mongodb("C:/WhereWeGo/place_data/Transformed_data/transed_culture_0.json")
