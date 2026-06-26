# -*- coding: utf-8 -*-
import os
import sys
import subprocess

# --- প্যানেল বুট হওয়ার সময় প্রয়োজনীয় সব প্যাকেজ অটো-ইনস্টল মেকানিজম ---
def install_essential_packages():
    essentials = ["flask", "requests", "pyTelegramBotAPI", "python-telegram-bot", "aiohttp"]
    print("📦 Checking and installing essential packages...")
    for package in essentials:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package, "--quiet"])
        except Exception as e:
            print(f"⚠️ Could not install {package}: {str(e)}")

install_essential_packages()

import zipfile
import shutil
import time
import base64
import threading
import requests
from flask import Flask, render_template_string, request, redirect, url_for, flash, session

app = Flask('')
app.secret_key = "x71_secret_key_secure_local"

# --- আপনার ফায়ারবেস কনফিগারেশন ---
FIREBASE_DB_URL = "https://x71-hosting-panel-default-rtdb.firebaseio.com" 

running_processes = {}

def run_bot_worker(target_dir, filename, unique_id):
    try:
        file_path = os.path.join(target_dir, filename)
        executable_filename = filename
        
        if filename.endswith('.zip'):
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_ref.extractall(target_dir)
            
            if os.path.exists(os.path.join(target_dir, "requirements.txt")):
                subprocess.run([sys.executable, "-m", "pip", "install", "-r", os.path.join(target_dir, "requirements.txt")], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            all_files = os.listdir(target_dir)
            for f in ["main.py", "bot.py", "index.js", "app.js"]:
                if f in all_files:
                    executable_filename = f
                    break
            full_run_path = os.path.join(target_dir, executable_filename)
        else:
            full_run_path = file_path

        if executable_filename.endswith('.py'):
            proc = subprocess.Popen([sys.executable, full_run_path], cwd=target_dir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            running_processes[unique_id] = {"process": proc, "path": target_dir, "filename": filename}
        elif executable_filename.endswith('.js'):
            proc = subprocess.Popen(["node", full_run_path], cwd=target_dir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            running_processes[unique_id] = {"process": proc, "path": target_dir, "filename": filename}
            
        print(f"🚀 Thread Started Process for: {filename}")
    except Exception as e:
        print(f"❌ Worker Exception for {unique_id}: {str(e)}")

def execute_bot(target_dir, filename, unique_id):
    stop_bot_process(unique_id)
    t = threading.Thread(target=run_bot_worker, args=(target_dir, filename, unique_id))
    t.daemon = True
    t.start()

def stop_bot_process(unique_id):
    if unique_id in running_processes:
        try:
            running_processes[unique_id]["process"].terminate()
            running_processes[unique_id]["process"].wait(timeout=1)
        except:
            try:
                running_processes[unique_id]["process"].kill()
            except:
                pass
        running_processes.pop(unique_id, None)

def restore_all_scripts():
    print("🔄 Booting & Restoring Active Scripts from Firebase...")
    try:
        res = requests.get(f"{FIREBASE_DB_URL}/active_bots.json", timeout=10)
        if res.status_code == 200 and res.json():
            bots = res.json()
            for unique_id, info in bots.items():
                if not info or not isinstance(info, dict): continue
                status = info.get("status", "ON")
                if status == "ON":
                    filename = info.get("filename") or info.get("file_name")
                    file_data_b64 = info.get("file_data")
                    
                    if filename and file_data_b64:
                        target_dir = os.path.join(os.getcwd(), "hosted_bots", unique_id)
                        os.makedirs(target_dir, exist_ok=True)
                        file_path = os.path.join(target_dir, filename)
                        
                        with open(file_path, "wb") as f:
                            f.write(base64.b64decode(file_data_b64.encode('utf-8')))
                        
                        execute_bot(target_dir, filename, unique_id)
    except Exception as e:
        print(f"❌ Auto-Restore Exception: {str(e)}")

with app.app_context():
    restore_all_scripts()

# --- সার্ভার-সাইড রেন্ডার করা মোবাইল ফ্রেন্ডলি ইন্টারফেস ---
INTERFACE_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>X71 HOSTING</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: 'Segoe UI', Arial, sans-serif; background: #0f172a; color: #f8fafc; padding: 15px; }
        .container { max-width: 500px; margin: 20px auto; }
        .header { text-align: center; padding: 20px 0; background: linear-gradient(135deg, #1e3a8a, #3b82f6); border-radius: 12px; margin-bottom: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.3); }
        .header h1 { font-size: 24px; color: #fff; font-weight: bold; }
        .header p { font-size: 13px; color: #93c5fd; margin-top: 5px; }
        .alert { background: #ef4444; color: white; padding: 12px; border-radius: 8px; margin-bottom: 15px; text-align: center; font-size: 14px; }
        .alert.success { background: #22c55e; }
        .card { background: #1e293b; padding: 20px; border-radius: 12px; border: 1px solid #334155; box-shadow: 0 4px 10px rgba(0,0,0,0.2); margin-bottom: 20px; }
        .card h2 { font-size: 16px; margin-bottom: 15px; color: #f1f5f9; border-left: 4px solid #3b82f6; padding-left: 8px; text-transform: uppercase; }
        .form-group { margin-bottom: 15px; }
        .form-group input[type="password"], .form-group input[type="file"] { width: 100%; padding: 12px; background: #0f172a; border: 1px solid #334155; border-radius: 8px; color: #fff; font-size: 14px; }
        .btn { display: block; width: 100%; padding: 12px; background: #2563eb; color: #fff; border: none; border-radius: 8px; font-size: 15px; font-weight: bold; cursor: pointer; text-align: center; text-decoration: none; }
        .btn:hover { background: #1d4ed8; }
        
        .script-wrapper { background: #0f172a; border: 1px solid #334155; border-radius: 8px; margin-bottom: 12px; overflow: hidden; }
        .script-item { padding: 14px; display: flex; justify-content: space-between; align-items: center; }
        .script-info h4 { font-size: 14px; color: #f1f5f9; word-break: break-all; padding-right: 10px; }
        .script-info p { font-size: 11px; color: #64748b; margin-top: 2px; }
        
        .badge-status { padding: 4px 10px; border-radius: 6px; font-size: 11px; font-weight: bold; text-transform: uppercase; }
        .badge-status.on { background: #16a34a; color: white; }
        .badge-status.off { background: #dc2626; color: white; }

        .control-panel { display: flex; background: #1e293b; padding: 10px; border-top: 1px solid #334155; justify-content: space-around; gap: 8px; }
        .control-btn { flex: 1; padding: 10px; border: none; border-radius: 6px; font-size: 12px; font-weight: bold; cursor: pointer; text-align: center; color: white; text-decoration: none; }
        
        .state-active { background: #ea580c; }
        .state-inactive { background: #16a34a; }
        .btn-delete { background: #dc2626; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>X71 HOSTING</h1>
            <p>Telegram - @jahidx71</p>
        </div>

        {% with messages = get_flashed_messages(with_categories=true) %}
          {% if messages %}
            {% for category, message in messages %}
              <div class="alert {% if category == 'success' %}success{% endif %}">{{ message }}</div>
            {% endfor %}
          {% endif %}
        {% endwith %}

        {% if not session.get('logged_in') %}
        <div class="card">
            <h2>Authentication Required</h2>
            <form action="/login" method="POST">
                <div class="form-group">
                    <input type="password" name="password" placeholder="Type Password" required>
                </div>
                <button type="submit" class="btn">Login</button>
            </form>
        </div>
        {% else %}

        <div class="card">
            <h2>Upload Script (ZIP, PY, JS)</h2>
            <form action="/upload" method="POST" enctype="multipart/form-data">
                <div class="form-group">
                    <input type="file" name="bot_file" accept=".py,.js,.zip" required>
                </div>
                <button type="submit" class="btn">Upload & Run</button>
            </form>
        </div>

        <div class="card">
            <h2>Your Active Scripts</h2>
            {% if not bots_list %}
                <p style="text-align: center; color: #64748b; font-size: 13px; padding: 10px;">No script found.</p>
            {% else %}
                {% for bot in bots_list %}
                <div class="script-wrapper">
                    <div class="script-item">
                        <div class="script-info">
                            <h4>{{ bot.filename }}</h4>
                            <p>ID: {{ bot.id }}</p>
                        </div>
                        <div>
                            <span class="badge-status {{ bot.status.lower() }}">{{ bot.status }}</span>
                        </div>
                    </div>
                    <div class="control-panel">
                        {% if bot.status == "ON" %}
                            <a href="/status/{{ bot.id }}/OFF" class="control-btn state-active">OFF</a>
                        {% else %}
                            <a href="/status/{{ bot.id }}/ON" class="control-btn state-inactive">ON</a>
                        {% endif %}
                        <a href="/delete/{{ bot.id }}" class="control-btn btn-delete">DELETE</a>
                    </div>
                </div>
                {% endfor %}
            {% endif %}
        </div>
        
        <div style="text-align: center; margin-top: 15px;">
            <a href="/logout" style="color: #64748b; font-size: 13px; text-decoration: none;">Logout</a>
        </div>
        {% endif %}
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    bots_list = []
    try:
        res = requests.get(f"{FIREBASE_DB_URL}/active_bots.json", timeout=10)
        if res.status_code == 200 and res.json():
            db_data = res.json()
            for id_key, val in db_data.items():
                if val and isinstance(val, dict):
                    bots_list.append({
                        "id": id_key,
                        "filename": val.get("filename") or val.get("file_name") or "Unknown File",
                        "status": val.get("status", "ON")
                    })
    except Exception as e:
        print(f"Error fetching for server side render: {str(e)}")
        
    return render_template_string(INTERFACE_HTML, bots_list=bots_list)

@app.route('/login', methods=['POST'])
def login():
    if request.form.get('password') == "@xlxjahidx711":
        session['logged_in'] = True
    else:
        flash("Wrong password 🔑", "error")
    return redirect(url_for('home'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/upload', methods=['POST'])
def upload_file():
    if not session.get('logged_in'): return redirect(url_for('home'))
        
    file = request.files.get('bot_file')
    if not file or file.filename == '':
        flash("Please select a valid file.", "error")
        return redirect(url_for('home'))
    
    filename = file.filename
    unique_id = str(int(time.time()))
    
    target_dir = os.path.join(os.getcwd(), "hosted_bots", unique_id)
    os.makedirs(target_dir, exist_ok=True)
    file_path = os.path.join(target_dir, filename)
    file.save(file_path)
    
    with open(file_path, "rb") as f:
        file_bytes = f.read()
    file_b64_string = base64.b64encode(file_bytes).decode('utf-8')

    db_data = {"filename": filename, "file_data": file_b64_string, "status": "ON"}
    
    try:
        requests.put(f"{FIREBASE_DB_URL}/active_bots/{unique_id}.json", json=db_data, timeout=10)
        execute_bot(target_dir, filename, unique_id)
        flash(f"{filename} Uploaded & Execution Started!", "success")
    except Exception as e:
        flash(f"Uploaded but DB Sync Failed: {str(e)}", "error")
        
    return redirect(url_for('home'))

@app.route('/status/<unique_id>/<action>')
def change_bot_status(unique_id, action):
    if not session.get('logged_in'): return redirect(url_for('home'))
        
    try:
        res = requests.get(f"{FIREBASE_DB_URL}/active_bots/{unique_id}.json", timeout=10)
        if res.status_code == 200 and res.json():
            db_data = res.json()
            db_data["status"] = action
            requests.put(f"{FIREBASE_DB_URL}/active_bots/{unique_id}.json", json=db_data, timeout=10)
            
            filename = db_data.get("filename") or db_data.get("file_name")
            target_dir = os.path.join(os.getcwd(), "hosted_bots", unique_id)
            
            if action == "OFF":
                stop_bot_process(unique_id)
            elif action == "ON":
                file_path = os.path.join(target_dir, filename)
                if not os.path.exists(file_path):
                    os.makedirs(target_dir, exist_ok=True)
                    with open(file_path, "wb") as f:
                        f.write(base64.b64decode(db_data.get("file_data").encode('utf-8')))
                execute_bot(target_dir, filename, unique_id)
    except Exception as e:
        print(f"Error handling status: {str(e)}")
            
    return redirect(url_for('home'))

@app.route('/delete/<unique_id>')
def delete_script(unique_id):
    if not session.get('logged_in'): return redirect(url_for('home'))
        
    try:
        stop_bot_process(unique_id)
        target_dir = os.path.join(os.getcwd(), "hosted_bots", unique_id)
        if os.path.exists(target_dir):
            shutil.rmtree(target_dir)

        requests.delete(f"{FIREBASE_DB_URL}/active_bots/{unique_id}.json", timeout=10)
        flash("Script removed permanently.", "success")
    except Exception as e:
        flash(f"Delete action exception: {str(e)}", "error")
        
    return redirect(url_for('home'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
