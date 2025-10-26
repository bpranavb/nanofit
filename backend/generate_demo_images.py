import os
import base64
import asyncio
from google import genai
from google.genai import types
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

async def generate_demo_images():
    """Generate before and after demo images for the landing page slider"""
    
    gemini_api_key = os.environ.get('GEMINI_API_KEY')
    if not gemini_api_key:
        print("Error: GEMINI_API_KEY not found")
        return
    
    client = genai.Client(api_key=gemini_api_key)
    
    # Generate Before Image - Person with casual clothes (Shirt-A and Pant-A)
    print("Generating BEFORE image (casual outfit)...")
    before_prompt = "Generate a photorealistic portrait of a young professional person standing in a neutral studio background. They are wearing a light blue casual shirt and dark blue jeans. The person should have a friendly expression, natural lighting, and be centered in the frame. Portrait orientation, high quality, professional photography style."
    
    before_config = types.GenerateContentConfig(
        response_modalities=["IMAGE"]
    )
    
    before_content = types.Content(
        parts=[types.Part(text=before_prompt)]
    )
    
    before_response = await asyncio.to_thread(
        client.models.generate_content,
        model="gemini-2.5-flash-image",
        contents=before_content,
        config=before_config
    )
    
    # Extract and save before image
    before_image_base64 = None
    for part in before_response.parts:
        if part.inline_data is not None:
            image_data = part.inline_data.data
            if isinstance(image_data, bytes):
                before_image_base64 = base64.b64encode(image_data).decode('utf-8')
            else:
                before_image_base64 = image_data
            break
    
    if before_image_base64:
        before_bytes = base64.b64decode(before_image_base64)
        with open('/app/frontend/public/demo/before.png', 'wb') as f:
            f.write(before_bytes)
        print("✓ BEFORE image saved to /app/frontend/public/demo/before.png")
    else:
        print("✗ Failed to generate BEFORE image")
        return
    
    # Generate After Image - Same person with formal clothes (Shirt-B and Pant-B)
    print("Generating AFTER image (formal outfit)...")
    after_prompt = "Generate a photorealistic portrait of a young professional person standing in a neutral studio background. They are wearing a formal white dress shirt with a navy blue blazer and charcoal grey formal pants. The person should have a friendly expression, natural lighting, and be centered in the frame. Same pose and style as a professional portrait. Portrait orientation, high quality, professional photography style."
    
    after_config = types.GenerateContentConfig(
        response_modalities=["IMAGE"]
    )
    
    after_content = types.Content(
        parts=[types.Part(text=after_prompt)]
    )
    
    after_response = await asyncio.to_thread(
        client.models.generate_content,
        model="gemini-2.5-flash-image",
        contents=after_content,
        config=after_config
    )
    
    # Extract and save after image
    after_image_base64 = None
    for part in after_response.parts:
        if part.inline_data is not None:
            image_data = part.inline_data.data
            if isinstance(image_data, bytes):
                after_image_base64 = base64.b64encode(image_data).decode('utf-8')
            else:
                after_image_base64 = image_data
            break
    
    if after_image_base64:
        after_bytes = base64.b64decode(after_image_base64)
        with open('/app/frontend/public/demo/after.png', 'wb') as f:
            f.write(after_bytes)
        print("✓ AFTER image saved to /app/frontend/public/demo/after.png")
    else:
        print("✗ Failed to generate AFTER image")
        return
    
    print("\n✓ Demo images generated successfully!")
    print("Before: Casual outfit (light blue shirt + dark jeans)")
    print("After: Formal outfit (white shirt + navy blazer + grey pants)")

if __name__ == "__main__":
    asyncio.run(generate_demo_images())
