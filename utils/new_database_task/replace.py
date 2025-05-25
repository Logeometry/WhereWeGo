from pymongo import MongoClient

# MongoDB 연결
client = MongoClient("mongodb://localhost:27017")
db = client["place_db"]
collection = db["tourism"]

# 문서 순회
for doc in collection.find():
    reordered = {
        "name": doc.get("name"),
        "category": doc.get("category"),
        "category_group": doc.get("category_group"),
        "category_onehot": doc.get("category_onehot"),
        "tags": doc.get("tags", []),
        "description": doc.get("description", ""),
        "address": doc.get("address", ""),
        "region": doc.get("region", ""),
        "location": doc.get("location"),
        "rating": doc.get("rating", 0),
        "review_count": doc.get("review_count", 0),
        "visitors_count": doc.get("visitors_count", 0),
        "pretrained_vector": doc.get("pretrained_vector"),
        "vector_full": doc.get("vector_full"),
        "vector_version": doc.get("vector_version", 0),
        "created_at": doc.get("created_at"),
        "updated_at": doc.get("updated_at")
    }

    # 기존 문서 대체
    collection.replace_one({"_id": doc["_id"]}, reordered)

print("모든 문서가 정해진 필드 순서로 재정렬되었습니다.")


"""
image_url
"https://search.pstatic.net/common/?src=https%3A%2F%2Fdbscthumb-phinf.p…"

"""