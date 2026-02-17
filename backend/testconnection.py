import socket
import asyncio
import websockets
import ssl

HOST = "ori-asr-test.oriserve.com"
URL = f"wss://{HOST}/connect?model=ori-prime-v2.3&sample_rate=16000&language=en"

print(f"1. Testing DNS resolution for: {HOST}")
try:
    ip = socket.gethostbyname(HOST)
    print(f"   ✅ SUCCESS: Resolved to {ip}")
except socket.gaierror:
    print(f"   ❌ FAILED: Could not resolve '{HOST}'. Check your spelling or VPN.")
    exit()

async def test_ws():
    print(f"\n2. Testing WebSocket Connection to: {URL}")
    try:
        # Ignore SSL cert errors for testing purposes
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        async with websockets.connect(URL, ssl=ssl_context) as ws:
            print("   ✅ SUCCESS: Connected to WebSocket Server!")
            await ws.close()
    except Exception as e:
        print(f"   ❌ FAILED: {e}")

if __name__ == "__main__":
    asyncio.run(test_ws())