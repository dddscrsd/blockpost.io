import asyncio
import os
from aiohttp import web

# Интервал проверки активности (в секундах)
PING_INTERVAL = 25

async def ws_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    print("Client connected")

    try:
        # 1. Отправляем приветствие сразу после подключения
        await ws.send_str('{"type": "hello", "status": "ok"}')

        # Запускаем задачу, которая будет пинговать клиента каждые N секунд
        ping_task = asyncio.create_task(ping_client(ws))

        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                print(f"Received text: {msg.data[:200]}")
                # Эхо: отправляем обратно
                await ws.send_str(msg.data)
            elif msg.type == web.WSMsgType.BINARY:
                data = msg.data
                print(f"Received binary: length={len(data)} bytes")
                await ws.send_bytes(data)
            elif msg.type == web.WSMsgType.ERROR:
                print('WebSocket connection closed with an exception')
                break
            elif msg.type == web.WSMsgType.CLOSED:
                # Клиент сам закрыл соединение
                print("Client closed connection")
                break

    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        # Обязательно отменяем задачу пинга, когда соединение закрывается
        ping_task.cancel()
        if not ws.closed:
            await ws.close()
        print("Disconnected")

    return ws

async def ping_client(ws):
    """
    Каждые PING_INTERVAL секунд отправляет пинг клиенту.
    Если клиент не отвечает (ошибка отправки), разрываем соединение.
    """
    while True:
        await asyncio.sleep(PING_INTERVAL)
        try:
            # Отправляем специальный пинг-пакет
            # Важно: не используем send_str для служебных пакетов, если игра их не ждет,
            # но для теста можно отправить JSON. Лучше использовать ws.ping() если игра умеет обрабатывать pong.
            
            # Вариант А (Стандартный WS Ping - лучший вариант):
            await ws.ping()
            
            # Вариант Б (Если игра не понимает pong и ждет JSON):
            # await ws.send_str('{"type":"ping"}')
            
            print("Sent ping to client")
        except Exception:
            # Если не удалось отправить пинг, значит клиент уже отвалился
            print("Ping failed, client is gone")
            break

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
        
        # Бесконечное ожидание (правильный способ для asyncio)
        await asyncio.Event().wait()

    asyncio.run(main())
