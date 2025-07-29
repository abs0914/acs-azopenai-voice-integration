#!/usr/bin/env python3
"""
Test if Event Grid can reach our server
"""

import asyncio
import aiohttp
import json
import uuid
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_event_grid_webhook():
    """Test if our server can receive Event Grid events"""
    try:
        # Test the incoming call endpoint
        webhook_url = "https://v2vhskmw-8000.asse.devtunnels.ms/api/incomingCall"
        
        logger.info(f"📞 Testing Event Grid webhook: {webhook_url}")
        
        # Create a test Event Grid validation event
        validation_event = [{
            "id": str(uuid.uuid4()),
            "eventType": "Microsoft.EventGrid.SubscriptionValidationEvent",
            "subject": "test",
            "eventTime": "2025-07-29T06:30:00.000Z",
            "data": {
                "validationCode": "test-validation-code-12345"
            },
            "dataVersion": "1.0"
        }]
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                webhook_url,
                json=validation_event,
                headers={'Content-Type': 'application/json'}
            ) as response:
                result = await response.text()
                logger.info(f"📞 Validation response: {response.status} - {result}")
                
                if response.status == 200:
                    logger.info("✅ Event Grid webhook is reachable")
                    
                    # Now test a simulated incoming call
                    logger.info("📞 Testing simulated incoming call...")
                    
                    incoming_call_event = [{
                        "id": str(uuid.uuid4()),
                        "eventType": "Microsoft.Communication.IncomingCall",
                        "subject": "test-call",
                        "eventTime": "2025-07-29T06:30:00.000Z",
                        "data": {
                            "incomingCallContext": "test-call-context-12345",
                            "correlationId": str(uuid.uuid4()),
                            "from": {
                                "phoneNumber": "+1234567890"
                            },
                            "to": {
                                "phoneNumber": "+18449197485"
                            }
                        },
                        "dataVersion": "1.0"
                    }]
                    
                    async with session.post(
                        webhook_url,
                        json=incoming_call_event,
                        headers={'Content-Type': 'application/json'}
                    ) as call_response:
                        call_result = await call_response.text()
                        logger.info(f"📞 Incoming call response: {call_response.status} - {call_result}")
                        
                        if call_response.status == 200:
                            logger.info("✅ Incoming call webhook works")
                            return True
                        else:
                            logger.error("❌ Incoming call webhook failed")
                            return False
                else:
                    logger.error(f"❌ Event Grid webhook not reachable: {response.status}")
                    return False
                    
    except Exception as e:
        logger.error(f"❌ Event Grid test failed: {e}")
        return False

async def main():
    """Run Event Grid test"""
    logger.info("🧪 Testing Event Grid webhook accessibility...")
    
    success = await test_event_grid_webhook()
    
    if success:
        logger.info("✅ Event Grid webhook is working - events should reach our server")
        logger.info("🔍 The issue might be in the Azure Event Grid subscription configuration")
    else:
        logger.error("❌ Event Grid webhook is not working - this is why calls don't work")
        logger.error("🔧 Check dev tunnel URL and Event Grid subscription")

if __name__ == "__main__":
    asyncio.run(main())
