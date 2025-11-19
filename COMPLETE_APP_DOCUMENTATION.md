# Virtual Try-On Application - Complete Build Documentation

## 📋 Application Overview

A production-ready **AI-powered virtual try-on application** designed for shopping mall kiosks (tablet/iPad portrait mode). Users upload their photo and a clothing image, and the AI generates a realistic image of them wearing the new clothes.

---

## 🛠️ Tech Stack

### Backend
- **Framework:** FastAPI (Python)
- **Database:** MongoDB (Motor async driver)
- **AI Model:** Google Gemini 2.5 Flash Image (`gemini-2.5-flash-image`)
- **Image Processing:** Base64 encoding/decoding, Pillow
- **HTTP Client:** httpx (for webhook calls)
- **Server:** Uvicorn with supervisor

### Frontend
- **Framework:** React 18
- **Routing:** React Router v6
- **Styling:** CSS with soft theme (lavender, beige tones)
- **Image Handling:** Base64, FileReader API
- **Camera:** react-webcam
- **Storage:** localStorage (for try-on history)
- **Build Tool:** Create React App with CRACO

### Infrastructure
- **CORS:** Enabled for frontend-backend communication
- **Environment Variables:** dotenv for configuration
- **Process Manager:** Supervisor for service management

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React)                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Landing Page │  │  Try-On App  │  │   Feedback   │     │
│  │  (Slider)    │  │ (Main UI)    │  │    Viewer    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│         │                  │                   │            │
└─────────┼──────────────────┼───────────────────┼────────────┘
          │                  │                   │
          │          ┌───────▼───────────┐       │
          │          │   /api/tryon      │       │
          │          │   /api/feedback   │       │
          └──────────┤   /api/feedback/  │◄──────┘
                     │   daily-stats     │
                     └───────┬───────────┘
                             │
            ┌────────────────┼────────────────┐
            │      Backend (FastAPI)          │
            │  ┌──────────────────────────┐   │
            │  │  Gemini 2.5 Flash Image  │   │
            │  │   (Virtual Try-On AI)    │   │
            │  └──────────────────────────┘   │
            │  ┌──────────────────────────┐   │
            │  │    N8N Webhook           │   │
            │  │  (Async Image Export)    │   │
            │  └──────────────────────────┘   │
            └────────────────┬────────────────┘
                             │
                    ┌────────▼────────┐
                    │    MongoDB      │
                    │  - tryons       │
                    │  - feedback     │
                    └─────────────────┘
```

---

## ✨ Key Features

### 1. **Landing Page**
- Interactive before/after slider showcasing virtual try-on
- "Start Trying On" CTA button
- Soft lavender/beige theme

### 2. **Virtual Try-On Interface**
- Two upload areas: Person Photo + Clothing Photo
- Multiple input methods:
  - Upload from device gallery
  - Live camera capture
  - Drag & drop
  - Paste from clipboard
- Real-time preview of uploaded images
- "Generate Try-On" button with loading states
- Result display with prominent image

### 3. **Try-On History**
- Stores last 20 try-ons in localStorage
- Thumbnail view of past results
- Click to reload previous try-on
- Auto-cleanup when storage limit reached
- Clear history option

### 4. **Download & Share**
- Download result as PNG
- Email share option
- QR code share (placeholder)

### 5. **Feedback System**
- Customer name + 5-star rating
- Optional comments
- Linked to try-on results
- Serial number tracking
- Timestamp for daily analytics

### 6. **Feedback Viewer**
- Display all feedback with images
- Daily statistics view
- Filter by date
- Customer name tagging

### 7. **N8N Webhook Integration**
- Automatically sends all 3 images to n8n after each try-on
- Non-blocking async call
- Silent failure (doesn't interrupt user experience)
- Payload: Array of 3 image objects with type and base64 data

---

## 🔄 Application Flow

### User Journey

```
1. User lands on homepage
   ↓
2. Sees before/after slider demo
   ↓
3. Clicks "Start Trying On"
   ↓
4. Upload/capture person photo
   ↓
5. Upload/capture clothing photo
   ↓
6. Click "Generate Try-On"
   ↓
7. Backend sends to Gemini AI
   ↓
8. Result displayed prominently
   ↓
9. Webhook sends images to n8n (background)
   ↓
10. User can:
    - Download image
    - Share via email/QR
    - Submit feedback
    - Try again (Start Over)
```

### Technical Flow

```
Frontend Upload
     ↓
Convert to Base64
     ↓
POST /api/tryon
     ↓
Backend receives images
     ↓
Decode base64 to bytes
     ↓
Detect mime types
     ↓
Create Gemini API request
     ↓
Send: [person_image, clothing_image, prompt]
     ↓
Gemini generates result
     ↓
Encode result to base64
     ↓
Save to MongoDB
     ↓
Send to n8n webhook (async)
     ↓
Return result to frontend
     ↓
Display to user
     ↓
Save to localStorage history
```

---

## 🗄️ Database Schema

### MongoDB Collections

#### 1. **tryons** Collection
```javascript
{
  "id": "uuid-string",                    // UUID v4
  "person_image": "base64-string",        // Original person photo
  "clothing_image": "base64-string",      // Original clothing photo
  "result_image": "base64-string",        // Generated result
  "timestamp": ISODate("2025-10-26..."),  // Creation time
  "status": "completed",                   // Status
  "feedback": {                            // Optional - if feedback submitted
    "serial_number": 1,
    "rating": 5,
    "comment": "Amazing!",
    "customer_name": "John Doe",
    "feedback_timestamp": ISODate("..."),
    "feedback_date": "2025-10-26"
  }
}
```

---

## 🔌 API Endpoints

### 1. **POST /api/tryon**
**Purpose:** Generate virtual try-on image

**Request:**
```json
{
  "person_image": "base64-encoded-image",
  "clothing_image": "base64-encoded-image"
}
```

**Response:**
```json
{
  "id": "uuid",
  "result_image": "base64-encoded-image",
  "timestamp": "2025-10-26T22:19:00.123456",
  "status": "completed"
}
```

**Process:**
1. Decode base64 images
2. Detect mime types
3. Call Gemini 2.5 Flash Image API with prompt
4. Save to MongoDB
5. Send to n8n webhook (async)
6. Return result

---

### 2. **GET /api/tryon/{tryon_id}**
**Purpose:** Retrieve specific try-on result

**Response:**
```json
{
  "id": "uuid",
  "result_image": "base64-encoded-image",
  "timestamp": "...",
  "status": "completed"
}
```

---

### 3. **POST /api/feedback**
**Purpose:** Submit customer feedback

**Request:**
```json
{
  "tryon_id": "uuid",
  "rating": 5,
  "comment": "Great!",
  "customer_name": "Jane Doe"
}
```

**Response:** Success/Error status

**Process:**
1. Verify try-on exists
2. Generate serial number
3. Update try-on record with feedback
4. Add timestamp and date for analytics

---

### 4. **GET /api/feedback/daily-stats**
**Purpose:** Get daily feedback statistics

**Response:**
```json
{
  "date": "2025-10-26",
  "total_feedback": 15,
  "average_rating": 4.5,
  "ratings_breakdown": {
    "5": 10,
    "4": 3,
    "3": 2,
    "2": 0,
    "1": 0
  }
}
```

---

## 🤖 Gemini AI Prompt

### The Prompt (Lines 183-212 in server.py)

```
**Primary Directive: High-Fidelity Virtual Try-On**

You are an expert digital tailor. Your task is to execute a precise clothing swap.

**!!! CORE SAFETY DIRECTIVE: PROTECT IDENTITY !!!**
**This is the most important rule. The person's face and head in Image 1 are a STRICT NO-EDIT ZONE. They must be transferred to the final image perfectly, pixel for pixel, without ANY modification. Any change to the facial features, expression, skin tone, or hair is a complete failure of the task.**

**Input Definitions:**
- **Image 1 (The Canvas):** Contains the person, their pose, and the background. This is the base image that will be edited.
- **Image 2 (The Source):** Contains the garment(s). This is the ONLY source for the new clothing's appearance.

**--- CRITICAL RULES ---**

1.  **PRESERVE THE CANVAS:** As stated in the Core Safety Directive, the person's identity is paramount. In addition, the original **pose** and the entire **background** MUST be preserved with photorealistic accuracy. Do not change them.

2.  **EXTRACT FROM THE SOURCE:** You must analyze Image 2 to extract the garment's key attributes:
    - **Exact Color:** The precise hue, saturation, and brightness.
    - **Complete Pattern & Design:** The full visual design, embroidery, or print.
    - **Fabric Texture:** The material's look and feel (e.g., cotton, silk, denim).

3.  **DISCARD ORIGINAL CLOTHING:** You MUST completely ignore and discard all visual information from the clothes the person is wearing in Image 1. Their original clothing's color, pattern, and texture are IRRELEVANT and must NOT influence the output.

**--- STEP-BY-STEP EXECUTION ---**

1.  **Isolate:** Identify and isolate the primary garment(s) in Image 2. Ignore any mannequin, hanger, or person.
2.  **Map:** Identify the area of clothing on the person in Image 1, carefully excluding the head, neck, and hands.
3.  **Replace and Render:** Generate a new image where you flawlessly render the extracted garment attributes (Exact Color, Design, Texture) from Image 2 onto the mapped clothing area of Image 1. The new clothing must fit the person's body and pose naturally, including realistic folds and shadows.

**!! FINAL MANDATE !!**
The output image's clothing must be a perfect visual match to the garment in Image 2. The person's face and identity must be 100% identical to Image 1. There should be zero color blending from the original clothing. The resulting image must be photorealistic and seamlessly edited.
```

### Gemini Configuration
```python
model = "gemini-2.5-flash-image"
config = types.GenerateContentConfig(
    response_modalities=["IMAGE"]
)
content = types.Content(
    parts=[person_part, clothing_part, text_prompt_part]
)
```

---

## 🌐 N8N Webhook Integration

### Webhook URL
```
https://spantra.app.n8n.cloud/webhook-test/upload
```

### Payload Structure (Array Format)
```json
{
  "tryon_id": "uuid-string",
  "timestamp": "2025-10-26T22:35:00.123456",
  "images": [
    {
      "type": "person",
      "data": "base64-encoded-image"
    },
    {
      "type": "clothing",
      "data": "base64-encoded-image"
    },
    {
      "type": "result",
      "data": "base64-encoded-image"
    }
  ]
}
```

### Implementation Details
- **Async:** Non-blocking call using `asyncio.create_task()`
- **Timeout:** 30 seconds
- **Error Handling:** Silent failure - errors logged but don't break try-on
- **When:** Triggered after successful try-on generation and MongoDB save

---

## 📁 File Structure

```
/app/
├── backend/
│   ├── server.py                    # Main FastAPI app
│   ├── requirements.txt             # Python dependencies
│   ├── .env                         # Environment variables
│   └── generate_demo_images.py     # Demo image generator
│
├── frontend/
│   ├── public/
│   │   ├── index.html
│   │   ├── before.png              # Demo slider image
│   │   └── after.png               # Demo slider image
│   ├── src/
│   │   ├── index.js                # React entry point
│   │   ├── App.js                  # Main router
│   │   ├── App.css                 # Global styles
│   │   ├── index.css               # Base styles
│   │   ├── components/
│   │   │   ├── LandingPage.js      # Homepage with slider
│   │   │   ├── TryOnApp.js         # Main try-on interface
│   │   │   ├── BeforeAfterSlider.js # Image comparison slider
│   │   │   ├── CameraCapture.js    # Camera component
│   │   │   ├── HistoryPanel.js     # Try-on history
│   │   │   ├── FeedbackForm.js     # Feedback submission
│   │   │   └── FeedbackViewer.js   # Feedback display
│   │   └── styles/
│   │       ├── LandingPage.css
│   │       ├── TryOnApp.css
│   │       ├── BeforeAfterSlider.css
│   │       ├── CameraCapture.css
│   │       ├── HistoryPanel.css
│   │       ├── FeedbackForm.css
│   │       └── FeedbackViewer.css
│   ├── package.json                # Node dependencies
│   ├── .env                        # Frontend env vars
│   ├── craco.config.js             # CRACO config
│   ├── tailwind.config.js          # Tailwind config
│   └── postcss.config.js           # PostCSS config
│
├── test_result.md                  # Testing documentation
├── N8N_WEBHOOK_INTEGRATION.md      # Webhook docs
├── VIRTUAL_TRYON_PROMPT.md         # AI prompt docs
└── WEBHOOK_PAYLOAD_ARRAY_FORMAT.md # Payload structure docs
```

---

## ⚙️ Environment Variables

### Backend (.env)
```bash
MONGO_URL=mongodb://localhost:27017
DB_NAME=virtual_tryon_db
GEMINI_API_KEY=your_gemini_api_key_here
```

### Frontend (.env)
```bash
REACT_APP_BACKEND_URL=http://your-backend-url
```

---

## 📦 Dependencies

### Backend (requirements.txt)
```
fastapi==0.110.1
uvicorn==0.25.0
motor==3.3.1
pymongo==4.5.0
python-dotenv==1.1.1
python-multipart==0.0.20
pydantic==2.12.3
google-genai==1.46.0
google-generativeai==0.8.5
httpx==0.28.1
pillow==12.0.0
```

### Frontend (package.json)
```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.x",
    "axios": "^1.x",
    "react-webcam": "^7.x",
    "qrcode.react": "^3.x"
  }
}
```

---

## 🎨 Design Theme

### Color Palette
- **Primary:** Lavender (#b19cd9, #dda0dd)
- **Secondary:** Beige/Cream tones
- **Background:** Soft gradients
- **Text:** Dark gray (#333)

### Typography
- **Font:** System fonts (sans-serif stack)
- **Sizes:** Responsive (rem units)

### UI Elements
- **Buttons:** Rounded, gradient backgrounds, large touch targets
- **Cards:** Soft shadows, rounded corners
- **Inputs:** Hidden file inputs, custom styled areas
- **Modals:** Centered overlays with backdrop

### Responsive
- **Target:** iPad/Tablet portrait mode (1024x768)
- **Breakpoints:** Mobile-first approach

---

## 🚀 Deployment Requirements

### Services Needed
1. **Backend Server** - Uvicorn + FastAPI
2. **Frontend Server** - React dev server or static hosting
3. **MongoDB Instance** - Local or cloud (Atlas)
4. **Gemini API Access** - Google AI API key
5. **N8N Instance** - For webhook receiving (optional)

### Service Management (Supervisor)
```ini
[program:backend]
command=uvicorn server:app --host 0.0.0.0 --port 8001
directory=/app/backend
autostart=true
autorestart=true

[program:frontend]
command=yarn start
directory=/app/frontend
autostart=true
autorestart=true

[program:mongodb]
command=mongod --dbpath /data/db
autostart=true
autorestart=true
```

---

## 🔑 Key Implementation Notes

### 1. **Image Handling**
- All images stored/transferred as base64 strings
- Mime type detection from magic bytes
- Size limits managed through localStorage cleanup

### 2. **Error Handling**
- Try-catch on all API calls
- User-friendly error messages
- Webhook failures don't interrupt user flow
- MongoDB connection error handling

### 3. **Performance**
- Gemini API calls run in thread pool (asyncio.to_thread)
- Webhook calls are non-blocking
- localStorage has auto-cleanup to prevent quota issues
- Image compression via quality settings

### 4. **Security**
- CORS properly configured
- API keys in environment variables
- No hardcoded URLs/credentials
- UUID for all IDs (not MongoDB ObjectId for JSON serialization)

### 5. **User Experience**
- Loading states during generation
- Progress messages ("Preparing...", "Creating...", "Finalizing...")
- Prominent result display
- Easy retry with "Start Over"
- History persistence across sessions

---

## 📝 Important Code Snippets

### 1. Gemini API Call
```python
client = genai.Client(api_key=gemini_api_key)

person_part = types.Part.from_bytes(
    data=person_image_bytes,
    mime_type=person_mime
)

clothing_part = types.Part.from_bytes(
    data=clothing_image_bytes,
    mime_type=clothing_mime
)

text_prompt_part = types.Part(text=text_prompt)

config = types.GenerateContentConfig(
    response_modalities=["IMAGE"]
)

content = types.Content(
    parts=[person_part, clothing_part, text_prompt_part]
)

response = await asyncio.to_thread(
    client.models.generate_content,
    model="gemini-2.5-flash-image",
    contents=content,
    config=config
)
```

### 2. N8N Webhook Call
```python
async def send_to_n8n_webhook(person_image_base64, clothing_image_base64, result_image_base64, tryon_id):
    try:
        payload = {
            "tryon_id": tryon_id,
            "timestamp": datetime.utcnow().isoformat(),
            "images": [
                {"type": "person", "data": person_image_base64},
                {"type": "clothing", "data": clothing_image_base64},
                {"type": "result", "data": result_image_base64}
            ]
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(N8N_WEBHOOK_URL, json=payload)
            response.raise_for_status()
    except Exception as e:
        logger.error(f"Webhook error: {str(e)}")
```

### 3. Frontend API Call
```javascript
const response = await axios.post(`${API}/tryon`, {
    person_image: personImage.base64,
    clothing_image: clothingImage.base64
});

const resultImageUrl = `data:image/png;base64,${response.data.result_image}`;
setResultImage(resultImageUrl);
```

### 4. LocalStorage History Management
```javascript
const saveToHistory = (personImg, clothingImg, resultImg) => {
    const newItem = {
        personImage: personImg,
        clothingImage: clothingImg,
        resultImage: resultImg,
        timestamp: new Date().toISOString()
    };
    
    const updatedHistory = [newItem, ...history].slice(0, 20);
    
    try {
        setHistory(updatedHistory);
        localStorage.setItem('tryonHistory', JSON.stringify(updatedHistory));
    } catch (e) {
        if (e.name === 'QuotaExceededError') {
            // Handle quota exceeded
            const reducedHistory = [newItem, ...history].slice(0, 10);
            localStorage.setItem('tryonHistory', JSON.stringify(reducedHistory));
        }
    }
};
```

---

## 🎯 Replication Checklist

To replicate this application, ensure you:

- [ ] Set up MongoDB instance
- [ ] Get Gemini API key from Google AI Studio
- [ ] Configure environment variables in .env files
- [ ] Install all backend dependencies
- [ ] Install all frontend dependencies
- [ ] Set up supervisor for service management
- [ ] Configure CORS in backend
- [ ] Set correct backend URL in frontend .env
- [ ] Create before.png and after.png demo images
- [ ] Set up n8n webhook endpoint (optional)
- [ ] Test image upload and generation flow
- [ ] Verify history persistence
- [ ] Test feedback system
- [ ] Confirm webhook is sending data

---

## 📊 Testing Endpoints

### Quick Backend Test
```bash
# Test API is running
curl http://your-backend-url/api/

# Test try-on (with small base64 test images)
curl -X POST http://your-backend-url/api/tryon \
  -H "Content-Type: application/json" \
  -d '{
    "person_image": "base64_string_here",
    "clothing_image": "base64_string_here"
  }'
```

---

## 💡 Tips for Replication Agent

1. **Start with backend setup first** - Get Gemini API working
2. **Use exact prompt** - The prompt engineering is critical for results
3. **Test with small images first** - Avoid timeouts during development
4. **Handle base64 carefully** - Ensure proper encoding/decoding
5. **Implement webhook last** - It's optional and shouldn't block core functionality
6. **Pay attention to mime types** - Different image formats need different handling
7. **localStorage has limits** - Implement auto-cleanup from the start
8. **Use UUIDs not ObjectIds** - For JSON serialization compatibility
9. **Theme consistency** - Use the lavender/beige color palette throughout
10. **Test on actual tablet** - The app is optimized for iPad portrait mode

---

**Last Updated:** October 26, 2025  
**Version:** 1.0  
**Status:** Production Ready
