import asyncio
import aiohttp
import requests  # برای Telegram به Bale
from telegram import Bot
import os

# 🔑 توکن‌ها و آیدی‌ها
BALE_TOKEN = "1554796457:qtBrsaPQPEBelL8UjZaisy7O1XmXXgfiweyaxBx6"
BALE_GROUP_ID = 5996820705
TELEGRAM_TOKEN = "8312685029:AAFv34up4dCKBP6C159HTeXcNmK2V4GFAic"
TELEGRAM_GROUP_ID = -4958386258

tg_bot = Bot(token=TELEGRAM_TOKEN)
last_bale_update = 0
last_telegram_update = 0

# دریافت فایل از بله
async def download_file_bale(file_id, filename=None, suffix="bin"):
    url = f"https://tapi.bale.ai/bot{BALE_TOKEN}/getFile"
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json={"file_id": file_id}) as resp:
            data = await resp.json()
            if not data.get("ok"):
                print(f"Failed to get file: {data}")
                return None
            file_path = data["result"]["file_path"]
            file_url = f"https://tapi.bale.ai/file/bot{BALE_TOKEN}/{file_path}"
            async with session.get(file_url) as r:
                content = await r.read()
                save_as = filename if filename else f"temp.{suffix}"
                with open(save_as, "wb") as f:
                    f.write(content)
                return save_as

# نام فرستنده بله
def get_sender_name(msg):
    user = msg.get("from", {})
    first = user.get("first_name", "")
    last = user.get("last_name", "")
    name = (first + " " + last).strip()
    if not name:
        name = "ناشناس"
    return f"👤 {name}"

# اطلاعات ریپلای
def get_reply_info(msg):
    if "reply_to_message" not in msg:
        return ""
    replied = msg["reply_to_message"]
    if "text" in replied:
        preview = replied["text"]
    elif "caption" in replied:
        preview = replied["caption"]
    elif "document" in replied:
        preview = f"📎 فایل: {replied['document'].get('file_name','')}"
    elif "photo" in replied:
        preview = "🖼️ عکس"
    else:
        preview = "پیام قبلی"
    if len(preview) > 50:
        preview = preview[:50] + "..."
    sender = get_sender_name(replied)
    return f"\n🔁 ریپلای به {sender}: «{preview}»\n"

# ارسال پیام تلگرام به بله (با requests)
def send_text_to_bale(text):
    url = f"https://tapi.bale.ai/bot{BALE_TOKEN}/sendMessage"
    response = requests.post(url, json={"chat_id": BALE_GROUP_ID, "text": text})
    if response.status_code != 200:
        print(f"Failed to send to Bale: {response.text}")

# لوپ بله به تلگرام
async def bale_to_telegram_loop():
    global last_bale_update
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"https://tapi.bale.ai/bot{BALE_TOKEN}/getUpdates",
                    params={"offset": last_bale_update + 1, "timeout": 30}
                ) as resp:
                    data = await resp.json()
                    print("Bale updates:", data)  # دیباگ
                    if "result" in data:
                        for update in data["result"]:
                            last_bale_update = update["update_id"]
                            if "message" in update:
                                msg = update["message"]
                                if msg["chat"]["id"] != BALE_GROUP_ID:
                                    print(f"Ignoring message from chat {msg['chat']['id']}")
                                    continue
                                sender = get_sender_name(msg)
                                reply_info = get_reply_info(msg)

                                # متن
                                if "text" in msg:
                                    print(f"Sending to Telegram: {msg['text']}")  # دیباگ
                                    await tg_bot.send_message(
                                        chat_id=TELEGRAM_GROUP_ID,
                                        text=f"{sender}: {msg['text']}{reply_info}"
                                    )

                                # عکس
                                elif "photo" in msg:
                                    file_id = msg["photo"][-1]["file_id"]
                                    filename = await download_file_bale(file_id, suffix="jpg")
                                    if filename:
                                        with open(filename, "rb") as f:
                                            await tg_bot.send_photo(
                                                chat_id=TELEGRAM_GROUP_ID,
                                                photo=f,
                                                caption=f"{sender}: {msg.get('caption','')}{reply_info}"
                                            )
                                        os.remove(filename)

                                # ویدئو
                                elif "video" in msg:
                                    file_id = msg["video"]["file_id"]
                                    filename = await download_file_bale(file_id, suffix="mp4")
                                    if filename:
                                        with open(filename, "rb") as f:
                                            await tg_bot.send_video(
                                                chat_id=TELEGRAM_GROUP_ID,
                                                video=f,
                                                caption=f"{sender}: {msg.get('caption','')}{reply_info}"
                                            )
                                        os.remove(filename)

                                # صدا
                                elif "voice" in msg:
                                    file_id = msg["voice"]["file_id"]
                                    filename = await download_file_bale(file_id, suffix="ogg")
                                    if filename:
                                        with open(filename, "rb") as f:
                                            await tg_bot.send_voice(
                                                chat_id=TELEGRAM_GROUP_ID,
                                                voice=f,
                                                caption=f"{sender}: {msg.get('caption','')}{reply_info}"
                                            )
                                        os.remove(filename)

                                # فایل
                                elif "document" in msg:
                                    file_id = msg["document"]["file_id"]
                                    file_name = msg["document"].get("file_name", "temp.bin")
                                    filename = await download_file_bale(file_id, filename=file_name)
                                    if filename:
                                        with open(filename, "rb") as f:
                                            await tg_bot.send_document(
                                                chat_id=TELEGRAM_GROUP_ID,
                                                document=f,
                                                caption=f"{sender}: {msg.get('caption','')}{reply_info}"
                                            )
                                        os.remove(filename)
        except Exception as e:
            print(f"⚠️ خطا در بله → تلگرام: {e}")
        await asyncio.sleep(2)

# لوپ تلگرام به بله
async def telegram_to_bale_loop():
    global last_telegram_update
    while True:
        try:
            updates = await tg_bot.get_updates(offset=last_telegram_update + 1, timeout=30)
            for update in updates:
                last_telegram_update = update.update_id
                if update.message and update.message.text and update.message.chat.id == TELEGRAM_GROUP_ID:
                    text = update.message.text
                    print(f"Sending to Bale: {text}")  # دیباگ
                    send_text_to_bale(text)
        except Exception as e:
            print(f"⚠️ خطا در تلگرام → بله: {e}")
        await asyncio.sleep(1)

# اجرا
async def main():
    await asyncio.gather(
        bale_to_telegram_loop(),
        telegram_to_bale_loop()
    )

if __name__ == "__main__":
    asyncio.run(main())