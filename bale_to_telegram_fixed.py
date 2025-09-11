import asyncio
import requests
from telegram import Bot
import os

# 🔑 توکن‌ها
BALE_TOKEN = "647810379:rTEXavb9B4oKsVshr1LOysz2O7s7hu7p9nB7eKPY"
TELEGRAM_TOKEN = "8312685029:AAFv34up4dCKBP6C159HTeXcNmK2V4GFAic"
TELEGRAM_GROUP_ID = -4958386258  # آیدی گروه تلگرام

bot = Bot(token=TELEGRAM_TOKEN)
last_update_bale = 0
last_update_telegram = 0


# 📥 دانلود فایل از بله
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


# 👤 گرفتن اسم فرستنده
def get_sender_name(msg):
    user = msg.get("from", {})
    first = user.get("first_name", "")
    last = user.get("last_name", "")
    name = (first + " " + last).strip()
    if not name:
        name = "ناشناس"
    return f"👤 {name}"


# آیدی گروه بله
BALE_GROUP_ID = 5996820705

# 📤 فرستادن متن از تلگرام به بله
def send_text_to_bale(text, reply_to=None):
    url = f"https://tapi.bale.ai/bot{BALE_TOKEN}/sendMessage"
    payload = {"chat_id": BALE_GROUP_ID, "text": text}  # 👈 تغییر دادم
    if reply_to:
        payload["reply_to_message_id"] = reply_to
    resp = requests.post(url, json=payload).json()
    print("➡️ ارسال به بله:", resp)  # برای دیباگ
    return resp


# 🔄 حلقه اصلی
async def main_loop():
    global last_update_bale, last_update_telegram
    while True:
        try:
            # --- گرفتن آپدیت از بله ---
            resp_bale = requests.get(
                f"https://tapi.bale.ai/bot{BALE_TOKEN}/getUpdates",
                params={"offset": last_update_bale + 1}
            ).json()

            if "result" in resp_bale:
                for update in resp_bale["result"]:
                    last_update_bale = update["update_id"]

                    if "message" in update:
                        msg = update["message"]
                        sender = get_sender_name(msg)

                        reply_text = ""
                        if "reply_to_message" in msg:
                            replied = msg["reply_to_message"]
                            replied_sender = get_sender_name(replied)
                            if "text" in replied:
                                reply_text = f"\n↪️ در پاسخ به {replied_sender}: «{replied['text']}»"
                            elif "caption" in replied:
                                reply_text = f"\n↪️ در پاسخ به {replied_sender}: «{replied['caption']}»"

                        # متن
                        if "text" in msg:
                            await bot.send_message(
                                chat_id=TELEGRAM_GROUP_ID,
                                text=f"{sender}: {msg['text']}{reply_text}"
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
                                        caption=f"{sender}: {msg.get('caption','')}{reply_text}"
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
                                        caption=f"{sender}: {msg.get('caption','')}{reply_text}"
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
                                        caption=f"{sender}: {msg.get('caption','')}{reply_text}"
                                    )
                                os.remove(filename)

                        # فایل
                        elif "document" in msg:
                            file_id = msg["document"]["file_id"]
                            file_name = msg["document"].get("file_name", "temp.bin")
                            filename = await download_file_bale(file_id, filename=file_name)
                            if filename:
                                with open(filename, "rb") as f:
                                    await bot.send_document(
                                        chat_id=TELEGRAM_GROUP_ID,
                                        document=f,
                                        caption=f"{sender}: {msg.get('caption','')}{reply_text}"
                                    )
                                os.remove(filename)

            # --- گرفتن آپدیت از تلگرام ---
            resp_tg = await bot.get_updates(offset=last_update_telegram + 1, timeout=1)
            for update in resp_tg:
                last_update_telegram = update.update_id

                if update.message and update.message.text:
                    text = update.message.text
                    send_text_to_bale(text)

            await asyncio.sleep(2)

        except Exception as e:
            print("⚠️ خطا:", e)
            await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(main_loop())
