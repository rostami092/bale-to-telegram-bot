import asyncio
import requests
from telegram import Bot, Update
from telegram.ext import Updater, MessageHandler, Filters, CallbackContext
import os

# 🔑 توکن‌ها
BALE_TOKEN = "647810379:rTEXavb9B4oKsVshr1LOysz2O7s7hu7p9nB7eKPY"
TELEGRAM_TOKEN = "8312685029:AAFv34up4dCKBP6C159HTeXcNmK2V4GFAic"
TELEGRAM_GROUP_ID = -4958386258  # آیدی گروه تلگرام
BALE_CHAT_ID = "YOUR_BALE_GROUP_OR_USER_ID"  # جایگزین با آیدی گروه/چت بله

bot = Bot(token=TELEGRAM_TOKEN)
last_update = 0

# ======== ارسال پیام به بله ========
def send_text_to_bale(text, reply_to=None):
    url = f"https://tapi.bale.ai/bot{BALE_TOKEN}/sendMessage"
    payload = {
        "chat_id": BALE_CHAT_ID,
        "text": text
    }
    if reply_to:
        payload["reply_to_message_id"] = reply_to
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print("⚠️ خطا در ارسال به بله:", e)

# ======== دریافت اسم فرستنده بله ========
def get_sender_name(msg):
    user = msg.get("from", {})
    first = user.get("first_name", "")
    last = user.get("last_name", "")
    name = (first + " " + last).strip()
    if not name:
        name = "ناشناس"
    return f"👤 {name}"

# ======== دانلود فایل بله ========
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

# ======== حلقه اصلی دریافت پیام‌های بله ========
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

                        # متن
                        if "text" in msg:
                            await bot.send_message(
                                chat_id=TELEGRAM_GROUP_ID,
                                text=f"{sender}: {msg['text']}"
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

# ======== دریافت پیام‌های تلگرام و ارسال به بله ========
def telegram_to_bale(update: Update, context: CallbackContext):
    text = update.message.text
    if text:
        sender_name = update.message.from_user.first_name or "ناشناس"
        send_text_to_bale(f"👤 {sender_name}: {text}")

# ======== شروع ربات تلگرام ========
def start_telegram_bot():
    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(MessageHandler(Filters.text & (~Filters.command), telegram_to_bale))
    updater.start_polling()
    print("Telegram bot started...")
    return updater

if __name__ == "__main__":
    # اجرای همزمان
    updater = start_telegram_bot()
    asyncio.run(main_loop())
