from pymongo import MongoClient
from pprint import pprint

client = MongoClient("mongodb://localhost:27017")
db = client["place_db"]
collection = db["tourism"]

pipeline = [
    {
        "$group": {
            "_id": "$category",
            "category_groups": { "$addToSet": "$category_group" }
        }
    },
    {
        "$project": {
            "_id": 0,
            "category": "$_id",
            "category_groups": 1
        }
    }
]

result = list(collection.aggregate(pipeline))
pprint(result)
