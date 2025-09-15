from fastapi import APIRouter, HTTPException, Body
from typing import List

from schemas import (
    AddPlaceToCourseRequest,
    UpdatePlaceInCourseRequest,
    RemovePlaceFromCourseRequest,
    CourseResponse
)
from services.data_converter import data_converter
from services.course_service import course_service

router = APIRouter()

@router.post("/courses/add-place", response_model=CourseResponse)
async def add_place_to_course(request: AddPlaceToCourseRequest = Body(...)):
    """
    코스에 장소를 추가합니다.
    
    - **course_id**: 코스 ID
    - **place_id**: 추가할 장소 ID
    - **day**: 추가할 날짜 (1부터 시작)
    - **position**: 해당 날짜 내에서의 위치 (0부터 시작)
    - **estimated_duration**: 예상 체류 시간 (시간 단위, 기본값: 2)
    - **travel_time_from_previous**: 이전 장소로부터의 이동 시간 (분 단위, 기본값: 20)
    """
    try:
        return await course_service.add_place_to_course(request)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"장소 추가 중 오류가 발생했습니다: {str(e)}")

@router.put("/courses/update-place", response_model=CourseResponse)
async def update_place_in_course(request: UpdatePlaceInCourseRequest = Body(...)):
    """
    코스 내 장소 정보를 수정합니다.
    
    - **course_id**: 코스 ID
    - **place_id**: 수정할 장소 ID
    - **day**: 장소가 있는 날짜
    - **position**: 해당 날짜 내에서의 위치
    - **estimated_duration**: 예상 체류 시간 (시간 단위, 선택사항)
    - **travel_time_from_previous**: 이전 장소로부터의 이동 시간 (분 단위, 선택사항)
    """
    try:
        return await course_service.update_place_in_course(request)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"장소 수정 중 오류가 발생했습니다: {str(e)}")

@router.delete("/courses/remove-place", response_model=CourseResponse)
async def remove_place_from_course(request: RemovePlaceFromCourseRequest = Body(...)):
    """
    코스에서 장소를 제거합니다.
    
    - **course_id**: 코스 ID
    - **place_id**: 제거할 장소 ID
    - **day**: 장소가 있는 날짜
    - **position**: 해당 날짜 내에서의 위치
    """
    try:
        return await course_service.remove_place_from_course(request)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"장소 제거 중 오류가 발생했습니다: {str(e)}")

@router.get("/courses/{course_id}")
async def get_course(course_id: str, format: str = "backend"):
    """
    코스 ID로 코스를 조회합니다.
    
    - **course_id**: 조회할 코스 ID
    - **format**: 응답 형식 ("backend" 또는 "frontend")
    """
    try:
        course_response = await course_service.get_course_by_id(course_id)
        
        if format == "frontend":
            # CourseResponse를 dict로 변환 후 프론트엔드 형식으로 변환
            course_dict = course_response.dict()
            frontend_data = data_converter.convert_backend_to_frontend({
                "itinerary": {
                    "days": [
                        {
                            "day": i + 1,
                            "date": day.date,
                            "places": [
                                {
                                    "place_id": place.place_id,
                                    "name": place.name,
                                    "time": f"{place.start_time}~{place.end_time}"
                                }
                                for place in day.places
                            ]
                        }
                        for i, day in enumerate(course_dict["dailySchedule"])
                    ]
                }
            })
            
            return {
                "success": True,
                "course": course_dict,
                "itinerary": frontend_data
            }
        else:
            return course_response
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"코스 조회 중 오류가 발생했습니다: {str(e)}")

@router.get("/courses/{course_id}/places")
async def get_course_places(course_id: str, day: int = None, format: str = "backend"):
    """
    코스의 장소 목록을 조회합니다.
    
    - **course_id**: 코스 ID
    - **day**: 특정 날짜 (선택사항, 지정하지 않으면 전체 날짜)
    - **format**: 응답 형식 ("backend" 또는 "frontend")
    """
    try:
        course = await course_service.get_course_by_id(course_id)
        
        if day is not None:
            # 특정 날짜의 장소만 반환
            if day > len(course.dailySchedule):
                raise HTTPException(status_code=400, detail=f"요청된 날짜({day})가 코스 기간({len(course.dailySchedule)})을 초과합니다.")
            
            day_schedule = course.dailySchedule[day - 1]
            
            if format == "frontend":
                # 프론트엔드 형식으로 변환
                frontend_data = data_converter.convert_backend_to_frontend({
                    "itinerary": {
                        "days": [{
                            "day": day,
                            "date": day_schedule.date,
                            "places": [
                                {
                                    "place_id": place.place_id,
                                    "name": place.name,
                                    "time": f"{place.start_time}~{place.end_time}"
                                }
                                for place in day_schedule.places
                            ]
                        }]
                    }
                })
                return frontend_data[0]  # 첫 번째 날만 반환
            else:
                return {
                    "course_id": course_id,
                    "day": day,
                    "date": day_schedule.date,
                    "places": day_schedule.places
                }
        else:
            # 전체 코스의 장소 반환
            if format == "frontend":
                # 프론트엔드 형식으로 변환
                frontend_data = data_converter.convert_backend_to_frontend({
                    "itinerary": {
                        "days": [
                            {
                                "day": i + 1,
                                "date": day.date,
                                "places": [
                                    {
                                        "place_id": place.place_id,
                                        "name": place.name,
                                        "time": f"{place.start_time}~{place.end_time}"
                                    }
                                    for place in day.places
                                ]
                            }
                            for i, day in enumerate(course.dailySchedule)
                        ]
                    }
                })
                return frontend_data
            else:
                return {
                    "course_id": course_id,
                    "dailySchedule": course.dailySchedule
                }
            
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"코스 장소 조회 중 오류가 발생했습니다: {str(e)}")
