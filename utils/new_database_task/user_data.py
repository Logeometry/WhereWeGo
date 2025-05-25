from pymongo import MongoClient, ASCENDING
from datetime import datetime

# MongoDB 연결
client = MongoClient("mongodb://localhost:27017")
db = client["user_db"]  # 사용자 DB

# 1. user_data
db.create_collection("user_data")
db["user_data"].create_index([("email", ASCENDING), ("oauth", ASCENDING)], unique=True)
db["user_data"].create_index("user_id", unique=True)

# 예시 문서 (필요 시 삭제)
db["user_data"].insert_one({
    "user_id": "uuid-sample-001",
    "oauth": "kakao",
    "email": "sample@kakao.com",
    "created_at": datetime.utcnow(),
    "preference_vector": [],
    "wishlist": [],
})


# 2. user_review
db.create_collection("user_review")
db["user_review"].create_index("user_id")
db["user_review"].create_index("place_id")

# 예시 문서
db["user_review"].insert_one({
    "user_id": "uuid-sample-001",
    "place_id": "PLACE_OBJECT_ID",
    "rating": 4.5,
    "comment": "멋진 장소였어요!",
    "created_at": datetime.utcnow()
})


# 3. user_log
db.create_collection("user_log")
db["user_log"].create_index("user_id")
db["user_log"].create_index("event")

# 예시 문서
db["user_log"].insert_one({
    "user_id": "uuid-sample-001",
    "event": "click",
    "target_id": "PLACE_OBJECT_ID",
    "timestamp": datetime.utcnow()
})


# 4. user_feedback
db.create_collection("user_feedback")
db["user_feedback"].create_index("user_id")
db["user_feedback"].create_index("place_id")

# 예시 문서
db["user_feedback"].insert_one({
    "user_id": "uuid-sample-001",
    "place_id": "PLACE_OBJECT_ID",
    "feedback": "like",  # or "neutral", "dislike"
    "created_at": datetime.utcnow()
})

print("USERDB 초기화 완료.")
