# services/survey_service.py

from typing import List
from schemas import SurveyResponse
from db import places_col
from bson import ObjectId
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

async def recommend_similar_places_from_survey(survey: List[SurveyResponse]) -> List[dict]:
    liked_ids = [s.content_id for s in survey if s.responses == "like"]

    liked_vectors = []
    for pid in liked_ids:
        place = await places_col.find_one({"_id": ObjectId(pid)})
        if place and place.get("vector_full"):
            liked_vectors.append(np.array(place["vector_full"], dtype=np.float32))

    if not liked_vectors:
        raise ValueError("좋아요한 장소에 유효한 벡터가 없습니다.")

    avg_vector = np.mean(liked_vectors, axis=0)

    candidates = await places_col.find({
        "vector_full": {"$exists": True, "$ne": None}
    }).to_list(length=2000)

    scored = []
    for place in candidates:
        vector = place.get("vector_full")
        if not vector:
            continue
        try:
            sim = cosine_similarity([avg_vector], [np.array(vector, dtype=np.float32)])[0][0]
            place["_id"] = str(place["_id"])
            place["similarity"] = float(sim)
            scored.append(place)
        except:
            continue

    scored.sort(key=lambda x: -x["similarity"])
    return scored[:10]
