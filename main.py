import asyncio
import os
from aiohttp import web

async def ws_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    print("Client connected")

    try:
        print("Waiting for client handshake...")

        async for msg in ws:
            if msg.type == web.WSMsgType.BINARY:
                data = msg.data
                hex_data = data.hex()
                print(f"Received: {hex_data}")

                # --- ГЛАВНАЯ ЛОГИКА ---
                # Мы НЕ отправляем data обратно (это вызывало ошибку 48).
                # Мы формируем свой пакет ответа.
                
                # Вариант 1: Самый частый случай для старых игр.
                # Ответ: [Магия F5] [ID 0000] [Длина 0] [Статус 0]
                # Это значит: "Пакет принят, ошибок нет".
                response_packet = bytes([0xF5, 0x00, 0x00, 0x00, 0x00])
                
                # Если игра ждет ровно 4 байта, убери последний 0x00.
                # Но обычно 5 байт безопаснее.
                
                print(f"Sending OK packet: {response_packet.hex()}")
                await ws.send_bytes(response_packet)
                # -----------------------

            elif msg.type in (web.WSMsgType.ERROR, web.WSMsgType.CLOSED):
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
