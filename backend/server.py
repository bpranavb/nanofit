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
        
        # Create Part objects for images
        person_part = types.Part.from_bytes(
            data=person_image_bytes,
            mime_type="image/jpeg"
        )
        
        clothing_part = types.Part.from_bytes(
            data=clothing_image_bytes,
            mime_type="image/jpeg"
        )
        
        text_prompt = """
**CRITICAL VIRTUAL TRY-ON TASK:**

You MUST perform a clothing swap between two images. This is NOT an image description task.

**IMAGE 1 (THE PERSON TO KEEP):**
- This person's face, body, pose, and background MUST remain EXACTLY the same in the output
- ONLY their clothing should change

**IMAGE 2 (THE CLOTHING SOURCE):**
- First, check if someone is HOLDING clothing items (dress, shirt, pants in their hands):
  * If YES: Extract ONLY the clothing items being HELD (not what the person is wearing)
  * If NO: Extract the clothing items the person is WEARING
- COMPLETELY IGNORE the person themselves - only extract the clothes
- Focus on: garment style, color, pattern, texture, design details
- If multiple clothing items are visible (shirt AND pants), extract ALL of them

**YOUR MANDATORY TASK:**
1. Identify ALL clothing items in Image 2 (shirt, pants, jacket, dress, etc.)
2. Remove ALL clothes from the person in Image 1
3. Dress the person from Image 1 in ALL the clothes from Image 2
4. The person from Image 1 should now be wearing ALL garments from Image 2
5. Maintain the person's original pose, face, body, and background from Image 1

**CRITICAL REQUIREMENTS:**
- The OUTPUT must show Image 1's person wearing Image 2's clothes
- The OUTPUT must be VISIBLY DIFFERENT from Image 1 (clothes MUST change)
- If Image 2 has multiple clothing items (shirt AND pants), ALL must appear in the output
- The clothing from Image 2 must FIT naturally on the person from Image 1
- Preserve Image 1's lighting, pose, and background

**FAILURE CONDITIONS (DO NOT DO THESE):**
❌ Returning Image 1 unchanged
❌ Returning Image 2 unchanged  
❌ Mixing the people from both images
❌ Only changing some clothes but not all
❌ Describing the images instead of generating a new one

✅ CORRECT OUTPUT: Image 1's person wearing ALL of Image 2's clothes, photorealistic and natural-looking."""
        
        # Create text part
        text_part = types.Part(text=text_prompt)
        
        logger.info("Calling Gemini 2.5 Flash Image model...")
        
        # Configure generation settings
        config = types.GenerateContentConfig(
            response_modalities=["IMAGE"]
        )
        
        # Create a Content object with all parts (matching TypeScript structure)
        content = types.Content(
            parts=[person_part, clothing_part, text_part]
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
