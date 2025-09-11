import asyncio
import requests
from telegram import Bot
import os

# 🔑 توکن‌ها و آیدی‌ها
BALE_TOKEN = "647810379:rTEXavb9B4oKsVshr1LOysz2O7s7hu7p9nB7eKPY"
TELEGRAM_TOKEN = "8312685029:AAFv34up4dCKBP6C159HTeXcNmK2V4GFAic"
TELEGRAM_GROUP_ID = -4958386258  # گروه تلگرام
BALE_GROUP_ID = 5996820705       # گروه بله

bot = Bot(token=TELEGRAM_TOKEN)
last_update = 0

# ================= فایل‌ها از بله دانلود میشن =================
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

# ================= نام فرستنده =================
def get_sender_name(msg):
    user = msg.get("from", {})
    first = user.get("first_name", "")
    last = user.get("last_name", "")
    name = (first + " " + last).strip()
    return f"👤 {name}" if name else "👤 ناشناس"

# ================= ارسال متن به بله =================
def send_text_to_bale(text, reply_to=None):
    url = f"https://tapi.bale.ai/bot{BALE_TOKEN}/sendMessage"
    payload = {"chat_id": BALE_GROUP_ID, "text": text}
    if reply_to:
        payload["reply_to_message_id"] = reply_to
    try:
        resp = requests.post(url, json=payload).json()
        print("➡️ ارسال به بله:", payload)
        print("⬅️ پاسخ بله:", resp)
        return resp
    except Exception as e:
        print("⚠️ خطا ارسال به بله:", e)
        return None

# ================= حلقه اصلی =================
async def main_loop():
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
                        reply_to = msg.get("reply_to_message", {}).get("message_id")

                        # متن
                        if "text" in msg:
                            # بله → تلگرام
                            await bot.send_message(
                                chat_id=TELEGRAM_GROUP_ID,
                                text=f"{sender}: {msg['text']}",
                                reply_to_message_id=reply_to
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
                                        caption=f"{sender}: {msg.get('caption','')}"
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
                                        caption=f"{sender}: {msg.get('caption','')}"
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
                                        caption=f"{sender}: {msg.get('caption','')}"
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
                                        caption=f"{sender}: {msg.get('caption','')}"
                                    )
                                os.remove(filename)

            await asyncio.sleep(2)
        except Exception as e:
            print("⚠️ خطا:", e)
            await asyncio.sleep(5)

# ================= پاسخ به پیام‌های تلگرام و ارسال به بله =================
from telegram.ext import Updater, MessageHandler, Filters, CallbackContext

def telegram_to_bale(update, context: CallbackContext):
    text = update.message.text
    if text:
        send_text_to_bale(text, reply_to=None)

# ================= اجرای برنامه =================
if __name__ == "__main__":
    # بخش تلگرام برای دریافت پیام‌ها
    from telegram.ext import Updater
    updater = Updater(token=TELEGRAM_TOKEN)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, telegram_to_bale))
    updater.start_polling()

    # بخش دریافت پیام از بله
    asyncio.run(main_loop())
