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
from io import BytesIO
from PIL import Image as PILImage


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
        session_id_analysis = str(uuid.uuid4())
        session_id_generation = str(uuid.uuid4())
        
        logger.info("Step 1: Analyzing person image...")
        
        # Step 1: Analyze the person image to get detailed description
        chat_person = LlmChat(
            api_key=gemini_api_key,
            session_id=session_id_analysis,
            system_message="You are an expert at analyzing images and providing detailed descriptions."
        )
        chat_person.with_model("gemini", "gemini-2.0-flash-exp")
        
        msg_person = UserMessage(
            text="Describe this person in detail: their physical appearance, pose, body type, facial features, skin tone, and any visible characteristics. Be specific and detailed.",
            file_contents=[ImageContent(request.person_image)]
        )
        
        person_description = await chat_person.send_message(msg_person)
        logger.info(f"Person description: {person_description[:200]}...")
        
        logger.info("Step 2: Analyzing clothing image...")
        
        # Step 2: Analyze the clothing image
        chat_clothing = LlmChat(
            api_key=gemini_api_key,
            session_id=f"{session_id_analysis}_clothing",
            system_message="You are an expert at analyzing fashion and clothing items."
        )
        chat_clothing.with_model("gemini", "gemini-2.0-flash-exp")
        
        msg_clothing = UserMessage(
            text="Describe this clothing item in detail: the type of garment, color, pattern, style, material, fit, and any distinctive features. Be specific about the design.",
            file_contents=[ImageContent(request.clothing_image)]
        )
        
        clothing_description = await chat_clothing.send_message(msg_clothing)
        logger.info(f"Clothing description: {clothing_description[:200]}...")
        
        logger.info("Step 3: Generating virtual try-on image...")
        
        # Step 3: Generate the try-on image using Gemini image generation
        chat_generate = LlmChat(
            api_key=gemini_api_key,
            session_id=session_id_generation,
            system_message="You are an expert at generating photorealistic images."
        )
        chat_generate.with_model("gemini", "gemini-2.5-flash-image-preview").with_params(
            modalities=["image", "text"]
        )
        
        # Create a detailed prompt combining both descriptions
        generation_prompt = f"""Generate a photorealistic image of a person wearing specific clothing.

Person details: {person_description}

Clothing to wear: {clothing_description}

Create a natural, professional photo showing this person wearing the described clothing. The image should look realistic with proper lighting, natural poses, and the clothing fitting naturally on the person. Maintain the person's appearance and characteristics while showing them in the new outfit. Generate the image in portrait orientation."""
        
        msg_generate = UserMessage(text=generation_prompt)
        
        # Generate image
        text_response, images = await chat_generate.send_message_multimodal_response(msg_generate)
        
        logger.info(f"Generation response - Text: {text_response[:200] if text_response else 'None'}...")
        logger.info(f"Number of images returned: {len(images) if images else 0}")
        
        if not images or len(images) == 0:
            logger.error("No images returned from Gemini image generation")
            logger.error(f"Full text response: {text_response}")
            raise HTTPException(
                status_code=500,
                detail="Failed to generate try-on image. The model did not return an image. This might be due to API limitations. Please try with different images or contact support."
            )
        
        # Get the generated image
        result_image_base64 = images[0]['data']
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
