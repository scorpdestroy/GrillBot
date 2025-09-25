# main.py
import os
import asyncio
from aiohttp import web
from telethon import TelegramClient, events
from telethon.sessions import StringSession

# ======= ENV =======
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
STRING_SESSION = os.getenv("STRING_SESSION", "")  # см. как получить ниже
SOURCE_CHANNEL = os.getenv("SOURCE_CHANNEL", "aerogrill_recepti")
TARGET_CHANNEL = os.getenv("TARGET_CHANNEL", "CookingWithGrill")

# ======= TELETHON CLIENT =======
if not (API_ID and API_HASH and STRING_SESSION):
    raise RuntimeError("Заполни API_ID, API_HASH и STRING_SESSION в переменных окружения.")

client = TelegramClient(StringSession(STRING_SESSION), API_ID, API_HASH)

print("Я родился!")

def del_bad_from_str(msg: str) -> str:
    """
    Удаляет содержимое в скобках [ ] и ( ), 
    а также заменяет некоторые спецсимволы.
    """
    replacements = {"⏰": "🕐", "📖": "✨", "🌡️": "🔥"}
    result = []
    skip = False
    for ch in msg:
        if skip:
            if ch in ("]", ")"):
                skip = False
            continue
        if ch in ("[", "("):
            skip = True
            continue
        result.append(replacements.get(ch, ch))
    return "".join(result)

def is_post(msg: str) -> bool:
    "Определяет пост ли то сообщение которое мы скачали"
    return "Подписаться!" in msg

@client.on(events.NewMessage(chats=SOURCE_CHANNEL))
async def handler(event):
    msg = event.message
    raw_text = (msg.text or msg.message or "")
    if not is_post(raw_text):
        print("Скачанное сообщение - не пост")
        return
    clean_text = del_bad_from_str(raw_text) if raw_text else ""
    if msg.media:
        await client.send_file(TARGET_CHANNEL, msg.media, caption=clean_text)
    else:
        if clean_text.strip():
            await client.send_message(TARGET_CHANNEL, clean_text)
        else:
            print("Пропущено пустое текстовое сообщение")

# ======= AIOHTTP APP (для Render) =======
async def health(request):
    # простой healthcheck — Render будет видеть открытый порт
    return web.Response(text="ok")

async def on_startup(app):
    await client.start()
    # запускаем Telethon-петлю в фоне
    app["tg_task"] = asyncio.create_task(client.run_until_disconnected())
    print("Telegram client started")

async def on_cleanup(app):
    await client.disconnect()
    tg_task = app.get("tg_task")
    if tg_task:
        tg_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await tg_task

def make_app():
    app = web.Application()
    app.router.add_get("/", health)
    app.on_startup.append(on_startup)
    app.on_cleanup.append(on_cleanup)
    return app

if __name__ == "__main__":
    port = int(os.getenv("PORT", "10000"))
    web.run_app(make_app(), host="0.0.0.0", port=port)
