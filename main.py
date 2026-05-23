# -*- coding: utf-8 -*-
import subprocess
import sys
import os

# ✅ প্রয়োজনীয় প্যাকেজ অটো-ইনস্টল
def auto_install(package):
    try:
        __import__(package)
    except ModuleNotFoundError:
        print(f"📦 Installing missing package: {package} ...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])

for mod in ["telebot", "psutil", "requests", "flask"]:
    auto_install(mod)

import telebot
import zipfile
import tempfile
import shutil
from telebot import types
import time
from datetime import datetime
import psutil
import sqlite3
import threading
import re
from flask import Flask, render_template_string, jsonify
from threading import Thread

# --- Flask Web Server Setup ---
app = Flask('')

# HTML & CSS ড্যাশবোর্ড টেমপ্লেট
DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>X71 HOSTING PANEL</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #1a1a2e; color: #fff; margin: 0; padding: 20px; }
        .container { max-width: 1000px; margin: 0 auto; }
        h1 { color: #00f2fe; border-bottom: 2px solid #00f2fe; padding-bottom: 10px; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1max)); gap: 20px; margin-bottom: 30px; }
        .card { background: #16213e; padding: 20px; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.3); border-left: 5px solid #00f2fe; }
        .card h3 { margin: 0 0 10px 0; color: #e94560; }
        .card p { font-size: 24px; font-weight: bold; margin: 0; }
        .bot-list { background: #16213e; padding: 20px; border-radius: 10px; }
        table { width: 100%; border-collapse: collapse; margin-top: 15px; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #0f3460; }
        th { color: #00f2fe; }
        .status-running { color: #4eed50; font-weight: bold; }
        .status-stopped { color: #ff4757; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 X71 Hosting Bot - Web Management Panel</h1>
        
        <div class="stats-grid">
            <div class="card">
                <h3>Total Active Users</h3>
                <p>{{ total_users }}</p>
            </div>
            <div class="card">
                <h3>Total Hosted Files</h3>
                <p>{{ total_files }}</p>
            </div>
            <div class="card">
                <h3>Running Bots</h3>
                <p>{{ running_bots }}</p>
            </div>
            <div class="card">
                <h3>System RAM Usage</h3>
                <p>{{ ram_usage }}%</p>
            </div>
        </div>

        <div class="bot-list">
            <h2>📜 Active Scripts in Server</h2>
            <table>
                <thead>
                    <tr>
                        <th>User ID</th>
                        <th>Script Name</th>
                        <th>Type</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    {% for key, info in bot_scripts.items() %}
                    <tr>
                        <td>{{ info.script_owner_id }}</td>
                        <td>{{ info.file_name }}</td>
                        <td>{{ info.type | upper }}</td>
                        <td><span class="status-running">🟢 Running (PID: {{ info.process.pid }})</span></td>
                    </tr>
                    {% endfor %}
                    {% if not bot_scripts %}
                    <tr>
                        <td colspan="4" style="text-align: center; color: #888;">বর্তমানে কোনো বট স্ক্রিপ্ট রান করছে না।</td>
                    </tr>
                    {% endif %}
                </tbody>
            </table>
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    # ড্যাশবোর্ডের জন্য ডেটা প্রসেসিং
    total_users = len(active_users)
    total_files = sum(len(files) for files in user_files.values())
    running_bots = len(bot_scripts)
    ram_usage = psutil.virtual_memory().percent
    
    return render_template_string(
        DASHBOARD_TEMPLATE, 
        total_users=total_users, 
        total_files=total_files, 
        running_bots=running_bots,
        ram_usage=ram_usage,
        bot_scripts=bot_scripts
    )

@app.route('/api/stats')
def api_stats():
    # অন্য কোনো অ্যাপ বা সাইট থেকে ডেটা নেওয়ার জন্য API Endpoint
    return jsonify({
        "status": "online",
        "total_users": len(active_users),
        "running_bots": len(bot_scripts),
        "ram_usage": psutil.virtual_memory().percent
    })

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()
    print("🌐 Web Dashboard Server started on port 8080.")

# --- (বাকি কোড আপনার ফাইলের মতোই থাকবে) ---
# [এখানে আপনার দেওয়া বাকি টোকেন, ডেটাবেজ ও টেলিগ্রাম বটের লজিকগুলো বসে যাবে]

# উদাহরণস্বরূপ স্টার্টআপে keep_alive কল করা:
if __name__ == "__main__":
    # ডেটাবেজ লোড করার পর
    keep_alive()
    # এখানে bot.infinity_polling() বা আপনার রানিং মেথড থাকবে

