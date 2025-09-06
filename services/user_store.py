import os
from typing import Optional, Dict
from pymongo import MongoClient
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

MONGO_ATLAS_URI: str = os.getenv("MONGO_ATLAS_URI", "")
_client = MongoClient(MONGO_ATLAS_URI)
_user_db = _client.get_database("user_db")
user_data_col = _user_db.get_collection("user_data")


def find_user_by_id(user_id: str) -> Optional[Dict]:
    print(f"[DEBUG] find_user_by_id called with: {user_id}")
    user = user_data_col.find_one({"user_id": user_id})
    if user:
        print(f"[DEBUG] User found: {user}")
        return user
    print(f"[DEBUG] User not found for ID: {user_id}")
    return None


def find_user_by_email(email: str) -> Optional[Dict]:
    return user_data_col.find_one({"email": email})


def find_user_by_oauth(oauth: str, oauth_id: str) -> Optional[Dict]:
    print(f"[DEBUG] find_user_by_oauth called with: oauth={oauth}, oauth_id={oauth_id}")
    user = user_data_col.find_one({"oauth": oauth, "oauth_id": oauth_id})
    if user:
        print(f"[DEBUG] Existing user found: {user}")
    else:
        print(f"[DEBUG] No existing user found for oauth={oauth}, oauth_id={oauth_id}")
    return user


def add_user(user: Dict) -> None:
    print(f"[DEBUG] add_user called with: {user}")
    result = user_data_col.insert_one(user)
    print(f"[DEBUG] User saved successfully with ID: {result.inserted_id}")


def update_user_refresh_token(user_id: str, refresh_token: str) -> None:
    """사용자의 리프레시 토큰을 업데이트"""
    print(f"[DEBUG] update_user_refresh_token called with user_id: {user_id}")
    result = user_data_col.update_one(
        {"user_id": user_id},
        {"$set": {"refresh_token": refresh_token, "updated_at": datetime.utcnow().isoformat()}}
    )
    print(f"[DEBUG] Refresh token updated: {result.modified_count} documents modified")


def get_user_refresh_token(user_id: str) -> Optional[str]:
    """사용자의 리프레시 토큰을 조회"""
    print(f"[DEBUG] get_user_refresh_token called with user_id: {user_id}")
    user = user_data_col.find_one({"user_id": user_id}, {"refresh_token": 1})
    if user and "refresh_token" in user:
        print(f"[DEBUG] Refresh token found for user: {user_id}")
        return user["refresh_token"]
    print(f"[DEBUG] No refresh token found for user: {user_id}")
    return None