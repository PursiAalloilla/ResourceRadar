from datetime import datetime
from enum import Enum
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.sqlite import JSON
from extensions import db


class UserType(Enum):
    NGO = 'NGO'
    CORPORATE = 'corporate'
    CIVILIAN = 'civilian'
    CORPORATE_ENTITY = 'corporate entity'
    AI_MODEL = 'ai model'


class Resource(db.Model):
    __tablename__ = 'resources'

    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(120), nullable=True)
    name = db.Column(db.String(200), nullable=False)
    quantity = db.Column(db.Integer, nullable=True)
    location_geojson = db.Column(JSON, nullable=True)
    phone_number = db.Column(db.String(64), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    first_name = db.Column(db.String(120), nullable=True)
    last_name = db.Column(db.String(120), nullable=True)
    social_security_number = db.Column(db.String(64), nullable=True)

    source_text = db.Column(db.Text, nullable=True)
    user_type = db.Column(SAEnum(UserType), nullable=True)

    flagged = db.Column(db.Boolean, default=False, nullable=False) 


class AppSetting(db.Model):
    __tablename__ = 'app_settings'

    id = db.Column(db.Integer, primary_key=True)
    llm_backend = db.Column(db.String(20), default='hf')
    hf_model_id = db.Column(db.String(200), default='microsoft/Phi-3.5-MoE-instruct')
    hf_device = db.Column(db.String(16), default='cpu')
    openai_model = db.Column(db.String(50), default='gpt-4o-mini')
