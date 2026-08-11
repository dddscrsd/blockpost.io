import os
from aiohttp import web

# 1. HTTP: отдаём index.html на /
async def handle_html(request):
    try:
        with open("index.html", "r", encoding="utf-8") as f:
            return web.Response(text=f.read(), content_type="text/html; charset=utf-8")
    except FileNotFoundError:
        return web.Response(text="index.html not found", status=404)

# 2. WebSocket: логика внутри aiohttp
async def ws_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    print("Client connected")

    # Сразу шлем приветствие
    await ws.send_str('{"type":"hello","status":"ok"}')
    print('Server sent (text): {"type":"hello","status":"ok"}')

    async for msg in ws:
        if msg.type == web.WSMsgType.TEXT:
            print(f"Game sent (text): {msg.data[:200]}")
            await ws.send_str(msg.data)
            print(f"Server sent (text): {msg.data[:200]}")
        elif msg.type == web.WSMsgType.BINARY:
            data = msg.data
            print(f"Game sent (binary): length={len(data)} bytes, first_10_bytes={data[:10].hex()}")
            await ws.send_bytes(data)
            print(f"Server sent (binary): length={len(data)} bytes")
        elif msg.type == web.WSMsgType.ERROR:
            print(f"WebSocket connection closed with exception {ws.exception()}")

    print("Disconnected")
    return ws

app = web.Application()
app.router.add_get('/', handle_html)
app.router.add_get('/ws', ws_handler)  # WS будет на /ws

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    print(f"HTTP + WebSocket server running on port {port}")
    web.run_app(app, host="0.0.0.0", port=port)

