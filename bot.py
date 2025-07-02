from pyrogram import Client, filters
from flask import Flask, send_file, Response, request
import asyncio
import threading
import os

# ========== CONFIG ==========

API_ID = 26195153          # <-- আপনার API ID দিন
API_HASH = "cffc45876502fd70a6d20141b3bd1c8f"
BOT_TOKEN = "7611511169:AAGHJMNrHeTt5FHkYEAmmBJz8ce_plixDmw"
BASE_URL = "https://mighty-allene-nahidcrk-2718c779.koyeb.app/"  # Render এর URL বসান

# ========== PYROGRAM BOT ==========

bot = Client("file_stream_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@bot.on_message(filters.document | filters.video)
async def handle_file(client, message):
    file_id = message.document.file_id if message.document else message.video.file_id
    file_name = message.document.file_name if message.document else message.video.file_name

    stream_link = f"{BASE_URL}/watch/{file_id}"
    download_link = f"{BASE_URL}/download/{file_id}"

    reply_text = f"🎬 **File Name:** `{file_name}`\n\n"
    reply_text += f"▶️ Stream: [Click Here]({stream_link})\n"
    reply_text += f"⬇️ Download: [Click Here]({download_link})"

    await message.reply_text(reply_text, disable_web_page_preview=True)

# ========== FLASK SERVER ==========

app = Flask(__name__)
bot_started = False

def run_bot():
    global bot_started
    if not bot_started:
        bot.start()
        bot_started = True

@app.route("/")
def home():
    return "✅ Telegram File Stream Bot is Running."

@app.route("/watch/<file_id>")
def stream_file(file_id):
    run_bot()
    tg_file = bot.download_media(file_id)
    return Response(open(tg_file, "rb"), mimetype="video/mp4")

@app.route("/download/<file_id>")
def download_file(file_id):
    run_bot()
    tg_file = bot.download_media(file_id)
    return send_file(tg_file, as_attachment=True)

# ========== RUN FLASK + BOT TOGETHER ==========

def run_flask():
    app.run(host="0.0.0.0", port=5000)

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    asyncio.run(bot.run())
