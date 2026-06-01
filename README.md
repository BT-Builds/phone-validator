# Phone Validator API

Validate and parse international phone numbers via a simple HTTP API.

## Endpoints

### GET /health
Health check endpoint (no auth required).

### POST /validate
Validate a phone number and get parsed details.

**Headers:**
```
X-API-Key: demo-key-change-me
Content-Type: application/json
```

**Body:**
```json
{"phone": "+14155551234"}
```

**Response:**
```json
{
  "valid": true,
  "formatted": "+14155551234",
  "country_code": "+1",
  "national_number": "4155551234",
  "carrier": "AT&T",
  "region": "US",
  "type": "Mobile"
}
```

**Curl example:**
```bash
curl -X POST https://phone-validator.vercel.app/validate \
  -H "Content-Type: application/json" \
  -H "X-API-Key: demo-key-change-me" \
  -d '{"phone": "+14155551234"}'
```

## Pricing
- $19/month for 10,000 validations
- $49/month for 100,000 validations

Built for developers who need reliable phone validation without heavy libraries.