from pyrogram import Client, filters
from flask import Flask, send_file, Response, render_template_string
import asyncio
import threading
import os

# ========== CONFIG ==========
API_ID = 26195153
API_HASH = "cffc45876502fd70a6d20141b3bd1c8f"
BOT_TOKEN = "7611511169:AAGHJMNrHeTt5FHkYEAmmBJz8ce_plixDmw"
BASE_URL = "https://mighty-allene-nahidcrk-2718c779.koyeb.app"  # BASE_URL এর শেষে `/` দেবেন না

# ========== INITIALIZE ==========
bot = Client("modern_stream_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
app = Flask(__name__)
download_cache = {}

# ========== FLASK HTML TEMPLATE ==========
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
  <title>📽️ {{ file_name }}</title>
  <style>
    body { font-family: Arial; background: #0f172a; color: white; text-align: center; padding: 50px; }
    video { width: 90%; max-width: 720px; margin-top: 20px; border: 4px solid #1e293b; border-radius: 10px; }
    a.button {
      display: inline-block;
      margin-top: 20px;
      padding: 10px 20px;
      background-color: #3b82f6;
      color: white;
      text-decoration: none;
      border-radius: 8px;
    }
    h1 { font-size: 22px; }
  </style>
</head>
<body>
  <h1>📁 {{ file_name }}</h1>
  <video controls autoplay>
    <source src="{{ stream_url }}" type="video/mp4">
    Your browser does not support the video tag.
  </video>
  <br>
  <a class="button" href="{{ download_url }}">⬇️ Download</a>
</body>
</html>
"""

# ========== TELEGRAM HANDLER ==========
@bot.on_message(filters.document | filters.video)
async def handle_file(client, message):
    file_id = message.document.file_id if message.document else message.video.file_id
    file_name = message.document.file_name if message.document else message.video.file_name

    stream_link = f"{BASE_URL}/watch/{file_id}"
    download_link = f"{BASE_URL}/download/{file_id}"

    reply_text = (
        f"🎬 **{file_name}**\n\n"
        f"▶️ [Watch Now]({stream_link})\n"
        f"⬇️ [Download]({download_link})"
    )

    await message.reply_text(reply_text, disable_web_page_preview=True)

# ========== FLASK ROUTES ==========
@app.route("/")
def home():
    return "✅ File Stream Bot is running!"

def run_bot():
    if not bot.is_connected:
        bot.start()

@app.route("/watch/<file_id>")
def watch_file(file_id):
    run_bot()
    if file_id in download_cache:
        tg_file = download_cache[file_id]
    else:
        tg_file = bot.download_media(file_id)
        download_cache[file_id] = tg_file

    file_name = os.path.basename(tg_file)
    stream_url = f"/stream/{file_id}"
    download_url = f"/download/{file_id}"

    return render_template_string(
        HTML_TEMPLATE,
        file_name=file_name,
        stream_url=stream_url,
        download_url=download_url
    )

@app.route("/stream/<file_id>")
def stream_raw(file_id):
    run_bot()
    tg_file = download_cache.get(file_id) or bot.download_media(file_id)
    download_cache[file_id] = tg_file
    return Response(open(tg_file, "rb"), mimetype="video/mp4")

@app.route("/download/<file_id>")
def download_file(file_id):
    run_bot()
    tg_file = download_cache.get(file_id) or bot.download_media(file_id)
    download_cache[file_id] = tg_file
    return send_file(tg_file, as_attachment=True)

# ========== START SERVER & BOT ==========
def run_flask():
    app.run(host="0.0.0.0", port=5000)

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    asyncio.run(bot.run())
