## api.py


import os
import tempfile
from datetime import datetime
from typing import Any, Dict

from flask import Blueprint, request, jsonify, json

from app import db
from models import Resource, AppSetting, UserType, VerifiedEmail
from services.geocode import geocode_to_geojson
from services.transcribe import transcribe_audio
from services.legal_entity_verification import verify_legal_entity

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
    location_json = request.args.get('incident_location_geojson')

    if situation:
        from services.resource_matcher import match_resources_to_situation
        try:
            incident_location = json.loads(location_json) if location_json else None
        except Exception:
            incident_location = None

        matched = match_resources_to_situation(situation, incident_location)
        return jsonify({
            "situation": situation,
            "incident_location": incident_location,
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


@api_bp.post("/resources/create/")
def create_resource():
    """
    Manually create a new Resource entry.

    Example JSON body:
    {
        "category": "medical",
        "name": "first aid kit",
        "quantity": 12,
        "location_text": "Tampere central hospital",
        "location_geojson": {
            "type": "Point",
            "coordinates": [23.7610, 61.4981]
        },
        "phone_number": "+358401234567",
        "first_name": "Liisa",
        "last_name": "Virtanen",
        "social_security_number": "123456-789A",
        "user_type": "GOVERNMENT_AGENCY",
        "source_text": "manual entry"
    }
    """
    data = request.get_json(silent=True) or {}

    # Basic validation
    if not data.get("name"):
        return jsonify({"ok": False, "error": "Field 'name' is required."}), 400

    # Handle optional fields safely
    try:
        quantity = int(data["quantity"]) if data.get("quantity") is not None else None
    except ValueError:
        return jsonify({"ok": False, "error": "Invalid 'quantity' (must be integer)."}), 400

    # Parse user_type enum if provided
    user_type = None
    if data.get("user_type"):
        from models import UserType
        try:
            user_type = UserType[data["user_type"].upper()]
        except KeyError:
            return jsonify({"ok": False, "error": f"Invalid user_type '{data['user_type']}'."}), 400

    # Build resource instance
    resource = Resource(
        category=data.get("category"),
        name=data.get("name"),
        quantity=quantity,
        location_geojson=data.get("location_geojson"),
        location_text=data.get("location_text"),
        distance_km=data.get("distance_km"),
        phone_number=data.get("phone_number"),
        first_name=data.get("first_name"),
        last_name=data.get("last_name"),
        social_security_number=data.get("social_security_number"),
        source_text=data.get("source_text") or "manual entry",
        user_type=user_type,
        flagged=False,
        abuse_reason=None,
    )

    db.session.add(resource)
    db.session.commit()

    return jsonify({
        "ok": True,
        "message": "Resource created successfully.",
        "resource": {
            "id": resource.id,
            "category": resource.category,
            "name": resource.name,
            "quantity": resource.quantity,
            "location": resource.location_geojson,
            "phone_number": resource.phone_number,
            "first_name": resource.first_name,
            "last_name": resource.last_name,
            "user_type": resource.user_type.value if resource.user_type else None,
            "created_at": resource.created_at.isoformat() + "Z"
        }
    }), 201

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

@api_bp.post("/verify-legal-entity/request/")
def request_verification():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    user_type = (data.get("user_type") or "").strip().upper()

    if not email or not user_type:
        return jsonify({"ok": False, "error": "Email and user_type are required."}), 400

    result = verify_legal_entity(email, user_type)
    if not result["ok"]:
        return jsonify({
            "ok": False,
            "verified": False,
            "reason": result["reason"],
            "domain": result["domain"]
        }), 403

    # Store if not already in DB
    record = VerifiedEmail.query.filter_by(email=email).first()
    if not record:
        db.session.add(VerifiedEmail(email=email, user_type=user_type))
        db.session.commit()

    return jsonify({
        "ok": True,
        "message": "Verification code (mock) created.",
        "email": email,
        "domain": result["domain"],
        "user_type": user_type,
        "reason": result["reason"],
    }), 200


@api_bp.post("/verify-legal-entity/confirm/")
def confirm_verification():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    code = (data.get("code") or "").strip()

    if not email or not code:
        return jsonify({"ok": False, "error": "Email and code are required."}), 400

    record = VerifiedEmail.query.filter_by(email=email).first()
    if not record:
        return jsonify({"ok": False, "error": "Email not found."}), 404

    if code != "123456":
        return jsonify({"ok": False, "error": "Invalid code."}), 400

    return jsonify({
        "ok": True,
        "verified": True,
        "email": email,
        "user_type": record.user_type,
        "message": "Verification successful."
    }), 200
