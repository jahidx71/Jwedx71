# -*- coding: utf-8 -*-
import os
import sys
import subprocess

# ✅ প্রয়োজনীয় প্যাকেজ অটো-ইনস্টল (Render-এর জন্য)
def auto_install(package):
    try:
        __import__(package)
    except ModuleNotFoundError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])

for mod in ["telebot", "psutil", "requests", "flask"]:
    auto_install(mod)

import telebot
import zipfile
import shutil
import psutil
from flask import Flask, render_template_string, request, redirect, url_for, flash
from threading import Thread

# --- Flask App Setup ---
app = Flask('')
app.secret_key = "x71_secret_key_for_hosting"

# বোতস এবং ফাইল ট্র্যাকিংয়ের জন্য ডামি বা গ্লোবাল ডিকশনারি (আপনার আসল কোডের সাথে মিলিয়ে নেবেন)
# আপনার মূল কোডের active_users, bot_scripts ইত্যাদি ভেরিয়েবল এখানে কাজ করবে।
if 'bot_scripts' not in globals():
    bot_scripts = {}
if 'user_files' not in globals():
    user_files = {}

# 📱 মোবাইল ফ্রেন্ডলি মেটেরিয়াল ডিজাইন ড্যাশবোর্ড (HTML + CSS)
UPLOAD_HTML = """
<!DOCTYPE html>
<html lang="bn">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>X71 HOSTING PANEL</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: 'Segoe UI', Arial, sans-serif; background: #0f172a; color: #f8fafc; padding: 15px; }
        .container { max-width: 600px; margin: 0 auto; }
        
        /* Header */
        .header { text-align: center; padding: 20px 0; background: linear-gradient(135deg, #1e3a8a, #3b82f6); border-radius: 12px; margin-bottom: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.3); }
        .header h1 { font-size: 24px; color: #fff; }
        .header p { font-size: 14px; color: #93c5fd; margin-top: 5px; }

        /* Stats Card */
        .stats-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 20px; }
        .stat-card { background: #1e293b; padding: 15px; border-radius: 10px; text-align: center; border: 1px solid #334155; }
        .stat-card h3 { font-size: 12px; color: #94a3b8; text-transform: uppercase; }
        .stat-card p { font-size: 20px; font-weight: bold; color: #38bdf8; margin-top: 5px; }

        /* Alert Messages */
        .alert { background: #22c55e; color: white; padding: 12px; border-radius: 8px; margin-bottom: 15px; text-align: center; font-size: 14px; }
        .alert.error { background: #ef4444; }

        /* Upload Form Container */
        .card { background: #1e293b; padding: 20px; border-radius: 12px; border: 1px solid #334155; box-shadow: 0 4px 10px rgba(0,0,0,0.2); margin-bottom: 20px; }
        .card h2 { font-size: 18px; margin-bottom: 15px; color: #f1f5f9; border-left: 4px solid #3b82f6; padding-left: 8px; }
        
        .form-group { margin-bottom: 15px; }
        .form-group label { display: block; font-size: 14px; color: #94a3b8; margin-bottom: 5px; }
        .form-group input[type="text"], .form-group input[type="file"] { width: 100%; padding: 12px; background: #0f172a; border: 1px solid #334155; border-radius: 8px; color: #fff; font-size: 14px; }
        .form-group input[type="file"] { padding: 8px; }
        
        .btn { display: block; width: 100%; padding: 12px; background: #2563eb; color: #fff; border: none; border-radius: 8px; font-size: 16px; font-weight: bold; cursor: pointer; transition: background 0.2s; text-align: center; text-decoration: none; }
        .btn:hover { background: #1d4ed8; }

        /* Running Scripts List */
        .script-item { background: #0f172a; padding: 12px; border-radius: 8px; margin-bottom: 10px; border: 1px solid #334155; display: flex; justify-content: space-between; align-items: center; }
        .script-info h4 { font-size: 14px; color: #f1f5f9; }
        .script-info p { font-size: 12px; color: #64748b; }
        .badge { background: #16a34a; color: white; padding: 4px 8px; border-radius: 12px; font-size: 11px; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 X71 HOSTING WEB PANEL</h1>
            <p>আপনার পাইথন ও জিপ ফাইল মোবাইল থেকেই হোস্ট করুন</p>
        </div>

        <div class="stats-grid">
            <div class="stat-card">
                <h3>রানিং বট স্ক্রিপ্ট</h3>
                <p>{{ total_bots }}</p>
            </div>
            <div class="stat-card">
                <h3>সার্ভার র‍্যাম (RAM)</h3>
                <p>{{ ram_usage }}%</p>
            </div>
        </div>

        {% with messages = get_flashed_messages(with_categories=true) %}
          {% if messages %}
            {% for category, message in messages %}
              <div class="alert {% if category == 'error' %}error{% endif %}">{{ message }}</div>
            {% endfor %}
          {% endif %}
        {% endwith %}

        <div class="card">
            <h2>📁 নতুন ফাইল আপলোড করুন</h2>
            <form action="/upload" method="POST" enctype="multipart/form-data">
                <div class="form-group">
                    <label>ইউজার আইডি (User ID)</label>
                    <input type="text" name="user_id" placeholder="উদাহরণ: 12345678" required>
                </div>
                <div class="form-group">
                    <label>পাইথন (.py) অথবা জিপ (.zip) ফাইল সিলেক্ট করুন</label>
                    <input type="file" name="bot_file" accept=".py,.js,.zip" required>
                </div>
                <button type="submit" class="btn">🚀 আপলোড এবং রান করুন</button>
            </form>
        </div>

        <div class="card">
            <h2>📜 সচল স্ক্রিপ্ট সমূহ (Active Scripts)</h2>
            {% for key, info in bot_scripts.items() %}
            <div class="script-item">
                <div class="script-info">
                    <h4>{{ info.get('file_name', 'Unknown') }}</h4>
                    <p>ইউজার আইডি: {{ info.get('script_owner_id', key) }}</p>
                </div>
                <div>
                    <span class="badge">🟢 Running</span>
                </div>
            </div>
            {% tragedies %}
            {% else %}
            <p style="text-align: center; color: #64748b; font-size: 14px; padding: 10px;">বর্তমানে কোনো ফাইল রান করা নেই।</p>
            {% endfor %}
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    ram_usage = psutil.virtual_memory().percent
    total_bots = len(bot_scripts)
    return render_template_string(UPLOAD_HTML, ram_usage=ram_usage, total_bots=total_bots, bot_scripts=bot_scripts)

@app.route('/upload', methods=['POST'])
def upload_file():
    user_id = request.form.get('user_id')
    file = request.files.get('bot_file')
    
    if not user_id or not file:
        flash("❌ দয়া করে ইউজার আইডি এবং ফাইল উভয়ই প্রদান করুন।", "error")
        return redirect(url_for('home'))
    
    filename = file.filename
    # ফাইল এক্সটেনশন চেক (.py, .zip)
    if not (filename.endswith('.py') or filename.endswith('.zip') or filename.endswith('.js')):
        flash("❌ শুধুমাত্র .py, .js অথবা .zip ফাইল আপলোড করা সম্ভব।", "error")
        return redirect(url_for('home'))
    
    # 📁 এখানে ফাইল সেভ এবং রান করার লজিক (আপনার আসল main.py এর হ্যান্ডলারের মতো)
    # উদাহরণস্বরূপ একটি ডামি সেভ অ্যান্ড রান প্রসেস:
    try:
        # ফাইলটি সেভ করার জন্য একটি টেম্পোরারি বা নির্দিষ্ট ডিরেক্টরি ব্যবহার করুন
        target_dir = os.path.join(os.getcwd(), "hosted_bots", user_id)
        os.makedirs(target_dir, exist_ok=True)
        file_path = os.path.join(target_dir, filename)
        file.save(file_path)
        
        # জিপ ফাইল হলে আনজিপ করার লজিক
        if filename.endswith('.zip'):
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_ref.extractall(target_dir)
        
        # আপনার অরিজিনাল মেইন ফাইলের `start_bot_process` ফাংশনটি এখানে কল হবে।
        # ডামি ট্র্যাকিং ডেটা যোগ করা হচ্ছে ড্যাশবোর্ডে দেখানোর জন্য:
        bot_scripts[user_id] = {
            "file_name": filename,
            "script_owner_id": user_id,
            "status": "running"
        }
        
        flash(f"✅ {filename} সফলভাবে আপলোড হয়েছে এবং রান করা হয়েছে!", "success")
    except Exception as e:
        flash(f"❌ ফাইল রান করতে সমস্যা হয়েছে: {str(e)}", "error")

    return redirect(url_for('home'))

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()

# --- Telegram Bot Activation ---
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE" # আপনার আসল টোকেনটি এখানে বসাবেন

if __name__ == '__main__':
    # ১. ওয়েবসাইট ও ফাইল আপলোডার চালু করা
    print("🌐 Mobile Responsive Web Server starting...")
    keep_alive()
    
    # ২. টেলিগ্রাম বট চালু করা (যদি টোকেন দেওয়া থাকে)
    if BOT_TOKEN != "YOUR_BOT_TOKEN_HERE":
        bot = telebot.TeleBot(BOT_TOKEN)
        print("🤖 Telegram Bot Polling started...")
        # bot.infinity_polling()
    else:
        print("⚠️ Telegram BOT_TOKEN setup করা হয়নি। শুধু ওয়েব প্যানেলটি চালু রয়েছে।")
        # Render-কে চালু রাখার জন্য মেইন থ্রেড হোল্ড করা
        import time
        while True:
            time.sleep(3600)
