from fastapi import APIRouter, HTTPException, Body
from typing import List
import os
from pymongo import MongoClient
from services.data_converter import data_converter

# MongoDB 연결 (코스 조회용 - recommeded_cors_router와 호환)
MONGO_URI = os.getenv("MONGO_URI") or os.getenv("MONGO_ATLAS_URI", "mongodb://localhost:27017/")
try:
    client = MongoClient(MONGO_URI)
    db = client["wherewego"]
    courses_collection = db["courses"]
    print("✅ 코스 관리용 MongoDB 연결 성공")
except Exception as e:
    print(f"❌ 코스 관리용 MongoDB 연결 실패: {e}")
    courses_collection = None

router = APIRouter()

@router.delete("/courses/{course_id}")
async def delete_course(course_id: str):
    """
    코스를 삭제합니다.
    
    - **course_id**: 삭제할 코스 ID
    """
    if courses_collection is None:
        raise HTTPException(status_code=503, detail="데이터베이스 연결이 되어있지 않습니다.")
    
    try:
        result = courses_collection.delete_one({"course_id": course_id})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="코스를 찾을 수 없습니다.")
        
        return {
            "success": True,
            "message": "코스가 성공적으로 삭제되었습니다."
        }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"코스 삭제 중 오류 발생: {e}")
        raise HTTPException(status_code=500, detail=f"서버 내부 오류가 발생했습니다: {e}")

@router.put("/courses/{course_id}")
async def overwrite_course(course_id: str, course_data: dict = Body(...)):
    """
    코스를 완전히 덮어씁니다.
    
    - **course_id**: 덮어쓸 코스 ID
    - **course_data**: 새로운 코스 데이터
    """
    if courses_collection is None:
        raise HTTPException(status_code=503, detail="데이터베이스 연결이 되어있지 않습니다.")
    
    try:
        from datetime import datetime
        
        # 기존 코스가 있는지 확인
        existing_course = courses_collection.find_one({"course_id": course_id})
        if not existing_course:
            raise HTTPException(status_code=404, detail="코스를 찾을 수 없습니다.")
        
        # 새로운 코스 데이터에 메타데이터 추가
        course_data["course_id"] = course_id
        course_data["user_id"] = existing_course.get("user_id")  # 기존 사용자 ID 유지
        course_data["created_at"] = existing_course.get("created_at")  # 생성일 유지
        course_data["updated_at"] = datetime.utcnow()  # 업데이트 시간 갱신
        
        # 코스 덮어쓰기
        result = courses_collection.replace_one(
            {"course_id": course_id},
            course_data
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=500, detail="코스 업데이트에 실패했습니다.")
        
        return {
            "success": True,
            "message": "코스가 성공적으로 업데이트되었습니다.",
            "course_id": course_id
        }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"코스 덮어쓰기 중 오류 발생: {e}")
        raise HTTPException(status_code=500, detail=f"서버 내부 오류가 발생했습니다: {e}")

@router.get("/user/{user_id}")
async def get_user_courses(user_id: str):
    """
    특정 사용자의 저장된 코스 목록을 조회합니다.
    """
    if courses_collection is None:
        raise HTTPException(status_code=503, detail="데이터베이스 연결이 되어있지 않습니다.")
    
    try:
        # 사용자의 코스 목록 조회 (recommeded_cors_router와 동일한 구조)
        courses = list(courses_collection.find(
            {"user_id": user_id},
            {"course_id": 1, "course_name": 1, "created_at": 1, "updated_at": 1}
        ).sort("created_at", -1))
        
        # ObjectId를 문자열로 변환
        for course in courses:
            course["_id"] = str(course["_id"])
            course["created_at"] = course["created_at"].isoformat()
            course["updated_at"] = course["updated_at"].isoformat()
        
        return {
            "success": True,
            "courses": courses
        }
        
    except Exception as e:
        print(f"코스 조회 중 오류 발생: {e}")
        raise HTTPException(status_code=500, detail=f"서버 내부 오류가 발생했습니다: {e}")

@router.get("/course/{course_id}")
async def get_course_detail(course_id: str, format: str = "frontend"):
    """
    특정 코스의 상세 정보를 조회합니다.
    
    Args:
        course_id: 코스 ID
        format: 응답 형식 ("frontend" 또는 "backend", 기본값: "frontend")
    """
    if courses_collection is None:
        raise HTTPException(status_code=503, detail="데이터베이스 연결이 되어있지 않습니다.")
    
    try:
        # 코스 상세 정보 조회 (recommeded_cors_router와 동일한 구조)
        course = courses_collection.find_one({"course_id": course_id})
        
        if not course:
            raise HTTPException(status_code=404, detail="코스를 찾을 수 없습니다.")
        
        # ObjectId를 문자열로 변환
        course["_id"] = str(course["_id"])
        course["created_at"] = course["created_at"].isoformat()
        course["updated_at"] = course["updated_at"].isoformat()
        
        if format == "frontend":
            # 프론트엔드 형식으로 변환
            frontend_data = data_converter.convert_backend_to_frontend(course)
            return {
                "success": True,
                "course": course,  # 원본 데이터
                "itinerary": frontend_data  # 프론트엔드 형식 데이터
            }
        else:
            # 기존 백엔드 형식
            return {
                "success": True,
                "course": course
            }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"코스 상세 조회 중 오류 발생: {e}")
        raise HTTPException(status_code=500, detail=f"서버 내부 오류가 발생했습니다: {e}")

@router.get("/course/{course_id}/frontend")
async def get_course_for_frontend(course_id: str):
    """
    프론트엔드에서 바로 사용할 수 있는 형식으로 코스를 반환합니다.
    """
    if courses_collection is None:
        raise HTTPException(status_code=503, detail="데이터베이스 연결이 되어있지 않습니다.")
    
    try:
        # 코스 상세 정보 조회
        course = courses_collection.find_one({"course_id": course_id})
        
        if not course:
            raise HTTPException(status_code=404, detail="코스를 찾을 수 없습니다.")
        
        # 프론트엔드 형식으로 변환
        frontend_data = data_converter.convert_backend_to_frontend(course)
        
        return frontend_data  # 배열 형태로 직접 반환
        
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"프론트엔드용 코스 조회 중 오류 발생: {e}")
        raise HTTPException(status_code=500, detail=f"서버 내부 오류가 발생했습니다: {e}")
