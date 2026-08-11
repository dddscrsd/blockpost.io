import asyncio
import os
import websockets
from aiohttp import web

# HTTP: отдаём index.html на /
async def handle_html(request):
    try:
        with open("index.html", "r", encoding="utf-8") as f:
            return web.Response(text=f.read(), content_type="text/html; charset=utf-8")
    except FileNotFoundError:
        return web.Response(text="index.html not found", status=404)

app = web.Application()
app.router.add_get('/', handle_html)

# WebSocket: твоя логика
async def ws_handler(websocket):
    print("Client connected")
    try:
        hello_msg = '{"type":"hello","status":"ok"}'
        await websocket.send(hello_msg)
        print(f"Server sent (text): {hello_msg}")

        async for message in websocket:
            if isinstance(message, str):
                print(f"Game sent (text): {message[:200]}")
            else:
                print(f"Game sent (binary): length={len(message)} bytes, first_10_bytes={message[:10].hex()}")

            # Эхо: отправляем обратно то же самое
            await websocket.send(message)
            if isinstance(message, str):
                print(f"Server sent (text): {message[:200]}")
            else:
                print(f"Server sent (binary): length={len(message)} bytes")
    except Exception as e:
        print(f"Disconnected: {e}")

async def start_ws_server():
    port = int(os.getenv("PORT", 8080))
    async with websockets.serve(ws_handler, "0.0.0.0", port):
        await asyncio.Future()  # run forever

async def main():
    # HTTP на том же порту
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8080)
    await site.start()
    print("HTTP server running on port 8080")

    # Параллельно запускаем WebSocket
    await start_ws_server()

if __name__ == "__main__":
    asyncio.run(main())
