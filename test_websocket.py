import asyncio
import websockets
import json

async def test_websocket():
    try:
        print("Connecting to WebSocket...")
        async with websockets.connect('wss://0hwxmpkp-8000.asse.devtunnels.ms/ws') as ws:
            print("Connected successfully!")
            
            # Send a test message
            test_message = json.dumps({"test": "message"})
            await ws.send(test_message)
            print(f"Sent: {test_message}")
            
            # Wait for response
            try:
                response = await asyncio.wait_for(ws.recv(), timeout=5.0)
                print(f"Received: {response}")
            except asyncio.TimeoutError:
                print("No response received within 5 seconds")
                
    except Exception as e:
        print(f"WebSocket connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_websocket())
