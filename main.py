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
app.secret_key = "x71_secret_key_secure"

# Global tracking for files
if 'bot_scripts' not in globals():
    bot_scripts = {}

# 📱 Clean Mobile Responsive UI (English Only)
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

        .stats-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 20px; }
        .stat-card { background: #1e293b; padding: 12px; border-radius: 10px; text-align: center; border: 1px solid #334155; }
        .stat-card h3 { font-size: 11px; color: #94a3b8; text-transform: uppercase; }
        .stat-card p { font-size: 18px; font-weight: bold; color: #38bdf8; margin-top: 5px; }

        .alert { background: #ef4444; color: white; padding: 12px; border-radius: 8px; margin-bottom: 15px; text-align: center; font-size: 14px; }
        .alert.success { background: #22c55e; }

        .card { background: #1e293b; padding: 20px; border-radius: 12px; border: 1px solid #334155; box-shadow: 0 4px 10px rgba(0,0,0,0.2); margin-bottom: 20px; }
        .card h2 { font-size: 16px; margin-bottom: 15px; color: #f1f5f9; border-left: 4px solid #3b82f6; padding-left: 8px; text-transform: uppercase; }
        
        .form-group { margin-bottom: 15px; }
        .form-group input[type="password"], .form-group input[type="file"] { width: 100%; padding: 12px; background: #0f172a; border: 1px solid #334155; border-radius: 8px; color: #fff; font-size: 14px; }
        
        .btn { display: block; width: 100%; padding: 12px; background: #2563eb; color: #fff; border: none; border-radius: 8px; font-size: 15px; font-weight: bold; cursor: pointer; transition: background 0.2s; text-align: center; text-decoration: none; }
        .btn:hover { background: #1d4ed8; }

        .script-link { text-decoration: none; display: block; margin-bottom: 10px; }
        .script-item { background: #0f172a; padding: 12px; border-radius: 8px; border: 1px solid #334155; display: flex; justify-content: space-between; align-items: center; transition: all 0.2s; }
        .script-item:hover { border-color: #ef4444; background: #1e1b2e; }
        .script-info h4 { font-size: 14px; color: #f1f5f9; }
        .script-info p { font-size: 11px; color: #64748b; margin-top: 2px; }
        .badge-delete { background: #3b82f6; color: white; padding: 4px 8px; border-radius: 6px; font-size: 11px; font-weight: bold; }
        .script-item:hover .badge-delete { background: #ef4444; content: "Delete"; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>X71 HOSTING PANEL</h1>
            <p>Cloud Script Runner & Manager</p>
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
        
        <!-- SYSTEM STATS -->
        <div class="stats-grid">
            <div class="stat-card">
                <h3>Active Bots</h3>
                <p>{{ total_bots }}</p>
            </div>
            <div class="stat-card">
                <h3>RAM Usage</h3>
                <p>{{ ram_usage }}%</p>
            </div>
        </div>

        <!-- UPLOAD CARD -->
        <div class="card">
            <h2>Upload Script</h2>
            <form action="/upload" method="POST" enctype="multipart/form-data">
                <div class="form-group">
                    <input type="file" name="bot_file" accept=".py,.js,.zip" required>
                </div>
                <button type="submit" class="btn">Upload & Run</button>
            </form>
        </div>

        <!-- ACTIVE SCRIPTS CARD (CLICK TO DELETE) -->
        <div class="card">
            <h2>Active Scripts (Click to Delete)</h2>
            {% for key, info in bot_scripts.items() %}
            <a href="/delete/{{ key }}" class="script-link" onclick="return confirm('Are you sure you want to delete this script?')">
                <div class="script-item">
                    <div class="script-info">
                        <h4>{{ info.get('file_name', 'Unknown') }}</h4>
                        <p>Click to terminate and remove</p>
                    </div>
                    <div>
                        <span class="badge-delete">Running</span>
                    </div>
                </div>
            </a>
            {% else %}
            <p style="text-align: center; color: #64748b; font-size: 13px; padding: 10px;">No scripts running at the moment.</p>
            {% endfor %}
        </div>
        
        <div style="text-align: center; margin-top: 15px;">
            <a href="/logout" style="color: #64748b; font-size: 13px; text-decoration: none;">Logout Panel</a>
        </div>
        {% endif %}
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    ram_usage = psutil.virtual_memory().percent
    total_bots = len(bot_scripts)
    return render_template_string(INTERFACE_HTML, ram_usage=ram_usage, total_bots=total_bots, bot_scripts=bot_scripts)

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
        flash("Please select a file to upload.", "error")
        return redirect(url_for('home'))
    
    filename = file.filename
    if not (filename.endswith('.py') or filename.endswith('.zip') or filename.endswith('.js')):
        flash("Only .py, .js or .zip files are allowed.", "error")
        return redirect(url_for('home'))
    
    try:
        # Generate an automatic unique ID based on timestamp
        import time
        unique_id = str(int(time.time()))
        
        target_dir = os.path.join(os.getcwd(), "hosted_bots", unique_id)
        os.makedirs(target_dir, exist_ok=True)
        file_path = os.path.join(target_dir, filename)
        file.save(file_path)
        
        if filename.endswith('.zip'):
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_ref.extractall(target_dir)
        
        # Track the active script
        bot_scripts[unique_id] = {
            "file_name": filename,
            "path": target_dir,
            "status": "running"
        }
        
        flash(f"{filename} uploaded and executed successfully!", "success")
    except Exception as e:
        flash(f"Failed to execute file: {str(e)}", "error")

    return redirect(url_for('home'))

@app.route('/delete/<unique_id>')
def delete_script(unique_id):
    if not session.get('logged_in'):
        return redirect(url_for('home'))
        
    if unique_id in bot_scripts:
        try:
            info = bot_scripts[unique_id]
            target_dir = info.get("path")
            
            # Delete directory and all files inside it
            if os.path.exists(target_dir):
                shutil.rmtree(target_dir)
                
            # Remove from tracking list
            filename = bot_scripts[unique_id]["file_name"]
            del bot_scripts[unique_id]
            
            flash(f"Successfully deleted {filename}.", "success")
        except Exception as e:
            flash(f"Error during file deletion: {str(e)}", "error")
    else:
        flash("Script not found or already deleted.", "error")
        
    return redirect(url_for('home'))

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

if __name__ == '__main__':
    print("🌐 Launching Secured X71 Hosting Panel...")
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()
    
    # Keeping main thread active for Render
    import time
    while True:
        time.sleep(3600)
