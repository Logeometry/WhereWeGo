import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

MONGO_ATLAS_URI: str = os.getenv("MONGO_ATLAS_URI", "")

_client: AsyncIOMotorClient = AsyncIOMotorClient(MONGO_ATLAS_URI)

_place_db = _client.get_database("place_db")
places_col = _place_db.get_collection("places")

_user_db = _client.get_database("user_db")
user_data_col     = _user_db.get_collection("user_data")
user_feedback_col = _user_db.get_collection("user_feedback")
user_log_col      = _user_db.get_collection("user_log")
user_review_col   = _user_db.get_collection("user_review")