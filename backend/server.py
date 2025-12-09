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
from PIL import Image
import io


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
    person_image: Optional[str] = None  # base64 encoded image (for backward compatibility)
    clothing_image: Optional[str] = None  # base64 encoded image (for backward compatibility)
    person_upload_id: Optional[str] = None  # upload ID from /api/upload/person
    clothing_upload_id: Optional[str] = None  # upload ID from /api/upload/clothing

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
N8N_WEBHOOK_URL = os.environ.get("N8N_WEBHOOK_URL", "https://spantra.app.n8n.cloud/webhook/upload")

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


@api_router.post("/upload/person", response_model=ImageUploadResponse)
async def upload_person_image(request: ImageUploadRequest):
    """
    Upload person image and get an upload ID for later use
    """
    try:
        logger.info("Uploading person image...")
        
        upload_id = str(uuid.uuid4())
        
        # Store the uploaded image in MongoDB
        upload_record = {
            "upload_id": upload_id,
            "image_type": "person",
            "image_data": request.image,
            "timestamp": datetime.utcnow(),
            "status": "uploaded"
        }
        
        await db.uploads.insert_one(upload_record)
        logger.info(f"Person image uploaded with ID: {upload_id}")
        
        return ImageUploadResponse(
            upload_id=upload_id,
            timestamp=upload_record["timestamp"],
            status="uploaded"
        )
        
    except Exception as e:
        logger.error(f"Error uploading person image: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload person image: {str(e)}"
        )


@api_router.post("/upload/clothing", response_model=ImageUploadResponse)
async def upload_clothing_image(request: ImageUploadRequest):
    """
    Upload clothing image and get an upload ID for later use
    """
    try:
        logger.info("Uploading clothing image...")
        
        upload_id = str(uuid.uuid4())
        
        # Store the uploaded image in MongoDB
        upload_record = {
            "upload_id": upload_id,
            "image_type": "clothing",
            "image_data": request.image,
            "timestamp": datetime.utcnow(),
            "status": "uploaded"
        }
        
        await db.uploads.insert_one(upload_record)
        logger.info(f"Clothing image uploaded with ID: {upload_id}")
        
        return ImageUploadResponse(
            upload_id=upload_id,
            timestamp=upload_record["timestamp"],
            status="uploaded"
        )
        
    except Exception as e:
        logger.error(f"Error uploading clothing image: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload clothing image: {str(e)}"
        )


@api_router.post("/tryon", response_model=TryOnResponse)
async def create_tryon(request: TryOnRequest):
    """
    Virtual try-on endpoint that uses Gemini Nano Banana to generate
    an image of the person wearing the clothing from the second image.
    
    Supports two modes:
    1. Direct images: Pass person_image and clothing_image as base64
    2. Upload IDs: Pass person_upload_id and clothing_upload_id from previous uploads
    """
    try:
        logger.info("Starting virtual try-on process...")
        
        # Get Gemini API key from environment
        gemini_api_key = os.environ.get('GEMINI_API_KEY')
        if not gemini_api_key:
            logger.error("GEMINI_API_KEY not found in environment")
            raise HTTPException(status_code=500, detail="Gemini API key not configured")
        
        tryon_id = str(uuid.uuid4())
        
        # Determine if using direct images or upload IDs
        person_image_base64 = None
        clothing_image_base64 = None
        
        if request.person_upload_id and request.clothing_upload_id:
            # Mode 1: Using upload IDs
            logger.info("Using upload IDs mode")
            
            # Fetch person image from uploads collection - Explicitly project image_data
            person_upload = await db.uploads.find_one(
                {"upload_id": request.person_upload_id},
                {"image_data": 1, "_id": 0}
            )
            if not person_upload:
                raise HTTPException(status_code=404, detail=f"Person upload ID not found: {request.person_upload_id}")
            
            # Fetch clothing image from uploads collection - Explicitly project image_data
            clothing_upload = await db.uploads.find_one(
                {"upload_id": request.clothing_upload_id},
                {"image_data": 1, "_id": 0}
            )
            if not clothing_upload:
                raise HTTPException(status_code=404, detail=f"Clothing upload ID not found: {request.clothing_upload_id}")
            
            person_image_base64 = person_upload["image_data"]
            clothing_image_base64 = clothing_upload["image_data"]
            
            logger.info(f"Retrieved images from uploads: person={request.person_upload_id}, clothing={request.clothing_upload_id}")
            
        elif request.person_image and request.clothing_image:
            # Mode 2: Direct images (backward compatibility)
            logger.info("Using direct images mode")
            person_image_base64 = request.person_image
            clothing_image_base64 = request.clothing_image
            
        else:
            raise HTTPException(
                status_code=400,
                detail="Must provide either (person_image + clothing_image) OR (person_upload_id + clothing_upload_id)"
            )
        
        # Create Gemini client
        client = genai.Client(api_key=gemini_api_key)
        
        logger.info("Preparing images for Gemini...")
        
        # Decode base64 to create Part objects with inline data
        person_image_bytes = base64.b64decode(person_image_base64)
        clothing_image_bytes = base64.b64decode(clothing_image_base64)
        
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
        
        # Calculate aspect ratio from person image
        try:
            with Image.open(io.BytesIO(person_image_bytes)) as img:
                width, height = img.size
                ratio = width / height
                
                # Determine closest supported aspect ratio for Gemini
                # Supported: "1:1", "3:4", "4:3", "9:16", "16:9"
                supported_ratios = {
                    "1:1": 1.0,
                    "3:4": 0.75,
                    "4:3": 1.33,
                    "9:16": 0.5625,
                    "16:9": 1.77
                }
                
                closest_ratio = min(supported_ratios.items(), key=lambda x: abs(x[1] - ratio))
                target_aspect_ratio = closest_ratio[0]
                logger.info(f"Input dimensions: {width}x{height} (Ratio: {ratio:.2f}). Target Gemini Ratio: {target_aspect_ratio}")
        except Exception as e:
            logger.warning(f"Failed to calculate aspect ratio: {e}")
            target_aspect_ratio = "1:1" # Default fallback
        
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
        
        # Enhanced prompt with strongest identity preservation + Headwear support
        text_prompt = """**Primary Directive: High-Fidelity Virtual Try-On**

You are an expert digital tailor. Your task is to execute a precise clothing/accessory swap.

**!!! CORE SAFETY DIRECTIVE: PROTECT FACIAL IDENTITY !!!**
**The person's facial features (eyes, nose, mouth, jawline, skin tone) in Image 1 are a STRICT NO-EDIT ZONE. They must be preserved perfectly to maintain identity. Any distortion to the face is a failure.**

**Input Definitions:**
- **Image 1 (The Canvas):** Contains the person.
- **Image 2 (The Source):** Contains the garment(s) or accessory.

**--- CRITICAL RULES ---**

1.  **PRESERVE THE CANVAS:** Keep the original pose, background, and **ASPECT RATIO** exactly as they are in Image 1. Do not crop, stretch, or resize the person.
2.  **SMART MAPPING (Headwear Exception):** 
    - generally, do NOT edit the head or hair.
    - **HOWEVER**, if the source item is **HEADWEAR** (hat, cap, beanie, sunglasses, etc.), you **MUST** apply it to the person's head/face appropriately, modifying hair/head shape only as needed to fit the item realistically.
3.  **EXTRACT FROM THE SOURCE:** Accurately transfer the color, pattern, and texture from Image 2.
4.  **DISCARD ORIGINAL CLOTHING:** Ignore the old clothes in the target area.

**--- STEP-BY-STEP EXECUTION ---**

1.  **Analyze Source:** Is it a shirt? Pants? A Hat? A Dress?
2.  **Map Target:** 
    - If Shirt/Pants/Dress -> Map to body, exclude head/hands.
    - If Hat/Glasses -> Map to head/face, preserving identity features underneath.
3.  **Render:** Generate the photorealistic result within the exact bounds of Image 1.

**!! FINAL MANDATE !!**
Identity protected. Clothing/Accessory perfectly transferred. Photorealistic. No stretching or distortion."""
        
        optimized_text_part = types.Part(text=text_prompt)
        
        logger.info("Calling Gemini 2.5 Flash Image model...")
        
        # Minimal config - let model use defaults
        config = types.GenerateContentConfig(
            response_modalities=["IMAGE"],
            image_config=types.ImageConfig(
                aspect_ratio=target_aspect_ratio
            )
        )
        
        # Create a Content object with all parts
        content = types.Content(
            parts=[person_part, clothing_part, optimized_text_part]
        )
        
        # Generate content
        response = await asyncio.to_thread(
            client.models.generate_content,
            model="gemini-3-pro-image-preview",
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
            "person_image": person_image_base64,
            "clothing_image": clothing_image_base64,
            "result_image": result_image_base64,
            "timestamp": datetime.utcnow(),
            "status": "completed"
        }
        
        await db.tryons.insert_one(tryon_record)
        logger.info(f"Saved try-on record to database with id: {tryon_id}")
        
        # Send data to n8n webhook (non-blocking, fails silently)
        asyncio.create_task(
            send_to_n8n_webhook(
                person_image_base64=person_image_base64,
                clothing_image_base64=clothing_image_base64,
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
        # Find all try-ons that have feedback - Limit to 50 for performance
        tryons_with_feedback = await db.tryons.find(
            {"feedback": {"$exists": True}}
        ).sort("feedback.feedback_timestamp", -1).limit(50).to_list(50)
        
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
