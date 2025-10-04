import os
import json
from typing import Dict, Any, Optional, List
from models import AppSetting, Category, Subcategory
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

    # Step 1: Extraction schema (matches Resource model)
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
                            "subcategory": {"type": "string"},
                            "name": {"type": "string"},
                            "quantity": {"type": "integer"},
                            "num_available_people": {"type": "integer"},
                            "location_text": {"type": "string"},
                            "first_name": {"type": "string"},
                            "last_name": {"type": "string"},
                            "email": {"type": "string"},
                            "phone_number": {"type": "string"}
                        },
                        "required": ["name", "category"],
                        "additionalProperties": False
                    }
                }
            },
            "required": ["resources"],
            "additionalProperties": False
        }
    }

    # List of allowed categories and subcategories
    allowed_categories = [c.value for c in Category]
    allowed_subcategories = [s.value for s in Subcategory]

    setting = AppSetting.query.first()
    model = setting.openai_model if setting and setting.openai_model else "gpt-4o-mini"

    # Prompt: ensure LLM extracts only valid categories/subcategories and skips invalid resources
    system_prompt = {
        "role": "system",
        "content": (
            "You are an information extraction system for emergency resource reporting. "
            "Extract ONLY resources that fit the predefined categories and subcategories. "
            f"Allowed categories: {', '.join(allowed_categories)}. "
            f"Allowed subcategories: {', '.join(allowed_subcategories)}. "
            "If a mentioned item does not fit these categories, DO NOT include it. "
            "If the location is missing, unclear, or cannot be localized, skip that resource. "
            "Infer quantities from text ('few' → 3, 'dozen' → 12). "
            "Return clean 'location_text' (e.g., 'Kilpisjärvi K-Market') suitable for geocoding. "
            "Output MUST strictly match the provided JSON schema."
        )
    }

    resp = client.chat.completions.create(
        model=model,
        response_format={"type": "json_schema", "json_schema": extraction_schema},
        messages=[system_prompt, {"role": "user", "content": text}],
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
                    r["location_geojson"] = {
                        "type": "Point",
                        "coordinates": [loc.longitude, loc.latitude],
                    }
                else:
                    r["location_geojson"] = None
            except Exception:
                r["location_geojson"] = None
        else:
            r["location_geojson"] = None

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
                            "reason": {"type": "string"},
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
            "You are a compliance auditor. Evaluate whether each listed resource is realistic "
            "for the given user type, location, and distance. "
            "Flag resources as 'flagged': true if quantities or types are implausible, "
            "unrelated to emergencies, or suspicious. "
            "Only provide 'reason' if flagged=true; omit or leave blank otherwise."
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

    final_resources = []
    for r in resources:
        # Skip resources with no location
        if not r.get("location_geojson"):
            continue

        abuse_data = flagged_items.get(r["name"])
        if abuse_data:
            flagged = abuse_data.get("flagged", False)
            r["flagged"] = flagged
            r["abuse_reason"] = abuse_data.get("reason") if flagged else None
        else:
            r["flagged"] = False
            r["abuse_reason"] = None

        final_resources.append(r)

    return final_resources





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
