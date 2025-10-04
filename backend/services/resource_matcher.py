# services/resource_matcher.py

import math
from typing import List, Dict, Any
from models import Resource
from services.geocode import geocode_to_geojson
from services.llm import extract_resource_fields

# Helper: haversine distance in km
def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


# services/resource_matcher.py

import math
from typing import List, Dict, Any, Union
from models import Resource
from services.geocode import geocode_to_geojson
from services.llm import extract_resource_fields

# Helper: haversine distance in km
def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371  # km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2)**2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def match_resources_to_situation(situation_text: str, max_results: int = 10) -> List[Dict[str, Any]]:
    """
    Given a situation (e.g. 'there's been a fire near K-Market Kilpisjärvi'),
    extract location + relevant categories, find nearby resources and rank them.
    """

    # 1) Extract location from situation using LLM
    extracted = extract_resource_fields(situation_text)
    if isinstance(extracted, list):
        location_text = next((e.get('location_text') for e in extracted if e.get('location_text')), None)
    elif isinstance(extracted, dict):
        location_text = extracted.get('location_text')
    else:
        location_text = None

    if not location_text:
        # crude fallback: use the entire situation as location
        location_text = situation_text

    # 2) Geocode the location
    geo = geocode_to_geojson(location_text)
    if not geo:
        return []

    # Support both Feature and Point
    if geo.get('type') == 'Point':
        lon, lat = geo['coordinates']
    elif geo.get('geometry', {}).get('type') == 'Point':
        lon, lat = geo['geometry']['coordinates']
    else:
        return []

    # 3) Derive relevant categories from situation keywords
    situation_lower = situation_text.lower()
    relevant_categories = set()
    if "fire" in situation_lower:
        relevant_categories.update(["water", "shelter", "tools", "electricity"])
    if "flood" in situation_lower:
        relevant_categories.update(["boats", "water", "food", "shelter"])
    if "earthquake" in situation_lower:
        relevant_categories.update(["shelter", "tools", "medical"])
    # (You can expand this mapping later)

    # 4) Score all resources
    resources = Resource.query.all()
    scored = []
    for r in resources:
        if not r.location_geojson:
            continue

        # Handle Feature or Point in stored resource location
        if r.location_geojson.get('type') == 'Point':
            loc_lon, loc_lat = r.location_geojson['coordinates']
        else:
            loc_lon, loc_lat = r.location_geojson['geometry']['coordinates']

        dist = haversine(lat, lon, loc_lat, loc_lon)
        score = -dist  # closer is better

        if r.category and r.category.lower() in relevant_categories:
            score += 100  # strong category match

        scored.append((score, r))

    # 5) Return top N sorted by score
    scored.sort(key=lambda x: x[0], reverse=True)
    top_resources = scored[:max_results]

    return [
        {
            "id": r.id,
            "category": r.category,
            "name": r.name,
            "quantity": r.quantity,
            "location": r.location_geojson,
            "phone_number": r.phone_number,
            "first_name": r.first_name,
            "last_name": r.last_name,
            "user_type": r.user_type.value if r.user_type else None,
            "score": score
        }
        for score, r in top_resources
    ]
