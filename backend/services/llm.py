import os
import json
from typing import Dict, Any, Optional, List
from models import AppSetting
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
from openai import OpenAI


# ----- OpenAI extraction and abuse detection -----
def _openai_extract(
    text: str,
    incident_location: Optional[dict] = None,  # GeoJSON
    user_type: str = "civilian",
    user_location: Optional[dict] = None
) -> List[Dict[str, Any]]:

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    # Step 1: Extraction schema
    extraction_schema = {
        "name": "ResourceExtractionList",
        "schema": {
            "type": "object",
            "properties": {
                "resources": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "category": {"type": "string"},
                            "name": {"type": "string"},
                            "quantity": {"type": "integer"},
                            "location_text": {"type": "string"},
                            "first_name": {"type": "string"},
                            "last_name": {"type": "string"},
                            "social_security_number": {"type": "string"}
                        },
                        "required": ["name"],
                        "additionalProperties": False
                    }
                }
            },
            "required": ["resources"],
            "additionalProperties": False
        }
    }

    setting = AppSetting.query.first()
    model = setting.openai_model if setting and setting.openai_model else "gpt-4o-mini"

    resp = client.chat.completions.create(
        model=model,
        response_format={"type": "json_schema", "json_schema": extraction_schema},
        messages=[
            {
                "role": "system",
                "content": (
                    "You must follow these instructions with absolute precision. "
                    "Any deviation from the required JSON schema will be treated as a critical error. "
                    "Return ONLY valid JSON matching the schema exactly. "
                    "Do not include commentary or extra text. "
                    "Use singular forms (e.g., 'generators' → 'generator'). "
                    "Infer integers for quantity ('few' → 3, 'three dozen' → 36). "
                    "Return clean 'location_text' suitable for geocoding, e.g. 'Kilpisjärvi K-Market'."
                )
            },
            {"role": "user", "content": text},
        ],
        temperature=0,
    )

    extracted = json.loads(resp.choices[0].message.content)
    resources = extracted.get("resources", [])

    # Step 2: Compute distance for each resource
    geolocator = Nominatim(user_agent="incident_resource_checker")

    incident_coords = None
    if incident_location and incident_location.get("type") == "Point":
        try:
            lon, lat = incident_location["coordinates"]
            incident_coords = (lat, lon)
        except Exception:
            pass

    for r in resources:
        r["distance_km"] = None
        if incident_coords and r.get("location_text"):
            try:
                loc = geolocator.geocode(r["location_text"])
                if loc:
                    dist = geodesic(incident_coords, (loc.latitude, loc.longitude)).km
                    r["distance_km"] = round(dist, 1)
            except Exception:
                pass

    # Step 3: Abuse detection
    abuse_schema = {
        "name": "ResourceAbuseAssessment",
        "schema": {
            "type": "object",
            "properties": {
                "resources": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "quantity": {"type": "integer"},
                            "flagged": {"type": "boolean"},
                            "reason": {"type": "string"}
                        },
                        "required": ["name", "flagged"],
                        "additionalProperties": False
                    }
                }
            },
            "required": ["resources"],
            "additionalProperties": False
        }
    }

    abuse_prompt = {
        "role": "system",
        "content": (
            "You are a strict compliance auditor. Evaluate whether the listed resources "
            "seem realistic for the given user type, incident location, and user location. "
            "Flag items as 'flagged': true if quantities or types are implausible or too far "
            "from the incident (e.g., '20 trucks' for a civilian 2000 km away). "
            "Provide concise reasoning in 'reason'."
        ),
    }

    user_prompt = {
        "role": "user",
        "content": json.dumps({
            "user_type": user_type,
            "incident_location": incident_location,
            "user_location": user_location,
            "resources": resources,
        }, ensure_ascii=False)
    }

    abuse_resp = client.chat.completions.create(
        model=model,
        response_format={"type": "json_schema", "json_schema": abuse_schema},
        messages=[abuse_prompt, user_prompt],
        temperature=0,
    )

    abuse_result = json.loads(abuse_resp.choices[0].message.content)
    flagged_items = {r["name"]: r for r in abuse_result.get("resources", [])}

    for r in resources:
        abuse_data = flagged_items.get(r["name"])
        if abuse_data:
            r["flagged"] = abuse_data.get("flagged", False)
            r["abuse_reason"] = abuse_data.get("reason")
        else:
            r["flagged"] = False
            r["abuse_reason"] = None

    return resources




# ----- Public entrypoint -----
def extract_resource_fields(
    text: str,
    incident_location: Optional[dict] = None,
    user_type: Optional[str] = "civilian",
    user_location: Optional[dict] = None
) -> List[Dict[str, Any]]:
    """Extract resources using OpenAI."""
    return _openai_extract(
        text=text,
        incident_location=incident_location,
        user_type=user_type,
        user_location=user_location
    )
