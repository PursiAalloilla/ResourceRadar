import json
import os
from typing import Dict, Any
from models import AppSetting
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline

_hf_pipeline_cache = None

def preload_hf_model(model_id: str, device: str = 'cpu'):
    """Load Hugging Face model once at startup and cache the pipeline."""
    global _hf_pipeline_cache
    if _hf_pipeline_cache is not None:
        return _hf_pipeline_cache
    tok = AutoTokenizer.from_pretrained(model_id)
    mdl = AutoModelForCausalLM.from_pretrained(model_id, torch_dtype="auto")
    _hf_pipeline_cache = pipeline(
        'text-generation',
        model=mdl,
        tokenizer=tok,
        device_map='auto' if device == 'auto' else None
    )
    return _hf_pipeline_cache


def _openai_extract(text: str) -> list[Dict[str, Any]]:
    from openai import OpenAI

    schema = {
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
                            "name": {"type": "string"},
                            "quantity": {"type": "integer"},
                            "location_text": {"type": "string"},
                            "first_name": {"type": "string"},
                            "last_name": {"type": "string"},
                            "social_security_number": {"type": "string"}
                        },
                        "required": ["name"],
                        "additionalProperties": False
                    }
                }
            },
            "required": ["resources"],
            "additionalProperties": False
        }
    }

    setting = AppSetting.query.first()
    model = setting.openai_model if setting and setting.openai_model else 'gpt-4o-mini'

    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

    resp = client.chat.completions.create(
    model=model,
    response_format={"type": "json_schema", "json_schema": schema},
    messages=[
        {
            "role": "system",
            "content": (
                "You must follow these instructions with absolute precision. "
                "Any deviation from the required JSON schema will be treated as a critical error. "
                "Your response will be strictly evaluated for compliance. "
                "Return ONLY valid JSON that exactly matches the schema. "
                "Do not include explanations, commentary, or any text outside the JSON structure. "
                "For 'name', always use the singular form (e.g. 'generators' → 'generator'). "
                "For 'quantity', infer integers when possible (e.g. 'few' → 3, 'three dozen' → 36). "
                "For 'location_text', return only the clean landmark or place name suitable for geocoding "
                "(e.g. 'Kilpisjärvi K-Market'), not phrases like 'near Kilpisjärvi K-Market' or partial words. "
                "Non-compliant outputs will be considered a system failure."
            )
        },
        {"role": "user", "content": text}
    ],
        temperature=0,
    )


    content = json.loads(resp.choices[0].message.content)
    return content.get("resources", [])




# ----- Hugging Face (local) backend -----
def _hf_extract(text: str) -> Dict[str, Any]:
    from models import AppSetting
    global _hf_pipeline_cache

    if _hf_pipeline_cache is None:
        setting = AppSetting.query.first()
        preload_hf_model(
            setting.hf_model_id if setting else 'microsoft/Phi-3.5-MoE-instruct',
            setting.hf_device if setting else 'cpu'
        )

    gen = _hf_pipeline_cache
    prompt = (
        "You are an information extractor. Given a message, produce ONLY a compact JSON object with keys: "
        "category (string), name (string), quantity (integer or null), location_text (string or null), "
        "first_name (string or null), last_name (string or null), social_security_number (string or null).\n"
        "Rules: Use singular for name. If quantity is vague like 'few', set 3. If unspecified, null. "
        "Output strictly valid JSON with double quotes, no trailing text.\n\n"
        f"Message: {text}\nJSON:"
    )

    out = gen(prompt, max_new_tokens=256, do_sample=False)[0]['generated_text']
    import re, json
    m = re.search(r"\{[\s\S]*\}", out)
    if not m:
        return {"name": None}
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return {"name": None}


def extract_resource_fields(text: str):
    """Return a list of extracted resources."""
    setting = AppSetting.query.first()
    backend = (setting.llm_backend if setting else 'hf').lower()
    if backend == 'openai':
        return _openai_extract(text)

    # HF backend can also be updated similarly if needed
    return [_hf_extract(text)]  # wrap single dict in a list
