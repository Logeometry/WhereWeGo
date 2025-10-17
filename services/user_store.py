import os
import hashlib
from typing import Optional, Dict
from pymongo import MongoClient
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

MONGO_ATLAS_URI: str = os.getenv("MONGO_ATLAS_URI", "mongodb://localhost:27017")

# MongoDB URI가 비어있는지 확인
if not MONGO_ATLAS_URI or MONGO_ATLAS_URI.strip() == "":
    MONGO_ATLAS_URI = "mongodb://localhost:27017"
    print("Warning: MONGO_ATLAS_URI not set, using default localhost connection")

try:
    _client = MongoClient(MONGO_ATLAS_URI, serverSelectionTimeoutMS=5000)
    # 연결 테스트
    _client.admin.command('ping')
    print("MongoDB 연결 성공")
except Exception as e:
    print(f"MongoDB 연결 실패: {e}")
    print("로컬 MongoDB를 사용합니다.")
    _client = MongoClient("mongodb://localhost:27017", serverSelectionTimeoutMS=5000)
_user_db = _client.get_database("user_db")
user_data_col = _user_db.get_collection("user_data")
blacklisted_tokens_col = _user_db.get_collection("blacklisted_tokens")


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
    # 리프레시 토큰 만료 시간을 1일 후로 설정
    refresh_token_expiry = datetime.utcnow() + timedelta(days=1)
    
    result = user_data_col.update_one(
        {"user_id": user_id},
        {
            "$set": {
                "refresh_token": refresh_token, 
                "refresh_token_expiry": refresh_token_expiry.isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
        }
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


def add_to_blacklist(token: str, user_id: str, reason: str = "logout") -> None:
    """JWT 토큰을 블랙리스트에 추가"""
    print(f"[DEBUG] add_to_blacklist called with user_id: {user_id}, reason: {reason}")
    
    # JWT 토큰에서 만료 시간 추출
    try:
        from jose import jwt
        payload = jwt.decode(token, options={"verify_signature": False})
        expires_at = datetime.fromtimestamp(payload.get("exp", 0))
    except:
        # 토큰 파싱 실패 시 기본값 사용
        expires_at = datetime.utcnow() + timedelta(hours=2)
    
    # 토큰 해시 생성
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    
    # 블랙리스트에 추가
    blacklist_entry = {
        "token_hash": token_hash,
        "user_id": user_id,
        "expires_at": expires_at,
        "blacklisted_at": datetime.utcnow(),
        "reason": reason
    }
    
    result = blacklisted_tokens_col.insert_one(blacklist_entry)
    print(f"[DEBUG] Token added to blacklist with ID: {result.inserted_id}")


def is_token_blacklisted(token: str) -> bool:
    """JWT 토큰이 블랙리스트에 있는지 확인"""
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    
    # 블랙리스트에서 토큰 검색
    blacklisted_token = blacklisted_tokens_col.find_one({"token_hash": token_hash})
    
    if blacklisted_token:
        print(f"[DEBUG] Token found in blacklist: {token_hash[:20]}...")
        return True
    
    print(f"[DEBUG] Token not in blacklist: {token_hash[:20]}...")
    return False


def update_user_refresh_token_expiry(user_id: str, new_refresh_token: str) -> None:
    """사용자의 리프레시 토큰을 갱신 (다른 OAuth 제공자로 로그인 시)"""
    print(f"[DEBUG] update_user_refresh_token_expiry called with user_id: {user_id}")
    # 리프레시 토큰 만료 시간을 1일 후로 설정
    refresh_token_expiry = datetime.utcnow() + timedelta(days=1)
    
    result = user_data_col.update_one(
        {"user_id": user_id},
        {
            "$set": {
                "refresh_token": new_refresh_token,
                "refresh_token_expiry": refresh_token_expiry.isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "last_login": datetime.utcnow().isoformat()
            }
        }
    )
    print(f"[DEBUG] Refresh token updated: {result.modified_count} documents modified")


def is_refresh_token_expired(user_id: str) -> bool:
    """사용자의 리프레시 토큰이 만료되었는지 확인"""
    print(f"[DEBUG] is_refresh_token_expired called with user_id: {user_id}")
    user = user_data_col.find_one({"user_id": user_id}, {"refresh_token_expiry": 1})
    
    if not user or "refresh_token_expiry" not in user:
        print(f"[DEBUG] No refresh token expiry found for user: {user_id}")
        return True  # 만료 시간이 없으면 만료된 것으로 간주
    
    try:
        expiry_time = datetime.fromisoformat(user["refresh_token_expiry"].replace('Z', '+00:00'))
        is_expired = datetime.utcnow() > expiry_time
        print(f"[DEBUG] Refresh token expiry: {expiry_time}, Current: {datetime.utcnow()}, Expired: {is_expired}")
        return is_expired
    except Exception as e:
        print(f"[DEBUG] Error parsing refresh token expiry: {e}")
        return True  # 파싱 오류 시 만료된 것으로 간주