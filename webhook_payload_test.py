#!/usr/bin/env python3
"""
Test to verify the exact webhook payload structure being sent to n8n
"""

import asyncio
import base64
import json
import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, patch

# Add backend to path
sys.path.append(str(Path(__file__).parent / "backend"))

from server import send_to_n8n_webhook

async def test_webhook_payload():
    """Test the exact payload structure sent to n8n webhook"""
    print("🔍 Testing N8N Webhook Payload Structure")
    print("=" * 50)
    
    # Test data
    test_tryon_id = "test-123-456"
    test_person_image = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
    test_clothing_image = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
    test_result_image = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
    
    # Mock httpx client to capture the payload
    captured_payload = None
    captured_url = None
    
    class MockResponse:
        def __init__(self):
            self.status_code = 200
        
        def raise_for_status(self):
            pass
    
    async def mock_post(url, json=None, **kwargs):
        nonlocal captured_payload, captured_url
        captured_url = url
        captured_payload = json
        return MockResponse()
    
    # Patch httpx.AsyncClient.post
    with patch('httpx.AsyncClient.post', side_effect=mock_post):
        await send_to_n8n_webhook(
            person_image_base64=test_person_image,
            clothing_image_base64=test_clothing_image,
            result_image_base64=test_result_image,
            tryon_id=test_tryon_id
        )
    
    print(f"✅ Webhook URL: {captured_url}")
    print(f"✅ Payload captured successfully")
    print("\n📋 Payload Structure:")
    print(json.dumps(captured_payload, indent=2))
    
    # Verify payload structure
    required_fields = ['tryon_id', 'timestamp', 'person_image', 'clothing_image', 'result_image']
    missing_fields = [field for field in required_fields if field not in captured_payload]
    
    if missing_fields:
        print(f"❌ Missing required fields: {missing_fields}")
        return False
    
    print(f"\n✅ All required fields present: {required_fields}")
    
    # Verify data types
    print(f"\n🔍 Field Verification:")
    print(f"  - tryon_id: {type(captured_payload['tryon_id']).__name__} = '{captured_payload['tryon_id']}'")
    print(f"  - timestamp: {type(captured_payload['timestamp']).__name__} = '{captured_payload['timestamp']}'")
    print(f"  - person_image: {type(captured_payload['person_image']).__name__} (length: {len(captured_payload['person_image'])})")
    print(f"  - clothing_image: {type(captured_payload['clothing_image']).__name__} (length: {len(captured_payload['clothing_image'])})")
    print(f"  - result_image: {type(captured_payload['result_image']).__name__} (length: {len(captured_payload['result_image'])})")
    
    # Verify timestamp format
    try:
        datetime.fromisoformat(captured_payload['timestamp'])
        print(f"  ✅ Timestamp format is valid ISO format")
    except ValueError:
        print(f"  ❌ Invalid timestamp format: {captured_payload['timestamp']}")
        return False
    
    # Verify base64 images
    for img_field in ['person_image', 'clothing_image', 'result_image']:
        try:
            base64.b64decode(captured_payload[img_field])
            print(f"  ✅ {img_field} is valid base64")
        except Exception as e:
            print(f"  ❌ {img_field} is invalid base64: {e}")
            return False
    
    print(f"\n🎉 Webhook payload structure is CORRECT!")
    return True

if __name__ == "__main__":
    asyncio.run(test_webhook_payload())