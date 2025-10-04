## services/geocode.py

from typing import Optional, Dict, Any
from geopy.geocoders import Nominatim


_geocoder = None


def _get_geocoder():
    global _geocoder
    if _geocoder is None:
        _geocoder = Nominatim(user_agent='resource-intake-app')
    return _geocoder


def geocode_to_geojson(location_text: str) -> Optional[Dict[str, Any]]:
    if not location_text:
        return None
    geocoder = _get_geocoder()
    loc = geocoder.geocode(location_text, addressdetails=True, timeout=10)
    if not loc:
        return None
    return {
        "type": "Feature",
        "geometry": {
            "type": "Point",
            "coordinates": [loc.longitude, loc.latitude]
        },
        "properties": {
            "display_name": loc.address
        }
    }

