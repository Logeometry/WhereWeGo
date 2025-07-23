import os
from dotenv import load_dotenv
from pymongo import MongoClient
from motor.motor_asyncio import AsyncIOMotorClient
# from pymongo.errors import PyMongoError
from bson import ObjectId
from typing import List

# .env 파일에서 환경 변수 로드
load_dotenv()

# --- MongoDB 설정 ---
MONGO_DB_URL = os.getenv("MONGO_ATLAS_URI")
if not MONGO_DB_URL:
    raise ValueError("MONGO_DB_URL 환경변수를 설정해주세요.")

try:
    # 애플리케이션 실행 시 MongoDB 클라이언트 연결
    client = AsyncIOMotorClient(MONGO_DB_URL)
    # 'place_db' 데이터베이스 사용
    db = client.place_db
    # 'tourism' 컬렉션 사용
    tourism_collection = db.tourism
    # 'start_point' 컬렉션 사용
    starting_point_collection = db.starting_point
    # 'user_log' 컬렉션 사용
    user_log_collection = client.user_db.user_log
    # 서버 정보 확인으로 연결 테스트
    client.server_info()
    print("✅ MongoDB에 성공적으로 연결되었습니다.")
except AsyncIOMotorClient.errors.PyMongoError as e:
    print(f"❌ MongoDB 연결에 실패했습니다: {e}")
    client = None
    tourism_collection = None


def get_random_places(count: int = 10) -> List[ObjectId]:
    """
    tourism 컬렉션에서 무작위로 N개의 관광지 _id를 가져옵니다.

    Args:
        count (int): 가져올 관광지의 수. 기본값은 10입니다.

    Returns:
        List[ObjectId]: 무작위로 선택된 관광지의 ObjectId 리스트.
                         연결 실패 또는 문서가 부족할 경우 빈 리스트를 반환합니다.
    """
    if tourism_collection is None:
        print("MongoDB 컬렉션에 연결되지 않아 랜덤 장소를 가져올 수 없습니다.")
        return []

    try:
        # $sample aggregation pipeline을 사용하여 무작위 문서를 가져옵니다.
        # $project를 사용해 _id 필드만 가져와 네트워크 부하를 줄입니다.
        pipeline = [
            {"$sample": {"size": count}},
            {"$project": {"_id": 1}}
        ]
        
        # aggregation 실행
        random_docs = list(tourism_collection.aggregate(pipeline))

        if not random_docs:
            print(f"경고: DB에서 랜덤 장소를 찾지 못했습니다. 컬렉션이 비어있을 수 있습니다.")
            return []
            
        # 결과에서 _id 값만 추출하여 리스트로 반환
        place_ids = [doc['_id'] for doc in random_docs]
        
        return place_ids

    except AsyncIOMotorClient.errors.PyMongoError as e:
        print(f"DB에서 랜덤 장소를 가져오는 중 오류 발생: {e}")
        return []

 # --- 테스트용 코드 ---
# if __name__ == "__main__":
#    random_ids = get_random_places(5)
#    if random_ids:
#        print(f"랜덤으로 선택된 장소 ID ({len(random_ids)}개):")
#        for pid in random_ids:
#            print(pid)