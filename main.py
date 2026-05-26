# -*- coding: utf-8 -*-
import os
import sys
import subprocess
import zipfile
import shutil
import time
import requests
from flask import Flask, render_template_string, request, redirect, url_for, flash, session
from threading import Thread

# --- Flask App Setup ---
app = Flask('')
app.secret_key = "x71_secret_key_secure_local"

# --- গিটহাব এবং ফায়ারবেস কনফিগারেশন ---
GITHUB_TOKEN = "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"  
GITHUB_USER = "jahidx71"                                  
GITHUB_REPO = "jhfx71all"                                 
FIREBASE_DB_URL = "https://x71-hosting-panel-default-rtdb.firebaseio.com" 

# রানিং প্রসেস ট্র্যাকিং
running_processes = {}

# 🛠️ গিটহাব মেথডস
def upload_to_github(file_path, github_path):
    with open(file_path, "rb") as f:
        content = f.read()
    url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{github_path}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    res = requests.get(url, headers=headers)
    sha = res.json().get("sha") if res.status_code == 200 else None
    
    import base64
    encoded_content = base64.b64encode(content).decode("utf-8")
    data = {"message": f"Upload {github_path}", "content": encoded_content}
    if sha: data["sha"] = sha
        
    response = requests.put(url, headers=headers, json=data)
    return response.status_code in [200, 201]

def delete_from_github(github_path):
    url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{github_path}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    res = requests.get(url, headers=headers)
    if res.status_code == 200:
        sha = res.json().get("sha")
        data = {"message": f"Delete {github_path}", "sha": sha}
        requests.delete(url, headers=headers, json=data)

def download_from_github(github_path, download_path):
    url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{github_path}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3.raw"}
    res = requests.get(url, headers=headers)
    if res.status_code == 200:
        with open(download_path, "wb") as f:
            f.write(res.content)
        return True
    return False

# 🛠️ প্রসেস রানিং ও টার্মিনেট লজিক
def execute_bot(target_dir, filename, unique_id):
    try:
        # প্রসেস অলরেডি চললে আগে বন্ধ করি
        stop_bot_process(unique_id)
        
        file_path = os.path.join(target_dir, filename)
        if filename.endswith('.zip') and not os.path.exists(os.path.join(target_dir, "requirements.txt")):
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_ref.extractall(target_dir)
            if os.path.exists(os.path.join(target_dir, "requirements.txt")):
                subprocess.Popen([sys.executable, "-m", "pip", "install", "-r", os.path.join(target_dir, "requirements.txt")])
            
            all_files = os.listdir(target_dir)
            for f in ["main.py", "bot.py", "index.js", "app.js"]:
                if f in all_files:
                    filename = f
                    break
            full_run_path = os.path.join(target_dir, filename)
        else:
            full_run_path = file_path

        if filename.endswith('.py'):
            proc = subprocess.Popen([sys.executable, full_run_path], cwd=target_dir)
            running_processes[unique_id] = {"process": proc, "path": target_dir, "filename": filename}
        elif filename.endswith('.js'):
            proc = subprocess.Popen(["node", full_run_path], cwd=target_dir)
            running_processes[unique_id] = {"process": proc, "path": target_dir, "filename": filename}
    except Exception as e:
        print(f"Error executing bot {unique_id}: {str(e)}")

def stop_bot_process(unique_id):
    if unique_id in running_processes:
        try:
            running_processes[unique_id]["process"].terminate()
            running_processes[unique_id]["process"].wait(timeout=2)
        except:
            try:
                running_processes[unique_id]["process"].kill()
            except:
                pass
        del running_processes[unique_id]

# 🔄 রেন্ডার রিসেট অটো-রিস্টার্ট মেকানিজম
def restore_all_scripts():
    print("🔄 Checking Firebase & GitHub to restore active ON scripts...")
    try:
        res = requests.get(f"{FIREBASE_DB_URL}/active_bots.json")
        if res.status_code == 200 and res.json():
            bots = res.json()
            for unique_id, info in bots.items():
                status = info.get("status", "ON")
                if status == "ON":  # শুধুমাত্র যেগুলো ON ছিল সেগুলোই রিস্টার্ট হবে
                    filename = info.get("filename")
                    target_dir = os.path.join(os.getcwd(), "hosted_bots", unique_id)
                    os.makedirs(target_dir, exist_ok=True)
                    file_path = os.path.join(target_dir, filename)
                    
                    github_path = f"bots/{unique_id}/{filename}"
                    if download_from_github(github_path, file_path):
                        execute_bot(target_dir, filename, unique_id)
                        print(f"✅ Restored and Started: {filename}")
    except Exception as e:
        print(f"❌ Restore failed: {str(e)}")

# --- সম্পূর্ণ মডিফাইড মোবাইল ফ্রেন্ডলি ইন্টারফেস ---
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
        
        /* নিউ স্ক্রিপ্ট লিস্ট স্টাইল */
        .script-wrapper { background: #0f172a; border: 1px solid #334155; border-radius: 8px; margin-bottom: 12px; overflow: hidden; }
        .script-item { padding: 14px; display: flex; justify-content: space-between; align-items: center; cursor: pointer; transition: background 0.2s; }
        .script-item:hover { background: #1e293b; }
        .script-info h4 { font-size: 14px; color: #f1f5f9; word-break: break-all; }
        .script-info p { font-size: 11px; color: #64748b; margin-top: 2px; }
        
        .badge-status { padding: 4px 10px; border-radius: 6px; font-size: 11px; font-weight: bold; text-transform: uppercase; }
        .badge-status.on { background: #16a34a; color: white; }
        .badge-status.off { background: #dc2626; color: white; }

        /* ড্রপডাউন কন্ট্রোল প্যানেল */
        .control-panel { display: none; background: #1e293b; padding: 10px; border-top: 1px solid #334155; justify-content: space-around; gap: 8px; }
        .control-btn { flex: 1; padding: 8px; border: none; border-radius: 6px; font-size: 12px; font-weight: bold; cursor: pointer; text-align: center; color: white; text-decoration: none; }
        .btn-on { background: #16a34a; }
        .btn-on:hover { background: #15803d; }
        .btn-off { background: #ea580c; }
        .btn-off:hover { background: #c2410c; }
        .btn-delete { background: #dc2626; }
        .btn-delete:hover { background: #b91c1c; }
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
            <div id="localFilesList"></div>
        </div>
        
        <div style="text-align: center; margin-top: 15px;">
            <a href="/logout" style="color: #64748b; font-size: 13px; text-decoration: none;">Logout</a>
        </div>
        {% endif %}
    </div>

    <script>
        // আপলোড সাকসেস হলে মোবাইলে আইডি সেভ করা
        {% if uploaded_id and uploaded_name %}
            let currentFiles = JSON.parse(localStorage.getItem('x71_files')) || {};
            currentFiles["{{ uploaded_id }}"] = "{{ uploaded_name }}";
            localStorage.setItem('x71_files', JSON.stringify(currentFiles));
            window.location.href = "/";
        {% endif %}

        // ফায়ারবেস থেকে লাইভ রিয়েলটাইম স্ট্যাটাস নিয়ে লিস্ট তৈরি করা
        async function loadMobileSavedFiles() {
            const listContainer = document.getElementById('localFilesList');
            if (!listContainer) return;

            let savedFiles = JSON.parse(localStorage.getItem('x71_files')) || {};
            let keys = Object.keys(savedFiles);

            if (keys.length === 0) {
                listContainer.innerHTML = '<p style="text-align: center; color: #64748b; font-size: 13px; padding: 10px;">No script.</p>';
                return;
            }

            listContainer.innerHTML = '';
            
            // ফায়ারবেস থেকে কারেন্ট স্ট্যাটাস ডিরেক্ট ফেচ করা হচ্ছে
            try {
                let response = await fetch("{{ db_url }}/active_bots.json");
                let dbData = await response.json() || {};

                keys.forEach(id => {
                    let filename = savedFiles[id];
                    let currentStatus = (dbData[id] && dbData[id].status) ? dbData[id].status : "ON";
                    let badgeClass = currentStatus.toLowerCase();

                    listContainer.innerHTML += `
                        <div class="script-wrapper" id="wrapper-${id}">
                            <div class="script-item" onclick="toggleControlPanel('${id}')">
                                <div class="script-info">
                                    <h4>${filename}</h4>
                                    <p>Tap to manage controls</p>
                                </div>
                                <div>
                                    <span class="badge-status ${badgeClass}" id="badge-${id}">${currentStatus}</span>
                                </div>
                            </div>
                            <div class="control-panel" id="panel-${id}">
                                <button class="control-btn btn-on" onclick="changeStatus('${id}', 'ON')">ON</button>
                                <button class="control-btn btn-off" onclick="changeStatus('${id}', 'OFF')">OFF</button>
                                <button class="control-btn btn-delete" onclick="triggerDelete('${id}', '${filename}')">DELETE</button>
                            </div>
                        </div>
                    `;
                });
            } catch(e) {
                listContainer.innerHTML = '<p style="text-align: center; color: #ef4444; font-size: 13px;">Sync Error.</p>';
            }
        }

        // ক্লিক করলে কন্ট্রোল প্যানেল স্লাইড/শো করা
        function toggleControlPanel(id) {
            let panel = document.getElementById(`panel-${id}`);
            if (panel.style.display === "flex") {
                panel.style.display = "none";
            } else {
                panel.style.display = "flex";
            }
        }

        // ON/OFF স্ট্যাটাস চেঞ্জার (কোনো রিলোড ছাড়া লাইভ হবে)
        async function changeStatus(id, action) {
            let badge = document.getElementById(`badge-${id}`);
            badge.innerText = action;
            badge.className = `badge-status ${action.toLowerCase()}`;
            
            // সার্ভারে রিকোয়েস্ট পাঠানো
            await fetch(`/status/${id}/${action}`);
        }

        // ডিরেক্ট ডিলিট লজিক (কোনো ওকে/কনফার্মেশন পপআপ আসবে না)
        function triggerDelete(id, name) {
            // লোকাল স্টোরেজ থেকে সাথে সাথে মুছে ফেলা
            let savedFiles = JSON.parse(localStorage.getItem('x71_files')) || {};
            delete savedFiles[id];
            localStorage.setItem('x71_files', JSON.stringify(savedFiles));

            // পেজ থেকে ডিরেক্ট রিমুভ করা
            document.getElementById(`wrapper-${id}`).remove();

            // সার্ভার সাইড ডিলিট রিকোয়েস্ট পাঠানো
            window.location.href = `/delete/${id}`;
        }

        document.addEventListener("DOMContentLoaded", loadMobileSavedFiles);
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    uploaded_id = session.pop('uploaded_id', None)
    uploaded_name = session.pop('uploaded_name', None)
    return render_template_string(INTERFACE_HTML, uploaded_id=uploaded_id, uploaded_name=uploaded_name, db_url=FIREBASE_DB_URL)

@app.route('/login', methods=['POST'])
def login():
    password = request.form.get('password')
    if password == "@jahidx71":
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
    if not session.get('logged_in'):
        return redirect(url_for('home'))
        
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
    
    github_path = f"bots/{unique_id}/{filename}"
    if not upload_to_github(file_path, github_path):
        flash("GitHub Sync Failed.", "error")
        return redirect(url_for('home'))

    # ডিফল্ট স্ট্যাটাস 'ON' দিয়ে ফায়ারবেসে সেভ করা হচ্ছে
    db_data = {"filename": filename, "github_path": github_path, "status": "ON"}
    requests.put(f"{FIREBASE_DB_URL}/active_bots/{unique_id}.json", json=db_data)
    
    execute_bot(target_dir, filename, unique_id)
    
    session['uploaded_id'] = unique_id
    session['uploaded_name'] = file.filename
    flash(f"{file.filename} API Launched Successfully!", "success")
    return redirect(url_for('home'))

# ⚡ লাইভ অন/অফ রাউট
@app.route('/status/<unique_id>/<action>')
def change_bot_status(unique_id, action):
    if not session.get('logged_in'):
        return "Unauthorized", 401
        
    # ফায়ারবেস আপডেট
    res = requests.get(f"{FIREBASE_DB_URL}/active_bots/{unique_id}.json")
    if res.status_code == 200 and res.json():
        db_data = res.json()
        db_data["status"] = action
        requests.put(f"{FIREBASE_DB_URL}/active_bots/{unique_id}.json", json=db_data)
        
        filename = db_data.get("filename")
        target_dir = os.path.join(os.getcwd(), "hosted_bots", unique_id)
        
        if action == "OFF":
            stop_bot_process(unique_id)
        elif action == "ON":
            # যদি ফাইল লোকালি না থাকে তবে গিটহাব থেকে নামিয়ে নেবে
            file_path = os.path.join(target_dir, filename)
            if not os.path.exists(file_path):
                os.makedirs(target_dir, exist_ok=True)
                download_from_github(db_data.get("github_path"), file_path)
            execute_bot(target_dir, filename, unique_id)
            
    return "OK", 200

@app.route('/delete/<unique_id>')
def delete_script(unique_id):
    if not session.get('logged_in'):
        return redirect(url_for('home'))
        
    filename = None
    if unique_id in running_processes:
        filename = running_processes[unique_id].get("filename")
        stop_bot_process(unique_id)
        
    target_dir = os.path.join(os.getcwd(), "hosted_bots", unique_id)
    if os.path.exists(target_dir):
        shutil.rmtree(target_dir)

    if not filename:
        res = requests.get(f"{FIREBASE_DB_URL}/active_bots/{unique_id}.json")
        if res.status_code == 200 and res.json():
            filename = res.json().get("filename")

    if filename:
        delete_from_github(f"bots/{unique_id}/{filename}")

    requests.delete(f"{FIREBASE_DB_URL}/active_bots/{unique_id}.json")
    flash("Script permanently deleted.", "success")
    return redirect(url_for('home'))

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

if __name__ == '__main__':
    # রিস্টার্ট ব্যাকআপ মেকানিজম রান করানো হচ্ছে
    restore_all_scripts()
    
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()
    
    while True:
        time.sleep(3600)
        
