from pymongo import MongoClient

# 데이터베이스에서 필드 제거
def remove_fields():
    client = MongoClient("mongodb://localhost:27017")
    db = client["place_db"]  
    collection = db["tourism"] 

    fields_to_remove = {
        "place_url": "",
        "vector": "",
        "vector_method": "",
        "image_url": "",
        # "vector_version": "" 
    }

    result = collection.update_many({}, {"$unset": fields_to_remove})
    print(f"{result.modified_count} documents updated.")

if __name__ == "__main__":
    remove_fields()
