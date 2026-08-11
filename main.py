import asyncio
import os
from aiohttp import web
import struct

# --- КОНФИГУРАЦИЯ ---
PLAYER_ID = 12288 
# ID команды авторизации (из FriendClient.send_auth -> packetid: 0)
CMD_AUTH = 0
# ID команды запроса списка друзей (packetid: 1)
CMD_FRIENDS_LIST = 1

def write_string(s: str) -> bytes:
    """Эмуляция NET.WRITE_STRING: [4 байта длина][байты строки UTF-8]"""
    encoded = s.encode('utf-8')
    length = len(encoded)
    # Little Endian длина + данные
    return struct.pack('<I', length) + encoded

def generate_fake_friends_list() -> bytes:
    """Генерирует бинарный пакет со списком друзей, который поймет клиент"""
    friends = [
        {"gid": 555111, "name": "SuperGamer", "status": 1}, # 1 = Online
        {"gid": 999888, "name": "NoobMaster", "status": 0}, # 0 = Offline
        {"gid": PLAYER_ID, "name": "MeMyself", "status": 1}
    ]
    
    data = bytearray()
    
    # 1. Пишем количество друзей (int, 4 байта, LE)
    data.extend(struct.pack('<I', len(friends)))
    
    for f in friends:
        # Структура для recv_friend: status(byte), gid(long), name(string), fstatus(byte)
        
        # Status (1 байт)
        data.append(f['status'])
        
        # GID (Long, 8 байт, LE) - в C# long это 8 байт
        data.extend(struct.pack('<Q', f['gid']))
        
        # Name (String: Len + Bytes)
        data.extend(write_string(f['name']))
        
        # FStatus (1 байт) - часто дублирует статус или имеет спец значение
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
                
                # --- ЛОГИКА ПАРСИНГА ПАКЕТА КЛИЕНТА ---
                # Предполагаем формат клиента: [Length:4][CmdID:2][Body...]
                if len(data) < 6:
                    print("Packet too short")
                    continue

                # Читаем длину (первые 4 байта)
                packet_len = struct.unpack('<I', data[0:4])[0]
                # Читаем Command ID (следующие 2 байта)
                cmd_id = struct.unpack('<H', data[4:6])[0]
                
                print(f"Received CMD: {cmd_id} (Hex: {hex(cmd_id)})")

                response_data = b""

                if cmd_id == CMD_AUTH:
                    # Клиент отправил send_auth()
                    # Ожидаем: Long(gid), String(name), String(sign)
                    # Мы просто подтверждаем успех. 
                    # ВАЖНО: Какой ответ ждет клиент после Auth?
                    # Обычно это пустой пакет или пакет с подтверждением.
                    # Но судя по FakeServer, после Auth клиент сразу ждет списки.
                    
                    print("Auth received. Sending empty OK response.")
                    # Возвращаем пакет с длиной 0 или просто подтверждение
                    response_data = struct.pack('<I', 0) # Длина 0
                    
                elif cmd_id == CMD_FRIENDS_LIST:
                    # Клиент запросил список друзей (send_friendlist)
                    print("Friends List requested. Generating fake data...")
                    
                    # Формируем полный бинарный пакет
                    body = generate_fake_friends_list()
                    total_len = len(body)
                    
                    # Собираем ответ: [Длина тела][CmdID ответа?][Тело]
                    # Часто сервер шлет тот же CmdID или специальный ID ответа.
                    # Попробуем отправить тело сразу, либо с заголовком.
                    # Если клиент читает через NET.BEGIN_READ(..., startpos: 4), 
                    # значит первые 4 байта - это длина, которую он может игнорировать или использовать.
                    
                    header = struct.pack('<I', total_len)
                    response_data = header + body
                    
                else:
                    print(f"Unknown command {cmd_id}. Sending generic error.")
                    response_data = struct.pack('<I', 1) + bytes([0xFF]) # Error byte

                # Отправляем ответ
                if response_data:
                    print(f"Sending response: {len(response_data)} bytes")
                    await ws.send_bytes(response_data)

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

