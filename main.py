import asyncio
import os
import websockets

async def handler(websocket):
    print("Client connected")
    try:
        # 1. Отправляем «приветствие» и логируем это
        hello_msg = '{"type":"hello","status":"ok"}'
        await websocket.send(hello_msg)
        print(f"Server sent (text): {hello_msg}")

        async for message in websocket:
            # 2. Логируем, что пришла игра
            if isinstance(message, str):
                print(f"Game sent (text): {message[:200]}")
            else:
                # Для бинарных данных показываем длину и первые байты (hex), чтобы было понятнее
                print(f"Game sent (binary): length={len(message)} bytes, first_10_bytes={message[:10].hex()}")

            # 3. Отправляем обратно (эхо) и логируем отправку
            await websocket.send(message)
            if isinstance(message, str):
                print(f"Server sent (text): {message[:200]}")
            else:
                print(f"Server sent (binary): length={len(message)} bytes")

    except Exception as e:
        print(f"Disconnected: {e}")

async def main():
    port = int(os.getenv("PORT", 8080))
    server = websockets.serve(handler, "0.0.0.0", port)
    print(f"WebSocket server running on port {port}")
    await server

if __name__ == "__main__":
    asyncio.run(main())
