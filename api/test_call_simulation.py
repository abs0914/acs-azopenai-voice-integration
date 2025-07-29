#!/usr/bin/env python3
"""
Simulate a call to test the greeting functionality
"""

import asyncio
import aiohttp
import json
import uuid
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def simulate_incoming_call():
    """Simulate an incoming call event"""
    try:
        # Create a simulated incoming call event
        correlation_id = str(uuid.uuid4())
        
        incoming_call_event = [{
            "eventType": "Microsoft.Communication.IncomingCall",
            "data": {
                "incomingCallContext": "simulated_call_context_12345",
                "correlationId": correlation_id,
                "from": {
                    "phoneNumber": "+1234567890"
                },
                "to": {
                    "phoneNumber": "+18449197485"
                }
            },
            "eventTime": "2025-07-29T05:55:00.000Z",
            "id": str(uuid.uuid4()),
            "dataVersion": "1.0"
        }]
        
        logger.info("📞 Simulating incoming call...")
        
        async with aiohttp.ClientSession() as session:
            # Send the incoming call event
            async with session.post(
                'http://localhost:8000/api/incomingCall',
                json=incoming_call_event,
                headers={'Content-Type': 'application/json'}
            ) as response:
                result = await response.text()
                logger.info(f"📞 Incoming call response: {response.status} - {result}")
                
                if response.status == 200:
                    logger.info("✅ Incoming call processed successfully")
                    
                    # Now simulate the CallConnected event
                    await simulate_call_connected(correlation_id)
                else:
                    logger.error(f"❌ Incoming call failed: {response.status}")
                    
    except Exception as e:
        logger.error(f"❌ Error simulating incoming call: {e}")
        import traceback
        logger.error(traceback.format_exc())

async def simulate_call_connected(correlation_id: str):
    """Simulate a CallConnected event"""
    try:
        logger.info("🔗 Simulating call connected event...")
        
        # Wait a moment for the call to be processed
        await asyncio.sleep(2)
        
        call_connected_event = [{
            "type": "Microsoft.Communication.CallConnected",
            "data": {
                "callConnectionId": "simulated-call-connection-12345",
                "serverCallId": "simulated-server-call-id",
                "correlationId": correlation_id
            },
            "eventTime": "2025-07-29T05:55:05.000Z",
            "id": str(uuid.uuid4())
        }]
        
        async with aiohttp.ClientSession() as session:
            # Send the call connected event
            callback_url = f'http://localhost:8000/api/callbacks/{correlation_id}'
            async with session.post(
                callback_url,
                json=call_connected_event,
                headers={'Content-Type': 'application/json'}
            ) as response:
                result = await response.text()
                logger.info(f"🔗 Call connected response: {response.status} - {result}")
                
                if response.status == 200:
                    logger.info("✅ Call connected event processed - Emma should greet now!")
                    
                    # Simulate PlayCompleted event after greeting
                    await simulate_play_completed(correlation_id)
                else:
                    logger.error(f"❌ Call connected event failed: {response.status}")
                    
    except Exception as e:
        logger.error(f"❌ Error simulating call connected: {e}")

async def simulate_play_completed(correlation_id: str):
    """Simulate PlayCompleted event after greeting"""
    try:
        logger.info("🎵 Simulating play completed event...")
        
        # Wait for the greeting to "play"
        await asyncio.sleep(3)
        
        play_completed_event = [{
            "type": "Microsoft.Communication.PlayCompleted",
            "data": {
                "callConnectionId": "simulated-call-connection-12345",
                "operationContext": "emma-greeting",
                "correlationId": correlation_id,
                "resultInformation": {
                    "code": 200,
                    "subCode": 0,
                    "message": "Action completed successfully."
                }
            },
            "eventTime": "2025-07-29T05:55:10.000Z",
            "id": str(uuid.uuid4())
        }]
        
        async with aiohttp.ClientSession() as session:
            callback_url = f'http://localhost:8000/api/callbacks/{correlation_id}'
            async with session.post(
                callback_url,
                json=play_completed_event,
                headers={'Content-Type': 'application/json'}
            ) as response:
                result = await response.text()
                logger.info(f"🎵 Play completed response: {response.status} - {result}")
                
                if response.status == 200:
                    logger.info("✅ Play completed - Voice Live should be ready for conversation!")
                else:
                    logger.error(f"❌ Play completed event failed: {response.status}")
                    
    except Exception as e:
        logger.error(f"❌ Error simulating play completed: {e}")

async def main():
    """Run the call simulation"""
    logger.info("🧪 Starting call simulation test...")
    
    # Test the complete call flow
    await simulate_incoming_call()
    
    logger.info("🎉 Call simulation completed!")

if __name__ == "__main__":
    asyncio.run(main())
