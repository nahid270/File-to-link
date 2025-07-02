import os
import asyncio
import threading
import psutil
import aiohttp
import cloudscraper
from pyrogram import Client, filters
from flask import Flask, send_file, Response, render_template_string, jsonify
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from jinja2 import Template

# ========= LOAD ENVIRONMENT =========
load_dotenv()

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")
BASE_URL = os.getenv("BASE_URL", "http://localhost:5000")

# ========= SETUP =========
bot = Client("file_link_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
app = Flask(__name__)
db = AsyncIOMotorClient(MONGO_URI).bot_db
scraper = cloudscraper.create_scraper()

download_cache = {}

# ========= HTML TEMPLATE =========
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
  <title>{{ file_name }}</title>
  <style>
    body { font-family: sans-serif; background: #1e293b; color: white; padding: 40px; text-align: center; }
    video { width: 90%; max-width: 720px; border-radius: 12px; margin-top: 20px; }
    .btn { display: inline-block; padding: 12px 25px; margin-top: 20px; background: #3b82f6; color: white; border-radius: 6px; text-decoration: none; }
  </style>
</head>
<body>
  <h2>🎬 {{ file_name }}</h2>
  <video controls autoplay>
    <source src="{{ stream_url }}" type="video/mp4">
    Your browser does not support the video tag.
  </video>
  <br>
  <a class="btn" href="{{ download_url }}">⬇️ Download</a>
</body>
</html>
"""

# ========= TELEGRAM HANDLER =========
@bot.on_message(filters.document | filters.video)
async def handle_file(client, message):
    media = message.document or message.video
    file_id = media.file_id
    file_name = media.file_name or "Untitled.mp4"
    user_id = message.from_user.id

    await db.files.insert_one({"user_id": user_id, "file_id": file_id, "file_name": file_name})

    stream_link = f"{BASE_URL}/watch/{file_id}"
    download_link = f"{BASE_URL}/download/{file_id}"

    reply = f"🎬 **{file_name}**\n\n▶️ [Stream]({stream_link}) | ⬇️ [Download]({download_link})"
    await message.reply_text(reply, disable_web_page_preview=True)

# ========= FLASK ROUTES =========
@app.route("/")
def index():
    return "✅ File to Link Bot is Running!"

@app.route("/watch/<file_id>")
def watch(file_id):
    tg_file = get_file(file_id)
    if not tg_file: return "File not found"
    file_name = os.path.basename(tg_file)
    return render_template_string(HTML_TEMPLATE,
        file_name=file_name,
        stream_url=f"/stream/{file_id}",
        download_url=f"/download/{file_id}"
    )

@app.route("/stream/<file_id>")
def stream(file_id):
    tg_file = get_file(file_id)
    return Response(open(tg_file, "rb"), mimetype="video/mp4")

@app.route("/download/<file_id>")
def download(file_id):
    tg_file = get_file(file_id)
    return send_file(tg_file, as_attachment=True)

@app.route("/status")
def status():
    return jsonify({
        "cpu_percent": psutil.cpu_percent(),
        "ram_used_mb": round(psutil.virtual_memory().used / (1024 * 1024), 2),
        "uptime": f"{psutil.boot_time()} (epoch)"
    })

# ========= HELPER =========
def get_file(file_id):
    if file_id in download_cache:
        return download_cache[file_id]
    tg_file = bot.download_media(file_id)
    download_cache[file_id] = tg_file
    return tg_file

def run_flask():
    app.run(host="0.0.0.0", port=5000)

# ========= MAIN =========
if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    asyncio.run(bot.run())
