# -*- coding: utf-8 -*-
import os
import sys
import subprocess
import zipfile
import shutil
import psutil
from flask import Flask, render_template_string, request, redirect, url_for, flash, session
from threading import Thread

# --- Flask App Setup ---
app = Flask('')
app.secret_key = "x71_secret_key_secure_local"

# রানিং প্রসেস ট্র্যাকিং (রানিং সেশনের জন্য)
running_processes = {}

# 📱 সম্পূর্ণ মোবাইল ফ্রেন্ডলি ইন্টারফেস (LocalStorage ট্র্যাকিং সহ)
INTERFACE_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>X71 HOSTING PANEL</title>
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
        .script-item { background: #0f172a; padding: 12px; border-radius: 8px; border: 1px solid #334155; display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; cursor: pointer; transition: all 0.2s; }
        .script-item:hover { border-color: #ef4444; background: #1e1b2e; }
        .script-info h4 { font-size: 14px; color: #f1f5f9; }
        .script-info p { font-size: 11px; color: #64748b; margin-top: 2px; }
        .badge-status { background: #16a34a; color: white; padding: 4px 8px; border-radius: 6px; font-size: 11px; font-weight: bold; }
        .script-item:hover .badge-status { background: #ef4444; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>X71 HOSTING PANEL</h1>
            <p>Mobile Device Storage Sync Enabled</p>
        </div>

        {% with messages = get_flashed_messages(with_categories=true) %}
          {% if messages %}
            {% for category, message in messages %}
              <div class="alert {% if category == 'success' %}success{% endif %}">{{ message }}</div>
            {% endfor %}
          {% endif %}
        {% endwith %}

        {% if not session.get('logged_in') %}
        <!-- LOGIN CARD -->
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

        <!-- UPLOAD CARD -->
        <div class="card">
            <h2>Upload Script (ZIP, PY, JS)</h2>
            <form id="uploadForm" action="/upload" method="POST" enctype="multipart/form-data">
                <div class="form-group">
                    <input type="file" name="bot_file" accept=".py,.js,.zip" required>
                </div>
                <button type="submit" class="btn">Upload & Run</button>
            </form>
        </div>

        <!-- ACTIVE SCRIPTS CARD (SAVED IN YOUR MOBILE STORAGE) -->
        <div class="card">
            <h2>Your Active Scripts (Click to Delete)</h2>
            <div id="localFilesList">
                <!-- আপনার মোবাইলে সেভ থাকা ফাইলগুলো এখানে জাভাস্ক্রিপ্ট দিয়ে শো হবে -->
            </div>
        </div>
        
        <div style="text-align: center; margin-top: 15px;">
            <a href="/logout" style="color: #64748b; font-size: 13px; text-decoration: none;">Logout Panel</a>
        </div>
        {% endif %}
    </div>

    <!-- 🌐 LOCAL STORAGE STORAGE CONTROLLER -->
    <script>
        // ১. সার্ভার থেকে নতুন আপলোড করা ফাইলের রেসপন্স পেলে তা মোবাইলে সেভ করা
        {% if uploaded_id and uploaded_name %}
            let currentFiles = JSON.parse(localStorage.getItem('x71_files')) || {};
            currentFiles["{{ uploaded_id }}"] = "{{ uploaded_name }}";
            localStorage.setItem('x71_files', JSON.stringify(currentFiles));
            window.location.href = "/"; // পেজ ক্লিন করা
        {% endif %}

        // ২. মোবাইল স্টোরেজ থেকে ফাইলগুলোর লিস্ট ব্রাউজারে রেন্ডার করা
        function loadMobileSavedFiles() {
            const listContainer = document.getElementById('localFilesList');
            if (!listContainer) return;

            let savedFiles = JSON.parse(localStorage.getItem('x71_files')) || {};
            let keys = Object.keys(savedFiles);

            if (keys.length === 0) {
                listContainer.innerHTML = '<p style="text-align: center; color: #64748b; font-size: 13px; padding: 10px;">No scripts saved on this device.</p>';
                return;
            }

            listContainer.innerHTML = '';
            keys.forEach(id => {
                let filename = savedFiles[id];
                listContainer.innerHTML += `
                    <div class="script-item" onclick="deleteLocalFile('${id}', '${filename}')">
                        <div class="script-info">
                            <h4>${filename}</h4>
                            <p>Stored on this phone</p>
                        </div>
                        <div>
                            <span class="badge-status" id="badge-${id}">Active</span>
                        </div>
                    </div>
                `;
            });
        }

        // ৩. ফাইলের ওপর ক্লিক করলে মোবাইল মেমোরি ও সার্ভার থেকে একসাথে ডিলিট করার লজিক
        function deleteLocalFile(id, name) {
            if (confirm(`Do you want to delete and terminate ${name}?`)) {
                // মোবাইল লোকাল স্টোরেজ থেকে ডিলিট
                let savedFiles = JSON.parse(localStorage.getItem('x71_files')) || {};
                delete savedFiles[id];
                localStorage.setItem('x71_files', JSON.stringify(savedFiles));

                // সার্ভারকে ডিলিট করার রিকোয়েস্ট পাঠানো
                window.location.href = `/delete/${id}`;
            }
        }

        // পেজ লোড হওয়া মাত্রই মোবাইলের ফাইল লিস্ট লোড হবে
        document.addEventListener("DOMContentLoaded", loadMobileSavedFiles);
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    # সেশন ক্লিয়ারিং বা নরমাল ভিউ লোড
    uploaded_id = session.pop('uploaded_id', None)
    uploaded_name = session.pop('uploaded_name', None)
    return render_template_string(INTERFACE_HTML, uploaded_id=uploaded_id, uploaded_name=uploaded_name)

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
    import time
    unique_id = str(int(time.time())) # ফাইলের একটি ইউনিক আইডি
    
    target_dir = os.path.join(os.getcwd(), "hosted_bots", unique_id)
    os.makedirs(target_dir, exist_ok=True)
    file_path = os.path.join(target_dir, filename)
    file.save(file_path)
    
    # জিপ ফাইল হ্যান্ডলিং ও ব্যাকগ্রাউন্ড রান প্রসেস
    try:
        if filename.endswith('.zip'):
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_ref.extractall(target_dir)
            
            # requirements.txt বা package.json থাকলে অটো রান হবে
            if os.path.exists(os.path.join(target_dir, "requirements.txt")):
                subprocess.Popen([sys.executable, "-m", "pip", "install", "-r", os.path.join(target_dir, "requirements.txt")])
            
            # মেইন ফাইল খোঁজা
            all_files = os.listdir(target_dir)
            for f in ["main.py", "bot.py", "index.js", "app.js"]:
                if f in all_files:
                    filename = f
                    break

        full_run_path = os.path.join(target_dir, filename)
        
        # প্রসেস স্টার্ট
        if filename.endswith('.py'):
            proc = subprocess.Popen([sys.executable, full_run_path], cwd=target_dir)
            running_processes[unique_id] = {"process": proc, "path": target_dir}
        elif filename.endswith('.js'):
            proc = subprocess.Popen(["node", full_run_path], cwd=target_dir)
            running_processes[unique_id] = {"process": proc, "path": target_dir}

        # মোবাইলের লোকাল স্টোরেজে পুশ করার জন্য সেশনে ডাটা পাঠানো হচ্ছে
        session['uploaded_id'] = unique_id
        session['uploaded_name'] = file.filename
        flash(f"{file.filename} uploaded and running!", "success")
        
    except Exception as e:
        flash(f"Upload success but execution failed: {str(e)}", "error")
        
    return redirect(url_for('home'))

@app.route('/delete/<unique_id>')
def delete_script(unique_id):
    if not session.get('logged_in'):
        return redirect(url_for('home'))
        
    # সার্ভার যদি সচল থাকে তবে রানিং প্রসেস কিল করো
    if unique_id in running_processes:
        try:
            running_processes[unique_id]["process"].terminate()
        except:
            pass
        target_dir = running_processes[unique_id]["path"]
        if os.path.exists(target_dir):
            shutil.rmtree(target_dir)
        del running_processes[unique_id]
    else:
        # রেন্ডার রিস্টার্টের পর ফাইল ফোল্ডার ডিলিট করতে চাইলে
        target_dir = os.path.join(os.getcwd(), "hosted_bots", unique_id)
        if os.path.exists(target_dir):
            shutil.rmtree(target_dir)

    flash("Script removed successfully.", "success")
    return redirect(url_for('home'))

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

if __name__ == '__main__':
    print("🌐 Launching LocalStorage Synchronized Hosting Panel...")
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()
    
    import time
    while True:
        time.sleep(3600)
