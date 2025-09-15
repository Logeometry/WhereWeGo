# services/cache_service.py
"""
근처 장소 조회 API용 캐싱 서비스
Redis를 사용한 고성능 캐싱으로 응답 시간 대폭 단축
"""

import json
import hashlib
from typing import Optional, Any, Dict, List
from datetime import timedelta
import redis
import os
from dotenv import load_dotenv

load_dotenv()

class CacheService:
    def __init__(self):
        # Redis 연결 설정 (환경변수에서 가져오기)
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        try:
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            # 연결 테스트
            self.redis_client.ping()
            print("✅ Redis 캐시 서비스 연결 성공")
        except Exception as e:
            print(f"⚠️ Redis 연결 실패, 메모리 캐시 사용: {e}")
            self.redis_client = None
            # 메모리 기반 캐시 딕셔너리
            self._memory_cache: Dict[str, Dict] = {}
    
    def _generate_cache_key(self, prefix: str, place_id: str, max_distance: float, **kwargs) -> str:
        """캐시 키 생성"""
        params = f"{place_id}:{max_distance}"
        if kwargs:
            params += ":" + ":".join(f"{k}={v}" for k, v in sorted(kwargs.items()))
        
        # 해시화로 키 길이 제한
        hash_suffix = hashlib.md5(params.encode()).hexdigest()[:8]
        return f"nearby:{prefix}:{hash_suffix}"
    
    async def get_cached_result(self, prefix: str, place_id: str, max_distance: float, **kwargs) -> Optional[Any]:
        """캐시된 결과 조회"""
        cache_key = self._generate_cache_key(prefix, place_id, max_distance, **kwargs)
        
        try:
            if self.redis_client:
                # Redis 캐시에서 조회
                cached_data = self.redis_client.get(cache_key)
                if cached_data:
                    return json.loads(cached_data)
            else:
                # 메모리 캐시에서 조회
                if cache_key in self._memory_cache:
                    cache_entry = self._memory_cache[cache_key]
                    # 만료 시간 확인 (메모리 캐시용)
                    import time
                    if time.time() < cache_entry['expires_at']:
                        return cache_entry['data']
                    else:
                        del self._memory_cache[cache_key]
        except Exception as e:
            print(f"캐시 조회 오류: {e}")
        
        return None
    
    async def set_cached_result(self, prefix: str, place_id: str, max_distance: float, data: Any, ttl_seconds: int = 300, **kwargs):
        """결과를 캐시에 저장 (기본 5분 TTL)"""
        cache_key = self._generate_cache_key(prefix, place_id, max_distance, **kwargs)
        
        try:
            # 직렬화 가능한 형태로 변환
            if hasattr(data, 'dict'):
                # Pydantic 모델의 경우
                serializable_data = [item.dict() for item in data] if isinstance(data, list) else data.dict()
            elif isinstance(data, list) and all(hasattr(item, 'dict') for item in data):
                serializable_data = [item.dict() for item in data]
            else:
                serializable_data = data
            
            if self.redis_client:
                # Redis에 저장
                self.redis_client.setex(
                    cache_key, 
                    ttl_seconds, 
                    json.dumps(serializable_data, ensure_ascii=False, default=str)
                )
            else:
                # 메모리 캐시에 저장
                import time
                self._memory_cache[cache_key] = {
                    'data': serializable_data,
                    'expires_at': time.time() + ttl_seconds
                }
                
                # 메모리 캐시 크기 제한 (최대 1000개 항목)
                if len(self._memory_cache) > 1000:
                    # 가장 오래된 항목 제거
                    oldest_key = min(self._memory_cache.keys(), 
                                   key=lambda k: self._memory_cache[k]['expires_at'])
                    del self._memory_cache[oldest_key]
                    
        except Exception as e:
            print(f"캐시 저장 오류: {e}")
    
    async def invalidate_cache(self, prefix: str, place_id: str = None):
        """캐시 무효화"""
        try:
            if self.redis_client:
                if place_id:
                    # 특정 장소 관련 캐시만 삭제
                    pattern = f"nearby:{prefix}:*{place_id}*"
                    keys = self.redis_client.keys(pattern)
                    if keys:
                        self.redis_client.delete(*keys)
                else:
                    # 해당 prefix의 모든 캐시 삭제
                    pattern = f"nearby:{prefix}:*"
                    keys = self.redis_client.keys(pattern)
                    if keys:
                        self.redis_client.delete(*keys)
            else:
                # 메모리 캐시에서 패턴 매칭으로 삭제
                keys_to_delete = []
                search_pattern = f"nearby:{prefix}:"
                if place_id:
                    search_pattern += f"*{place_id}*"
                
                for key in self._memory_cache.keys():
                    if key.startswith(search_pattern):
                        keys_to_delete.append(key)
                
                for key in keys_to_delete:
                    del self._memory_cache[key]
                    
        except Exception as e:
            print(f"캐시 무효화 오류: {e}")

# 전역 캐시 서비스 인스턴스
cache_service = CacheService()


# 데코레이터 방식의 캐싱 유틸리티
def cached_nearby_api(prefix: str, ttl_seconds: int = 300):
    """근처 장소 API용 캐싱 데코레이터"""
    def decorator(func):
        async def wrapper(place_id: str, max_distance: float = 5.0, **kwargs):
            # 캐시 조회
            cached_result = await cache_service.get_cached_result(
                prefix, place_id, max_distance, **kwargs
            )
            
            if cached_result is not None:
                print(f"🚀 캐시 히트: {prefix} - {place_id}")
                return cached_result
            
            # 캐시 미스 - 실제 함수 실행
            print(f"💾 캐시 미스: {prefix} - {place_id}")
            result = await func(place_id, max_distance, **kwargs)
            
            # 결과를 캐시에 저장
            await cache_service.set_cached_result(
                prefix, place_id, max_distance, result, ttl_seconds, **kwargs
            )
            
            return result
        return wrapper
    return decorator
