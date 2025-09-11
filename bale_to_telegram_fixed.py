import asyncio
import requests
from telegram import Bot
import os
import telegram

# 🔑 توکن‌ها و آی‌دی‌ها
BALE_TOKEN = "647810379:hIODnzAUI6bSZLzTpHdnLozk7CxxRL7Ojg3RtCsa"
BALE_GROUP_ID = 5996820705
TELEGRAM_TOKEN = "8312685029:AAFv34up4dCKBP6C159HTeXcNmK2V4GFAic"
TELEGRAM_GROUP_ID = -4958386258

# بات‌ها
bot = Bot(token=TELEGRAM_TOKEN)
tg_bot = telegram.Bot(token=TELEGRAM_TOKEN)

last_update = 0
last_telegram_update = 0

# ------------------- بله → تلگرام -------------------
async def download_file_bale(file_id, filename=None, suffix="bin"):
    url = f"https://tapi.bale.ai/bot{BALE_TOKEN}/getFile"
    resp = requests.post(url, json={"file_id": file_id}).json()
    if not resp.get("ok"):
        return None
    file_path = resp["result"]["file_path"]
    file_url = f"https://tapi.bale.ai/file/bot{BALE_TOKEN}/{file_path}"
    r = requests.get(file_url)

    if filename:
        save_as = filename
    else:
        save_as = f"temp.{suffix}"

    with open(save_as, "wb") as f:
        f.write(r.content)
    return save_as

def get_sender_name(msg):
    user = msg.get("from", {})
    first = user.get("first_name", "")
    last = user.get("last_name", "")
    name = (first + " " + last).strip()
    if not name:
        name = "ناشناس"
    return f"👤 {name}"

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

async def bale_to_telegram_loop():
    global last_update
    while True:
        try:
            resp = requests.get(
                f"https://tapi.bale.ai/bot{BALE_TOKEN}/getUpdates",
                params={"offset": last_update + 1}
            )
            data = resp.json()

            if "result" in data:
                for update in data["result"]:
                    last_update = update["update_id"]

                    if "message" in update:
                        msg = update["message"]
                        sender = get_sender_name(msg)
                        reply_info = get_reply_info(msg)

                        # متن
                        if "text" in msg:
                            await bot.send_message(
                                chat_id=TELEGRAM_GROUP_ID,
                                text=f"{sender}: {msg['text']}{reply_info}"
                            )

                        # عکس
                        elif "photo" in msg:
                            file_id = msg["photo"][-1]["file_id"]
                            filename = await download_file_bale(file_id, suffix="jpg")
                            if filename:
                                with open(filename, "rb") as f:
                                    await bot.send_photo(
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
                                    await bot.send_video(
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
                                    await bot.send_voice(
                                        chat_id=TELEGRAM_GROUP_ID,
                                        voice=f,
                                        caption=f"{sender}: {msg.get('caption','')}{reply_info}"
                                    )
                                os.remove(filename)

                        # فایل (Document)
                        elif "document" in msg:
                            file_id = msg["document"]["file_id"]
                            file_name = msg["document"].get("file_name", "temp.bin")
                            filename = await download_file_bale(file_id, filename=file_name)
                            if filename:
                                with open(filename, "rb") as f:
                                    await bot.send_document(
                                        chat_id=TELEGRAM_GROUP_ID,
                                        document=f,
                                        caption=f"{sender}: {msg.get('caption','')}{reply_info}"
                                    )
                                os.remove(filename)

            await asyncio.sleep(2)
        except Exception as e:
            print("⚠️ خطا:", e)
            await asyncio.sleep(5)

# ------------------- تلگرام → بله -------------------
async def telegram_to_bale_loop():
    global last_telegram_update
    while True:
        try:
            updates = tg_bot.get_updates(offset=last_telegram_update + 1, timeout=5)
            for upd in updates:
                last_telegram_update = upd.update_id
                if upd.message and upd.message.text:
                    text = upd.message.text
                    sender_name = upd.message.from_user.first_name
                    payload = {
                        "chat_id": BALE_GROUP_ID,
                        "text": f"{sender_name}: {text}"
                    }
                    requests.post(f"https://tapi.bale.ai/bot{BALE_TOKEN}/sendMessage", json=payload)
        except Exception as e:
            print("⚠️ خطای تلگرام → بله:", e)
        await asyncio.sleep(1)

# ------------------- اجرای همزمان -------------------
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(bale_to_telegram_loop())    # بله → تلگرام
    loop.create_task(telegram_to_bale_loop())    # تلگرام → بله
    loop.run_forever()
