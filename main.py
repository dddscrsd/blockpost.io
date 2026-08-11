import asyncio
import os
from aiohttp import web

async def ws_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    print("Client connected")

    # Отправляем приветствие
    await ws.send_str('{"type":"hello","status":"ok"}')

    async for msg in ws:
        if msg.type == web.WSMsgType.TEXT:
            print(f"Received text: {msg.data[:200]}")
            # Эхо: отправляем обратно то же самое
            await ws.send_str(msg.data)
        elif msg.type == web.WSMsgType.BINARY:
            data = msg.data
            print(f"Received binary: length={len(data)} bytes")
            await ws.send_bytes(data)
        elif msg.type == web.WSMsgType.ERROR:
            print('WebSocket connection closed with an exception')

    print("Disconnected")
    return ws

app = web.Application()
# WebSocket доступен только по пути /ws
app.router.add_get('/ws', ws_handler)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    runner = web.AppRunner(app)
    asyncio.run(runner.setup())
    site = web.TCPSite(runner, "0.0.0.0", port)
    print(f"Server running on port {port}")
    asyncio.run(site.start())
    # Держим процесс живым
    while True:
        asyncio.run(asyncio.sleep(3600))
