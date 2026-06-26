# -*- coding: utf-8 -*-
import os
import sys
import subprocess
import zipfile
import shutil
import time
import base64
import requests
from flask import Flask, render_template_string, request, redirect, url_for, flash, session

# --- Flask App Setup ---
app = Flask('')
app.secret_key = "x71_secret_key_secure_local"

# --- আপনার ফায়ারবেস কনফিগারেশন ---
FIREBASE_DB_URL = "https://x71-hosting-panel-default-rtdb.firebaseio.com" 

# রানিং প্রসেস ট্র্যাকিং ডিকশনারি
running_processes = {}

# 🛠️ সুরক্ষিত ফাইল এক্সিকিউশন মেকানিজম (যেকোনো স্ক্রিপ্ট আইসোলেটেড রান করবে)
def execute_bot(target_dir, filename, unique_id):
    try:
        stop_bot_process(unique_id)
        
        file_path = os.path.join(target_dir, filename)
        executable_filename = filename
        
        if filename.endswith('.zip'):
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_ref.extractall(target_dir)
            
            if os.path.exists(os.path.join(target_dir, "requirements.txt")):
                # মেইন থ্রেডকে ব্লক না করে রিকোয়ারমেন্টস ইনস্টল করা
                subprocess.Popen([sys.executable, "-m", "pip", "install", "-r", os.path.join(target_dir, "requirements.txt")])
            
            all_files = os.listdir(target_dir)
            for f in ["main.py", "bot.py", "index.js", "app.js"]:
                if f in all_files:
                    executable_filename = f
                    break
            full_run_path = os.path.join(target_dir, executable_filename)
        else:
            full_run_path = file_path

        # stdout ও stderr কে DEVNULL এ পাঠিয়ে প্রসেস সম্পূর্ণ আলাদা করা হলো যেন মেইন অ্যাপ কখনো ক্র্যাশ না করে
        if executable_filename.endswith('.py'):
            proc = subprocess.Popen([sys.executable, full_run_path], cwd=target_dir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            running_processes[unique_id] = {"process": proc, "path": target_dir, "filename": filename}
        elif executable_filename.endswith('.js'):
            proc = subprocess.Popen(["node", full_run_path], cwd=target_dir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            running_processes[unique_id] = {"process": proc, "path": target_dir, "filename": filename}
            
        print(f"🚀 Started Script: {filename}")
    except Exception as e:
        print(f"❌ Error running script {unique_id}: {str(e)}")

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

# 🔄 রেন্ডার অনলাইন বা রিস্টার্ট হওয়া মাত্রই ফায়ারবেস থেকে সিঙ্ক করার মেকানিজম
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
                    filename = info.get("filename")
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

# --- আপনার অরিজিনাল ইন্টারফেস (On/Off একটি ডাইনামিক বাটনে ফিক্সড) ---
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
        .container { max-width: 500px; margin: 40px auto; }
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
        .script-info h4 { font-size: 14px; color: #f1f5f9; word-break: break-all; }
        .script-info p { font-size: 11px; color: #64748b; margin-top: 2px; }
        
        .badge-status { padding: 4px 10px; border-radius: 6px; font-size: 11px; font-weight: bold; text-transform: uppercase; }
        .badge-status.on { background: #16a34a; color: white; }
        .badge-status.off { background: #dc2626; color: white; }

        .control-panel { display: flex; background: #1e293b; padding: 10px; border-top: 1px solid #334155; justify-content: space-around; gap: 8px; }
        .control-btn { flex: 1; padding: 8px; border: none; border-radius: 6px; font-size: 12px; font-weight: bold; cursor: pointer; text-align: center; color: white; text-decoration: none; }
        
        .state-active { background: #ea580c; } /* চালু থাকলে বাটনে লাল/কমলা OFF দেখাবে */
        .state-inactive { background: #16a34a; } /* বন্ধ থাকলে বাটনে সবুজ ON দেখাবে */
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
            <form id="uploadForm" action="/upload" method="POST" enctype="multipart/form-data">
                <div class="form-group">
                    <input type="file" name="bot_file" accept=".py,.js,.zip" required>
                </div>
                <button type="submit" class="btn">Upload & Run</button>
            </form>
        </div>

        <div class="card">
            <h2>Your Active Scripts</h2>
            <div id="localFilesList">⚡ Loading scripts from server...</div>
        </div>
        
        <div style="text-align: center; margin-top: 15px;">
            <a href="/logout" style="color: #64748b; font-size: 13px; text-decoration: none;">Logout</a>
        </div>
        {% endif %}
    </div>

    <script>
        async function loadGlobalScripts() {
            const listContainer = document.getElementById('localFilesList');
            if (!listContainer) return;

            try {
                let response = await fetch("{{ db_url }}/active_bots.json?t=" + new Date().getTime());
                let dbData = await response.json();

                if (!dbData || Object.keys(dbData).length === 0) {
                    listContainer.innerHTML = '<p style="text-align: center; color: #64748b; font-size: 13px; padding: 10px;">No script found.</p>';
                    return;
                }

                listContainer.innerHTML = '';
                
                Object.keys(dbData).forEach(id => {
                    if (!dbData[id] || typeof dbData[id] !== 'object') return;
                    
                    let filename = dbData[id].filename || "Unknown File";
                    let currentStatus = dbData[id].status || "ON";
                    let badgeClass = currentStatus.toLowerCase();
                    
                    let toggleBtnText = (currentStatus === "ON") ? "OFF" : "ON";
                    let toggleBtnClass = (currentStatus === "ON") ? "state-active" : "state-inactive";

                    listContainer.innerHTML += `
                        <div class="script-wrapper" id="wrapper-${id}">
                            <div class="script-item">
                                <div class="script-info">
                                    <h4>${filename}</h4>
                                    <p>ID: ${id}</p>
                                </div>
                                <div>
                                    <span class="badge-status ${badgeClass}" id="badge-${id}">${currentStatus}</span>
                                </div>
                            </div>
                            <div class="control-panel">
                                <button class="control-btn ${toggleBtnClass}" id="toggle-${id}" onclick="toggleStatus('${id}')">${toggleBtnText}</button>
                                <button class="control-btn btn-delete" onclick="triggerDelete('${id}')">DELETE</button>
                            </div>
                        </div>
                    `;
                });
            } catch(e) {
                listContainer.innerHTML = '<p style="text-align: center; color: #ef4444; font-size: 13px;">Sync Error.</p>';
            }
        }

        async function toggleStatus(id) {
            let badge = document.getElementById(`badge-${id}`);
            let btn = document.getElementById(`toggle-${id}`);
            if(!badge || !btn) return;
            
            let currentAction = badge.innerText;
            let nextAction = (currentAction === "ON") ? "OFF" : "ON";
            
            badge.innerText = nextAction;
            badge.className = `badge-status ${nextAction.toLowerCase()}`;
            
            btn.innerText = (nextAction === "ON") ? "OFF" : "ON";
            btn.className = `control-btn ${(nextAction === "ON") ? "state-active" : "state-inactive"}`;
            
            await fetch(`/status/${id}/${nextAction}`);
        }

        async function triggerDelete(id) {
            let elem = document.getElementById(`wrapper-${id}`);
            if(elem) elem.remove();
            window.location.href = `/delete/${id}`;
        }

        document.addEventListener("DOMContentLoaded", loadGlobalScripts);
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(INTERFACE_HTML, db_url=FIREBASE_DB_URL)

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

    # এখানে ভ্যারিয়েবল ১০০% মিলিয়ে 'filename' করা হয়েছে
    db_data = {"filename": filename, "file_data": file_b64_string, "status": "ON"}
    
    try:
        requests.put(f"{FIREBASE_DB_URL}/active_bots/{unique_id}.json", json=db_data, timeout=10)
        execute_bot(target_dir, filename, unique_id)
        flash(f"{filename} Uploaded & Executed Successfully!", "success")
    except Exception as e:
        flash(f"Uploaded but DB Sync Failed: {str(e)}", "error")
        
    return redirect(url_for('home'))

@app.route('/status/<unique_id>/<action>')
def change_bot_status(unique_id, action):
    if not session.get('logged_in'): return "Unauthorized", 401
        
    try:
        res = requests.get(f"{FIREBASE_DB_URL}/active_bots/{unique_id}.json", timeout=10)
        if res.status_code == 200 and res.json():
            db_data = res.json()
            db_data["status"] = action
            requests.put(f"{FIREBASE_DB_URL}/active_bots/{unique_id}.json", json=db_data, timeout=10)
            
            filename = db_data.get("filename")
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
        print(f"Error handling status endpoint: {str(e)}")
            
    return "OK", 200

@app.route('/delete/<unique_id>')
def delete_script(unique_id):
    if not session.get('logged_in'): return redirect(url_for('home'))
        
    try:
        stop_bot_process(unique_id)
        target_dir = os.path.join(os.getcwd(), "hosted_bots", unique_id)
        if os.path.exists(target_dir):
            shutil.rmtree(target_dir)

        requests.delete(f"{FIREBASE_DB_URL}/active_bots/{unique_id}.json", timeout=10)
        flash("Script removed from system permanently.", "success")
    except Exception as e:
        flash(f"Delete action exception: {str(e)}", "error")
        
    return redirect(url_for('home'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
