# New Upload API Endpoints Documentation

## Overview
Added separate API endpoints for uploading images and triggering try-on, while maintaining backward compatibility with the existing direct submission flow.

---

## API Flow Options

### Option 1: New Flow (Upload IDs)
```
1. POST /api/upload/person     → Returns upload_id
2. POST /api/upload/clothing   → Returns upload_id  
3. POST /api/tryon              → Use upload IDs
```

### Option 2: Old Flow (Direct Images - Backward Compatible)
```
1. POST /api/tryon → Send both images directly
```

---

## New API Endpoints

### 1. Upload Person Image

**Endpoint:** `POST /api/upload/person`

**Request Body:**
```json
{
  "image": "base64-encoded-image-string"
}
```

**Response:**
```json
{
  "upload_id": "uuid-string",
  "timestamp": "2025-10-26T23:30:00.123456",
  "status": "uploaded"
}
```

**Example with curl:**
```bash
curl -X POST http://your-backend-url/api/upload/person \
  -H "Content-Type: application/json" \
  -d '{
    "image": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAY..."
  }'
```

**Response Fields:**
- `upload_id` - UUID to use in tryon request
- `timestamp` - When the image was uploaded
- `status` - Always "uploaded" on success

---

### 2. Upload Clothing Image

**Endpoint:** `POST /api/upload/clothing`

**Request Body:**
```json
{
  "image": "base64-encoded-image-string"
}
```

**Response:**
```json
{
  "upload_id": "uuid-string",
  "timestamp": "2025-10-26T23:30:00.123456",
  "status": "uploaded"
}
```

**Example with curl:**
```bash
curl -X POST http://your-backend-url/api/upload/clothing \
  -H "Content-Type: application/json" \
  -d '{
    "image": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAY..."
  }'
```

---

### 3. Try-On with Upload IDs (NEW)

**Endpoint:** `POST /api/tryon`

**Request Body (Using Upload IDs):**
```json
{
  "person_upload_id": "uuid-from-person-upload",
  "clothing_upload_id": "uuid-from-clothing-upload"
}
```

**Response:**
```json
{
  "id": "tryon-uuid",
  "result_image": "base64-encoded-result-image",
  "timestamp": "2025-10-26T23:31:00.123456",
  "status": "completed"
}
```

**Example with curl:**
```bash
curl -X POST http://your-backend-url/api/tryon \
  -H "Content-Type: application/json" \
  -d '{
    "person_upload_id": "abc-123-def-456",
    "clothing_upload_id": "xyz-789-uvw-012"
  }'
```

---

### 4. Try-On with Direct Images (BACKWARD COMPATIBLE)

**Endpoint:** `POST /api/tryon`

**Request Body (Using Direct Images):**
```json
{
  "person_image": "base64-encoded-person-image",
  "clothing_image": "base64-encoded-clothing-image"
}
```

**Response:**
```json
{
  "id": "tryon-uuid",
  "result_image": "base64-encoded-result-image",
  "timestamp": "2025-10-26T23:31:00.123456",
  "status": "completed"
}
```

**Example with curl:**
```bash
curl -X POST http://your-backend-url/api/tryon \
  -H "Content-Type: application/json" \
  -d '{
    "person_image": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAY...",
    "clothing_image": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAY..."
  }'
```

---

## Complete Usage Examples

### Example 1: Using New Upload Flow (Python)

```python
import requests
import base64

# Backend URL
BACKEND_URL = "http://your-backend-url"

# Read and encode person image
with open("person.jpg", "rb") as f:
    person_base64 = base64.b64encode(f.read()).decode('utf-8')

# Read and encode clothing image
with open("clothing.jpg", "rb") as f:
    clothing_base64 = base64.b64encode(f.read()).decode('utf-8')

# Step 1: Upload person image
person_response = requests.post(
    f"{BACKEND_URL}/api/upload/person",
    json={"image": person_base64}
)
person_upload_id = person_response.json()["upload_id"]
print(f"Person uploaded: {person_upload_id}")

# Step 2: Upload clothing image
clothing_response = requests.post(
    f"{BACKEND_URL}/api/upload/clothing",
    json={"image": clothing_base64}
)
clothing_upload_id = clothing_response.json()["upload_id"]
print(f"Clothing uploaded: {clothing_upload_id}")

# Step 3: Trigger try-on with upload IDs
tryon_response = requests.post(
    f"{BACKEND_URL}/api/tryon",
    json={
        "person_upload_id": person_upload_id,
        "clothing_upload_id": clothing_upload_id
    }
)

result = tryon_response.json()
print(f"Try-on completed: {result['id']}")

# Save result image
result_image_data = base64.b64decode(result["result_image"])
with open("result.png", "wb") as f:
    f.write(result_image_data)
```

---

### Example 2: Using Old Direct Flow (Python)

```python
import requests
import base64

BACKEND_URL = "http://your-backend-url"

# Read and encode images
with open("person.jpg", "rb") as f:
    person_base64 = base64.b64encode(f.read()).decode('utf-8')

with open("clothing.jpg", "rb") as f:
    clothing_base64 = base64.b64encode(f.read()).decode('utf-8')

# Direct try-on (old method - still works!)
tryon_response = requests.post(
    f"{BACKEND_URL}/api/tryon",
    json={
        "person_image": person_base64,
        "clothing_image": clothing_base64
    }
)

result = tryon_response.json()
print(f"Try-on completed: {result['id']}")
```

---

### Example 3: Using New Upload Flow (JavaScript/React)

```javascript
const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

// Convert file to base64
const fileToBase64 = (file) => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.readAsDataURL(file);
    reader.onload = () => {
      const base64 = reader.result.split(',')[1];
      resolve(base64);
    };
    reader.onerror = reject;
  });
};

// Upload person image
const uploadPersonImage = async (file) => {
  const base64 = await fileToBase64(file);
  
  const response = await fetch(`${BACKEND_URL}/api/upload/person`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ image: base64 })
  });
  
  const data = await response.json();
  return data.upload_id;
};

// Upload clothing image
const uploadClothingImage = async (file) => {
  const base64 = await fileToBase64(file);
  
  const response = await fetch(`${BACKEND_URL}/api/upload/clothing`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ image: base64 })
  });
  
  const data = await response.json();
  return data.upload_id;
};

// Trigger try-on
const generateTryon = async (personUploadId, clothingUploadId) => {
  const response = await fetch(`${BACKEND_URL}/api/tryon`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      person_upload_id: personUploadId,
      clothing_upload_id: clothingUploadId
    })
  });
  
  const data = await response.json();
  return data;
};

// Complete flow
const handleTryOn = async (personFile, clothingFile) => {
  try {
    // Step 1: Upload person image
    console.log('Uploading person image...');
    const personUploadId = await uploadPersonImage(personFile);
    
    // Step 2: Upload clothing image
    console.log('Uploading clothing image...');
    const clothingUploadId = await uploadClothingImage(clothingFile);
    
    // Step 3: Generate try-on
    console.log('Generating try-on...');
    const result = await generateTryon(personUploadId, clothingUploadId);
    
    console.log('Try-on completed:', result.id);
    return result;
    
  } catch (error) {
    console.error('Error:', error);
    throw error;
  }
};
```

---

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Must provide either (person_image + clothing_image) OR (person_upload_id + clothing_upload_id)"
}
```

### 404 Not Found
```json
{
  "detail": "Person upload ID not found: abc-123-def-456"
}
```
or
```json
{
  "detail": "Clothing upload ID not found: xyz-789-uvw-012"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Failed to upload person image: [error message]"
}
```

---

## Database Schema

### New Collection: `uploads`

```javascript
{
  "upload_id": "uuid-string",
  "image_type": "person" | "clothing",
  "image_data": "base64-encoded-image",
  "timestamp": ISODate("2025-10-26..."),
  "status": "uploaded"
}
```

**Fields:**
- `upload_id` - Unique identifier for the upload
- `image_type` - Either "person" or "clothing"
- `image_data` - Base64-encoded image data
- `timestamp` - When the image was uploaded
- `status` - Current status (always "uploaded")

---

## Benefits of New Upload Flow

### 1. **Separation of Concerns**
- Upload images separately from try-on generation
- Better error handling for each step

### 2. **Flexibility**
- Can upload images ahead of time
- Try-on can be triggered multiple times with same images
- Can swap clothing/person without re-uploading

### 3. **Better UX**
- Show upload progress separately
- User knows exactly which step is happening
- Can retry try-on without re-uploading

### 4. **Reusability**
- Upload person photo once, try multiple outfits
- Upload multiple clothing items, use with same person

### 5. **Backward Compatible**
- Old frontend code still works
- Gradual migration possible
- No breaking changes

---

## Frontend Integration Guide

### Option A: Migrate to New Flow (Recommended)

Update your `TryOnApp.js` to use the new flow:

```javascript
// State for upload IDs
const [personUploadId, setPersonUploadId] = useState(null);
const [clothingUploadId, setClothingUploadId] = useState(null);

// Upload person image
const handlePersonImageUpload = async (file) => {
  const base64 = await fileToBase64(file);
  const response = await axios.post(`${API}/upload/person`, {
    image: base64
  });
  setPersonUploadId(response.data.upload_id);
};

// Upload clothing image
const handleClothingImageUpload = async (file) => {
  const base64 = await fileToBase64(file);
  const response = await axios.post(`${API}/upload/clothing`, {
    image: base64
  });
  setClothingUploadId(response.data.upload_id);
};

// Generate try-on
const handleGenerate = async () => {
  const response = await axios.post(`${API}/tryon`, {
    person_upload_id: personUploadId,
    clothing_upload_id: clothingUploadId
  });
  
  setResultImage(`data:image/png;base64,${response.data.result_image}`);
};
```

### Option B: Keep Old Flow (No Changes Needed)

Your existing code will continue to work as-is:

```javascript
const handleGenerate = async () => {
  const response = await axios.post(`${API}/tryon`, {
    person_image: personImage.base64,
    clothing_image: clothingImage.base64
  });
  
  setResultImage(`data:image/png;base64,${response.data.result_image}`);
};
```

---

## Testing

### Test Upload Endpoints
```bash
# Test person upload
curl -X POST http://localhost:8001/api/upload/person \
  -H "Content-Type: application/json" \
  -d '{"image":"iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAY..."}'

# Test clothing upload
curl -X POST http://localhost:8001/api/upload/clothing \
  -H "Content-Type: application/json" \
  -d '{"image":"iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAY..."}'
```

### Test Try-On with IDs
```bash
curl -X POST http://localhost:8001/api/tryon \
  -H "Content-Type: application/json" \
  -d '{
    "person_upload_id":"abc-123",
    "clothing_upload_id":"xyz-789"
  }'
```

### Test Old Flow (Backward Compatibility)
```bash
curl -X POST http://localhost:8001/api/tryon \
  -H "Content-Type: application/json" \
  -d '{
    "person_image":"base64...",
    "clothing_image":"base64..."
  }'
```

---

## Summary

✅ **Added:** `POST /api/upload/person` - Upload person image  
✅ **Added:** `POST /api/upload/clothing` - Upload clothing image  
✅ **Updated:** `POST /api/tryon` - Supports both upload IDs and direct images  
✅ **Backward Compatible:** Old frontend code still works  
✅ **Database:** New `uploads` collection for temporary storage  
✅ **Flexible:** Upload once, try-on multiple times  

---

**Backend Status:** Running (PID: 342)  
**Updated:** 2025-10-26 23:45 UTC  
**Version:** 2.0 with Upload API
