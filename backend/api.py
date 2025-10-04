## api.py


import os
import tempfile
from datetime import datetime

from flask import Blueprint, request, jsonify, json

from app import db
from models import Resource, UserType, VerifiedEmail, Category, Subcategory
from services.transcribe import transcribe_audio
from services.legal_entity_verification import verify_legal_entity

api_bp = Blueprint('api', __name__)


@api_bp.post('/process_message/')
def process_message():
    from services.llm import extract_resource_fields

    payload = {}

    if request.content_type and request.content_type.startswith('multipart/form-data'):
        meta_json = request.form.get('metadata', '{}')
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

    incident_location = metadata.get("incident_location")
    if not incident_location:
        return jsonify({"error": "Missing required 'incident_location' field in metadata."}), 400

    user_location = metadata.get("user_location")
    user_type_val = metadata.get("user_type")

    extracted_list = extract_resource_fields(
        text=text,
        incident_location=incident_location,
        user_type=user_type_val,
        user_location=user_location,
    )
    if not extracted_list:
        return jsonify({"error": "Could not extract any valid resources from the message."}), 400

    location_geojson = incident_location
    resources_created = []

    for extracted in extracted_list:
        if not extracted.get("location_geojson"):
            continue

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
            subcategory=extracted.get('subcategory'),
            name=extracted.get('name') or 'unknown',
            quantity=quantity,
            num_available_people=extracted.get('num_available_people'),
            location_geojson=extracted.get("location_geojson") or location_geojson,
            location_text=extracted.get("location_text"),
            distance_km=extracted.get("distance_km"),
            phone_number=extracted.get("phone_number") or metadata.get("phone_number"),
            email=extracted.get("email") or metadata.get("email"),
            first_name=extracted.get("first_name") or metadata.get("first_name"),
            last_name=extracted.get("last_name") or metadata.get("last_name"),
            source_text=text,
            user_type=user_type,
            created_at=datetime.utcnow(),
            flagged=extracted.get('flagged', False),
            abuse_reason=extracted.get('abuse_reason'),
        )

        db.session.add(resource)
        resources_created.append(resource)

    db.session.commit()

    return jsonify({
        "ok": True,
        "resources": [
            {
                "id": r.id,
                "category": r.category.value if r.category else None,
                "subcategory": r.subcategory.value if r.subcategory else None,
                "name": r.name,
                "quantity": r.quantity,
                "num_available_people": r.num_available_people,
                "location_geojson": r.location_geojson,
                "location_text": r.location_text,
                "distance_km": r.distance_km,
                "phone_number": r.phone_number,
                "email": r.email,
                "first_name": r.first_name,
                "last_name": r.last_name,
                "source_text": r.source_text,
                "user_type": r.user_type.value if r.user_type else None,
                "created_at": r.created_at.isoformat() + 'Z',
                "flagged": r.flagged,
                "abuse_reason": r.abuse_reason,
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
                "category": r.category.value if r.category else None,
                "subcategory": r.subcategory.value if getattr(r, "subcategory", None) else None,
                "name": r.name,
                "quantity": r.quantity,
                "num_available_people": r.num_available_people,
                "location_geojson": r.location_geojson,
                "location_text": r.location_text,
                "distance_km": r.distance_km,
                "phone_number": r.phone_number,
                "email": r.email,
                "first_name": r.first_name,
                "last_name": r.last_name,
                "source_text": r.source_text,
                "user_type": r.user_type.value if r.user_type else None,
                "created_at": r.created_at.isoformat() + 'Z',
                "flagged": r.flagged,
                "abuse_reason": r.abuse_reason,
            }
            for r in resources
        ]
    })



@api_bp.post("/resources/create/")
def create_resource():
    """
    Manually create a new Resource entry.

    Example JSON body:
    {
        "category": "MEDICAL_SUPPLIES",
        "subcategory": "FIRST_AID",
        "name": "first aid kit",
        "quantity": 12,
        "num_available_people": 3,
        "location_text": "Tampere central hospital",
        "location_geojson": {
            "type": "Point",
            "coordinates": [23.7610, 61.4981]
        },
        "phone_number": "+358401234567",
        "email": "liisa.virtanen@example.com",
        "first_name": "Liisa",
        "last_name": "Virtanen",
        "user_type": "GOVERNMENT_AGENCY",
        "source_text": "manual entry"
    }
    """
    data = request.get_json(silent=True) or {}

    # Basic validation
    if not data.get("name"):
        return jsonify({"ok": False, "error": "Field 'name' is required."}), 400

    # Parse category and subcategory enums
    category = None
    subcategory = None
    if data.get("category"):
        try:
            category = Category[data["category"].upper()]
        except KeyError:
            return jsonify({"ok": False, "error": f"Invalid category '{data['category']}'."}), 400

    if data.get("subcategory"):
        try:
            subcategory = Subcategory[data["subcategory"].upper()]
        except KeyError:
            return jsonify({"ok": False, "error": f"Invalid subcategory '{data['subcategory']}'."}), 400

    # Quantity and num_available_people
    try:
        quantity = int(data["quantity"]) if data.get("quantity") is not None else None
    except ValueError:
        return jsonify({"ok": False, "error": "Invalid 'quantity' (must be integer)."}), 400

    try:
        num_available_people = int(data["num_available_people"]) if data.get("num_available_people") is not None else None
    except ValueError:
        return jsonify({"ok": False, "error": "Invalid 'num_available_people' (must be integer)."}), 400

    # Parse user_type enum if provided
    user_type = None
    if data.get("user_type"):
        try:
            user_type = UserType[data["user_type"].upper()]
        except KeyError:
            return jsonify({"ok": False, "error": f"Invalid user_type '{data['user_type']}'."}), 400

    # Build resource instance
    resource = Resource(
        category=category,
        subcategory=subcategory,
        name=data.get("name"),
        quantity=quantity,
        num_available_people=num_available_people,
        location_geojson=data.get("location_geojson"),
        location_text=data.get("location_text"),
        distance_km=data.get("distance_km"),
        phone_number=data.get("phone_number"),
        email=data.get("email"),
        first_name=data.get("first_name"),
        last_name=data.get("last_name"),
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
            "category": resource.category.value if resource.category else None,
            "subcategory": resource.subcategory.value if resource.subcategory else None,
            "name": resource.name,
            "quantity": resource.quantity,
            "num_available_people": resource.num_available_people,
            "location_geojson": resource.location_geojson,
            "location_text": resource.location_text,
            "distance_km": resource.distance_km,
            "phone_number": resource.phone_number,
            "email": resource.email,
            "first_name": resource.first_name,
            "last_name": resource.last_name,
            "source_text": resource.source_text,
            "user_type": resource.user_type.value if resource.user_type else None,
            "created_at": resource.created_at.isoformat() + "Z",
            "flagged": resource.flagged,
            "abuse_reason": resource.abuse_reason,
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
