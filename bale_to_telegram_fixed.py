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

                        # بررسی ریپلای
                        reply_text = ""
                        if "reply_to_message" in msg:
                            replied_msg = msg["reply_to_message"]
                            if "text" in replied_msg:
                                reply_text = f"(در پاسخ به: {replied_msg['text']})\n"
                            elif "document" in replied_msg:
                                reply_text = f"(در پاسخ به فایل: {replied_msg['document'].get('file_name','فایل')})\n"
                            elif "photo" in replied_msg:
                                reply_text = "(در پاسخ به عکس)\n"
                            elif "video" in replied_msg:
                                reply_text = "(در پاسخ به ویدئو)\n"
                            elif "voice" in replied_msg:
                                reply_text = "(در پاسخ به ویس)\n"

                        # متن
                        if "text" in msg:
                            await bot.send_message(
                                chat_id=TELEGRAM_GROUP_ID,
                                text=f"{sender}:\n{reply_text}{msg['text']}"
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
                                        caption=f"{sender}:\n{reply_text}{msg.get('caption','')}"
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
                                        caption=f"{sender}:\n{reply_text}{msg.get('caption','')}"
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
                                        caption=f"{sender}:\n{reply_text}{msg.get('caption','')}"
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
                                        caption=f"{sender}:\n{reply_text}{msg.get('caption','')}"
                                    )
                                os.remove(filename)

            await asyncio.sleep(2)
        except Exception as e:
            print("⚠️ خطا:", e)
            await asyncio.sleep(5)
