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
from emergentintegrations.llm.chat import LlmChat, UserMessage, ImageContent


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
        
        # Create unique session ID for this try-on
        session_id = str(uuid.uuid4())
        tryon_id = str(uuid.uuid4())
        
        logger.info(f"Creating LlmChat instance with session_id: {session_id}")
        
        # Initialize LlmChat with Gemini Nano Banana model
        chat = LlmChat(
            api_key=gemini_api_key,
            session_id=session_id,
            system_message="You are an expert fashion AI that can virtually dress people in different outfits."
        )
        
        # Configure to use Gemini with image generation capability
        chat.with_model("gemini", "gemini-2.5-flash-image-preview").with_params(
            modalities=["image", "text"]
        )
        
        logger.info("Sending images to Gemini Nano Banana for try-on...")
        
        # Create the message with both images
        # The prompt instructs the AI to dress the person from the first image
        # in the clothing from the second image
        msg = UserMessage(
            text="Take the person from the first image and dress them in the clothing item shown in the second image. Make it look realistic, natural, and professionally styled. Ensure the clothing fits naturally on the person's body, maintaining proper proportions and lighting. Generate a high-quality portrait-style image.",
            file_contents=[
                ImageContent(request.person_image),
                ImageContent(request.clothing_image)
            ]
        )
        
        # Send message and get response with image
        text, images = await chat.send_message_multimodal_response(msg)
        
        logger.info(f"Received response from Gemini. Text: {text[:100] if text else 'None'}...")
        
        if not images or len(images) == 0:
            logger.error("No images returned from Gemini")
            raise HTTPException(
                status_code=500,
                detail="Failed to generate try-on image. No image was returned from the AI model."
            )
        
        # Get the first generated image
        result_image = images[0]
        result_image_base64 = result_image['data']
        
        logger.info(f"Successfully generated image. Size: {len(result_image_base64)} characters")
        
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
