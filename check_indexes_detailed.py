#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

async def check_indexes_detailed():
    load_dotenv()
    client = AsyncIOMotorClient(os.getenv('MONGO_ATLAS_URI'))
    place_db = client.get_database('place_db')
    
    print("🔍 MongoDB 인덱스 상세 확인...")
    
    for col_name in ['tourism', 'cafe', 'restaurant']:
        collection = place_db.get_collection(col_name)
        
        # 컬렉션 통계
        try:
            stats = await place_db.command('collStats', col_name)
            doc_count = stats.get('count', 0)
            index_count = stats.get('nindexes', 0)
        except:
            doc_count = await collection.count_documents({})
            index_count = "unknown"
        
        print(f'\n📊 {col_name} 컬렉션:')
        print(f'   문서 수: {doc_count:,}')
        print(f'   총 인덱스 수: {index_count}')
        
        # 인덱스 목록
        indexes = await collection.list_indexes().to_list(length=None)
        print(f'   인덱스 목록:')
        for idx in indexes:
            name = idx.get('name', 'Unknown')
            key = idx.get('key', {})
            print(f'     • {name}')
            print(f'       키: {key}')
            if '2dsphere' in str(key):
                print(f'       ✅ 지리적 인덱스!')
    
    client.close()
    print("\n✅ 인덱스 확인 완료")

if __name__ == "__main__":
    asyncio.run(check_indexes_detailed())
