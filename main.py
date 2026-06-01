# -*- coding: utf-8 -*-
import os
import sys
import subprocess
import zipfile
import shutil
import time
import base64
import requests
import threading
from flask import Flask, render_template_string, request, redirect, url_for, flash, session

# --- Flask App Setup ---
app = Flask('')
app.secret_key = "x71_secret_key_secure_local_ultra_premium"

# --- ১০০% ফ্রি ফায়ারবেস কনফিগারেশন ---
FIREBASE_DB_URL = "https://x71-hosting-panel-default-rtdb.firebaseio.com" 

# রানিং প্রসেস ট্র্যাকিং
running_processes = {}

# 🛠️ ইউনিভার্সাল ফাইল এক্সিকিউশন মেকানিজম (সুরক্ষিত ও ক্র্যাশ-প্রুফ)
def execute_bot(target_dir, filename, unique_id):
    # ভেতরের কোনো বটের ভুলের কারণে যেন মেইন প্যানেল ক্র্যাশ না করে, তাই সম্পূর্ণ আলাদা থ্রেডে রান করানো হচ্ছে
    def run_target():
        try:
            stop_bot_process(unique_id)
            file_path = os.path.join(target_dir, filename)
            
            # জিপ ফাইল এক্সট্রাক্ট এবং ডিপেন্ডেন্সি অটো-ইনস্টল মেথড
            if filename.endswith('.zip'):
                if not os.path.exists(os.path.join(target_dir, "requirements.txt")) and not os.path.exists(os.path.join(target_dir, "package.json")):
                    with zipfile.ZipFile(file_path, 'r') as zip_ref:
                        zip_ref.extractall(target_dir)
                
                if os.path.exists(os.path.join(target_dir, "requirements.txt")):
                    subprocess.run([sys.executable, "-m", "pip", "install", "-r", os.path.join(target_dir, "requirements.txt")])
                
                if os.path.exists(os.path.join(target_dir, "package.json")):
                    subprocess.run(["npm", "install"], cwd=target_dir)
                
                all_files = os.listdir(target_dir)
                for f in ["main.py", "bot.py", "index.js", "app.js", "start.sh", "run.py"]:
                    if f in all_files:
                        filename_env = f
                        break
                full_run_path = os.path.join(target_dir, filename_env)
            else:
                full_run_path = file_path
                filename_env = filename

            # এনভায়রনমেন্টাল এক্সিকিউশন
            if filename_env.endswith('.py'):
                proc = subprocess.Popen([sys.executable, full_run_path], cwd=target_dir)
            elif filename_env.endswith('.js'):
                proc = subprocess.Popen(["node", full_run_path], cwd=target_dir)
            elif filename_env.endswith('.sh') or filename_env.endswith('.bash'):
                proc = subprocess.Popen(["bash", full_run_path], cwd=target_dir)
            else:
                proc = subprocess.Popen([full_run_path], cwd=target_dir, shell=True)
                
            running_processes[unique_id] = {"process": proc, "path": target_dir, "filename": filename_env}
        except Exception as bot_err:
            # কোনো বট স্ক্রিপ্টে মডিউল বা কোড এরর থাকলে তা এখানে আটকে যাবে, মেইন সার্ভার সেভ থাকবে
            print(f"⚠️ [Bot Error] Failed to run script {filename}: {str(bot_err)}")

    # থ্রেড ট্রিগার
    bot_thread = threading.Thread(target=run_target)
    bot_thread.daemon = True
    bot_thread.start()

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

# 🔄 ফায়ারবেস ক্লাউড থেকে সব স্ক্রিপ্ট একসাথে সিঙ্ক করার গলোবাল মেথড
def restore_all_scripts():
    print("⚡ Syncing & Core Booting all premium environments from Firebase...")
    try:
        res = requests.get(f"{FIREBASE_DB_URL}/active_bots.json")
        if res.status_code == 200 and res.json():
            bots = res.json()
            for unique_id, info in bots.items():
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
                        print(f"🚀 Premium Engine Started: {filename}")
    except Exception as e:
        print(f"❌ Restore failed: {str(e)}")

with app.app_context():
    restore_all_scripts()

# --- আল্ট্রা প্রিমিয়াম মডার্ন ড্যাশবোর্ড ইন্টারফেস (Cyberpunk Glassmorphism UI) ---
INTERFACE_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>X71 HOSTING PREMIUM</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; transition: all 0.3s ease; }
        body { font-family: 'Poppins', 'Segoe UI', sans-serif; background: #090d16; color: #e2e8f0; padding: 15px; overflow-x: hidden; }
        
        body::before {
            content: ''; position: fixed; top: -10%; left: -10%; width: 50%; height: 50%;
            background: radial-gradient(circle, rgba(37, 99, 235, 0.15) 0%, transparent 80%); z-index: -1;
        }
        
        .container { max-width: 480px; margin: 30px auto; }
        
        .header { 
            text-align: center; padding: 30px 20px; 
            background: linear-gradient(135deg, #1e1b4b 0%, #0f172a 100%); 
            border-radius: 20px; margin-bottom: 25px; 
            border: 1px solid rgba(59, 130, 246, 0.2);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5), inset 0 2px 4px rgba(255,255,255,0.05);
        }
        .header h1 { font-size: 28px; color: #fff; font-weight: 800; letter-spacing: 1px; text-shadow: 0 0 15px rgba(59,130,246,0.6); }
        .header p { font-size: 13px; color: #38bdf8; margin-top: 6px; font-weight: 500; }
        
        .alert { background: #f43f5e; color: white; padding: 14px; border-radius: 12px; margin-bottom: 20px; text-align: center; font-size: 14px; font-weight: 500; box-shadow: 0 0 15px rgba(244,63,94,0.3); border-left: 5px solid #be123c; }
        .alert.success { background: #10b981; box-shadow: 0 0 15px rgba(16,185,129,0.3); border-left: 5px solid #047857; }
        
        .card { background: rgba(30, 41, 59, 0.7); backdrop-filter: blur(12px); padding: 24px; border-radius: 20px; border: 1px solid rgba(255, 255, 255, 0.08); box-shadow: 0 10px 25px rgba(0,0,0,0.3); margin-bottom: 25px; }
        .card h2 { font-size: 15px; margin-bottom: 20px; color: #94a3b8; letter-spacing: 0.5px; text-transform: uppercase; display: flex; align-items: center; gap: 8px; }
        .card h2 i { color: #3b82f6; text-shadow: 0 0 8px rgba(59,130,246,0.5); }
        
        .form-group { margin-bottom: 18px; position: relative; }
        .form-group input[type="password"] { width: 100%; padding: 14px 14px 14px 42px; background: #0f172a; border: 1px solid #334155; border-radius: 12px; color: #fff; font-size: 14px; }
        .form-group i.lock-icon { position: absolute; left: 15px; top: 16px; color: #64748b; }
        .form-group input[type="password"]:focus { border-color: #3b82f6; box-shadow: 0 0 10px rgba(59,130,246,0.3); outline: none; }
        
        .file-upload-wrapper { position: relative; width: 100%; height: 60px; background: #0f172a; border: 2px dashed #334155; border-radius: 12px; display: flex; justify-content: center; align-items: center; cursor: pointer; }
        .file-upload-wrapper:hover { border-color: #3b82f6; background: rgba(59,130,246,0.05); }
        .file-upload-wrapper input[type="file"] { position: absolute; width: 100%; height: 100%; opacity: 0; cursor: pointer; }
        .file-upload-wrapper span { font-size: 13px; color: #94a3b8; font-weight: 500; display: flex; align-items: center; gap: 8px; }
        
        .btn { display: flex; justify-content: center; align-items: center; gap: 8px; width: 100%; padding: 14px; background: linear-gradient(135deg, #2563eb, #1d4ed8); color: #fff; border: none; border-radius: 12px; font-size: 15px; font-weight: 600; cursor: pointer; text-decoration: none; box-shadow: 0 4px 12px rgba(37,99,235,0.3); }
        .btn:hover { background: linear-gradient(135deg, #1d4ed8, #1e40af); transform: translateY(-2px); box-shadow: 0 6px 20px rgba(37,99,235,0.4); }
        
        .script-wrapper { background: #0f172a; border: 1px solid rgba(255,255,255,0.05); border-radius: 14px; margin-bottom: 14px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.15); }
        .script-wrapper:hover { border-color: rgba(59,130,246,0.3); transform: scale(1.01); }
        .script-item { padding: 16px; display: flex; justify-content: space-between; align-items: center; }
        .script-info { display: flex; align-items: center; gap: 12px; max-width: 65%; }
        .script-icon-box { width: 38px; height: 38px; background: rgba(59,130,246,0.1); border-radius: 10px; display: flex; justify-content: center; align-items: center; color: #38bdf8; font-size: 16px; }
        .script-details h4 { font-size: 14px; color: #f1f5f9; font-weight: 600; word-break: break-all; margin-bottom: 2px; }
        .script-details p { font-size: 11px; color: #64748b; font-weight: 400; }
        
        .actions-area { display: flex; align-items: center; gap: 10px; }
        
        .smart-toggle { position: relative; width: 75px; height: 32px; background: #334155; border-radius: 20px; cursor: pointer; display: flex; align-items: center; justify-content: space-between; padding: 0 8px; box-shadow: inset 0 2px 4px rgba(0,0,0,0.4); }
        .smart-toggle .toggle-knob { position: absolute; left: 3px; width: 26px; height: 26px; background: #fff; border-radius: 50%; box-shadow: 0 2px 5px rgba(0,0,0,0.3); }
        .smart-toggle span { font-size: 10px; font-weight: 800; letter-spacing: 0.5px; }
        .smart-toggle .text-on { color: #4ade80; opacity: 0; }
        .smart-toggle .text-off { color: #94a3b8; margin-left: auto; }
        
        .smart-toggle.active { background: linear-gradient(135deg, #059669, #10b981); box-shadow: 0 0 10px rgba(16,185,129,0.4); }
        .smart-toggle.active .toggle-knob { left: 46px; }
        .smart-toggle.active .text-on { opacity: 1; }
        .smart-toggle.active .text-off { opacity: 0; }
        
        .btn-trash { width: 32px; height: 32px; background: rgba(244,63,94,0.1); border: 1px solid rgba(244,63,94,0.2); border-radius: 8px; display: flex; justify-content: center; align-items: center; color: #f43f5e; cursor: pointer; }
        .btn-trash:hover { background: #f43f5e; color: #fff; box-shadow: 0 0 10px rgba(244,63,94,0.4); }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>X71 HOSTING</h1>
            <p><i class="fab fa-telegram"></i> Cloud Control Panel - @jahidx71</p>
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
            <h2><i class="fas fa-shield-alt"></i> Access Gate</h2>
            <form action="/login" method="POST">
                <div class="form-group">
                    <i class="fas fa-lock lock-icon"></i>
                    <input type="password" name="password" placeholder="Enter System Password" required>
                </div>
                <button type="submit" class="btn">Unlock Engine <i class="fas fa-sign-in-alt"></i></button>
            </form>
        </div>
        {% else %}

        <div class="card">
            <h2><i class="fas fa-cloud-upload-alt"></i> Deploy Universal File</h2>
            <form id="uploadForm" action="/upload" method="POST" enctype="multipart/form-data">
                <div class="form-group">
                    <div class="file-upload-wrapper" id="uploadBox">
                        <input type="file" name="bot_file" id="fileInput" required>
                        <span id="uploadText"><i class="fas fa-file-code"></i> Tap to select any file or ZIP</span>
                    </div>
                </div>
                <button type="submit" class="btn">Deploy & Run Cluster <i class="fas fa-rocket"></i></button>
            </form>
        </div>

        <div class="card">
            <h2><i class="fas fa-server"></i> Multi-Cluster Environments</h2>
            <div id="localFilesList">⚡ Synchronizing secure clusters...</div>
        </div>
        
        <div style="text-align: center; margin-top: 20px;">
            <a href="/logout" style="color: #64748b; font-size: 13px; text-decoration: none; font-weight: 500;"><i class="fas fa-power-off"></i> Secure Terminate</a>
        </div>
        {% endif %}
    </div>

    <script>
        const fileInput = document.getElementById('fileInput');
        if(fileInput) {
            fileInput.addEventListener('change', function() {
                const uploadText = document.getElementById('uploadText');
                if(this.files.length > 0) {
                    uploadText.innerHTML = `<i class="fas fa-check-circle" style="color:#10b981;"></i> ${this.files[0].name}`;
                }
            });
        }

        async function loadGlobalScripts() {
            const listContainer = document.getElementById('localFilesList');
            if (!listContainer) return;

            try {
                let response = await fetch("{{ db_url }}/active_bots.json");
                let dbData = await response.json();

                if (!dbData || Object.keys(dbData).length === 0) {
                    listContainer.innerHTML = '<p style="text-align: center; color: #64748b; font-size: 13px; padding: 15px;"><i class="fas fa-folder-open"></i> No environment active currently.</p>';
                    return;
                }

                listContainer.innerHTML = '';
                
                Object.keys(dbData).forEach(id => {
                    let filename = dbData[id].filename;
                    let currentStatus = dbData[id].status || "ON";
                    let isChecked = currentStatus === "ON" ? "active" : "";
                    
                    let iconClass = "fa-file-code";
                    if(filename.endsWith('.py')) iconClass = "fab fa-python";
                    else if(filename.endsWith('.js')) iconClass = "fab fa-node-js";
                    else if(filename.endsWith('.zip')) iconClass = "fa-file-archive";

                    listContainer.innerHTML += `
                        <div class="script-wrapper" id="wrapper-${id}">
                            <div class="script-item">
                                <div class="script-info">
                                    <div class="script-icon-box">
                                        <i class="fas ${iconClass}"></i>
                                    </div>
                                    <div class="script-details">
                                        <h4>${filename}</h4>
                                        <p>ID: ${id}</p>
                                    </div>
                                </div>
                                <div class="actions-area">
                                    <div class="smart-toggle ${isChecked}" id="toggle-${id}" onclick="handleToggle('${id}')">
                                        <span class="text-on">ON</span>
                                        <div class="toggle-knob"></div>
                                        <span class="text-off">OFF</span>
                                    </div>
                                    <div class="btn-trash" onclick="triggerDelete('${id}')" title="Delete Script">
                                        <i class="fas fa-trash-alt"></i>
                                    </div>
                                </div>
                            </div>
                        </div>
                    `;
                });
            } catch(e) {
                listContainer.innerHTML = '<p style="text-align: center; color: #f43f5e; font-size: 13px;"><i class="fas fa-exclamation-triangle"></i> Engine Sync Interrupted.</p>';
            }
        }

        async function handleToggle(id) {
            let toggleEl = document.getElementById(`toggle-${id}`);
            let targetAction = "";
            
            if(toggleEl.classList.contains('active')) {
                toggleEl.classList.remove('active');
                targetAction = "OFF";
            } else {
                toggleEl.classList.add('active');
                targetAction = "ON";
            }
            
            await fetch(`/status/${id}/${targetAction}`);
        }

        function triggerDelete(id) {
            if(confirm("Are you sure you want to completely erase this cluster environment?")) {
                document.getElementById(`wrapper-${id}`).remove();
                window.location.href = `/delete/${id}`;
            }
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
    if request.form.get('password') == "@Xhunterx71jb":
        session['logged_in'] = True
    else:
        flash("System Access Refused! Wrong Key 🔑", "error")
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
        flash("Invalid target runtime payload.", "error")
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
    requests.put(f"{FIREBASE_DB_URL}/active_bots/{unique_id}.json", json=db_data)
    
    execute_bot(target_dir, filename, unique_id)
    
    flash(f"{file.filename} Deployed into Multi-Cluster successfully!", "success")
    return redirect(url_for('home'))

@app.route('/status/<unique_id>/<action>')
def change_bot_status(unique_id, action):
    if not session.get('logged_in'): return "Unauthorized", 401
        
    res = requests.get(f"{FIREBASE_DB_URL}/active_bots/{unique_id}.json")
    if res.status_code == 200 and res.json():
        db_data = res.json()
        db_data["status"] = action
        requests.put(f"{FIREBASE_DB_URL}/active_bots/{unique_id}.json", json=db_data)
        
        filename = db_data.get("filename")
        target_dir = os.path.join(os.getcwd(), "hosted_bots", unique_id)
        
        if action == "OFF":
            stop_bot_process(unique_id)
        elif acti
