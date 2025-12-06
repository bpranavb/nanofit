# N8N API Integration Guide - Person Image Upload

## Complete API Endpoint Details for Person Upload

---

## Endpoint Information

**Full URL:**
```
https://virtual-tryon-55.preview.emergentagent.com/api/upload/person
```

**Method:** `POST`

**Content-Type:** `application/json`

---

## Request Format

### Headers
```
Content-Type: application/json
```

### Body (JSON)
```json
{
  "image": "base64-encoded-image-string"
}
```

**Important:** The image must be base64-encoded WITHOUT the data URI prefix.

❌ **Wrong:** `"data:image/png;base64,iVBORw0KGgo..."`  
✅ **Correct:** `"iVBORw0KGgo..."`

---

## Response Format

### Success Response (200 OK)
```json
{
  "upload_id": "c6921362-d6b4-4cfe-8b03-d33c86120be2",
  "timestamp": "2025-12-06T20:47:47.613920",
  "status": "uploaded"
}
```

**Response Fields:**
- `upload_id` - UUID to use in the try-on API call
- `timestamp` - When the image was uploaded (ISO format)
- `status` - Always "uploaded" on success

### Error Response (400/500)
```json
{
  "detail": "Error message here"
}
```

---

## N8N Configuration

### Node: HTTP Request

**Configuration:**

1. **Method:** `POST`

2. **URL:** `https://virtual-tryon-55.preview.emergentagent.com/api/upload/person`

3. **Authentication:** None (unless you add auth later)

4. **Body Content Type:** `JSON`

5. **Body Parameters:**
   ```json
   {
     "image": "{{ $json.image_base64 }}"
   }
   ```
   
   Or if you have the image data directly:
   ```json
   {
     "image": "{{ $binary.data.toString('base64') }}"
   }
   ```

6. **Headers:**
   - Name: `Content-Type`
   - Value: `application/json`

---

## Complete N8N Workflow Example

### Step 1: Read File or Receive Webhook
Configure to receive/read the image file

### Step 2: Convert to Base64 (if needed)
Use Code node:
```javascript
// If you have binary data
const base64Image = $input.item.binary.data.toString('base64');

return {
  json: {
    image_base64: base64Image
  }
};
```

### Step 3: HTTP Request - Upload Person Image
- **Method:** POST
- **URL:** `https://virtual-tryon-55.preview.emergentagent.com/api/upload/person`
- **Body:**
  ```json
  {
    "image": "{{ $json.image_base64 }}"
  }
  ```

### Step 4: Extract Upload ID
Use Set node to save the upload_id:
```javascript
{
  "person_upload_id": "{{ $json.upload_id }}"
}
```

---

## Testing with cURL

### Basic Test
```bash
curl -X POST https://virtual-tryon-55.preview.emergentagent.com/api/upload/person \
  -H "Content-Type: application/json" \
  -d '{
    "image": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
  }'
```

### With Real Image File
```bash
# First, encode your image to base64
base64 -w 0 person.jpg > person_base64.txt

# Then send it
curl -X POST https://virtual-tryon-55.preview.emergentagent.com/api/upload/person \
  -H "Content-Type: application/json" \
  -d "{\"image\":\"$(cat person_base64.txt)\"}"
```

### Expected Response
```json
{
  "upload_id": "abc-123-def-456",
  "timestamp": "2025-12-06T20:47:47.613920",
  "status": "uploaded"
}
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
https://virtual-tryon-55.preview.emergentagent.com/api/upload/person
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
  "image": "={{ $json.image_base64 }}"
}
```

**Options → Response:**
- Response Format: `JSON`
- Full Response: `No` (just get body)

---

## Complete N8N Example (JSON Format)

You can import this directly into n8n:

```json
{
  "nodes": [
    {
      "parameters": {
        "method": "POST",
        "url": "https://virtual-tryon-55.preview.emergentagent.com/api/upload/person",
        "sendBody": true,
        "bodyParameters": {
          "parameters": [
            {
              "name": "image",
              "value": "={{ $json.image_base64 }}"
            }
          ]
        },
        "options": {}
      },
      "name": "Upload Person Image",
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 4.1,
      "position": [400, 300]
    }
  ]
}
```

---

## Handling Image from Different Sources

### From File Upload (Binary Data)
```javascript
// Code node to convert binary to base64
const binaryData = $input.item.binary.data;
const base64String = binaryData.toString('base64');

return {
  json: {
    image_base64: base64String
  }
};
```

### From URL
1. Use HTTP Request node to download image
2. Get binary data
3. Convert to base64 (see above)
4. Send to upload endpoint

### From Base64 String
If you already have base64, just pass it directly:
```json
{
  "image": "{{ $json.existing_base64_field }}"
}
```

---

## Error Handling in N8N

### Check for Success
Add an IF node after the HTTP Request:

**Condition:**
```
{{ $json.status }} equals "uploaded"
```

**True Branch:** Continue to next step  
**False Branch:** Handle error (send notification, log, etc.)

### Retry on Failure
In HTTP Request node options:
- Enable "Retry On Fail"
- Max Retries: 3
- Wait Between Retries: 1000ms

---

## Full Workflow: Upload Person Image

```
[Trigger/Start]
    ↓
[Read/Receive Image]
    ↓
[Convert to Base64]
    ↓
[HTTP POST to /api/upload/person]
    ↓
[Extract upload_id]
    ↓
[Store for later use]
```

---

## Quick Copy-Paste Values for N8N

**Endpoint URL:**
```
https://virtual-tryon-55.preview.emergentagent.com/api/upload/person
```

**Method:**
```
POST
```

**Headers:**
```
Content-Type: application/json
```

**Body (JSON):**
```json
{
  "image": "={{ $json.image_base64 }}"
}
```

**Response Path to Upload ID:**
```
{{ $json.upload_id }}
```

---

## Testing Your N8N Setup

### Test with Small Image
Use this tiny 1x1 pixel PNG for testing:
```
iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==
```

### Expected Successful Response
- Status Code: 200
- Response contains: `upload_id`, `timestamp`, `status`
- `status` should be: "uploaded"

### Common Issues

**Issue 1: "Invalid base64"**
- Solution: Remove data URI prefix (data:image/png;base64,)

**Issue 2: Timeout**
- Solution: Image might be too large, compress it first

**Issue 3: 404 Not Found**
- Solution: Check URL is correct with `/api/` prefix

---

## Summary

✅ **Endpoint:** `https://virtual-tryon-55.preview.emergentagent.com/api/upload/person`  
✅ **Method:** POST  
✅ **Body:** `{"image": "base64-string"}`  
✅ **Returns:** `{"upload_id": "uuid", ...}`  
✅ **Use upload_id** in the try-on API call  

---

**Ready to use in your N8N workflow!**
