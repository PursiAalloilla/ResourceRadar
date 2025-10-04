import os
import re
import json
from flask import current_app
from openai import OpenAI

# Try initializing OpenAI client
_OPENAI_AVAILABLE = bool(os.getenv("OPENAI_API_KEY"))
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY")) if _OPENAI_AVAILABLE else None

# Disallowed personal or educational domains
DISALLOWED_DOMAINS = [
    "gmail.com", "yahoo.com", "hotmail.com", "outlook.com",
    "protonmail.com", "icloud.com", "mail.com", "edu"
]


def extract_domain(email: str) -> str:
    """Extract domain name from email address."""
    match = re.search(r"@([\w\.-]+)$", (email or "").lower())
    return match.group(1) if match else ""


def is_generic_domain(domain: str) -> bool:
    """Return True if domain looks personal or educational."""
    return any(bad in domain for bad in DISALLOWED_DOMAINS)


def _heuristic_verification(domain: str, user_type: str) -> dict:
    """Offline fallback check using simple rules."""
    d = domain.lower()
    t = user_type.upper()

    # Block generics
    if is_generic_domain(d):
        return {"ok": False, "reason": f"Generic or educational domain ({d}) not allowed.", "domain": d}

    # Simple heuristics
    if t == "GOVERNMENT_AGENCY":
        if d.endswith(".gov") or d.endswith(".gov.fi") or "valtioneuvosto" in d or "police" in d or "defence" in d:
            return {"ok": True, "reason": "Recognized as a government domain.", "domain": d}
        return {"ok": False, "reason": "Domain not recognized as governmental.", "domain": d}

    if t == "LOCAL_AUTHORITY":
        if d.endswith(".fi") and any(city in d for city in ["helsinki", "turku", "tampere", "oulu", "espoo"]):
            return {"ok": True, "reason": "Municipal Finnish domain detected.", "domain": d}
        return {"ok": False, "reason": "No municipal indicators in domain.", "domain": d}

    if t == "NGO":
        if d.endswith(".org") or ".org." in d or "ngo" in d or "aid" in d or "foundation" in d:
            return {"ok": True, "reason": "Domain suggests non-profit organization.", "domain": d}
        return {"ok": False, "reason": "Domain lacks NGO indicators.", "domain": d}

    if t == "CORPORATE_ENTITY":
        if any(d.endswith(suf) for suf in [".com", ".net", ".io", ".co", ".fi"]) and not (
            "gov" in d or "org" in d
        ):
            return {"ok": True, "reason": "Likely corporate or private domain.", "domain": d}
        return {"ok": False, "reason": "Domain not typical for corporate entities.", "domain": d}

    # Fallback default
    return {"ok": False, "reason": "Unknown user_type or unrecognized domain.", "domain": d}


def verify_legal_entity(email: str, user_type: str):
    """
    Uses OpenAI to check if an email domain plausibly matches the claimed user_type.
    Falls back to rule-based heuristic if OpenAI is unavailable.
    Returns: {"ok": bool, "reason": str, "domain": str}
    """
    domain = extract_domain(email)
    if not domain:
        return {"ok": False, "reason": "Invalid email format.", "domain": None}

    if is_generic_domain(domain):
        return {"ok": False, "reason": f"Generic or educational domain ({domain}) not allowed.", "domain": domain}

    # --- If no OpenAI key or client, fallback immediately ---
    if not _OPENAI_AVAILABLE:
        current_app.logger.warning("[legal_entity_verification] OpenAI key not found, using fallback heuristics.")
        return _heuristic_verification(domain, user_type)

    # --- OpenAI-powered verification ---
    prompt = f"""
    You are a domain verification AI for a national emergency coordination platform.

    The email domain is "{domain}".
    The user claims to represent a "{user_type}".

    Determine if this domain plausibly belongs to that type:
    - GOVERNMENT_AGENCY → national or regional government domains (.gov, .gov.fi, valtioneuvosto.fi)
    - LOCAL_AUTHORITY → municipal or city domains (e.g., helsinki.fi, tampere.fi)
    - NGO → domains ending in .org, .org.fi, or containing 'ngo', 'aid', or 'foundation'
    - CORPORATE_ENTITY → private company domains (.com, .fi, .net, .io, .co), not government or NGO

    Respond only with valid JSON:
    {{
      "valid": true or false,
      "reason": "short justification"
    }}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Output valid JSON only."},
                {"role": "user", "content": prompt},
            ],
            temperature=0,
        )
        text = response.choices[0].message.content.strip()
        parsed = json.loads(text)
        valid = parsed.get("valid", False)
        reason = parsed.get("reason", "No reason provided.")
        return {"ok": bool(valid), "reason": reason, "domain": domain}

    except Exception as e:
        current_app.logger.error(f"[legal_entity_verification] OpenAI check failed: {e}")
        return _heuristic_verification(domain, user_type)
