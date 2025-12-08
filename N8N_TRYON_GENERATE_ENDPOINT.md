# N8N API Integration Guide - Generate Try-On (Button Click)

## Complete API Endpoint Details for Try-On Generation

---

## Endpoint Information

**Full URL:**
```
https://tablet-bugfix.preview.emergentagent.com/api/tryon
```

**Method:** `POST`

**Content-Type:** `application/json`

---

## Request Format (Using Upload IDs)

### Headers
```
Content-Type: application/json
```

### Body (JSON)
```json
{
  "person_upload_id": "uuid-from-person-upload",
  "clothing_upload_id": "uuid-from-clothing-upload"
}
```

**Note:** Use the `upload_id` values you received from the previous upload API calls.

---

## Response Format

### Success Response (200 OK)
```json
{
  "id": "tryon-abc-123-def-456",
  "result_image": "base64-encoded-result-image-string",
  "timestamp": "2025-12-06T20:50:00.123456",
  "status": "completed"
}
```

**Response Fields:**
- `id` - Unique try-on ID
- `result_image` - Base64-encoded generated image (person wearing the clothing)
- `timestamp` - When the try-on was generated (ISO format)
- `status` - "completed" on success

### Error Response (400/404/500)
```json
{
  "detail": "Error message here"
}
```

**Common Errors:**
- `404` - "Person upload ID not found" or "Clothing upload ID not found"
- `400` - "Must provide either (person_image + clothing_image) OR (person_upload_id + clothing_upload_id)"
- `500` - Gemini API errors or processing errors

---

## N8N Configuration

### Node: HTTP Request

**Configuration:**

1. **Method:** `POST`

2. **URL:** `https://tablet-bugfix.preview.emergentagent.com/api/tryon`

3. **Authentication:** None

4. **Body Content Type:** `JSON`

5. **Body Parameters:**
   ```json
   {
     "person_upload_id": "{{ $json.person_upload_id }}",
     "clothing_upload_id": "{{ $json.clothing_upload_id }}"
   }
   ```

6. **Headers:**
   - Name: `Content-Type`
   - Value: `application/json`

7. **Timeout:** Set to 60000ms (60 seconds) - AI generation takes time!

---

## Complete N8N Workflow (All 3 Steps)

### Step 1: Upload Person Image
```
HTTP POST to /api/upload/person
→ Returns: person_upload_id
```

### Step 2: Upload Clothing Image
```
HTTP POST to /api/upload/clothing
→ Returns: clothing_upload_id
```

### Step 3: Generate Try-On (This endpoint)
```
HTTP POST to /api/tryon
→ Returns: result_image (base64)
```

---

## Complete N8N Workflow Example

### Node 1: Upload Person Image
- **URL:** `https://tablet-bugfix.preview.emergentagent.com/api/upload/person`
- **Method:** POST
- **Body:** `{"image": "{{ $json.person_image_base64 }}"}`

### Node 2: Upload Clothing Image
- **URL:** `https://tablet-bugfix.preview.emergentagent.com/api/upload/clothing`
- **Method:** POST
- **Body:** `{"image": "{{ $json.clothing_image_base64 }}"}`

### Node 3: Generate Try-On
- **URL:** `https://tablet-bugfix.preview.emergentagent.com/api/tryon`
- **Method:** POST
- **Body:**
  ```json
  {
    "person_upload_id": "{{ $('Upload Person Image').item.json.upload_id }}",
    "clothing_upload_id": "{{ $('Upload Clothing Image').item.json.upload_id }}"
  }
  ```

### Node 4: Save Result Image
Extract and save the result:
```javascript
// Code node to save base64 image
const resultBase64 = $json.result_image;
const tryonId = $json.id;

// Convert base64 to buffer for saving
const imageBuffer = Buffer.from(resultBase64, 'base64');

return {
  json: {
    tryon_id: tryonId,
    timestamp: $json.timestamp
  },
  binary: {
    data: imageBuffer
  }
};
```

---

## Testing with cURL

### Complete Flow Test

```bash
# Step 1: Upload person image
PERSON_RESPONSE=$(curl -s -X POST https://tablet-bugfix.preview.emergentagent.com/api/upload/person \
  -H "Content-Type: application/json" \
  -d '{
    "image": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
  }')

PERSON_UPLOAD_ID=$(echo $PERSON_RESPONSE | jq -r '.upload_id')
echo "Person Upload ID: $PERSON_UPLOAD_ID"

# Step 2: Upload clothing image
CLOTHING_RESPONSE=$(curl -s -X POST https://tablet-bugfix.preview.emergentagent.com/api/upload/clothing \
  -H "Content-Type: application/json" \
  -d '{
    "image": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
  }')

CLOTHING_UPLOAD_ID=$(echo $CLOTHING_RESPONSE | jq -r '.upload_id')
echo "Clothing Upload ID: $CLOTHING_UPLOAD_ID"

# Step 3: Generate try-on
curl -X POST https://tablet-bugfix.preview.emergentagent.com/api/tryon \
  -H "Content-Type: application/json" \
  -d "{
    \"person_upload_id\": \"$PERSON_UPLOAD_ID\",
    \"clothing_upload_id\": \"$CLOTHING_UPLOAD_ID\"
  }"
```

### Direct Test (if you already have upload IDs)
```bash
curl -X POST https://tablet-bugfix.preview.emergentagent.com/api/tryon \
  -H "Content-Type: application/json" \
  -d '{
    "person_upload_id": "c6921362-d6b4-4cfe-8b03-d33c86120be2",
    "clothing_upload_id": "0da6ba92-81e9-44ed-9e68-196000c2d8ad"
  }'
```

---

## N8N Node Configuration (Visual Guide)

### HTTP Request Node Settings

**Request Method:**
```
POST
```

**URL:**
```
https://tablet-bugfix.preview.emergentagent.com/api/tryon
```

**Authentication:**
```
None
```

**Send Body:**
```
Yes
```

**Body Content Type:**
```
JSON
```

**Specify Body:**
```
Using JSON
```

**JSON Body:**
```json
{
  "person_upload_id": "={{ $json.person_upload_id }}",
  "clothing_upload_id": "={{ $json.clothing_upload_id }}"
}
```

**Options:**
- **Timeout:** 60000 (60 seconds - important for AI generation!)
- **Response Format:** JSON
- **Full Response:** No

---

## Complete N8N Workflow (Importable JSON)

```json
{
  "nodes": [
    {
      "parameters": {
        "method": "POST",
        "url": "https://tablet-bugfix.preview.emergentagent.com/api/upload/person",
        "sendBody": true,
        "bodyParameters": {
          "parameters": [
            {
              "name": "image",
              "value": "={{ $json.person_image_base64 }}"
            }
          ]
        }
      },
      "name": "Upload Person Image",
      "type": "n8n-nodes-base.httpRequest",
      "position": [400, 300]
    },
    {
      "parameters": {
        "method": "POST",
        "url": "https://tablet-bugfix.preview.emergentagent.com/api/upload/clothing",
        "sendBody": true,
        "bodyParameters": {
          "parameters": [
            {
              "name": "image",
              "value": "={{ $json.clothing_image_base64 }}"
            }
          ]
        }
      },
      "name": "Upload Clothing Image",
      "type": "n8n-nodes-base.httpRequest",
      "position": [600, 300]
    },
    {
      "parameters": {
        "method": "POST",
        "url": "https://tablet-bugfix.preview.emergentagent.com/api/tryon",
        "sendBody": true,
        "bodyParameters": {
          "parameters": [
            {
              "name": "person_upload_id",
              "value": "={{ $('Upload Person Image').item.json.upload_id }}"
            },
            {
              "name": "clothing_upload_id",
              "value": "={{ $('Upload Clothing Image').item.json.upload_id }}"
            }
          ]
        },
        "options": {
          "timeout": 60000
        }
      },
      "name": "Generate Try-On",
      "type": "n8n-nodes-base.httpRequest",
      "position": [800, 300]
    }
  ],
  "connections": {
    "Upload Person Image": {
      "main": [
        [
          {
            "node": "Upload Clothing Image",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Upload Clothing Image": {
      "main": [
        [
          {
            "node": "Generate Try-On",
            "type": "main",
            "index": 0
          }
        ]
      ]
    }
  }
}
```

---

## Handling the Result Image

### Option 1: Save to File
```javascript
// Code node after try-on
const base64Image = $json.result_image;
const imageBuffer = Buffer.from(base64Image, 'base64');

return {
  binary: {
    data: imageBuffer,
    fileName: `tryon_${$json.id}.png`,
    mimeType: 'image/png'
  }
};
```

### Option 2: Send to Webhook/API
```json
{
  "tryon_id": "{{ $json.id }}",
  "result_image": "data:image/png;base64,{{ $json.result_image }}"
}
```

### Option 3: Upload to Cloud Storage
Use n8n's cloud storage nodes (S3, Google Drive, etc.) with the binary data

---

## Alternative: Direct Image Mode (Old Method)

If you want to skip the upload steps and send images directly:

### Request Body (Direct Images)
```json
{
  "person_image": "base64-person-image",
  "clothing_image": "base64-clothing-image"
}
```

**Note:** This still works for backward compatibility, but upload IDs method is recommended.

---

## Error Handling in N8N

### Check Upload IDs Before Try-On
Add an IF node:
```javascript
{{ $json.person_upload_id !== undefined && $json.clothing_upload_id !== undefined }}
```

### Retry Logic
In HTTP Request node options:
- **Retry On Fail:** Yes
- **Max Retries:** 2
- **Wait Between Retries:** 2000ms

### Handle Timeouts
- Set timeout to 60000ms (60 seconds)
- AI generation can take 20-40 seconds
- Add error handling for timeout cases

---

## Complete Flow Diagram

```
[Start]
    ↓
[Get Person Image] → [Convert to Base64]
    ↓
[POST /api/upload/person] → Get person_upload_id
    ↓
[Get Clothing Image] → [Convert to Base64]
    ↓
[POST /api/upload/clothing] → Get clothing_upload_id
    ↓
[POST /api/tryon] ← Use both upload_ids
    ↓
[Receive result_image (base64)]
    ↓
[Save/Process Result]
    ↓
[End]
```

---

## Performance Notes

### Expected Response Times:
- Upload Person: ~500ms
- Upload Clothing: ~500ms
- **Generate Try-On: 20-40 seconds** (AI processing)

### Tips:
- Set timeout to at least 60 seconds
- Show loading indicator during generation
- Consider adding retry logic
- Cache upload IDs if trying multiple outfits on same person

---

## Quick Copy-Paste for N8N

**Endpoint URL:**
```
https://tablet-bugfix.preview.emergentagent.com/api/tryon
```

**Method:**
```
POST
```

**Body (JSON):**
```json
{
  "person_upload_id": "={{ $json.person_upload_id }}",
  "clothing_upload_id": "={{ $json.clothing_upload_id }}"
}
```

**Timeout:**
```
60000
```

**Response - Result Image Path:**
```
{{ $json.result_image }}
```

**Response - Try-On ID:**
```
{{ $json.id }}
```

---

## What Happens Behind the Scenes

When you call this endpoint:

1. ✅ Backend retrieves both images from MongoDB using upload IDs
2. ✅ Images are decoded from base64 to bytes
3. ✅ Mime types are detected
4. ✅ Images + AI prompt sent to Gemini 2.5 Flash Image
5. ✅ AI generates the try-on result (20-40 seconds)
6. ✅ Result image encoded to base64
7. ✅ Saved to MongoDB with try-on ID
8. ✅ Sent to n8n webhook automatically (background)
9. ✅ Result returned to your request

---

## Summary

✅ **Endpoint:** `https://tablet-bugfix.preview.emergentagent.com/api/tryon`  
✅ **Method:** POST  
✅ **Body:** `{"person_upload_id": "uuid", "clothing_upload_id": "uuid"}`  
✅ **Returns:** `{"id": "tryon-id", "result_image": "base64", ...}`  
✅ **Timeout:** Set to 60 seconds minimum  
✅ **Processing Time:** 20-40 seconds  

---

**This is the "Generate Try-On" button API - ready to use!** 🚀
