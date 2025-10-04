## api.py


import os
import tempfile
from datetime import datetime
from typing import Any, Dict

from flask import Blueprint, request, jsonify

from app import db
from models import Resource, AppSetting, UserType
from services.geocode import geocode_to_geojson
from services.transcribe import transcribe_audio

api_bp = Blueprint('api', __name__)


@api_bp.post('/process_message/')
def process_message():
    from services.llm import extract_resource_fields
    """
    Accepts JSON or multipart/form-data.

    JSON body shape:
    {
      "text": "..." | null,
      "audio": null,                    # ignored unless multipart
      "metadata": {
         "phone_number": "+358...",
         "incident_location": {GeoJSON},  # REQUIRED, incident location
         "user_location": {GeoJSON or None},  # OPTIONAL, user location
         "first_name": "...", "last_name": "...",
         "social_security_number": "...",
         "user_type": "NGO|corporate|civilian|corporate entity|ai model"
      }
    }

    Multipart shape (for audio): fields: metadata (json), file (audio/*)
    """
    payload = {}

    # --- Parse request content ---
    if request.content_type and request.content_type.startswith('multipart/form-data'):
        # audio upload path
        meta_json = request.form.get('metadata', '{}')
        import json
        try:
            metadata = json.loads(meta_json or '{}')
        except Exception:
            metadata = {}
        file = request.files.get('file')
        if not file:
            return jsonify({"error": "No audio file provided."}), 400
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[-1] or '.wav') as tmp:
            file.save(tmp.name)
            audio_path = tmp.name
        # Local speech recognition
        text, _ = transcribe_audio(audio_path)
        os.unlink(audio_path)
        payload['text'] = text
        payload['metadata'] = metadata
    else:
        payload = request.get_json(silent=True) or {}

    text = (payload.get('text') or '').strip()
    metadata = payload.get('metadata') or {}

    if not text:
        return jsonify({"error": "No text to process (provide text or audio)."}), 400

    # --- Extract metadata inputs ---
    incident_location = metadata.get("incident_location")  # GeoJSON (required)
    if not incident_location:
        return jsonify({"error": "Missing required 'incident_location' field in metadata."}), 400

    user_location = metadata.get("user_location")  # GeoJSON (optional)
    user_type_val = metadata.get("user_type")

    # --- Extract resources using LLM ---
    extracted_list = extract_resource_fields(
        text=text,
        incident_location=incident_location,
        user_type=user_type_val,
        user_location=user_location  # Pass optional user location to LLM
    )
    if not extracted_list:
        return jsonify({"error": "Could not extract any resources from the message."}), 400

    # --- Resolve fallback location for resource saving ---
    location_geojson = incident_location

    resources_created = []

    for extracted in extracted_list:
        phone = metadata.get('phone_number')
        first_name = extracted.get('first_name') or metadata.get('first_name')
        last_name = extracted.get('last_name') or metadata.get('last_name')
        ssn = extracted.get('social_security_number') or metadata.get('social_security_number')

        user_type = None
        if user_type_val:
            try:
                user_type = UserType(user_type_val)
            except ValueError:
                pass

        try:
            quantity = int(extracted.get('quantity')) if extracted.get('quantity') is not None else None
        except Exception:
            quantity = None

        resource = Resource(
            category=extracted.get('category'),
            name=extracted.get('name') or 'unknown',
            quantity=quantity,
            location_geojson=extracted.get("location_geojson") or location_geojson,
            phone_number=phone,
            first_name=first_name,
            last_name=last_name,
            social_security_number=ssn,
            source_text=text,
            user_type=user_type,
            created_at=datetime.utcnow(),
            flagged=extracted.get('flagged', False),
            abuse_reason=extracted.get('abuse_reason'),
        )

        if extracted.get("distance_km") is not None:
            resource.distance_km = extracted["distance_km"]

        db.session.add(resource)
        resources_created.append(resource)

    db.session.commit()

    return jsonify({
        "ok": True,
        "resources": [
            {
                "id": r.id,
                "category": r.category,
                "name": r.name,
                "quantity": r.quantity,
                "location": r.location_geojson,
                "distance_km": getattr(r, "distance_km", None),
                "flagged": r.flagged,
                "abuse_reason": r.abuse_reason,
                "phone_number": r.phone_number,
                "created_at": r.created_at.isoformat() + 'Z',
                "first_name": r.first_name,
                "last_name": r.last_name,
                "social_security_number": r.social_security_number,
                "user_type": r.user_type.value if r.user_type else None
            }
            for r in resources_created
        ]
    }), 201



@api_bp.get('/resources/')
def list_resources():
    situation = request.args.get('situation')

    # --- If a situation is provided, use the LLM + geocoding matcher ---
    if situation:
        from services.resource_matcher import match_resources_to_situation
        matched = match_resources_to_situation(situation)
        return jsonify({
            "situation": situation,
            "resources": matched
        })

    # --- Otherwise: list all resources normally ---
    resources = Resource.query.all()
    return jsonify({
        "resources": [
            {
                "id": r.id,
                "category": r.category,
                "name": r.name,
                "quantity": r.quantity,
                "location": r.location_geojson,
                "phone_number": r.phone_number,
                "first_name": r.first_name,
                "last_name": r.last_name,
                "user_type": r.user_type.value if r.user_type else None
            } for r in resources
        ]
    })

@api_bp.patch('/resources/<int:resource_id>/')
def update_resource(resource_id):
    """
    Update a resource by ID. Accepts partial JSON body.
    Example:
    PATCH /api/resources/5/
    {
        "flagged": true,
        "category": "water",
        "quantity": 20
    }
    """
    resource = Resource.query.get(resource_id)
    if not resource:
        return jsonify({"error": f"Resource {resource_id} not found"}), 404

    data = request.get_json(silent=True) or {}

    if "category" in data:
        resource.category = data["category"]
    if "name" in data:
        resource.name = data["name"]
    if "quantity" in data:
        resource.quantity = data["quantity"]
    if "flagged" in data:
        resource.flagged = bool(data["flagged"])

    db.session.commit()

    return jsonify({
        "ok": True,
        "resource": {
            "id": resource.id,
            "category": resource.category,
            "name": resource.name,
            "quantity": resource.quantity,
            "flagged": resource.flagged
        }
    })

