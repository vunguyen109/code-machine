import asyncio
import json
import websockets

async def test_client():
    uri = "ws://127.0.0.1:8000/api/ws"
    print(f"Connecting to {uri}...")
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected successfully!")
            
            payload = {
                "prompt": "Write a simple python script",
                "api_key": ""
            }
            
            print(f"Sending payload: {payload}")
            await websocket.send(json.dumps(payload))
            
            print("Waiting for response...")
            while True:
                response = await websocket.recv()
                print(f"Received: {response}")
    except Exception as e:
        print(f"Connection closed/failed with error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_client())
