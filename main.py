import os
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
import phonenumbers
from phonenumbers import NumberParseException

app = FastAPI(title="Phone Validator API", version="1.0.0")

API_KEY = os.environ.get("API_KEY", "demo-key-change-me")

class PhoneRequest(BaseModel):
    phone: str

class PhoneResponse(BaseModel):
    valid: bool
    formatted: Optional[str] = None
    country_code: Optional[str] = None
    national_number: Optional[str] = None
    carrier: Optional[str] = None
    region: Optional[str] = None
    type: Optional[str] = None

def verify_api_key(x_api_key: str = ""):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/validate", response_model=PhoneResponse, dependencies=[Depends(verify_api_key)])
def validate_phone(request: PhoneRequest):
    try:
        parsed = phonenumbers.parse(request.phone, None)
    except NumberParseException:
        return {"valid": False}

    if not phonenumbers.is_valid_number(parsed):
        return {"valid": False}

    return {
        "valid": True,
        "formatted": phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164),
        "country_code": f"+{parsed.country_code}",
        "national_number": str(parsed.national_number),
        "carrier": phonenumbers.carrier.name_for_number(parsed, "en") if phonenumbers.carrier else None,
        "region": phonenumbers.region_code_for_number(parsed),
        "type": ["Fixed", "Mobile", "TollFree", "Premium", "Shared", "VoIP", "Personal", "Pager", "UAN", "Unknown"][phonenumbers.number_type(parsed)]
    }

try:
    from mangum import Mangum
    handler = Mangum(app, lifespan="off")
except ImportError:
    pass
