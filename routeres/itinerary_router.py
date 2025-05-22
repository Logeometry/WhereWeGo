from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from datetime import datetime, date, time
from typing import List, Dict, Tuple, Optional

from services.travel_time_estimator import DistanceBasedEstimator, TravelTimeEstimator
from services.itinerary_service import ItineraryService

router = APIRouter(prefix="/itinerary")

# Pydantic models for request/response
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
    alpha: float = Field(0.5, ge=0.0, le=1.0)

@router.post("/day", summary="Generate single-day ranked course")
async def create_ranked_course(req: RankedCourseRequest):
    # instantiate service
    estimator: TravelTimeEstimator = DistanceBasedEstimator()
    service = ItineraryService(estimator, alpha=req.alpha)
    try:
        plan = service.generate_ranked_course(
            candidates=[p.dict() for p in req.candidates],
            day=req.day,
            origin=req.origin.dict(),
            dest=req.dest.dict(),
            start_time=req.start_time,
            end_time=req.end_time,
            avg_stay=req.avg_stay
        )
        return {"date": req.day, "plan": plan}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/multi", summary="Generate multi-day ranked course")
async def create_multi_day_course(req: MultiDayCourseRequest):
    estimator: TravelTimeEstimator = DistanceBasedEstimator()
    service = ItineraryService(estimator, alpha=req.alpha)
    try:
        itinerary = service.generate_multi_day_course(
            candidates=[p.dict() for p in req.candidates],
            origin=req.origin.dict(),
            dest=req.dest.dict(),
            start_dt=req.start_dt,
            end_dt=req.end_dt,
            avg_stay=req.avg_stay
        )
        return itinerary
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
