import asyncio
import os
from aiohttp import web

# Наш известный ID игрока (12288 в десятичной = 0x3000 в hex)
PLAYER_ID = 12288 
PLAYER_ID_BYTES = PLAYER_ID.to_bytes(4, byteorder='little') # Превращаем в 4 байта: 00 30 00 00

async def ws_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    print("Client connected")

    try:
        print("Waiting for client handshake...")
        
        # Флаг, чтобы ответить только один раз на первый пакет
        first_response_sent = False

        async for msg in ws:
            if msg.type == web.WSMsgType.BINARY:
                data = msg.data
                hex_data = data.hex()
                print(f"Received: {hex_data}")

                if not first_response_sent and len(data) >= 4:
                    # --- ГЛАВНАЯ ЛОГИКА ---
                    
                    # Проверяем, является ли это первым пакетом проверки (ID 64 08)
                    # data[1] и data[2] - это байты ID команды
                    cmd_id_hex = f"{data[1]:02x}{data[2]:02x}"
                    
                    if cmd_id_hex == "6408":
                        print("Detected Handshake packet (6408). Sending Auth Success response.")
                        
                        # ФОРМИРУЕМ ОТВЕТ ДЛЯ АВТОРИЗАЦИИ
                        # Структура (предполагаемая): [F5] [ID ответа] [Status 0] [PlayerID]
                        # Попробуем ID ответа = 01 00 (часто значит "Success")
                        response_packet = bytes([0xF5, 0x01, 0x00, 0x00]) + PLAYER_ID_BYTES
                        
                        # Если игра ждет 9 байт, это оно. Если меньше - обрежется, но структура важнее.
                        print(f"Sending Auth Response: {response_packet.hex()}")
                        await ws.send_bytes(response_packet)
                        first_response_sent = True
                    else:
                        # Для других пакетов шлем простой ОК с тем же ID, но статусом 0
                        # Это запасной вариант, если игра ждет подтверждения на каждый шаг
                        response_packet = data[:3] + bytes([0x00]) 
                        print(f"Sending generic OK: {response_packet.hex()}")
                        await ws.send_bytes(response_packet)
                
                # Если первый ответ уже отправлен, просто эхом возвращаем пакеты, 
                # чтобы игра думала, что сервер живой, но не ломала протокол
                elif len(data) >= 3:
                     # Возвращаем минимальный пакет с тем же ID
                     response_packet = data[:3] + bytes([0x00])
                     await ws.send_bytes(response_packet)

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
