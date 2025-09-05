import os
import json
from datetime import datetime
from typing import List, Dict, Optional
from bson import ObjectId
from pymongo import MongoClient
from fastapi import HTTPException

from schemas import (
    AddPlaceToCourseRequest, 
    UpdatePlaceInCourseRequest, 
    RemovePlaceFromCourseRequest,
    CourseResponse,
    CourseDay,
    CoursePlace,
    Place
)
from services.db_handler import tourism_collection

class CourseService:
    def __init__(self):
        # MongoDB 연결
        mongo_uri = os.getenv("MONGO_ATLAS_URI")  # 환경변수명 통일
        if not mongo_uri:
            raise ValueError("MONGO_ATLAS_URI 환경변수가 설정되지 않았습니다.")
        self.client = MongoClient(mongo_uri)
        self.db = self.client.wherewego
        self.courses_collection = self.db.courses
        
    async def add_place_to_course(self, request: AddPlaceToCourseRequest) -> CourseResponse:
        """코스에 장소를 추가합니다."""
        try:
            # 코스 존재 확인
            course = self.courses_collection.find_one({"_id": ObjectId(request.course_id)})
            if not course:
                raise HTTPException(status_code=404, detail="코스를 찾을 수 없습니다.")
            
            # 장소 존재 확인
            place = tourism_collection.find_one({"_id": ObjectId(request.place_id)})
            if not place:
                raise HTTPException(status_code=404, detail="장소를 찾을 수 없습니다.")
            
            # 일정 데이터 파싱
            daily_schedule = course.get("dailySchedule", [])
            
            # 요청된 날짜가 존재하는지 확인
            if request.day > len(daily_schedule):
                raise HTTPException(status_code=400, detail=f"요청된 날짜({request.day})가 코스 기간({len(daily_schedule)})을 초과합니다.")
            
            # 해당 날짜의 장소 목록 가져오기
            day_index = request.day - 1
            day_schedule = daily_schedule[day_index]
            places = day_schedule.get("places", [])
            
            # 위치 유효성 검사
            if request.position > len(places):
                raise HTTPException(status_code=400, detail=f"요청된 위치({request.position})가 해당 날짜의 장소 수({len(places)})를 초과합니다.")
            
            # 새 장소 정보 생성
            new_place = {
                "_id": request.place_id,
                "estimated_duration": request.estimated_duration,
                "travel_time_from_previous": request.travel_time_from_previous
            }
            
            # 장소를 지정된 위치에 삽입
            places.insert(request.position, new_place)
            
            # 이동 시간 재계산 (삽입된 장소 이후의 장소들)
            for i in range(request.position + 1, len(places)):
                # 기본 이동 시간 설정 (실제로는 거리 계산이 필요하지만 여기서는 기본값 사용)
                places[i]["travel_time_from_previous"] = 30
            
            # 업데이트된 일정을 코스에 저장
            daily_schedule[day_index]["places"] = places
            
            # MongoDB 업데이트
            result = self.courses_collection.update_one(
                {"_id": ObjectId(request.course_id)},
                {
                    "$set": {
                        "dailySchedule": daily_schedule,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            if result.modified_count == 0:
                raise HTTPException(status_code=500, detail="코스 업데이트에 실패했습니다.")
            
            # 업데이트된 코스 반환
            return await self.get_course_by_id(request.course_id)
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"장소 추가 중 오류가 발생했습니다: {str(e)}")
    
    async def update_place_in_course(self, request: UpdatePlaceInCourseRequest) -> CourseResponse:
        """코스 내 장소 정보를 수정합니다."""
        try:
            # 코스 존재 확인
            course = self.courses_collection.find_one({"_id": ObjectId(request.course_id)})
            if not course:
                raise HTTPException(status_code=404, detail="코스를 찾을 수 없습니다.")
            
            # 일정 데이터 파싱
            daily_schedule = course.get("dailySchedule", [])
            
            # 요청된 날짜가 존재하는지 확인
            if request.day > len(daily_schedule):
                raise HTTPException(status_code=400, detail=f"요청된 날짜({request.day})가 코스 기간({len(daily_schedule)})을 초과합니다.")
            
            # 해당 날짜의 장소 목록 가져오기
            day_index = request.day - 1
            day_schedule = daily_schedule[day_index]
            places = day_schedule.get("places", [])
            
            # 위치 유효성 검사
            if request.position >= len(places):
                raise HTTPException(status_code=400, detail=f"요청된 위치({request.position})가 해당 날짜의 장소 수({len(places)})를 초과합니다.")
            
            # 장소 ID 확인
            target_place = places[request.position]
            if target_place.get("_id") != request.place_id:
                raise HTTPException(status_code=400, detail="지정된 위치의 장소 ID가 일치하지 않습니다.")
            
            # 업데이트할 필드들
            update_fields = {}
            if request.estimated_duration is not None:
                update_fields["estimated_duration"] = request.estimated_duration
            if request.travel_time_from_previous is not None:
                update_fields["travel_time_from_previous"] = request.travel_time_from_previous
            
            # 장소 정보 업데이트
            for field, value in update_fields.items():
                places[request.position][field] = value
            
            # 업데이트된 일정을 코스에 저장
            daily_schedule[day_index]["places"] = places
            
            # MongoDB 업데이트
            result = self.courses_collection.update_one(
                {"_id": ObjectId(request.course_id)},
                {
                    "$set": {
                        "dailySchedule": daily_schedule,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            if result.modified_count == 0:
                raise HTTPException(status_code=500, detail="코스 업데이트에 실패했습니다.")
            
            # 업데이트된 코스 반환
            return await self.get_course_by_id(request.course_id)
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"장소 수정 중 오류가 발생했습니다: {str(e)}")
    
    async def remove_place_from_course(self, request: RemovePlaceFromCourseRequest) -> CourseResponse:
        """코스에서 장소를 제거합니다."""
        try:
            # 코스 존재 확인
            course = self.courses_collection.find_one({"_id": ObjectId(request.course_id)})
            if not course:
                raise HTTPException(status_code=404, detail="코스를 찾을 수 없습니다.")
            
            # 일정 데이터 파싱
            daily_schedule = course.get("dailySchedule", [])
            
            # 요청된 날짜가 존재하는지 확인
            if request.day > len(daily_schedule):
                raise HTTPException(status_code=400, detail=f"요청된 날짜({request.day})가 코스 기간({len(daily_schedule)})을 초과합니다.")
            
            # 해당 날짜의 장소 목록 가져오기
            day_index = request.day - 1
            day_schedule = daily_schedule[day_index]
            places = day_schedule.get("places", [])
            
            # 위치 유효성 검사
            if request.position >= len(places):
                raise HTTPException(status_code=400, detail=f"요청된 위치({request.position})가 해당 날짜의 장소 수({len(places)})를 초과합니다.")
            
            # 장소 ID 확인
            target_place = places[request.position]
            if target_place.get("_id") != request.place_id:
                raise HTTPException(status_code=400, detail="지정된 위치의 장소 ID가 일치하지 않습니다.")
            
            # 장소 제거
            places.pop(request.position)
            
            # 이동 시간 재계산 (제거된 장소 이후의 장소들)
            for i in range(request.position, len(places)):
                # 기본 이동 시간 설정
                places[i]["travel_time_from_previous"] = 30
            
            # 업데이트된 일정을 코스에 저장
            daily_schedule[day_index]["places"] = places
            
            # MongoDB 업데이트
            result = self.courses_collection.update_one(
                {"_id": ObjectId(request.course_id)},
                {
                    "$set": {
                        "dailySchedule": daily_schedule,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            if result.modified_count == 0:
                raise HTTPException(status_code=500, detail="코스 업데이트에 실패했습니다.")
            
            # 업데이트된 코스 반환
            return await self.get_course_by_id(request.course_id)
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"장소 제거 중 오류가 발생했습니다: {str(e)}")
    
    async def get_course_by_id(self, course_id: str) -> CourseResponse:
        """코스 ID로 코스를 조회합니다."""
        try:
            course = self.courses_collection.find_one({"_id": ObjectId(course_id)})
            if not course:
                raise HTTPException(status_code=404, detail="코스를 찾을 수 없습니다.")
            
            # 장소 상세 정보 조회
            daily_schedule = []
            for day_schedule in course.get("dailySchedule", []):
                places = []
                for place_info in day_schedule.get("places", []):
                    # 장소 상세 정보 조회
                    place_details = None
                    if place_info.get("_id"):
                        place_detail = tourism_collection.find_one({"_id": ObjectId(place_info["_id"])})
                        if place_detail:
                            place_details = Place(
                                id=str(place_detail["_id"]),
                                name=place_detail["name"],
                                description=place_detail.get("description"),
                                address=place_detail["address"],
                                location=place_detail["location"],
                                estimated_duration=place_info.get("estimated_duration", 2),
                                travel_time_from_previous=place_info.get("travel_time_from_previous", 20)
                            )
                    
                    course_place = CoursePlace(
                        place_id=place_info["_id"],
                        estimated_duration=place_info.get("estimated_duration", 2),
                        travel_time_from_previous=place_info.get("travel_time_from_previous", 20),
                        place_details=place_details
                    )
                    places.append(course_place)
                
                course_day = CourseDay(
                    day=day_schedule["day"],
                    date=day_schedule["date"],
                    places=places
                )
                daily_schedule.append(course_day)
            
            return CourseResponse(
                course_id=str(course["_id"]),
                dailySchedule=daily_schedule,
                travelTips=course.get("travelTips", ""),
                created_at=course.get("created_at", datetime.utcnow()),
                updated_at=course.get("updated_at", datetime.utcnow())
            )
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"코스 조회 중 오류가 발생했습니다: {str(e)}")

# 서비스 인스턴스 생성
course_service = CourseService()
