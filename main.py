from telethon import TelegramClient
import pandas as pd

api_id = 25777914
api_hash = "91604debf83d64ab062607ab580f2ce7"

client = TelegramClient("my", api_id, api_hash)

SOURCE_CHANNEL = "aerogrill_recepti"
TARGET_CHANNEL = "CookingWithGrill"

def del_bad_from_str(msg: str) -> str:
    """
    Удаляет содержимое в скобках [ ] и ( ), 
    а также заменяет некоторые спецсимволы.
    """
    replacements = {
        "⏰": "🕐",
        "📖": "✨",
        "🌡️": "🔥",
    }
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
        await client.send_file(
            TARGET_CHANNEL,
            msg.media,
            caption=clean_text
        )
    else:
        if clean_text.strip():
            await client.send_message(TARGET_CHANNEL, clean_text)
        else:
            print("Пропущено пустое текстовое сообщение")

client.start()
client.run_until_disconnected()
