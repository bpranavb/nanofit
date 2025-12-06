from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime
import asyncio
import base64
from google import genai
from google.genai import types
import httpx


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")


# Define Models
class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class StatusCheckCreate(BaseModel):
    client_name: str

class TryOnRequest(BaseModel):
    person_image: str  # base64 encoded image
    clothing_image: str  # base64 encoded image

class TryOnResponse(BaseModel):
    id: str
    result_image: str  # base64 encoded image
    timestamp: datetime
    status: str

class FeedbackRequest(BaseModel):
    tryon_id: str
    rating: int  # 1-5 stars
    comment: Optional[str] = None
    customer_name: Optional[str] = None

class ImageUploadRequest(BaseModel):
    image: str  # base64 encoded image

class ImageUploadResponse(BaseModel):
    upload_id: str
    timestamp: datetime
    status: str

class TryOnWithIdsRequest(BaseModel):
    person_upload_id: str
    clothing_upload_id: str


# N8N Webhook Configuration
N8N_WEBHOOK_URL = "https://spantra.app.n8n.cloud/webhook/upload"

async def send_to_n8n_webhook(person_image_base64: str, clothing_image_base64: str, result_image_base64: str, tryon_id: str):
    """
    Send try-on images to n8n webhook
    This function fails silently to not interrupt the try-on process
    """
    try:
        logger.info(f"Sending try-on data to n8n webhook for tryon_id: {tryon_id}")
        
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
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(N8N_WEBHOOK_URL, json=payload)
            response.raise_for_status()
            logger.info(f"Successfully sent data to n8n webhook. Status: {response.status_code}")
            
    except httpx.HTTPError as e:
        logger.error(f"HTTP error sending to n8n webhook: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error sending to n8n webhook: {str(e)}")


# Add your routes to the router instead of directly to app
@api_router.get("/")
async def root():
    return {"message": "Virtual Try-On API is running"}

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.dict()
    status_obj = StatusCheck(**status_dict)
    _ = await db.status_checks.insert_one(status_obj.dict())
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find().to_list(1000)
    return [StatusCheck(**status_check) for status_check in status_checks]


@api_router.post("/tryon", response_model=TryOnResponse)
async def create_tryon(request: TryOnRequest):
    """
    Virtual try-on endpoint that uses Gemini Nano Banana to generate
    an image of the person wearing the clothing from the second image.
    """
    try:
        logger.info("Starting virtual try-on process...")
        
        # Get Gemini API key from environment
        gemini_api_key = os.environ.get('GEMINI_API_KEY')
        if not gemini_api_key:
            logger.error("GEMINI_API_KEY not found in environment")
            raise HTTPException(status_code=500, detail="Gemini API key not configured")
        
        tryon_id = str(uuid.uuid4())
        
        # Create Gemini client
        client = genai.Client(api_key=gemini_api_key)
        
        logger.info("Preparing images for Gemini...")
        
        # Decode base64 to create Part objects with inline data
        person_image_bytes = base64.b64decode(request.person_image)
        clothing_image_bytes = base64.b64decode(request.clothing_image)
        
        # Detect actual mime type from image bytes
        def detect_mime_type(image_bytes):
            # Check magic bytes to determine image type
            if image_bytes.startswith(b'\xff\xd8\xff'):
                return "image/jpeg"
            elif image_bytes.startswith(b'\x89PNG'):
                return "image/png"
            elif image_bytes.startswith(b'RIFF') and image_bytes[8:12] == b'WEBP':
                return "image/webp"
            elif image_bytes.startswith(b'GIF87a') or image_bytes.startswith(b'GIF89a'):
                return "image/gif"
            else:
                # Default to jpeg if unknown
                return "image/jpeg"
        
        person_mime = detect_mime_type(person_image_bytes)
        clothing_mime = detect_mime_type(clothing_image_bytes)
        
        logger.info(f"Person image mime type: {person_mime}")
        logger.info(f"Clothing image mime type: {clothing_mime}")
        
        # Create Part objects for images with correct mime types
        person_part = types.Part.from_bytes(
            data=person_image_bytes,
            mime_type=person_mime
        )
        
        clothing_part = types.Part.from_bytes(
            data=clothing_image_bytes,
            mime_type=clothing_mime
        )
        
        # Original text prompt (kept for reference)
        # text_prompt = """Your task is to perform a virtual try-on. The first image contains a person. The second image contains one or more clothing items. Identify the garments (e.g., shirt, pants, jacket) in the second image, ignoring any person or mannequin wearing them. Then, generate a new, photorealistic image where the person from the first image is wearing those garments. The person's original pose, face, and the background should be maintained."""
        
        logger.info("Calling Gemini for virtual try-on...")
        
        # Enhanced prompt with strongest identity preservation
        text_prompt = """**Primary Directive: High-Fidelity Virtual Try-On**

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
The output image's clothing must be a perfect visual match to the garment in Image 2. The person's face and identity must be 100% identical to Image 1. There should be zero color blending from the original clothing. The resulting image must be photorealistic and seamlessly edited."""
        
        optimized_text_part = types.Part(text=text_prompt)
        
        logger.info("Calling Gemini 2.5 Flash Image model...")
        
        # Minimal config - let model use defaults
        config = types.GenerateContentConfig(
            response_modalities=["IMAGE"]
        )
        
        # Create a Content object with all parts
        content = types.Content(
            parts=[person_part, clothing_part, optimized_text_part]
        )
        
        # Generate content
        response = await asyncio.to_thread(
            client.models.generate_content,
            model="gemini-2.5-flash-image",
            contents=content,
            config=config
        )
        
        logger.info("Received response from Gemini")
        logger.info(f"Response parts: {len(response.parts) if response.parts else 0}")
        
        # Find the image part in the response
        result_image_base64 = None
        
        for part in response.parts:
            if part.inline_data is not None:
                # The data comes as bytes, need to encode to base64
                image_data = part.inline_data.data
                if isinstance(image_data, bytes):
                    result_image_base64 = base64.b64encode(image_data).decode('utf-8')
                else:
                    result_image_base64 = image_data
                logger.info(f"Found generated image in response. Size: {len(result_image_base64)} characters")
                break
        
        if not result_image_base64:
            logger.error("No image found in Gemini response")
            logger.error(f"Response: {response}")
            raise HTTPException(
                status_code=500,
                detail="Failed to generate try-on image. No image was returned in the response."
            )
        
        # Save to database
        tryon_record = {
            "id": tryon_id,
            "person_image": request.person_image,
            "clothing_image": request.clothing_image,
            "result_image": result_image_base64,
            "timestamp": datetime.utcnow(),
            "status": "completed"
        }
        
        await db.tryons.insert_one(tryon_record)
        logger.info(f"Saved try-on record to database with id: {tryon_id}")
        
        # Send data to n8n webhook (non-blocking, fails silently)
        asyncio.create_task(
            send_to_n8n_webhook(
                person_image_base64=request.person_image,
                clothing_image_base64=request.clothing_image,
                result_image_base64=result_image_base64,
                tryon_id=tryon_id
            )
        )
        
        return TryOnResponse(
            id=tryon_id,
            result_image=result_image_base64,
            timestamp=tryon_record["timestamp"],
            status="completed"
        )
        
    except HTTPException as he:
        logger.error(f"HTTP Exception: {str(he)}")
        raise he
    except Exception as e:
        logger.error(f"Error in try-on process: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process try-on request: {str(e)}"
        )


@api_router.get("/tryon/{tryon_id}")
async def get_tryon(tryon_id: str):
    """
    Get a specific try-on result by ID
    """
    try:
        tryon = await db.tryons.find_one({"id": tryon_id})
        if not tryon:
            raise HTTPException(status_code=404, detail="Try-on not found")
        
        return TryOnResponse(
            id=tryon["id"],
            result_image=tryon["result_image"],
            timestamp=tryon["timestamp"],
            status=tryon["status"]
        )
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error fetching try-on: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/feedback")
async def submit_feedback(feedback: FeedbackRequest):
    """
    Submit customer feedback for a try-on result
    """
    try:
        # Verify try-on exists
        tryon = await db.tryons.find_one({"id": feedback.tryon_id})
        if not tryon:
            raise HTTPException(status_code=404, detail="Try-on not found")
        
        # Get the next serial number for feedback
        # Count all existing feedback to generate serial number
        feedback_count = await db.tryons.count_documents({"feedback": {"$exists": True}})
        serial_number = feedback_count + 1
        
        # Update try-on with feedback
        await db.tryons.update_one(
            {"id": feedback.tryon_id},
            {
                "$set": {
                    "feedback": {
                        "serial_number": serial_number,
                        "rating": feedback.rating,
                        "comment": feedback.comment,
                        "customer_name": feedback.customer_name,
                        "feedback_timestamp": datetime.utcnow(),
                        "feedback_date": datetime.utcnow().strftime("%Y-%m-%d")  # For daily tracking
                    }
                }
            }
        )
        
        logger.info(f"Feedback #{serial_number} saved for try-on {feedback.tryon_id}: {feedback.rating} stars")
        
        return {
            "success": True,
            "message": "Feedback submitted successfully",
            "serial_number": serial_number
        }
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error saving feedback: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/feedback/all")
async def get_all_feedback():
    """
    Get all feedback from try-ons with enhanced tracking
    """
    try:
        # Find all try-ons that have feedback
        tryons_with_feedback = await db.tryons.find(
            {"feedback": {"$exists": True}}
        ).to_list(1000)
        
        feedback_list = []
        daily_counts = {}
        
        for tryon in tryons_with_feedback:
            feedback_data = tryon.get("feedback", {})
            feedback_item = {
                "tryon_id": tryon.get("id"),
                "serial_number": feedback_data.get("serial_number"),
                "timestamp": tryon.get("timestamp"),
                "rating": feedback_data.get("rating"),
                "comment": feedback_data.get("comment"),
                "customer_name": feedback_data.get("customer_name"),
                "feedback_timestamp": feedback_data.get("feedback_timestamp"),
                "feedback_date": feedback_data.get("feedback_date"),
                "result_image": tryon.get("result_image")
            }
            feedback_list.append(feedback_item)
            
            # Count feedback per day
            date = feedback_data.get("feedback_date", "Unknown")
            daily_counts[date] = daily_counts.get(date, 0) + 1
        
        # Sort by serial number (descending - most recent first)
        feedback_list.sort(
            key=lambda x: x.get("serial_number") or 0,
            reverse=True
        )
        
        # Calculate daily statistics
        daily_stats = [
            {"date": date, "count": count}
            for date, count in sorted(daily_counts.items(), reverse=True)
        ]
        
        return {
            "total": len(feedback_list),
            "feedback": feedback_list,
            "daily_stats": daily_stats
        }
        
    except Exception as e:
        logger.error(f"Error fetching feedback: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
