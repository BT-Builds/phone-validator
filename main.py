import os as _o, time as _t, json as _j
from urllib.request import Request as _Rq, urlopen as _uo
from fastapi import Header, HTTPException, Depends
_UU=_o.environ.get('UPSTASH_REDIS_REST_URL','')
_UT=_o.environ.get('UPSTASH_REDIS_REST_TOKEN','')
_LIM={'free':1000,'starter':25000,'pro':200000,'demo':50}
def _redis(c):
    try: return _j.loads(_uo(_Rq(f'{_UU}/{c[0]}/'+'/'.join(map(str,c[1:])),headers={'Authorization':f'Bearer {_UT}'}),timeout=3).read()).get('result')
    except: return None
def verify_api_key(x_api_key: str = Header(default='free-demo-key')):
    if not _UU: return {'key':x_api_key,'tier':'free'}
    tier='demo'
    if x_api_key!='free-demo-key':
        raw=_redis(['GET',f'key:{x_api_key}'])
        if not raw: raise HTTPException(401,'Invalid key. Get one at btbuilds.lemonsqueezy.com')
        d=_j.loads(raw)
        if not d.get('active',True): raise HTTPException(401,'Key revoked')
        tier=d.get('tier','free')
    m=_t.strftime('%Y-%m')
    used=int(_redis(['INCR',f'usage:{x_api_key}:{m}']) or 1)
    if used==1: _redis(['EXPIRE',f'usage:{x_api_key}:{m}',2678400])
    lim=_LIM.get(tier,1000)
    if used>lim: raise HTTPException(429,f'Monthly limit {lim:,}/mo reached.')
    return {'key':x_api_key,'tier':tier,'used':used}

import re
from fastapi import FastAPI
from pydantic import BaseModel
from mangum import Mangum

app = FastAPI(title='Phone Validator API')

class PhoneRequest(BaseModel):
    phone: str

class BulkPhoneRequest(BaseModel):
    items: list[str]

def get_line_type(phone_e164: str) -> dict:
    if phone_e164.startswith('+1'):
        digits = phone_e164[2:]
        npa = digits[:3]
        voip_npas = ['500','533','544','566','577','588']
        if npa in voip_npas:
            return {'line_type': 'voip', 'carrier_hint': 'VoIP/Internet'}
        if npa in ['800','833','844','855','866','877','888']:
            return {'line_type': 'toll_free', 'carrier_hint': 'Toll-free'}
        return {'line_type': 'mobile_or_landline', 'carrier_hint': 'Unknown'}
    country_hints = {
        '+44': {'line_type': 'unknown', 'carrier_hint': 'UK number'},
        '+61': {'line_type': 'unknown', 'carrier_hint': 'Australian number'},
        '+49': {'line_type': 'unknown', 'carrier_hint': 'German number'},
    }
    for prefix, info in country_hints.items():
        if phone_e164.startswith(prefix):
            return info
    return {'line_type': 'unknown', 'carrier_hint': 'International'}

def parse_phone(phone: str) -> dict:
    digits = re.sub(r'[^\d+]', '', phone)
    if digits.startswith('+'): 
        clean = digits
    else:
        clean = '+' + digits
    valid = bool(re.match(r'^\+[1-9]\d{6,14}$', clean))
    result = {'valid': valid, 'normalized': clean if valid else None, 'input': phone}
    if valid:
        line_info = get_line_type(clean)
        result.update(line_info)
    else:
        result['line_type'] = None
        result['carrier_hint'] = None
    return result

@app.get('/health')
def health(): return {'status': 'ok'}

@app.post('/validate')
def validate(req: PhoneRequest, _=Depends(verify_api_key)):
    return parse_phone(req.phone)

@app.post('/bulk/validate')
def validate_bulk(req: BulkPhoneRequest, _=Depends(verify_api_key)):
    items = req.items[:1000]  # Cap at 1000 items
    results = []
    successful = 0
    for phone in items:
        try:
            output = parse_phone(phone)
            successful += 1
            results.append({"input": phone, "output": output, "error": None})
        except Exception as e:
            results.append({"input": phone, "output": None, "error": str(e)})
    return {"results": results, "total": len(items), "successful": successful}

handler = Mangum(app, lifespan='off')