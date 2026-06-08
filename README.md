# Phone Validator API

Validate and parse international phone numbers via a simple HTTP API.

## Endpoints

### GET /health
Health check endpoint (no auth required).

### POST /validate
Validate a phone number and get parsed details.

**Headers:**
```
X-API-Key: free-demo-key
Content-Type: application/json
```

**Body:**
```json
{"phone": "+141****1234"}
```

**Response:**
```json
{
  "valid": true,
  "normalized": "+141****1234",
  "line_type": "mobile_or_landline",
  "carrier_hint": "Unknown"
}
```

**Curl example:**
```bash
curl -X POST https://phone-validator.vercel.app/validate \\
  -H "Content-Type: application/json" \\
  -H "X-API-Key: free-demo-key" \\
  -d '{"phone": "+141****1234"}'
```

### POST /bulk/validate
Validate up to 1000 phone numbers in a single request.

**Body:**
```json
{"items": ["+141****1234", "+441****7890"]}
```

**Response:**
```json
{
  "results": [
    {"input": "+141****1234", "output": {"valid": true, ...}, "error": null}
  ],
  "total": 2,
  "successful": 2
}
```

**Curl example:**
```bash
curl -X POST https://phone-validator.vercel.app/bulk/validate \\
  -H "Content-Type: application/json" \\
  -H "X-API-Key: free-demo-key" \\
  -d '{"items": ["+141****1234", "+441****7890"]}'
```

## Pricing
- $19/month for 10,000 validations
- $49/month for 100,000 validations

Built for developers who need reliable phone validation without heavy libraries.

## Postman
[![Run in Postman](https://run.pstmn.io/button.svg)](https://raw.githubusercontent.com/BT-Builds/phone-validator/main/postman_collection.json)
