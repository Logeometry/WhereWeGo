# itinerary_router.py

from urllib import request
from fastapi import APIRouter, HTTPException
from typing import List, Optional, Tuple
from datetime import date, datetime, time

from pydantic import BaseModel, Field
from schemas import AutoMultiCourseInput, MultiDayItineraryResponse
from services.travel_time_estimator import TravelTimeService
from services.itinerary_service import ItineraryService
from routeres.survey_router import recommend_similar_places

router = APIRouter()

class Place(BaseModel):
    place_id: str
    coords: Tuple[float, float]
    rec_score: Optional[float] = Field(0.0, ge=0.0, le=1.0)

class RankedCourseRequest(BaseModel):
    candidates: List[Place]
    origin: Place
    dest: Place
    day: date
    start_time: time
    end_time: time
    avg_stay: int = Field(60, gt=0)
    alpha: float = Field(0.5, ge=0.0, le=1.0)

class MultiDayCourseRequest(BaseModel):
    candidates: List[Place]
    origin: Place
    dest: Place
    start_dt: datetime
    end_dt: datetime
    avg_stay: int = Field(60, gt=0)

@router.post("/auto-multi-from-survey", response_model=MultiDayItineraryResponse)
async def auto_multi_day_course_from_survey_with_input(data: AutoMultiCourseInput):
    try:
        similar_places = await recommend_similar_places(data.survey)

        if len(similar_places) < 3:
            raise HTTPException(status_code=400, detail="추천 장소가 부족합니다.")
        
        candidates = [
            Place(
                place_id=str(doc["_id"]),
                coords=tuple(doc["location"]["coordinates"]),
                rec_score=0.9
            ) for doc in similar_places
        ]

        origin = Place(place_id="origin", coords=data.origin_coords, rec_score=1.0)
        dest = Place(place_id="dest", coords=data.dest_coords, rec_score=1.0)

        estimator = TravelTimeService()
        service = ItineraryService(estimator)
        accommodation = Place(place_id="accommodation", coords=data.accommodation_coords, rec_score=0.8)

        request = MultiDayCourseRequest(
            candidates=candidates,
            origin=origin,
            dest=dest,
            start_dt=data.start_time,
            end_dt=data.end_time,
            avg_stay=data.avg_stay
        )

        itinerary = await service.generate_multi_day_course(**request.dict())
        return MultiDayItineraryResponse(itinerary=itinerary)

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"자동 코스 생성 실패: {str(e)}")
