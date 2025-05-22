import json
from typing import List
from schemas import LocationData, LogData

def load_location_data_from_json(file_path: str) -> List[LocationData]:
    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)
    return [LocationData(**item) for item in data]

def load_logs_data_from_json(file_path: str) -> List[LogData]:
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)
