"""
프론트엔드와 백엔드 간 데이터 변환 서비스
"""
from typing import List, Dict, Any, Union, Optional
from schemas import CourseSaveRequest, CourseItinerary, CourseDay, CoursePlace


class DataConverter:
    """프론트엔드 데이터를 백엔드 형식으로 변환하는 서비스"""
    
    @staticmethod
    def is_frontend_format(data: Any) -> bool:
        """프론트엔드 형식인지 확인"""
        if isinstance(data, list) and len(data) > 0:
            first_item = data[0]
            return isinstance(first_item, dict) and "dayName" in first_item and "places" in first_item
        return False
    
    @staticmethod
    def is_backend_format(data: Any) -> bool:
        """백엔드 형식인지 확인"""
        return (isinstance(data, dict) and 
                "itinerary" in data and 
                "user_id" in data and 
                "course_name" in data)
    
    @staticmethod
    def convert_frontend_to_backend(
        frontend_data: List[Dict], 
        user_id: str = "demo_user", 
        course_name: str = "부산 여행"
    ) -> Dict[str, Any]:
        """
        프론트엔드 형식을 백엔드 형식으로 변환
        
        Args:
            frontend_data: TravelPlanSamplePage 형태의 일정 데이터
            user_id: 사용자 ID
            course_name: 코스명
            
        Returns:
            CourseSaveRequest 형태의 딕셔너리
        """
        course_days = []
        
        for day_data in frontend_data:
            # "Day 1" -> 1 변환
            day_num = int(day_data["dayName"].split(" ")[1])
            
            # "2026. 8. 21." -> "2026-08-21" 변환
            date_parts = day_data["date"].replace(".", "").split()
            formatted_date = f"{date_parts[0]}-{date_parts[1].zfill(2)}-{date_parts[2].zfill(2)}"
            
            # 장소 데이터 변환
            places = []
            for place in day_data["places"]:
                places.append({
                    "place_id": place.get("placeId") or place.get("id", f"temp_{place.get('name', 'unknown')}"),
                    "name": place["name"],
                    "time": place["time"]
                })
            
            course_days.append({
                "day": day_num,
                "date": formatted_date,
                "places": places
            })
        
        return {
            "user_id": user_id,
            "course_name": course_name,
            "itinerary": {
                "days": course_days
            }
        }
    
    @staticmethod
    def convert_backend_to_frontend(backend_data: Dict[str, Any]) -> List[Dict]:
        """
        백엔드 형식을 프론트엔드 형식으로 변환
        
        Args:
            backend_data: CourseSaveRequest 형태의 데이터
            
        Returns:
            TravelPlanSamplePage 형태의 일정 데이터
        """
        frontend_data = []
        
        itinerary = backend_data.get("itinerary", {})
        days = itinerary.get("days", [])
        
        for day in days:
            # "2026-08-21" -> "2026. 8. 21." 변환
            date_parts = day["date"].split("-")
            formatted_date = f"{date_parts[0]}. {int(date_parts[1])}. {int(date_parts[2])}."
            
            # 장소 데이터 변환
            places = []
            for place in day.get("places", []):
                places.append({
                    "id": place.get("place_id") or place.get("id", "unknown"),
                    "placeId": place.get("place_id"),
                    "name": place["name"],
                    "time": place["time"],
                    "icon": None  # 프론트엔드에서 별도로 설정
                })
            
            frontend_data.append({
                "date": formatted_date,
                "dayName": f"Day {day['day']}",
                "places": places
            })
        
        return frontend_data
    
    @staticmethod
    def normalize_course_data(
        data: Union[List[Dict], Dict[str, Any]], 
        user_id: Optional[str] = None, 
        course_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        입력 데이터 형식을 자동 감지하여 백엔드 형식으로 정규화
        
        Args:
            data: 프론트엔드 또는 백엔드 형식의 데이터
            user_id: 사용자 ID (프론트엔드 형식일 때 사용)
            course_name: 코스명 (프론트엔드 형식일 때 사용)
            
        Returns:
            정규화된 백엔드 형식 데이터
        """
        if DataConverter.is_frontend_format(data):
            # 프론트엔드 형식 → 백엔드 형식 변환
            return DataConverter.convert_frontend_to_backend(
                data, 
                user_id or "demo_user", 
                course_name or "부산 여행"
            )
        elif DataConverter.is_backend_format(data):
            # 이미 백엔드 형식
            return data
        else:
            raise ValueError("지원하지 않는 데이터 형식입니다.")

# 전역 인스턴스
data_converter = DataConverter()
