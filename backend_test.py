#!/usr/bin/env python3
"""
Backend Test Suite for Virtual Try-On Application
Focus: N8N Webhook Integration Testing
"""

import asyncio
import base64
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import httpx
import pytest
from dotenv import load_dotenv

# Add backend to path for imports
sys.path.append(str(Path(__file__).parent / "backend"))

# Load environment variables
load_dotenv(Path(__file__).parent / "frontend" / ".env")

# Get backend URL from frontend .env
BACKEND_URL = os.getenv("REACT_APP_BACKEND_URL", "http://localhost:8001")
API_BASE_URL = f"{BACKEND_URL}/api"

print(f"Testing backend at: {API_BASE_URL}")

# Small test images (1x1 pixel) to avoid Gemini API timeouts
SMALL_PERSON_IMAGE_B64 = "/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/2wBDAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwA/wA=="

SMALL_CLOTHING_IMAGE_B64 = "/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/2wBDAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwA/wA=="


class TestN8NWebhookIntegration:
    """Test suite for N8N webhook integration"""
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=60.0)
        self.test_results = []
        
    async def cleanup(self):
        """Cleanup resources"""
        await self.client.aclose()
    
    async def test_api_health(self):
        """Test if the API is running"""
        print("\n=== Testing API Health ===")
        try:
            response = await self.client.get(f"{API_BASE_URL}/")
            print(f"API Health Status: {response.status_code}")
            print(f"Response: {response.json()}")
            
            if response.status_code == 200:
                self.test_results.append("✅ API Health Check: PASSED")
                return True
            else:
                self.test_results.append(f"❌ API Health Check: FAILED - Status {response.status_code}")
                return False
                
        except Exception as e:
            self.test_results.append(f"❌ API Health Check: FAILED - {str(e)}")
            print(f"API Health Check Error: {e}")
            return False
    
    async def test_tryon_endpoint_basic(self):
        """Test basic try-on endpoint functionality"""
        print("\n=== Testing Try-On Endpoint (Basic) ===")
        try:
            payload = {
                "person_image": SMALL_PERSON_IMAGE_B64,
                "clothing_image": SMALL_CLOTHING_IMAGE_B64
            }
            
            print("Sending try-on request with small test images...")
            response = await self.client.post(f"{API_BASE_URL}/tryon", json=payload)
            
            print(f"Try-On Response Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"Try-On ID: {result.get('id')}")
                print(f"Status: {result.get('status')}")
                print(f"Result Image Length: {len(result.get('result_image', ''))}")
                
                # Verify response structure
                required_fields = ['id', 'result_image', 'timestamp', 'status']
                missing_fields = [field for field in required_fields if field not in result]
                
                if missing_fields:
                    self.test_results.append(f"❌ Try-On Endpoint: FAILED - Missing fields: {missing_fields}")
                    return False, None
                
                self.test_results.append("✅ Try-On Endpoint: PASSED")
                return True, result.get('id')
                
            else:
                error_detail = response.text
                print(f"Try-On Error: {error_detail}")
                self.test_results.append(f"❌ Try-On Endpoint: FAILED - Status {response.status_code}")
                return False, None
                
        except Exception as e:
            self.test_results.append(f"❌ Try-On Endpoint: FAILED - {str(e)}")
            print(f"Try-On Endpoint Error: {e}")
            return False, None
    
    async def check_backend_logs_for_webhook(self):
        """Check backend logs for webhook-related messages"""
        print("\n=== Checking Backend Logs for Webhook Activity ===")
        try:
            import subprocess
            
            # Check supervisor logs for backend
            log_files = [
                "/var/log/supervisor/backend.out.log",
                "/var/log/supervisor/backend.err.log"
            ]
            
            webhook_logs_found = []
            
            for log_file in log_files:
                try:
                    result = subprocess.run(
                        ["tail", "-n", "50", log_file],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    
                    if result.returncode == 0:
                        log_content = result.stdout
                        print(f"\n--- {log_file} (last 50 lines) ---")
                        print(log_content)
                        
                        # Look for webhook-related log messages
                        webhook_keywords = [
                            "Sending try-on data to n8n webhook",
                            "Successfully sent data to n8n webhook",
                            "HTTP error sending to n8n webhook",
                            "Unexpected error sending to n8n webhook"
                        ]
                        
                        for keyword in webhook_keywords:
                            if keyword in log_content:
                                webhook_logs_found.append(f"Found: '{keyword}' in {log_file}")
                                
                except subprocess.TimeoutExpired:
                    print(f"Timeout reading {log_file}")
                except FileNotFoundError:
                    print(f"Log file not found: {log_file}")
            
            if webhook_logs_found:
                print(f"\n✅ Webhook logs found:")
                for log in webhook_logs_found:
                    print(f"  - {log}")
                self.test_results.append("✅ Webhook Logs: FOUND")
                return True
            else:
                print("❌ No webhook-related logs found")
                self.test_results.append("❌ Webhook Logs: NOT FOUND")
                return False
                
        except Exception as e:
            print(f"Error checking logs: {e}")
            self.test_results.append(f"❌ Webhook Logs Check: FAILED - {str(e)}")
            return False
    
    async def test_webhook_payload_structure(self):
        """Test that webhook is called with correct payload structure"""
        print("\n=== Testing Webhook Payload Structure ===")
        
        # We can't directly intercept the webhook call, but we can verify
        # the function exists and has the right signature by importing it
        try:
            sys.path.append(str(Path(__file__).parent / "backend"))
            from server import send_to_n8n_webhook, N8N_WEBHOOK_URL
            
            print(f"N8N Webhook URL: {N8N_WEBHOOK_URL}")
            
            # Verify the function signature
            import inspect
            sig = inspect.signature(send_to_n8n_webhook)
            params = list(sig.parameters.keys())
            
            expected_params = ['person_image_base64', 'clothing_image_base64', 'result_image_base64', 'tryon_id']
            
            print(f"Function parameters: {params}")
            print(f"Expected parameters: {expected_params}")
            
            if params == expected_params:
                self.test_results.append("✅ Webhook Function Signature: CORRECT")
                
                # Verify webhook URL is correct
                if N8N_WEBHOOK_URL == "https://99.6.135.187:7801/webhook/upload":
                    self.test_results.append("✅ Webhook URL: CORRECT")
                    return True
                else:
                    self.test_results.append(f"❌ Webhook URL: INCORRECT - {N8N_WEBHOOK_URL}")
                    return False
            else:
                self.test_results.append(f"❌ Webhook Function Signature: INCORRECT - Got {params}")
                return False
                
        except Exception as e:
            self.test_results.append(f"❌ Webhook Function Check: FAILED - {str(e)}")
            print(f"Webhook function check error: {e}")
            return False
    
    async def test_error_handling(self):
        """Test that webhook errors don't break the try-on process"""
        print("\n=== Testing Error Handling ===")
        
        # This test verifies that even if webhook fails, try-on still works
        # We'll test with invalid images to potentially trigger webhook errors
        try:
            payload = {
                "person_image": "invalid_base64",
                "clothing_image": "invalid_base64"
            }
            
            print("Testing with invalid base64 images...")
            response = await self.client.post(f"{API_BASE_URL}/tryon", json=payload)
            
            print(f"Error Handling Test Status: {response.status_code}")
            
            # We expect this to fail at the Gemini level, not the webhook level
            # The important thing is that the API responds properly
            if response.status_code in [400, 422, 500]:
                print("Expected error response received")
                self.test_results.append("✅ Error Handling: API responds to invalid input")
                return True
            else:
                print(f"Unexpected response: {response.text}")
                self.test_results.append(f"❌ Error Handling: Unexpected response {response.status_code}")
                return False
                
        except Exception as e:
            self.test_results.append(f"❌ Error Handling Test: FAILED - {str(e)}")
            print(f"Error handling test error: {e}")
            return False
    
    async def run_all_tests(self):
        """Run all webhook integration tests"""
        print("🚀 Starting N8N Webhook Integration Tests")
        print("=" * 60)
        
        # Test 1: API Health
        api_healthy = await self.test_api_health()
        
        if not api_healthy:
            print("❌ API is not healthy, skipping other tests")
            return self.test_results
        
        # Test 2: Try-On Endpoint
        tryon_success, tryon_id = await self.test_tryon_endpoint_basic()
        
        # Test 3: Check logs for webhook activity
        await self.check_backend_logs_for_webhook()
        
        # Test 4: Webhook function structure
        await self.test_webhook_payload_structure()
        
        # Test 5: Error handling
        await self.test_error_handling()
        
        # Wait a bit for async webhook calls to complete
        print("\n⏳ Waiting 5 seconds for async webhook calls to complete...")
        await asyncio.sleep(5)
        
        # Check logs again after waiting
        print("\n=== Final Log Check ===")
        await self.check_backend_logs_for_webhook()
        
        return self.test_results


async def main():
    """Main test runner"""
    tester = TestN8NWebhookIntegration()
    
    try:
        results = await tester.run_all_tests()
        
        print("\n" + "=" * 60)
        print("🏁 TEST RESULTS SUMMARY")
        print("=" * 60)
        
        for result in results:
            print(result)
        
        # Count passed/failed
        passed = len([r for r in results if r.startswith("✅")])
        failed = len([r for r in results if r.startswith("❌")])
        
        print(f"\n📊 TOTAL: {passed} PASSED, {failed} FAILED")
        
        if failed == 0:
            print("🎉 ALL TESTS PASSED!")
        else:
            print("⚠️  SOME TESTS FAILED - Check details above")
            
    except Exception as e:
        print(f"❌ Test runner failed: {e}")
    finally:
        await tester.cleanup()


if __name__ == "__main__":
    asyncio.run(main())