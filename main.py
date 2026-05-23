# -*- coding: utf-8 -*-
import os
import telebot
import zipfile
import tempfile
import shutil
import time
import psutil
from flask import Flask, render_template_string, jsonify
from threading import Thread

# --- Flask Web Server Setup ---
app = Flask('')

DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>X71 HOSTING PANEL</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: #1a1a2e; color: #fff; margin: 0; padding: 20px; text-align: center; }
        .container { max-width: 800px; margin: 50px auto; background: #16213e; padding: 30px; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.3); }
        h1 { color: #00f2fe; margin-bottom: 10px; }
        p { color: #888; font-size: 18px; }
        .status { font-weight: bold; color: #4eed50; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 X71 HOSTING BOT</h1>
        <p>Status: <span class="status">ONLINE 🟢</span></p>
        <p>Your Telegram Bot is running safely in the background.</p>
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(DASHBOARD_TEMPLATE)

def run_flask():
    # Render-এর ডাইনামিক পোর্ট হ্যান্ডেল করার জন্য os.environ.get ব্যবহার করা হয়েছে
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()

# --- আপনার টেলিগ্রাম বটের মূল কোড ---
# [এখানে আপনার বটের টোকেন এবং অন্যান্য লজিকগুলো বসিয়ে দিন]
# example: BOT_TOKEN = "YOUR_TOKEN"
# example: bot = telebot.TeleBot(BOT_TOKEN)

if __name__ == "__main__":
    # প্রথমে Flask ওয়েব সার্ভার ব্যাকগ্রাউন্ডে চালু হবে
    keep_alive()
    print("🌐 Web server started. Running Telegram Bot...")
    
    # আপনার বটের পোলিং মেথড (যেমন: bot.infinity_polling())
    # bot.infinity_polling()
    
