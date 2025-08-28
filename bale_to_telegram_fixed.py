import asyncio
import requests
from telegram import Bot
from telegram.constants import ParseMode

# 🔑 توکن‌ها
BALE_TOKEN = "647810379:rTEXavb9B4oKsVshr1LOysz2O7s7hu7p9nB7eKPY"
TELEGRAM_TOKEN = "8312685029:AAFv34up4dCKBP6C159HTeXcNmK2V4GFAic"
TELEGRAM_GROUP_ID = -4958386258

bot = Bot(token=TELEGRAM_TOKEN)
last_update = 0

async def download_file_bale(file_id, suffix="bin"):
    url = f"https://tapi.bale.ai/bot{BALE_TOKEN}/getFile"
    resp = requests.post(url, json={"file_id": file_id}).json()
    if not resp.get("ok"):
        return None, None
    file_path = resp["result"]["file_path"]
    file_name = resp["result"].get("file_name", f"temp.{suffix}")
    file_url = f"https://tapi.bale.ai/file/bot{BALE_TOKEN}/{file_path}"
    r = requests.get(file_url)
    with open(file_name, "wb") as f:
        f.write(r.content)
    return file_name, file_name

def get_sender_name(msg):
    user = msg.get("from", {})
    first = user.get("first_name", "")
    last = user.get("last_name", "")
    name = (first + " " + last).strip()
    if not name:
        name = "ناشناس"
    return f"👤 {name}"

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
                            text = msg["text"]
                            await bot.send_message(
                                chat_id=TELEGRAM_GROUP_ID,
                                text=f"{sender}: {text}"
                            )

                        # عکس
                        elif "photo" in msg:
                            file_id = msg["photo"][-1]["file_id"]
                            filename, _ = await download_file_bale(file_id, "jpg")
                            if filename:
                                with open(filename, "rb") as f:
                                    await bot.send_photo(
                                        chat_id=TELEGRAM_GROUP_ID,
                                        photo=f,
                                        caption=f"{sender}: {msg.get('caption','')}"
                                    )
                                import os; os.remove(filename)

                        # ویدئو
                        elif "video" in msg:
                            file_id = msg["video"]["file_id"]
                            filename, _ = await download_file_bale(file_id, "mp4")
                            if filename:
                                with open(filename, "rb") as f:
                                    await bot.send_video(
                                        chat_id=TELEGRAM_GROUP_ID,
                                        video=f,
                                        caption=f"{sender}: {msg.get('caption','')}"
                                    )
                                import os; os.remove(filename)

                        # صدا
                        elif "voice" in msg:
                            file_id = msg["voice"]["file_id"]
                            filename, _ = await download_file_bale(file_id, "ogg")
                            if filename:
                                with open(filename, "rb") as f:
                                    await bot.send_voice(
                                        chat_id=TELEGRAM_GROUP_ID,
                                        voice=f,
                                        caption=f"{sender}: {msg.get('caption','')}"
                                    )
                                import os; os.remove(filename)

                        # فایل (Document)
                        elif "document" in msg:
                            file_id = msg["document"]["file_id"]
                            filename, orig_name = await download_file_bale(file_id, "bin")
                            if filename:
                                with open(filename, "rb") as f:
                                    await bot.send_document(
                                        chat_id=TELEGRAM_GROUP_ID,
                                        document=f,
                                        filename=orig_name,
                                        caption=f"{sender}: {msg.get('caption','')}"
                                    )
                                import os; os.remove(filename)

            await asyncio.sleep(2)
        except Exception as e:
            print("⚠️ خطا:", e)
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main_loop())
