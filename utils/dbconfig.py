import os
import time
import pymongo
from dotenv import load_dotenv

# .env 파일에서 환경 변수 로드
load_dotenv()

def get_db_connection_string():
    """
    MongoDB 연결 문자열 반환
    MongoDB Atlas URL을 우선적으로 사용하고, 없는 경우 로컬 설정 사용
    """
    # MongoDB Atlas URL 사용 (우선)
    mongo_atlas_url = os.getenv("MONGO_ATLAS_URL")
    if mongo_atlas_url:
        return mongo_atlas_url
        
    # 이하는 이전 로컬 연결 방식 (폴백)
    mongo_host = os.getenv("MONGO_HOST", "localhost")
    mongo_port = os.getenv("MONGO_PORT", "27017")
    mongo_user = os.getenv("MONGO_USER", "")
    mongo_pass = os.getenv("MONGO_PASS", "")
    mongo_db = os.getenv("MONGO_DB", "tourism_recommendation")
    
    # 인증이 필요한 경우 (사용자 이름과 비밀번호가 있는 경우)
    if mongo_user and mongo_pass:
        connection_string = f"mongodb://{mongo_user}:{mongo_pass}@{mongo_host}:{mongo_port}/{mongo_db}"
    else:
        connection_string = f"mongodb://{mongo_host}:{mongo_port}/{mongo_db}"
    
    return connection_string

def get_db_client(max_retries=3):
    """
    MongoDB 클라이언트 객체 반환 (타임아웃 및 재시도 로직 포함)
    - max_retries: 연결 실패 시 최대 재시도 횟수
    """
    connection_string = get_db_connection_string()
    
    # 타임아웃 설정
    server_timeout = int(os.getenv("MONGO_SERVER_TIMEOUT_MS", "5000"))
    connect_timeout = int(os.getenv("MONGO_CONNECT_TIMEOUT_MS", "10000"))
    socket_timeout = int(os.getenv("MONGO_SOCKET_TIMEOUT_MS", "30000"))
    
    options = {
        "serverSelectionTimeoutMS": server_timeout,
        "connectTimeoutMS": connect_timeout,
        "socketTimeoutMS": socket_timeout
    }
    
    # 재시도 로직
    retry_count = 0
    while retry_count < max_retries:
        try:
            client = pymongo.MongoClient(connection_string, **options)
            # 연결 테스트
            client.server_info()
            return client
        except pymongo.errors.ServerSelectionTimeoutError as e:
            retry_count += 1
            if retry_count >= max_retries:
                raise Exception(f"MongoDB 연결 실패 (최대 재시도 횟수 초과): {str(e)}")
            
            wait_time = 1 * (2 ** (retry_count - 1))  # 지수 백오프
            print(f"MongoDB 연결 재시도 중... ({retry_count}/{max_retries}) {wait_time}초 대기")
            time.sleep(wait_time)
    
    # 여기까지 오면 모든 재시도 실패
    raise Exception("MongoDB 연결 실패")

def get_db_name():
    """데이터베이스 이름 반환"""
    return os.getenv("MONGO_DB", "tourism_recommendation")

# MongoDB 연결 테스트 함수
def test_connection():
    """MongoDB 연결 테스트"""
    try:
        client = get_db_client(max_retries=1)
        server_info = client.server_info()
        print(f"MongoDB 연결 성공: {server_info.get('version', 'unknown')}")
        return True
    except Exception as e:
        print(f"MongoDB 연결 실패: {str(e)}")
        return False

if __name__ == "__main__":
    # 직접 실행 시 연결 테스트 실행
    test_connection()
