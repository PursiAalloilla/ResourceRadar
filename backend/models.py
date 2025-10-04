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

class Category(Enum):
    SKILLS = "SKILLS"
    FUEL = "FUEL"
    FOOD = "FOOD"
    WATER = "WATER"
    MEDICAL_SUPPLIES = "MEDICAL_SUPPLIES"
    SHELTER = "SHELTER"
    TRANSPORT = "TRANSPORT"
    EQUIPMENT = "EQUIPMENT"
    COMMUNICATION = "COMMUNICATION"
    OTHER = "OTHER"


class Subcategory(Enum):
    # SKILLS
    MEDICAL = "MEDICAL"
    CONSTRUCTION = "CONSTRUCTION"
    IT = "IT"
    LANGUAGE = "LANGUAGE"
    MECHANIC = "MECHANIC"
    OTHER = "OTHER"

    # FUEL
    DIESEL = "DIESEL"
    GASOLINE = "GASOLINE"
    PROPANE = "PROPANE"
    BATTERIES = "BATTERIES"

    # FOOD
    NON_PERISHABLE = "NON_PERISHABLE"
    PERISHABLE = "PERISHABLE"
    BABY_FOOD = "BABY_FOOD"
    PET_FOOD = "PET_FOOD"

    # WATER
    BOTTLED = "BOTTLED"
    FILTERS = "FILTERS"
    PURIFICATION_TABLETS = "PURIFICATION_TABLETS"

    # MEDICAL_SUPPLIES
    FIRST_AID = "FIRST_AID"
    MEDICATION = "MEDICATION"
    EQUIPMENT = "EQUIPMENT"

    # SHELTER
    TENTS = "TENTS"
    BLANKETS = "BLANKETS"

    # TRANSPORT
    VEHICLES = "VEHICLES"
    BOATS = "BOATS"
    FUEL_TRUCKS = "FUEL_TRUCKS"

    # EQUIPMENT
    GENERATORS = "GENERATORS"
    TOOLS = "TOOLS"
    PROTECTIVE_GEAR = "PROTECTIVE_GEAR"

    # COMMUNICATION
    RADIOS = "RADIOS"
    SATPHONES = "SATPHONES"
    POWER_BANKS = "POWER_BANKS"

    # OTHER
    UNKNOWN = "UNKNOWN"

class Resource(db.Model):
    __tablename__ = 'resources'

    id = db.Column(db.Integer, primary_key=True)

    # Core resource details
    category = db.Column(SAEnum(Category), nullable=True)
    subcategory = db.Column(SAEnum(Subcategory), nullable=True)
    name = db.Column(db.String(200), nullable=False)
    quantity = db.Column(db.Integer, nullable=True)
    num_available_people = db.Column(db.Integer, nullable=True)

    # Location and distance info
    location_geojson = db.Column(JSON, nullable=True)
    location_text = db.Column(db.String(255), nullable=True)
    distance_km = db.Column(db.Float, nullable=True)

    # Contact or ownership data
    phone_number = db.Column(db.String(64), nullable=True)
    email = db.Column(db.String(255), nullable=True)
    first_name = db.Column(db.String(120), nullable=True)
    last_name = db.Column(db.String(120), nullable=True)

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
    openai_model = db.Column(db.String(50), default='gpt-4o-mini')
