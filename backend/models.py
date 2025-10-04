from datetime import datetime
from enum import Enum
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.sqlite import JSON
from extensions import db


class UserType(Enum):
    CIVILIAN = 'CIVILIAN'
    NGO = 'NGO'
    GOVERNMENT_AGENCY = 'GOVERNMENT_AGENCY'
    CORPORATE_ENTITY = 'CORPORATE_ENTITY'
    LOCAL_AUTHORITY = 'LOCAL_AUTHORITY'

class Resource(db.Model):
    __tablename__ = 'resources'

    id = db.Column(db.Integer, primary_key=True)

    # Core resource details
    category = db.Column(db.String(120), nullable=True)
    name = db.Column(db.String(200), nullable=False)
    quantity = db.Column(db.Integer, nullable=True)

    # Location and distance info
    location_geojson = db.Column(JSON, nullable=True)
    location_text = db.Column(db.String(255), nullable=True)
    distance_km = db.Column(db.Float, nullable=True)

    # Contact or ownership data
    phone_number = db.Column(db.String(64), nullable=True)
    first_name = db.Column(db.String(120), nullable=True)
    last_name = db.Column(db.String(120), nullable=True)
    social_security_number = db.Column(db.String(64), nullable=True)

    # Source and metadata
    source_text = db.Column(db.Text, nullable=True)
    user_type = db.Column(SAEnum(UserType), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Abuse detection flags
    flagged = db.Column(db.Boolean, default=False, nullable=False)
    abuse_reason = db.Column(db.Text, nullable=True)

    def mark_flagged(self, reason: str):
        """Helper method to mark a resource as suspicious."""
        self.flagged = True
        self.abuse_reason = reason

class VerifiedEmail(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    user_type = db.Column(db.String(64), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

class AppSetting(db.Model):
    __tablename__ = 'app_settings'

    id = db.Column(db.Integer, primary_key=True)
    llm_backend = db.Column(db.String(20), default='hf')
    hf_model_id = db.Column(db.String(200), default='microsoft/Phi-3.5-MoE-instruct')
    hf_device = db.Column(db.String(16), default='cpu')
    openai_model = db.Column(db.String(50), default='gpt-4o-mini')
