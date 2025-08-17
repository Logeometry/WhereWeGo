from fastapi import APIRouter, HTTPException
import httpx
import os
from dotenv import load_dotenv
from typing import List, Dict, Optional
from datetime import datetime, timedelta

load_dotenv()

router = APIRouter()

# 한국관광공사 API 키 (공공데이터포털에서 발급 필요)
TOUR_API_KEY = os.getenv("TOUR_API_KEY_Crowding")

# 부산 지역 코드 (한국관광공사 API 기준)
BUSAN_AREA_CODE = "26"  # 부산광역시

# 부산 구별 코드
BUSAN_DISTRICTS = {
    "중구": "26110",
    "서구": "26140", 
    "동구": "26170",
    "영도구": "26200",
    "부산진구": "26230",
    "동래구": "26260",
    "남구": "26290",
    "북구": "26320",
    "해운대구": "26350",
    "사하구": "26380",
    "금정구": "26410",
    "강서구": "26440",
    "연제구": "26470",
    "수영구": "26500",
    "사상구": "26530",
    "기장군": "26710"
}

async def get_crowding_data(area_code: str, sigungu_code: str = None, attraction_name: str = None) -> Dict:
    """관광지 집중률 데이터 조회"""
    try:
        url = "http://apis.data.go.kr/B551011/TatsCnctrRateService/tatsCnctrRatedList"
        
        # API 키 디코딩
        import urllib.parse
        decoded_key = urllib.parse.unquote(TOUR_API_KEY) if TOUR_API_KEY else ""
        
        params = {
            "serviceKey": decoded_key,  # 디코딩된 키 사용
            "pageNo": "1",
            "numOfRows": "1000",  # 최대 데이터 수로 설정하여 모든 관광지 데이터 수집
            "MobileOS": "ETC",
            "MobileApp": "WhereWeGo",
            "areaCd": area_code,
            "_type": "json"
        }
        
        # signguCd가 있는 경우에만 추가
        if sigungu_code:
            params["signguCd"] = sigungu_code
            
        # 관광지명이 있는 경우에만 추가
        if attraction_name:
            params["tAtsNm"] = attraction_name
        
        print(f"[DEBUG] API 키 디코딩: {TOUR_API_KEY[:20]}... -> {decoded_key[:20]}...")
        print(f"[DEBUG] 파라미터: {params}")
        
        async with httpx.AsyncClient() as client:
            # URL을 직접 구성하여 httpx의 자동 인코딩 방지
            query_string = "&".join([f"{k}={v}" for k, v in params.items()])
            full_url = f"{url}?{query_string}"
            
            print(f"[DEBUG] 최종 URL: {full_url}")
            
            response = await client.get(full_url)
            response.raise_for_status()
            
        data = response.json()
        return data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"API 호출 오류: {str(e)}")

@router.get("/crowding/busan", 
    summary="부산 전체 혼잡도 정보",
    description="부산 지역 전체의 관광지 혼잡도 정보를 조회합니다.",
    response_description="부산 전체 혼잡도 데이터",
    tags=["혼잡도"])
async def get_busan_crowding():
    """부산 전체 혼잡도 정보
    
    한국관광공사 API를 통해 부산 지역 전체의 관광지 혼잡도를 조회합니다.
    
    Returns:
        dict: 성공 여부와 혼잡도 데이터를 포함한 응답
        
    Raises:
        HTTPException: API 호출 실패 시 500 에러
    """
    try:
        data = await get_crowding_data(BUSAN_AREA_CODE)
        return {
            "success": True,
            "data": data,
            "message": "부산 지역 혼잡도 정보를 성공적으로 조회했습니다."
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "부산 지역 혼잡도 정보 조회에 실패했습니다."
        }

@router.get("/crowding/busan/{district}", 
    summary="부산 특정 구 혼잡도 정보",
    description="부산 특정 구의 관광지 혼잡도 정보를 조회합니다.",
    response_description="특정 구 혼잡도 데이터",
    tags=["혼잡도"])
async def get_district_crowding(district: str):
    """부산 특정 구 혼잡도 정보
    
    Args:
        district (str): 조회할 구 이름 (예: 해운대구, 중구, 서구 등)
        
    Returns:
        dict: 성공 여부와 해당 구의 혼잡도 데이터를 포함한 응답
        
    Raises:
        HTTPException: 지원하지 않는 구인 경우 400 에러
    """
    if district not in BUSAN_DISTRICTS:
        raise HTTPException(
            status_code=400, 
            detail=f"지원하지 않는 구입니다: {district}. 지원하는 구: {', '.join(BUSAN_DISTRICTS.keys())}"
        )
    
    try:
        sigungu_code = BUSAN_DISTRICTS[district]
        
        # 페이지네이션을 사용하여 모든 데이터 수집
        all_items = []
        page_no = 1
        max_pages = 10  # 최대 10페이지까지 조회 (안전장치)
        
        while page_no <= max_pages:
            try:
                url = "http://apis.data.go.kr/B551011/TatsCnctrRateService/tatsCnctrRatedList"
                
                # API 키 디코딩
                import urllib.parse
                decoded_key = urllib.parse.unquote(TOUR_API_KEY) if TOUR_API_KEY else ""
                
                params = {
                    "serviceKey": decoded_key,
                    "pageNo": str(page_no),
                    "numOfRows": "1000",  # 최대 데이터 수
                    "MobileOS": "ETC",
                    "MobileApp": "WhereWeGo",
                    "areaCd": BUSAN_AREA_CODE,
                    "signguCd": sigungu_code,
                    "_type": "json"
                }
                
                async with httpx.AsyncClient() as client:
                    query_string = "&".join([f"{k}={v}" for k, v in params.items()])
                    full_url = f"{url}?{query_string}"
                    response = await client.get(full_url)
                    response.raise_for_status()
                
                data = response.json()
                items = data.get("response", {}).get("body", {}).get("items", {}).get("item", [])
                
                if not items:  # 더 이상 데이터가 없으면 중단
                    break
                
                all_items.extend(items)
                
                # 전체 데이터 수 확인
                total_count = data.get("response", {}).get("body", {}).get("totalCount", 0)
                if len(all_items) >= total_count:  # 모든 데이터를 가져왔으면 중단
                    break
                
                page_no += 1
                
            except Exception as e:
                print(f"[ERROR] 페이지 {page_no} 조회 실패: {str(e)}")
                break
        
        # 고유한 관광지별로 그룹화하여 평균 혼잡도 계산
        unique_attractions = {}
        for item in all_items:
            attraction_name = item.get('tAtsNm', '')
            if attraction_name:
                if attraction_name not in unique_attractions:
                    unique_attractions[attraction_name] = []
                unique_attractions[attraction_name].append(float(item.get('cnctrRate', 0)))
        
        # 각 관광지의 평균 혼잡도 계산
        attraction_averages = []
        for attraction_name, rates in unique_attractions.items():
            avg_rate = sum(rates) / len(rates)
            attraction_averages.append(avg_rate)
        
        # 전체 평균 혼잡도 계산
        overall_avg_crowding = 0
        if attraction_averages:
            overall_avg_crowding = sum(attraction_averages) / len(attraction_averages)
        
        # 수집된 모든 데이터로 응답 구성
        result_data = {
            "response": {
                "body": {
                    "items": {
                        "item": all_items
                    },
                    "totalCount": len(all_items)
                }
            }
        }
        
        return {
            "success": True,
            "data": result_data,
            "district": district,
            "total_items": len(all_items),
            "pages_queried": page_no - 1,
            "unique_attractions": len(unique_attractions),
            "average_crowding": round(overall_avg_crowding, 1),
            "attraction_details": [
                {
                    "name": name,
                    "average_rate": round(sum(rates) / len(rates), 1),
                    "data_count": len(rates)
                }
                for name, rates in unique_attractions.items()
            ],
            "message": f"{district} 혼잡도 정보를 성공적으로 조회했습니다. (총 {len(all_items)}개 데이터, {len(unique_attractions)}개 고유 관광지, 평균 혼잡도: {round(overall_avg_crowding, 1)}%)"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"{district} 혼잡도 정보 조회에 실패했습니다."
        }

@router.get("/crowding/districts", 
    summary="부산 구 목록 조회",
    description="혼잡도 정보를 조회할 수 있는 부산 구 목록을 반환합니다.",
    response_description="부산 구 목록",
    tags=["혼잡도"])
async def get_available_districts():
    """사용 가능한 부산 구 목록
    
    혼잡도 정보를 조회할 수 있는 부산의 모든 구 목록을 반환합니다.
    
    Returns:
        dict: 성공 여부와 구 목록을 포함한 응답
    """
    return {
        "success": True,
        "districts": list(BUSAN_DISTRICTS.keys()),
        "message": "부산 구 목록을 성공적으로 조회했습니다."
    }

@router.get("/crowding/summary", 
    summary="부산 구별 혼잡도 요약",
    description="부산 전체와 주요 구들의 혼잡도 정보를 요약하여 제공합니다.",
    response_description="부산 구별 혼잡도 요약 데이터",
    tags=["혼잡도"])
async def get_crowding_summary():
    """부산 전체 구별 혼잡도 요약
    
    부산 전체와 주요 구들의 혼잡도 정보를 한 번에 조회합니다.
    API 호출 제한을 고려하여 최대 3개 구의 데이터만 포함합니다.
    
    Returns:
        dict: 성공 여부와 요약 데이터를 포함한 응답
        
    Raises:
        HTTPException: API 호출 실패 시 500 에러
    """
    try:
        summary = {}
        
        # 전체 부산 데이터
        busan_data = await get_crowding_data(BUSAN_AREA_CODE)
        summary["전체"] = busan_data
        
        # 각 구별 데이터 (최대 3개 구만 조회하여 API 호출 제한)
        district_count = 0
        for district, code in BUSAN_DISTRICTS.items():
            if district_count >= 3:  # API 호출 제한을 위해 3개 구만 조회
                break
            try:
                district_data = await get_crowding_data(BUSAN_AREA_CODE, code)
                summary[district] = district_data
                district_count += 1
            except:
                continue
        
        return {
            "success": True,
            "summary": summary,
            "message": "부산 구별 혼잡도 요약을 성공적으로 조회했습니다."
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "부산 구별 혼잡도 요약 조회에 실패했습니다."
        }

@router.get("/crowding/attractions/{district}", 
    summary="지역별 관광지 목록 조회",
    description="특정 지역에서 혼잡도 데이터가 있는 관광지 목록을 조회합니다.",
    response_description="지역별 관광지 목록",
    tags=["혼잡도"])
async def get_district_attractions(district: str):
    """지역별 관광지 목록 조회
    
    Args:
        district (str): 조회할 구 이름 (예: 해운대구, 중구, 서구 등)
        
    Returns:
        dict: 성공 여부와 해당 지역의 관광지 목록을 포함한 응답
    """
    if district not in BUSAN_DISTRICTS:
        raise HTTPException(
            status_code=400, 
            detail=f"지원하지 않는 구입니다: {district}. 지원하는 구: {', '.join(BUSAN_DISTRICTS.keys())}"
        )
    
    try:
        url = "http://apis.data.go.kr/B551011/TatsCnctrRateService/tatsCnctrRatedList"
        
        # API 키 디코딩
        import urllib.parse
        decoded_key = urllib.parse.unquote(TOUR_API_KEY) if TOUR_API_KEY else ""
        
        sigungu_code = BUSAN_DISTRICTS[district]
        
        params = {
            "serviceKey": decoded_key,
            "pageNo": "1",
            "numOfRows": "1000",  # 더 많은 관광지 조회 (최대값으로 설정)
            "MobileOS": "ETC",
            "MobileApp": "WhereWeGo",
            "areaCd": BUSAN_AREA_CODE,
            "signguCd": sigungu_code,
            "_type": "json"
        }
        
        # 페이지네이션으로 모든 데이터 수집
        all_items = []
        page_no = 1
        max_pages = 10  # 최대 10페이지까지 조회 (안전장치)
        
        while page_no <= max_pages:
            params["pageNo"] = str(page_no)
            
            async with httpx.AsyncClient() as client:
                query_string = "&".join([f"{k}={v}" for k, v in params.items()])
                full_url = f"{url}?{query_string}"
                response = await client.get(full_url)
                response.raise_for_status()
                
            data = response.json()
            items = data.get("response", {}).get("body", {}).get("items", {}).get("item", [])
            
            if not items:  # 더 이상 데이터가 없으면 중단
                break
                
            all_items.extend(items)
            
            # 전체 데이터 수 확인
            total_count = data.get("response", {}).get("body", {}).get("totalCount", 0)
            if len(all_items) >= total_count:  # 모든 데이터를 가져왔으면 중단
                break
                
            page_no += 1
        
        # 중복 제거하고 관광지명만 추출
        attractions = list(set([item.get("tAtsNm", "") for item in all_items if item.get("tAtsNm")]))
        attractions.sort()  # 알파벳 순 정렬
        
        return {
            "success": True,
            "district": district,
            "attractions": attractions,
            "total_count": len(attractions),
            "debug_info": {
                "total_items_collected": len(all_items),
                "pages_queried": page_no - 1,
                "unique_attractions": len(attractions)
            },
            "message": f"'{district}' 지역의 관광지 목록을 성공적으로 조회했습니다. (총 {len(all_items)}개 데이터에서 {len(attractions)}개 관광지)"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"'{district}' 지역의 관광지 목록 조회에 실패했습니다."
        }

@router.get("/crowding/check-key", 
    summary="API 키 확인",
    description="환경 변수에서 API 키가 제대로 설정되었는지 확인합니다.",
    tags=["혼잡도"])
async def check_api_key():
    """API 키 상태 확인
    
    Returns:
        dict: API 키 설정 상태
    """
    return {
        "success": True,
        "api_key_exists": bool(TOUR_API_KEY),
        "api_key_length": len(TOUR_API_KEY) if TOUR_API_KEY else 0,
        "api_key_preview": TOUR_API_KEY[:10] + "..." if TOUR_API_KEY and len(TOUR_API_KEY) > 10 else TOUR_API_KEY,
        "message": "API 키 상태 확인 완료"
    }

@router.get("/crowding/attraction/{attraction_name}", 
    summary="관광지명으로 혼잡도 조회",
    description="특정 관광지명으로 혼잡도 정보를 조회합니다.",
    response_description="관광지 혼잡도 데이터",
    tags=["혼잡도"])
async def get_attraction_crowding(attraction_name: str):
    """관광지명으로 혼잡도 조회
    
    Args:
        attraction_name (str): 조회할 관광지명 (예: SEA LIFE 부산아쿠아리움, 해운대해수욕장 등)
        
    Returns:
        dict: 성공 여부와 해당 관광지의 혼잡도 데이터를 포함한 응답
    """
    try:
        # 부산 지역에서 관광지명으로 검색
        data = await get_crowding_data(BUSAN_AREA_CODE, attraction_name=attraction_name)
        
        # 데이터가 있는지 확인
        if data.get("response", {}).get("body", {}).get("totalCount", 0) == 0:
            return {
                "success": False,
                "error": "해당 관광지의 혼잡도 데이터가 존재하지 않습니다.",
                "message": f"'{attraction_name}' 관광지의 혼잡도 정보를 찾을 수 없습니다."
            }
        
        return {
            "success": True,
            "data": data,
            "attraction_name": attraction_name,
            "message": f"'{attraction_name}' 관광지의 혼잡도 정보를 성공적으로 조회했습니다."
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"'{attraction_name}' 관광지 혼잡도 정보 조회에 실패했습니다."
        }




