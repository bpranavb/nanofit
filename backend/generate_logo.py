import os
from openai import OpenAI
from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv('/app/backend/.env')

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
    base_url="https://llm.emergent.sh/v1",
)

def generate_logo():
    print("Generating logo...")
    try:
        response = client.images.generate(
            model="gpt-image-1",
            prompt="A minimalist, award-winning app icon for a 'Virtual Try-On' fashion app. The design should be sleek, modern, and high-end. Use a color palette of deep charcoal, electric violet, and white. The icon should feature a stylized hanger or a clothing silhouette merging with a digital pixel or sparkle effect, representing AI fashion. Vector style, flat design, white background.",
            n=1,
            size="1024x1024"
        )
        
        image_url = response.data[0].url
        print(f"Logo generated: {image_url}")
        
        # Download and save
        img_data = requests.get(image_url).content
        output_path = '/app/frontend/public/logo_generated.png'
        with open(output_path, 'wb') as handler:
            handler.write(img_data)
        print(f"Logo saved to {output_path}")
        
    except Exception as e:
        print(f"Error generating logo: {e}")

if __name__ == "__main__":
    generate_logo()
