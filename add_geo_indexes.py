#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MongoDB 지리적 인덱스 추가 스크립트
근처 장소 조회 API 성능 최적화를 위한 2dsphere 인덱스 생성
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

async def create_geo_indexes():
    """MongoDB 컬렉션에 지리적 인덱스를 추가합니다."""
    
    MONGO_ATLAS_URI = os.getenv("MONGO_ATLAS_URI", "")
    if not MONGO_ATLAS_URI:
        print("❌ MONGO_ATLAS_URI 환경변수가 설정되지 않았습니다.")
        return
    
    client = AsyncIOMotorClient(MONGO_ATLAS_URI)
    place_db = client.get_database("place_db")
    
    collections = {
        "tourism": place_db.get_collection("tourism"),
        "cafe": place_db.get_collection("cafe"), 
        "restaurant": place_db.get_collection("restaurant")
    }
    
    print("🚀 MongoDB 지리적 인덱스 생성 시작...")
    
    for col_name, collection in collections.items():
        try:
            print(f"\n📍 {col_name} 컬렉션 처리 중...")
            
            # 기존 인덱스 확인
            existing_indexes = await collection.list_indexes().to_list(length=None)
            has_geo_index = any("location_2dsphere" in idx.get("name", "") for idx in existing_indexes)
            
            if has_geo_index:
                print(f"  ✅ {col_name}에 이미 지리적 인덱스가 존재합니다.")
                continue
            
            # 2dsphere 인덱스 생성
            result = await collection.create_index(
                [("location", "2dsphere")],
                name=f"location_2dsphere_{col_name}",
                background=True
            )
            print(f"  ✅ {col_name} 지리적 인덱스 생성 완료: {result}")
            
            # 좌표 데이터 통계 확인
            total_docs = await collection.count_documents({})
            location_docs = await collection.count_documents({"location": {"$exists": True}})
            coords_docs = await collection.count_documents({"location.coordinates": {"$exists": True}})
            
            print(f"  📊 {col_name} 통계:")
            print(f"     총 문서 수: {total_docs:,}")
            print(f"     location 필드 보유: {location_docs:,} ({location_docs/total_docs*100:.1f}%)")
            print(f"     coordinates 보유: {coords_docs:,} ({coords_docs/total_docs*100:.1f}%)")
            
        except Exception as e:
            print(f"  ❌ {col_name} 인덱스 생성 실패: {e}")
    
    # 복합 인덱스도 추가 (카테고리 + 지리)
    try:
        print(f"\n📍 tourism 복합 인덱스 생성 중...")
        await collections["tourism"].create_index(
            [("category_group", 1), ("location", "2dsphere")],
            name="category_location_compound",
            background=True
        )
        print(f"  ✅ 카테고리-위치 복합 인덱스 생성 완료")
    except Exception as e:
        print(f"  ❌ 복합 인덱스 생성 실패: {e}")
    
    client.close()
    print("\n🎉 인덱스 생성 작업 완료!")

if __name__ == "__main__":
    asyncio.run(create_geo_indexes())
