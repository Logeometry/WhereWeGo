import json
from geopy.distance import geodesic
from typing import List
from schemas import LocationData
from services.data_loader import load_location_data_from_json

FILE_PATH = "data/tourlist_spots_all.json"
all_places = load_location_data_from_json(FILE_PATH)

def get_place_by_id(place_id: str):
    for place in all_places:
        if place.content_id == place_id:
            return place
    raise ValueError(f"Place ID {place_id} not found.")

async def recommend_nearby_places(place_id:str, max_distance: float = 5.0) -> list:
    base_place = get_place_by_id(place_id)
    base_coords = (base_place.map_y, base_place.map_x)
    
    nearby_places = []
    for place in all_places:
        if place.content_id == place_id:
            continue
        if not place.map_y or not place.map_x:
            continue
        target_coords = (place.map_y, place.map_x)
        dist = geodesic(base_coords, target_coords).km
        if dist <= max_distance:
            nearby_places.append((place, dist))
    
    nearby_places.sort(key=lambda x: x[1])
    return [place for place, _ in nearby_places[:10]]