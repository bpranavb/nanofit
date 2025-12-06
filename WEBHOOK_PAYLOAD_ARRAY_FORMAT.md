# Webhook Payload Structure Update ✅

## Change Summary
Updated the n8n webhook payload to send images as an **array of objects** instead of flat fields.

---

## New Payload Structure (Option 2)

### Single POST Request with Array
```json
{
  "tryon_id": "83f01fb4-1fbd-4e32-b95b-6dcaf36eb77b",
  "timestamp": "2025-10-26T22:35:00.123456",
  "images": [
    {
      "type": "person",
      "data": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJ..."
    },
    {
      "type": "clothing",
      "data": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJ..."
    },
    {
      "type": "result",
      "data": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJ..."
    }
  ]
}
```

---

## Previous Payload Structure (For Reference)

### Old Format - Flat Fields
```json
{
  "tryon_id": "uuid",
  "timestamp": "ISO timestamp",
  "person_image": "base64...",
  "clothing_image": "base64...",
  "result_image": "base64..."
}
```

---

## Benefits of Array Structure

### 1. **Better Organization**
- Images are grouped in a single `images` array
- Each image object clearly identifies its type
- Easier to iterate through in n8n workflows

### 2. **Consistent Structure**
- All image objects have the same schema: `{ type, data }`
- Predictable and easier to validate

### 3. **Scalability**
- Easy to add more images in the future
- Simply append to the array

### 4. **N8N Workflow Friendly**
- Can use n8n's "Split In Batches" node to process each image
- Loop through array to save images individually
- Apply transformations to each image object

---

## How to Process in N8N

### Example N8N Workflow

#### Step 1: Webhook Trigger
Receives the POST request with the array payload

#### Step 2: Split Images (Optional)
Use **Split In Batches** node to process each image individually:
```javascript
// Expression to split
{{ $json.images }}
```

#### Step 3: Process Each Image
Loop through each image object:
```javascript
// Access image type
{{ $json.type }}  // "person", "clothing", or "result"

// Access image data
{{ $json.data }}  // base64 string
```

#### Step 4: Save or Transform
- Save each image to cloud storage (S3, Google Drive, etc.)
- Send to another API
- Store in database
- Generate thumbnails

---

## Code Changes

### File: `backend/server.py`
**Function:** `send_to_n8n_webhook()`

```python
payload = {
    "tryon_id": tryon_id,
    "timestamp": datetime.utcnow().isoformat(),
    "images": [
        {
            "type": "person",
            "data": person_image_base64
        },
        {
            "type": "clothing",
            "data": clothing_image_base64
        },
        {
            "type": "result",
            "data": result_image_base64
        }
    ]
}
```

---

## Testing the New Format

### 1. Check Backend Logs
```bash
tail -f /var/log/supervisor/backend.*.log | grep -i "webhook"
```

Expected output:
```
INFO - Sending try-on data to n8n webhook for tryon_id: [uuid]
INFO - Successfully sent data to n8n webhook. Status: 200
```

### 2. Verify in N8N
- Go to your n8n workflow at: https://spantra.app.n8n.cloud/webhook/upload
- Check the incoming webhook data
- Confirm `images` array contains 3 objects
- Each object should have `type` and `data` fields

### 3. Test Data Access
In your n8n workflow, test these expressions:
```javascript
// Get all images
{{ $json.images }}

// Get first image (person)
{{ $json.images[0] }}

// Get person image data
{{ $json.images[0].data }}

// Get clothing image type
{{ $json.images[1].type }}  // Returns: "clothing"

// Count images
{{ $json.images.length }}  // Returns: 3
```

---

## Sample N8N Workflow Setup

### Webhook Node Configuration
- **HTTP Method:** POST
- **Path:** `/webhook-test/upload`
- **Response Mode:** Immediately
- **Response Data:** Success Message

### Split In Batches Node
- **Batch Size:** 1
- **Options:** Check "Include binary data"

### Code Node (Process Each Image)
```javascript
// Access current image
const imageType = $input.item.json.type;
const imageData = $input.item.json.data;
const tryonId = $('Webhook').item.json.tryon_id;

// Return processed data
return {
  json: {
    tryon_id: tryonId,
    image_type: imageType,
    image_data: imageData,
    filename: `${tryonId}_${imageType}.png`
  }
};
```

---

## Rollback Instructions

If you need to revert to the old format:

1. Edit `backend/server.py` line ~71:
```python
payload = {
    "tryon_id": tryon_id,
    "timestamp": datetime.utcnow().isoformat(),
    "person_image": person_image_base64,
    "clothing_image": clothing_image_base64,
    "result_image": result_image_base64
}
```

2. Restart backend:
```bash
sudo supervisorctl restart backend
```

---

## Summary

✅ **Updated:** Webhook payload now uses array structure  
✅ **Format:** `images: [{type, data}, {type, data}, {type, data}]`  
✅ **Backend:** Restarted successfully (PID: 1871)  
✅ **Status:** Ready for n8n integration  

**Update completed at:** 2025-10-26 22:37 UTC
