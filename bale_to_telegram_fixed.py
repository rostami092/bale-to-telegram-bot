import asyncio
import requests
from telegram import Bot
import os

# 🔑 توکن‌ها و آیدی‌ها
BALE_TOKEN = "647810379:hIODnzAUI6bSZLzTpHdnLozk7CxxRL7Ojg3RtCsa"
BALE_GROUP_ID = 5996820705
TELEGRAM_TOKEN = "8312685029:AAFv34up4dCKBP6C159HTeXcNmK2V4GFAic"
TELEGRAM_GROUP_ID = -4958386258

bot = Bot(token=TELEGRAM_TOKEN)
last_update_bale = 0
last_update_telegram = 0

# --------------- دانلود فایل‌ها از بله ----------------
async def download_file_bale(file_id, filename=None, suffix="bin"):
    url = f"https://tapi.bale.ai/bot{BALE_TOKEN}/getFile"
    resp = requests.post(url, json={"file_id": file_id}).json()
    if not resp.get("ok"):
        return None
    file_path = resp["result"]["file_path"]
    file_url = f"https://tapi.bale.ai/file/bot{BALE_TOKEN}/{file_path}"
    r = requests.get(file_url)
    save_as = filename if filename else f"temp.{suffix}"
    with open(save_as, "wb") as f:
        f.write(r.content)
    return save_as

# --------------- اسم فرستنده ----------------
def get_sender_name(msg):
    user = msg.get("from", {})
    first = user.get("first_name", "")
    last = user.get("last_name", "")
    name = (first + " " + last).strip()
    return f"👤 {name}" if name else "👤 ناشناس"

# --------------- بله → تلگرام ----------------
async def bale_to_telegram_loop():
    global last_update_bale
    while True:
        try:
            resp = requests.get(
                f"https://tapi.bale.ai/bot{BALE_TOKEN}/getUpdates",
                params={"offset": last_update_bale + 1}
            )
            data = resp.json()
            if "result" in data:
                for update in data["result"]:
                    last_update_bale = update["update_id"]
                    if "message" not in update:
                        continue
                    msg = update["message"]
                    sender = get_sender_name(msg)

                    reply_text = ""
                    if "reply_to_message" in msg:
                        reply_msg = msg["reply_to_message"]
                        reply_text = reply_msg.get("text") or reply_msg.get("caption") or ""
                        sender = f"{sender} ↩️ به: {reply_text[:30]}"

                    # متن
                    if "text" in msg:
                        await bot.send_message(chat_id=TELEGRAM_GROUP_ID, text=f"{sender}: {msg['text']}")

                    # عکس
                    elif "photo" in msg:
                        file_id = msg["photo"][-1]["file_id"]
                        filename = await download_file_bale(file_id, suffix="jpg")
                        if filename:
                            with open(filename, "rb") as f:
                                await bot.send_photo(chat_id=TELEGRAM_GROUP_ID, photo=f,
                                                     caption=f"{sender}: {msg.get('caption','')}")
                            os.remove(filename)

                    # ویدئو
                    elif "video" in msg:
                        file_id = msg["video"]["file_id"]
                        filename = await download_file_bale(file_id, suffix="mp4")
                        if filename:
                            with open(filename, "rb") as f:
                                await bot.send_video(chat_id=TELEGRAM_GROUP_ID, video=f,
                                                     caption=f"{sender}: {msg.get('caption','')}")
                            os.remove(filename)

                    # صدا
                    elif "voice" in msg:
                        file_id = msg["voice"]["file_id"]
                        filename = await download_file_bale(file_id, suffix="ogg")
                        if filename:
                            with open(filename, "rb") as f:
                                await bot.send_voice(chat_id=TELEGRAM_GROUP_ID, voice=f,
                                                     caption=f"{sender}: {msg.get('caption','')}")
                            os.remove(filename)

                    # فایل (Document)
                    elif "document" in msg:
                        file_id = msg["document"]["file_id"]
                        file_name = msg["document"].get("file_name", "temp.bin")
                        filename = await download_file_bale(file_id, filename=file_name)
                        if filename:
                            with open(filename, "rb") as f:
                                await bot.send_document(chat_id=TELEGRAM_GROUP_ID, document=f,
                                                        caption=f"{sender}: {msg.get('caption','')}")
                            os.remove(filename)

            await asyncio.sleep(2)
        except Exception as e:
            print("⚠️ خطا در بله → تلگرام:", e)
            await asyncio.sleep(5)

# --------------- تلگرام → بله ----------------
async def telegram_to_bale_loop():
    global last_update_telegram
    while True:
        try:
            updates = bot.get_updates(offset=last_update_telegram + 1)
            for u in updates:
                last_update_telegram = u.update_id
                if not u.message:
                    continue
                text = u.message.text
                if not text:
                    continue
                sender_name = u.message.from_user.first_name or "ناشناس"
                full_text = f"👤 {sender_name}: {text}"
                requests.post(f"https://tapi.bale.ai/bot{BALE_TOKEN}/sendMessage",
                              json={"chat_id": BALE_GROUP_ID, "text": full_text})
            await asyncio.sleep(2)
        except Exception as e:
            print("⚠️ خطا در تلگرام → بله:", e)
            await asyncio.sleep(5)

# --------------- اجرای همزمان ----------------
async def main():
    await asyncio.gather(
        bale_to_telegram_loop(),
        telegram_to_bale_loop()  # متن‌ها از تلگرام → بله
    )

if __name__ == "__main__":
    asyncio.run(main())
