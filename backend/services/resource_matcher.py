import os
import json
from typing import List, Dict, Any, Optional
from openai import OpenAI
from models import Resource, AppSetting
from flask import current_app

def match_resources_to_situation(
    situation: str,
    incident_location_geojson: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Uses OpenAI to identify which stored resources best match the described emergency situation.
    Returns a ranked list of relevant resources with reasoning and full location data.

    Args:
        situation: A human-readable description of the current emergency.
        incident_location_geojson: Optional GeoJSON representing the incident area.
    """

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    setting = AppSetting.query.first()
    model = setting.openai_model if setting and setting.openai_model else "gpt-4o-mini"

    # --- 1. Fetch all resources ---
    resources = Resource.query.all()
    if not resources:
        return []

    resources_data = [
        {
            "id": r.id,
            "category": r.category,
            "name": r.name,
            "quantity": r.quantity,
            "user_type": r.user_type.value if r.user_type else None,
            "flagged": r.flagged,
            "location_text": r.location_text,
            "location_geojson": r.location_geojson,
        }
        for r in resources
    ]

    # --- 2. Define schema for OpenAI structured response ---
    match_schema = {
        "name": "MatchedResourceList",
        "schema": {
            "type": "object",
            "properties": {
                "matches": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "resource_id": {"type": "integer"},
                            "relevance_score": {"type": "number"},
                            "reason": {"type": "string"}
                        },
                        "required": ["resource_id", "relevance_score"],
                        "additionalProperties": False
                    }
                }
            },
            "required": ["matches"],
            "additionalProperties": False
        }
    }

    # --- 3. System instruction for the model ---
    system_prompt = (
        "You are an emergency coordination AI. "
        "Given an emergency situation and a list of available resources, "
        "determine which ones are most relevant for responding to the crisis. "
        "Use category, quantity, user_type, and proximity (based on coordinates) "
        "to rank relevance. Flagged resources should be ignored or scored low. "
        "Return a list of matched resources with relevance_score (0.0–1.0) and reasoning."
    )

    # --- 4. Build the contextual payload ---
    user_context = {
        "situation": situation,
        "incident_location_geojson": incident_location_geojson,
        "resources": resources_data,
    }

    try:
        resp = client.chat.completions.create(
            model=model,
            response_format={"type": "json_schema", "json_schema": match_schema},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(user_context, ensure_ascii=False)},
            ],
            temperature=0,
        )

        data = json.loads(resp.choices[0].message.content)
        matches = data.get("matches", [])

        # --- 5. Sort by relevance descending ---
        matches = sorted(matches, key=lambda m: m.get("relevance_score", 0), reverse=True)

        # --- 6. Enrich with full resource details ---
        id_map = {r.id: r for r in resources}
        enriched = []
        for m in matches:
            r = id_map.get(m["resource_id"])
            if not r:
                continue
            enriched.append({
                "id": r.id,
                "category": r.category,
                "name": r.name,
                "quantity": r.quantity,
                "user_type": r.user_type.value if r.user_type else None,
                "flagged": r.flagged,
                "location_text": r.location_text,
                "location_geojson": r.location_geojson,
                "relevance_score": m["relevance_score"],
                "reason": m.get("reason", ""),
            })

        return enriched

    except Exception as e:
        current_app.logger.error(f"[resource_matcher] OpenAI matching failed: {e}")
        return []
