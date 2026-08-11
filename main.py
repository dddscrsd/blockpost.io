import asyncio
import os
from aiohttp import web

async def ws_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    print("Client connected")

    try:
        # ВАЖНО: Пока НЕ отправляем ничего первым. 
        # Пусть игра сама сделает первый ход. Если она ждет тишины - это сработает.
        # Если ей нужно приветствие - мы увидим ошибку в логах игры и попробуем другие варианты.
        print("Waiting for client handshake...")

        async for msg in ws:
            if msg.type == web.WSMsgType.BINARY:
                data = msg.data
                # ГЛАВНОЕ: Выводим байты в HEX формате!
                hex_data = data.hex()
                print(f"Received binary ({len(data)} bytes): {hex_data}")
                
                # ЭХО: Возвращаем ровно то, что пришло. 
                # Старые игры часто проверяют, что сервер "отзеркалил" пакет.
                await ws.send_bytes(data)
            
            elif msg.type in (web.WSMsgType.ERROR, web.WSMgType.CLOSED):
                break

    except Exception as e:
        print(f"Error: {e}")
    finally:
        if not ws.closed:
            await ws.close()
        print("Disconnected")

app = web.Application()
app.router.add_get('/ws', ws_handler)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    runner = web.AppRunner(app)
    
    async def main():
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", port)
        await site.start()
        print(f"Server running on port {port}")
        await asyncio.Event().wait()

    asyncio.run(main())

