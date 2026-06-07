import os
from fastapi import Header, FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
import phonenumbers
from phonenumbers import NumberParseException

# ── API Key Auth (Upstash Redis) ───────────────────────────────────────────────
import os, time, json as _json
from urllib.request import Request as _Req, urlopen as _urlopen

_UPSTASH_URL   = os.environ.get('UPSTASH_REDIS_REST_URL', '')
_UPSTASH_TOKEN = os.environ.get('UPSTASH_REDIS_REST_TOKEN', '')
_TIERS = {'free': 1000, 'starter': 25000, 'pro': 200000, 'demo': 50}

def _redis(cmd):
    url = f'{_UPSTASH_URL}/{cmd[0]}/' + '/'.join(str(x) for x in cmd[1:])
    req = _Req(url, headers={'Authorization': f'Bearer {_UPSTASH_TOKEN}'})
    try:
        return _json.loads(_urlopen(req, timeout=3).read()).get('result')
    except: return None

def verify_api_key(x_api_key: str = Header(default='free-demo-key')):
    if not _UPSTASH_URL:  # no Upstash configured, allow all (dev mode)
        return {'key': x_api_key, 'tier': 'free'}
    tier = 'demo'
    if x_api_key != 'free-demo-key':
        raw = _redis(['GET', f'key:{x_api_key}'])
        if not raw:
            raise HTTPException(401, 'Invalid API key. Get one at btbuilds.lemonsqueezy.com')
        data = _json.loads(raw)
        if not data.get('active', True):
            raise HTTPException(401, 'API key revoked')
        tier = data.get('tier', 'free')
    month = time.strftime('%Y-%m')
    used = int(_redis(['INCR', f'usage:{x_api_key}:{month}']) or 1)
    if used == 1: _redis(['EXPIRE', f'usage:{x_api_key}:{month}', 2678400])
    limit = _TIERS.get(tier, 1000)
    if used > limit:
        raise HTTPException(429, f'Monthly limit reached ({limit:,}/mo). Upgrade at btbuilds.lemonsqueezy.com')
    return {'key': x_api_key, 'tier': tier, 'used': used}


app = FastAPI(title="Phone Validator API", version="1.0.0")
# === BT Builds Standard Middleware (auto-injected) ===
from fastapi.middleware.cors import CORSMiddleware as _BTCors
app.add_middleware(_BTCors, allow_origins=["*"], allow_methods=["*"],
    allow_headers=["*"], expose_headers=["X-RateLimit-Limit","X-RateLimit-Remaining","X-RateLimit-Reset"])

@app.middleware("http")
async def _bt_add_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Powered-By"] = "btbuilds"
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response


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