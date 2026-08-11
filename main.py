import asyncio
import os
from aiohttp import web
import struct

# --- КОНФИГУРАЦИЯ ---
PLAYER_ID = 12288 
CMD_AUTH = 0
CMD_FRIENDS_LIST = 1

def write_string(s: str) -> bytes:
    """Эмуляция NET.WRITE_STRING: [4 байта длина][байты строки UTF-8]"""
    encoded = s.encode('utf-8')
    length = len(encoded)
    return struct.pack('<I', length) + encoded

def generate_fake_friends_list() -> bytes:
    """Генерирует бинарный пакет со списком друзей"""
    friends = [
        {"gid": 555111, "name": "SuperGamer", "status": 1},
        {"gid": 999888, "name": "NoobMaster", "status": 0},
        {"gid": PLAYER_ID, "name": "MeMyself", "status": 1}
    ]
    
    data = bytearray()
    # 1. Количество друзей
    data.extend(struct.pack('<I', len(friends)))
    
    for f in friends:
        # Status (1 байт)
        data.append(f['status'])
        # GID (Long, 8 байт, LE)
        data.extend(struct.pack('<Q', f['gid']))
        # Name (String)
        data.extend(write_string(f['name']))
        # FStatus (1 байт) - дублируем статус
        data.append(f['status']) 

    return bytes(data)

async def ws_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    print("Client connected")

    try:
        async for msg in ws:
            if msg.type == web.WSMsgType.BINARY:
                data = msg.data
                
                # --- 1. Обработка служебного хендшейка (Критично!) ---
                # Игра часто шлет 2 байта: 0x64 0x08 перед началом работы
                if len(data) == 2 and data[0] == 0x64 and data[1] == 0x08:
                    print("[HANDSHAKE] Detected handshake. Echoing back.")
                    await ws.send_bytes(data) # Просто возвращаем то же самое
                    continue

                # Если пакет короче 6 байт - пропускаем (невалидный заголовок)
                if len(data) < 6:
                    print("Packet too short, skipping.")
                    continue

                # --- 2. Парсинг заголовка ---
                # Формат: [Length:4 bytes][CmdID:2 bytes][Body...]
                try:
                    packet_len = struct.unpack('<I', data[0:4])[0]
                    cmd_id = struct.unpack('<H', data[4:6])[0]
                except struct.error:
                    print("Failed to unpack header.")
                    continue
                
                print(f"Received CMD: {cmd_id} (Hex: {hex(cmd_id)})")

                response_data = b""

                # --- 3. Логика ответов ---
                if cmd_id == CMD_AUTH:
                    # Успешная авторизация. 
                    # Отправляем пустой пакет (длина 0). Это стандартный сигнал "OK" для таких игр.
                    print("Auth received. Sending empty OK response.")
                    response_data = struct.pack('<I', 0)
                
                elif cmd_id == CMD_FRIENDS_LIST:
                    # Запрос списка друзей
                    print("Friends List requested. Generating fake data...")
                    body = generate_fake_friends_list()
                    total_len = len(body)
                    header = struct.pack('<I', total_len)
                    response_data = header + body
                
                else:
                    # !!! ГЛАВНОЕ ИСПРАВЛЕНИЕ !!!
                    # Для неизвестных команд (например, твой CMD 119)
                    # МЫ НЕ ШЛЕМ ОШИБКУ. Мы шлем пустой пакет.
                    # Это предотвращает рассинхронизацию буфера и краш игры.
                    print(f"[SAFE MODE] Unknown command {cmd_id}. Sending empty OK to keep game alive.")
                    response_data = struct.pack('<I', 0) 

                # Отправка ответа
                if response_data:
                    await ws.send_bytes(response_data)
                    # print(f"Sent {len(response_data)} bytes") # Раскомментировать для отладки

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
