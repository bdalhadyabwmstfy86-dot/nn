# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════╗
║  🔥 𝗢𝗠𝗔𝗥 𝗨𝗡𝗟𝗜𝗠𝗜𝗧𝗘𝗗 𝗩𝗣𝗦 - VPS Control Panel (Lunes Host Style)                ║
║  # 𝚅𝙿𝚂 𝙾𝙼𝙰𝚁                                                       ║
╠══════════════════════════════════════════════════════════════════════════╣
║  - لوحة تحكم ويب (Flask) لإدارة VPS كاملة                                 ║
║  - تصميم مطابق لـ Lunes Host LLC (Pterodactyl style)                      ║
║  - متوافق مع Replit (يدعم بورتات متعددة)                                  ║
║  - تشغيل: python vps_panel.py                                             ║
╚══════════════════════════════════════════════════════════════════════════╝
"""

import os
import sys
import gc
import re
import ast
import json
import time
import uuid
import html
import shutil
import socket
import signal
import string
import random
import secrets
import hashlib
import logging
import platform
import zipfile
import tarfile
import threading
import subprocess
import warnings
import urllib.request
import urllib.parse
from datetime import datetime, timedelta
from functools import wraps
from collections import deque

try:
    import resource
except ImportError:
    resource = None

try:
    import psutil
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "psutil"])
    import psutil

try:
    import requests
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
    import requests

from flask import Flask, render_template_string, request, jsonify, session, redirect, url_for, send_file, send_from_directory, render_template
from werkzeug.utils import secure_filename

warnings.filterwarnings('ignore')

# =============================================================================
# 1)  وضع المصادر اللا‌محدود
# =============================================================================
def set_unlimited_resources():
    if not resource:
        return False
    try:
        resource.setrlimit(resource.RLIMIT_AS,    (resource.RLIM_INFINITY, resource.RLIM_INFINITY))
        resource.setrlimit(resource.RLIMIT_DATA,  (resource.RLIM_INFINITY, resource.RLIM_INFINITY))
        resource.setrlimit(resource.RLIMIT_STACK, (resource.RLIM_INFINITY, resource.RLIM_INFINITY))
        resource.setrlimit(resource.RLIMIT_NOFILE,(999999, 999999))
        resource.setrlimit(resource.RLIMIT_NPROC, (resource.RLIM_INFINITY, resource.RLIM_INFINITY))
        print("[🔥 UNLIMITED] Resource limits removed")
        return True
    except Exception as e:
        print(f"[⚠️ UNLIMITED] partial: {e}")
        return False

UNLIMITED_ACTIVE = set_unlimited_resources()

def unlimited_memory_monitor():
    while True:
        time.sleep(30)
        try:
            gc.collect()
            try:
                with open('/proc/sys/vm/drop_caches', 'w') as f:
                    f.write('3')
            except Exception:
                pass
        except Exception:
            pass

threading.Thread(target=unlimited_memory_monitor, daemon=True).start()

# =============================================================================
# 2)  المسارات والإعدادات (Replit-friendly)
# =============================================================================
# على Replit، استخدم المجلد الحالي بدل /tmp
DEFAULT_BASE = os.environ.get('BASE_PATH') or (
    os.path.join(os.getcwd(), 'panel_data') if os.path.exists('/home/runner') or 'REPL_ID' in os.environ else '/tmp'
)
BASE_PATH          = DEFAULT_BASE
os.makedirs(BASE_PATH, exist_ok=True)

USERS_FOLDER       = os.path.join(BASE_PATH, 'users_data')
USERS_FILE         = os.path.join(BASE_PATH, 'users.json')
PROCESSES_FILE     = os.path.join(BASE_PATH, 'processes.json')
SCHEDULES_FILE     = os.path.join(BASE_PATH, 'schedules.json')
LOGS_FILE          = os.path.join(BASE_PATH, 'activity.log')
USER_SESSIONS_FILE = os.path.join(BASE_PATH, 'user_sessions.json')
BACKUPS_FOLDER     = os.path.join(BASE_PATH, 'backups')
TEMP_FOLDER        = os.path.join(BASE_PATH, 'temp')
PACKAGES_FILE      = os.path.join(BASE_PATH, 'packages.json')
DOCKER_FILE        = os.path.join(BASE_PATH, 'docker.json')
MASTER_CONFIG_FILE = os.path.join(BASE_PATH, 'master_config.json')
BOT_CONFIG_FILE    = os.path.join(BASE_PATH, 'bot_config.json')
BOT_DATA_FILE      = os.path.join(BASE_PATH, 'bot_data.json')
PORTS_FILE         = os.path.join(BASE_PATH, 'ports.json')
ACTIVITY_FILE      = os.path.join(BASE_PATH, 'activity_feed.json')

PROFILE_IMAGE_URL = "https://iili.io/BL7bG5l.png"
ENTRY_SOUND_URL   = "https://b.top4top.io/m_3779fnnpd1.m4a"

# ملفات إعدادات المالك الخاصة
OWNER_CONFIG_FILE  = os.path.join(BASE_PATH, 'owner_config.json')
MAINTENANCE_FILE   = os.path.join(BASE_PATH, 'maintenance.json')
BOT_STATS_FILE     = os.path.join(BASE_PATH, 'bot_stats.json')
ANNOUNCE_FILE      = os.path.join(BASE_PATH, 'announcements.json')

# =============================================================================
# 3)  أدوات JSON
# =============================================================================
def init_json_file(file_path, default_data):
    if not os.path.exists(file_path):
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(default_data, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

def load_json_file(file_path, default=None):
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception:
        pass
    return default if default is not None else {}

def save_json_file(file_path, data):
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        return True
    except Exception:
        return False

# =============================================================================
# 4)  إعدادات لوحة المالك (Flask)
# =============================================================================
def load_master_config():
    default_config = {
        'master_username': 'OMAR_ADMIN',
        'master_password_hash': hashlib.sha256('OMAR_BOT'.encode()).hexdigest(),
        'port': 3178
    }
    if not os.path.exists(MASTER_CONFIG_FILE):
        save_json_file(MASTER_CONFIG_FILE, default_config)
        return default_config
    cfg = load_json_file(MASTER_CONFIG_FILE)
    if not cfg:
        return default_config
    for k, v in default_config.items():
        cfg.setdefault(k, v)
    return cfg

MASTER_CONFIG        = load_master_config()
MASTER_USERNAME      = MASTER_CONFIG.get('master_username', 'OMAR_ADMIN')
MASTER_PASSWORD_HASH = MASTER_CONFIG.get('master_password_hash')
SERVER_START_TIME    = time.time()

# =============================================================================
# 6)  إنشاء المجلدات والملفات
# =============================================================================
for folder in [USERS_FOLDER, TEMP_FOLDER, BACKUPS_FOLDER]:
    os.makedirs(folder, exist_ok=True)

init_json_file(USERS_FILE, {})
init_json_file(PROCESSES_FILE, {})
init_json_file(SCHEDULES_FILE, {})
init_json_file(USER_SESSIONS_FILE, {})
init_json_file(PACKAGES_FILE, {'pip': [], 'apt': [], 'custom': []})
init_json_file(DOCKER_FILE, {'containers': [], 'images': []})
init_json_file(PORTS_FILE, {'ports': []})
init_json_file(ACTIVITY_FILE, {'events': []})

# تهيئة ملفات المالك
init_json_file(OWNER_CONFIG_FILE, {'telegram_token': '', 'telegram_owner_id': '', 'bot_linked': False, 'panel_name': 'OMAR UNLIMITED VPS', 'welcome_msg': 'مرحباً بك في لوحة التحكم'})
init_json_file(MAINTENANCE_FILE, {'enabled': False, 'message': 'الموقع تحت الصيانة، يرجى المحاولة لاحقاً'})
init_json_file(BOT_STATS_FILE, {'total_users': 0, 'total_servers': 0, 'active_bots': 0, 'zip_files': 0, 'last_updated': ''})
init_json_file(ANNOUNCE_FILE, {'list': []})

def load_owner_config():
    default = {'telegram_token': '', 'telegram_owner_id': '', 'bot_linked': False, 'panel_name': 'OMAR UNLIMITED VPS', 'welcome_msg': 'مرحباً بك في لوحة التحكم'}
    cfg = load_json_file(OWNER_CONFIG_FILE, default)
    for k, v in default.items():
        cfg.setdefault(k, v)
    return cfg

def load_maintenance():
    return load_json_file(MAINTENANCE_FILE, {'enabled': False, 'message': 'الموقع تحت الصيانة، يرجى المحاولة لاحقاً'})

def save_maintenance(data):
    save_json_file(MAINTENANCE_FILE, data)

def load_bot_stats():
    return load_json_file(BOT_STATS_FILE, {'total_users': 0, 'total_servers': 0, 'active_bots': 0, 'zip_files': 0, 'last_updated': ''})

def load_announcements():
    return load_json_file(ANNOUNCE_FILE, {'list': []})

def save_announcements(data):
    save_json_file(ANNOUNCE_FILE, data)

# =============================================================================
# 6.5)  قالب صفحة الصيانة
# =============================================================================
MAINTENANCE_TEMPLATE = r'''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>صيانة - OMAR UNLIMITED VPS</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;font-family:"Inter","Segoe UI",sans-serif}
body{background:#1f2933;color:#d6dde3;min-height:100vh;display:flex;align-items:center;justify-content:center}
.maint-card{text-align:center;padding:50px 40px;background:#2b3a43;border:1px solid #3a4a55;border-radius:12px;max-width:500px;width:90%;box-shadow:0 20px 60px rgba(0,0,0,.5)}
.maint-icon{font-size:80px;margin-bottom:20px;animation:spin 4s linear infinite}
@keyframes spin{0%{transform:rotate(0deg)}100%{transform:rotate(360deg)}}
.maint-title{font-size:28px;font-weight:700;color:#fff;margin-bottom:10px}
.maint-sub{font-size:14px;color:#29c7d3;margin-bottom:24px;font-weight:600;text-transform:uppercase;letter-spacing:2px}
.maint-msg{font-size:16px;color:#9aa9b3;line-height:1.7;background:#1a242c;padding:16px 20px;border-radius:8px;border-left:4px solid #29c7d3}
.maint-footer{margin-top:24px;font-size:12px;color:#5a6c78}
.maint-footer a{color:#29c7d3;text-decoration:none}
.pulse{animation:pulse 2s infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.5}}
</style>
</head>
<body>
<div class="maint-card">
  <div class="maint-icon">⚙️</div>
  <div class="maint-title">صيانة مجدولة</div>
  <div class="maint-sub pulse">🔧 Under Maintenance</div>
  <div class="maint-msg">{{ message }}</div>
  <div class="maint-footer">جميع الحقوق محفوظة &copy; OMAR UNLIMITED VPS</div>
</div>
</body>
</html>
'''

# =============================================================================
# 7)  Flask App
# =============================================================================
app = Flask(__name__)

# مفتاح سري ثابت يُحفظ في ملف حتى لا تنتهي الجلسات عند إعادة التشغيل
_SECRET_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.secret_key')
if os.path.exists(_SECRET_FILE):
    with open(_SECRET_FILE, 'r') as _sf:
        app.secret_key = _sf.read().strip()
else:
    _new_key = secrets.token_hex(64)
    with open(_SECRET_FILE, 'w') as _sf:
        _sf.write(_new_key)
    app.secret_key = _new_key

app.permanent_session_lifetime = timedelta(days=30)
app.config['MAX_CONTENT_LENGTH'] = None
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

# Middleware لوضع الصيانة
@app.before_request
def check_maintenance():
    maint = load_maintenance()
    if not maint.get('enabled'):
        return None
    # السماح للمالك بالدخول دائماً
    if request.path in ['/login', '/logout'] or request.path.startswith('/api/'):
        return None
    if session.get('username') == MASTER_USERNAME:
        return None
    msg = maint.get('message', 'الموقع تحت الصيانة')
    return render_template_string(MAINTENANCE_TEMPLATE, message=msg), 503

# =============================================================================
# 8)  أدوات اللوحة (Activity feed محسّن لعرض على الواجهة)
# =============================================================================
def add_activity_event(username, action, details=""):
    """يضيف حدثاً للـ Activity feed (مثل صفحة Activity في Lunes Host)"""
    try:
        events = load_json_file(ACTIVITY_FILE, {'events': []}).get('events', [])
        events.insert(0, {
            'id': str(uuid.uuid4())[:8],
            'username': username,
            'action': action,
            'details': details,
            'ip': request.remote_addr if request else '-',
            'timestamp': datetime.now().isoformat(),
            'time_text': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        events = events[:300]  # احتفظ بأحدث 300 حدث
        save_json_file(ACTIVITY_FILE, {'events': events})
    except Exception:
        pass

def log_activity(username, action, details=""):
    try:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(LOGS_FILE, 'a', encoding='utf-8') as f:
            f.write(f"[{ts}] [{username}] {action} | {details}\n")
        add_activity_event(username, action, details)
    except Exception:
        pass

# =============================================================================
# Replit KV Store — تخزين دائم يصمد عبر كل عمليات النشر وإعادة التشغيل
# =============================================================================
_REPLIT_DB_URL = os.environ.get('REPLIT_DB_URL', '')
_KV_USERS_KEY  = 'omar_vps_users_v1'

def _kv_get(key):
    if not _REPLIT_DB_URL:
        return None
    try:
        url = _REPLIT_DB_URL.rstrip('/') + '/' + urllib.parse.quote(key, safe='')
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.read().decode('utf-8')
    except Exception:
        return None

def _kv_set(key, value):
    if not _REPLIT_DB_URL:
        return False
    try:
        data = urllib.parse.urlencode({key: value}).encode('utf-8')
        req = urllib.request.Request(_REPLIT_DB_URL, data=data, method='POST')
        urllib.request.urlopen(req, timeout=5)
        return True
    except Exception:
        return False

def load_users():
    # أولاً: حاول من KV Store (ثابت عبر النشر والإعادات)
    if _REPLIT_DB_URL:
        raw = _kv_get(_KV_USERS_KEY)
        if raw:
            try:
                data = json.loads(raw)
                if isinstance(data, dict):
                    # زامن مع الملف المحلي أيضاً
                    save_json_file(USERS_FILE, data)
                    return data
            except Exception:
                pass
    # ثانياً: الملف المحلي
    return load_json_file(USERS_FILE, {})

def save_users(u):
    if not isinstance(u, dict):
        return
    # حماية: لا تحفظ قاموساً فارغاً إذا كان هناك مستخدمون سابقون
    existing = load_json_file(USERS_FILE, {})
    if not u and existing:
        print("[⚠️ save_users] BLOCKED empty save — preserving existing users")
        return
    save_json_file(USERS_FILE, u)
    _kv_set(_KV_USERS_KEY, json.dumps(u, ensure_ascii=False))

def load_processes():        return load_json_file(PROCESSES_FILE)
def save_processes(p):       save_json_file(PROCESSES_FILE, p)
def load_schedules():        return load_json_file(SCHEDULES_FILE)
def save_schedules(s):       save_json_file(SCHEDULES_FILE, s)
def load_user_sessions():    return load_json_file(USER_SESSIONS_FILE)
def save_user_sessions(s):   save_json_file(USER_SESSIONS_FILE, s)
def load_packages():         return load_json_file(PACKAGES_FILE)
def save_packages(p):        save_json_file(PACKAGES_FILE, p)
def load_ports():            return load_json_file(PORTS_FILE, {'ports': []}).get('ports', [])
def save_ports(p):           save_json_file(PORTS_FILE, {'ports': p})

def get_user_path(username):
    if username == MASTER_USERNAME:
        return BASE_PATH
    return os.path.join(USERS_FOLDER, username)

def ensure_user_folder(username):
    if username == MASTER_USERNAME:
        return
    p = get_user_path(username)
    os.makedirs(p, exist_ok=True)

def is_path_allowed(username, requested_path):
    if username == MASTER_USERNAME:
        return True
    user_path = get_user_path(username)
    try:
        return os.path.realpath(requested_path).startswith(os.path.realpath(user_path))
    except Exception:
        return False

def can_user_login(username):
    sessions = load_user_sessions()
    users = load_users()
    if username not in users:
        return False
    ud = users[username] if isinstance(users[username], dict) else {}
    max_s = ud.get('max_sessions', 999)
    if sessions.get(username, 0) >= max_s:
        return False
    # فحص تاريخ الانتهاء
    expiry = ud.get('expiry')
    if expiry and expiry != '∞':
        try:
            if datetime.now() > datetime.fromisoformat(expiry):
                return False
        except Exception:
            pass
    return True

def register_session(username):
    sessions = load_user_sessions()
    sessions[username] = sessions.get(username, 0) + 1
    save_user_sessions(sessions)

def unregister_session(username):
    sessions = load_user_sessions()
    if username in sessions:
        sessions[username] = max(0, sessions[username] - 1)
        save_user_sessions(sessions)

def get_system_stats():
    try:
        net = psutil.net_io_counters()
        return {
            'cpu_percent': psutil.cpu_percent(interval=0.1),
            'memory_percent': psutil.virtual_memory().percent,
            'memory_used_mb': psutil.virtual_memory().used / (1024**2),
            'memory_total_mb': psutil.virtual_memory().total / (1024**2),
            'memory_used_gb': psutil.virtual_memory().used / (1024**3),
            'memory_total_gb': psutil.virtual_memory().total / (1024**3),
            'disk_percent': psutil.disk_usage('/').percent,
            'disk_used_mb': psutil.disk_usage('/').used / (1024**2),
            'disk_used_gb': psutil.disk_usage('/').used / (1024**3),
            'disk_total_gb': psutil.disk_usage('/').total / (1024**3),
            'uptime': int(time.time() - SERVER_START_TIME),
            'uptime_system': int(time.time() - psutil.boot_time()),
            'net_in_kb': net.bytes_recv / 1024,
            'net_out_kb': net.bytes_sent / 1024,
            'platform': platform.platform(),
            'hostname': socket.gethostname(),
            'public_ip': requests.get('https://api.ipify.org', timeout=2).text if 'requests' in globals() else 'N/A'
        }
    except Exception:
        return {}

def format_uptime(secs):
    secs = int(secs or 0)
    h = secs // 3600
    m = (secs % 3600) // 60
    s = secs % 60
    return f"{h}h {m}m {s}s"

# =============================================================================
# 9)  أدوات تشغيل الملفات (كاملة مع run/stop/output/input)
# =============================================================================
running_processes = {}
running_files     = {}
file_processes    = {}
port_processes    = {}  # للبورتات الإضافية

def extract_and_find_main(zip_path, extract_to):
    try:
        with zipfile.ZipFile(zip_path, 'r') as z:
            z.extractall(extract_to)
        main_files = ['main.py', 'app.py', 'bot.py', 'run.py', 'start.py', 'index.py']
        for root, dirs, files in os.walk(extract_to):
            for f in files:
                if f.lower() in main_files:
                    return os.path.join(root, f)
        for root, dirs, files in os.walk(extract_to):
            for f in files:
                if f.endswith(('.py', '.js', '.php', '.sh')):
                    return os.path.join(root, f)
    except Exception:
        pass
    return None

def validate_python_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read().strip()
        if not content:
            return False, "File is empty"
        try:
            ast.parse(content)
            return True, "Valid Python code"
        except SyntaxError as e:
            return False, f"Python syntax error: {e}"
    except Exception:
        return True, ""

def get_run_command(filepath):
    ext = filepath.split('.')[-1].lower()
    commands = {
        'py':   f'python3 -u "{filepath}"',
        'js':   f'node "{filepath}"',
        'php':  f'php "{filepath}"',
        'sh':   f'bash "{filepath}"',
        'bash': f'bash "{filepath}"',
        'rb':   f'ruby "{filepath}"',
        'pl':   f'perl "{filepath}"',
        'lua':  f'lua "{filepath}"',
        'go':   f'go run "{filepath}"',
        'java': f'java "{filepath}"',
        'jar':  f'java -jar "{filepath}"',
        'c':    f'gcc "{filepath}" -o "{os.path.splitext(filepath)[0]}" && "{os.path.splitext(filepath)[0]}"',
        'cpp':  f'g++ "{filepath}" -o "{os.path.splitext(filepath)[0]}" && "{os.path.splitext(filepath)[0]}"',
        'rs':   f'rustc "{filepath}" && "{os.path.splitext(filepath)[0]}"',
        'dart': f'dart "{filepath}"',
        'r':    f'Rscript "{filepath}"',
        'jl':   f'julia "{filepath}"',
    }
    return commands.get(ext, f'python3 -u "{filepath}"')

def read_process_output(proc_id, process, max_lines=2000, store=None):
    store = store if store is not None else file_processes
    output_buffer = deque(maxlen=max_lines)
    try:
        for line in iter(process.stdout.readline, ''):
            if proc_id not in store:
                break
            output_buffer.append(line.rstrip('\n'))
            store[proc_id]['output'] = list(output_buffer)
    except Exception:
        pass

def auto_install_dependencies(filepath):
    installed, failed = [], []
    try:
        cur = os.path.dirname(filepath)
        for _ in range(3):
            req_path = os.path.join(cur, 'requirements.txt')
            if os.path.exists(req_path):
                try:
                    r = subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', req_path],
                                       capture_output=True, text=True, timeout=300)
                    (installed if r.returncode == 0 else failed).append('requirements.txt')
                except Exception:
                    failed.append('requirements.txt')
                break
            cur = os.path.dirname(cur)

        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        packages = []
        if filepath.endswith('.py'):
            try:
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for a in node.names:
                            packages.append(a.name.split('.')[0])
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            packages.append(node.module.split('.')[0])
            except Exception:
                packages = re.findall(r'^(?:import|from)\s+([a-zA-Z0-9_]+)', content, re.MULTILINE)
        elif filepath.endswith('.js'):
            packages = re.findall(r'require\([\'"]([^\'"]+)[\'"]\)', content)
            packages += re.findall(r'import\s+.*?\s+from\s+[\'"]([^\'"]+)[\'"]', content)

        package_map = {
            'telegram': 'python-telegram-bot', 'telebot': 'pyTelegramBotAPI',
            'discord': 'discord.py', 'PIL': 'Pillow', 'cv2': 'opencv-python',
            'sklearn': 'scikit-learn', 'flask_sqlalchemy': 'Flask-SQLAlchemy',
            'flask_cors': 'Flask-Cors', 'bs4': 'beautifulsoup4', 'yaml': 'PyYAML',
            'dotenv': 'python-dotenv', 'mysql': 'mysql-connector-python',
            'psycopg2': 'psycopg2-binary', 'youtube_dl': 'youtube-dl',
            'yt_dlp': 'yt-dlp',
        }
        std_libs = {'os','sys','time','json','re','math','random','datetime','threading',
                    'subprocess','collections','io','typing','abc','flask','requests',
                    'psutil','hashlib','base64','uuid','socket','platform','signal',
                    'warnings','gc','resource','shutil','zipfile','tarfile','secrets',
                    'functools','itertools','string','textwrap','pathlib','glob',
                    'tempfile','contextlib','html','logging','ast'}

        for pkg in set(packages):
            if not pkg or pkg.startswith('.') or pkg in std_libs:
                continue
            actual = package_map.get(pkg, pkg)
            try:
                __import__(pkg)
            except Exception:
                try:
                    r = subprocess.run([sys.executable, '-m', 'pip', 'install', '--user', actual],
                                       capture_output=True, text=True, timeout=180)
                    (installed if r.returncode == 0 else failed).append(actual)
                except Exception:
                    failed.append(actual)
        return {'installed': installed, 'failed': failed}
    except Exception as e:
        return {'installed': installed, 'failed': failed + [str(e)]}

# =============================================================================
# 10)  ديكورات الـ Flask
# =============================================================================
def login_required(f):
    @wraps(f)
    def w(*a, **kw):
        if 'logged_in' not in session:
            if request.path.startswith('/api/'):
                return jsonify({'success': False, 'error': 'Session expired'}), 401
            return redirect('/login')
        return f(*a, **kw)
    return w

def master_required(f):
    @wraps(f)
    def w(*a, **kw):
        if session.get('username') != MASTER_USERNAME:
            return jsonify({'success': False, 'error': 'Master only'}), 403
        return f(*a, **kw)
    return w

# =============================================================================
# 13)  مسارات الـ Flask
# =============================================================================
@app.route('/')
@login_required
def index():
    username = session.get('username')
    is_master = (username == MASTER_USERNAME)
    # متغيرات إضافية للقالب
    session_id = str(uuid.uuid4())[:8]  # معرف جلسة وهمي للعرض
    master_port = MASTER_CONFIG.get('port', 3177)
    return render_template('index.html', 
                           session=session,
                           user_path=get_user_path(username),
                           is_master=is_master,
                           session_id=session_id,
                           master_port=master_port,
                           MASTER_USERNAME=MASTER_USERNAME)

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'GET':
        return render_template('login.html', error=None)
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    h = hashlib.sha256(password.encode()).hexdigest()
    if username == MASTER_USERNAME and h == MASTER_PASSWORD_HASH:
        session.permanent = True
        session['logged_in'] = True
        session['username'] = username
        register_session(username)
        log_activity(username, 'auth.login', 'Master login successful')
        return redirect('/')
    users = load_users()
    if username in users and users[username].get('password') == h and can_user_login(username):
        session.permanent = True
        session['logged_in'] = True
        session['username'] = username
        register_session(username)
        os.makedirs(get_user_path(username), exist_ok=True)
        log_activity(username, 'auth.login', 'User login successful')
        return redirect('/')
    log_activity(username or '-', 'auth.login.failed', 'Invalid credentials')
    return render_template('login.html', error='❌ Invalid credentials')

@app.route('/logout')
def logout():
    if 'username' in session:
        log_activity(session['username'], 'auth.logout', 'User logged out')
        unregister_session(session['username'])
    session.clear()
    return redirect('/login')

@app.route('/api/files/main-file')
@login_required
def get_main_file_api():
    """جلب الملف الأساسي للمستخدم الحالي"""
    username = session['username']
    if username == MASTER_USERNAME:
        main_file = MASTER_CONFIG.get('main_file', 'main.py')
    else:
        users = load_users()
        main_file = users.get(username, {}).get('main_file', 'main.py') if isinstance(users.get(username), dict) else 'main.py'
    return jsonify({'success': True, 'main_file': main_file})

@app.route('/api/profile')
@login_required
def get_profile():
    u = session['username']
    p = get_user_path(u)
    size = 0
    if os.path.exists(p):
        for r, d, f in os.walk(p):
            for fl in f:
                fp = os.path.join(r, fl)
                if os.path.exists(fp):
                    size += os.path.getsize(fp)
    users = load_users()
    ud = users.get(u, {})
    return jsonify({
        'username': u,
        'is_master': u == MASTER_USERNAME,
        'created': ud.get('created', datetime.now().isoformat()) if isinstance(ud, dict) else datetime.now().isoformat(),
        'expiry': ud.get('expiry', '∞') if isinstance(ud, dict) else '∞',
        'disk_usage_gb': size / (1024**3)
    })

@app.route('/api/system')
@login_required
def system_info():
    return jsonify(get_system_stats())

@app.route('/api/sysinfo')
@login_required
def sysinfo():
    return jsonify({'info': f"Platform: {platform.platform()}\nCPU: {psutil.cpu_percent()}%\nMemory: {psutil.virtual_memory().percent}%"})

@app.route('/api/system/action', methods=['POST'])
@login_required
def system_action_api():
    a = (request.json or {}).get('action')
    try:
        if a == 'clean':
            gc.collect()
        elif a == 'update':
            subprocess.run(['apt-get', 'update'], capture_output=True, timeout=120)
        log_activity(session['username'], 'system.action', a or '')
        return jsonify({'success': True, 'action': a})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# ----- Activity feed -----
@app.route('/api/activity')
@login_required
def activity_api():
    data = load_json_file(ACTIVITY_FILE, {'events': []})
    events = data.get('events', [])
    if session.get('username') != MASTER_USERNAME:
        events = [e for e in events if e.get('username') == session.get('username')]
    return jsonify({'events': events[:200]})

# ----- ملفات -----
@app.route('/api/files')
@login_required
def list_files_api():
    p = request.args.get('path', get_user_path(session['username']))
    if not is_path_allowed(session['username'], p):
        return jsonify({'success': False, 'error': 'forbidden'}), 403
    files = []
    try:
        for n in sorted(os.listdir(p), key=lambda x: (not os.path.isdir(os.path.join(p, x)), x.lower())):
            fp = os.path.join(p, n)
            files.append({
                'name': n,
                'is_dir': os.path.isdir(fp),
                'size': f"{os.path.getsize(fp)//1024} KB" if os.path.isfile(fp) else '',
            })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    return jsonify({'files': files})

@app.route('/api/files/upload', methods=['POST'])
@login_required
def upload_file_api():
    f = request.files.get('file')
    p = request.form.get('path', get_user_path(session['username']))
    if not f:
        return jsonify({'success': False, 'error': 'No file provided'}), 400
    if not is_path_allowed(session['username'], p):
        return jsonify({'success': False, 'error': 'Forbidden path'}), 403
    try:
        filename = secure_filename(f.filename) if f.filename else ''
        if not filename:
            filename = 'uploaded_file'
        os.makedirs(p, exist_ok=True)
        save_path = os.path.join(p, filename)
        f.save(save_path)
        log_activity(session['username'], 'server.file.upload', filename)
        return jsonify({'success': True, 'filename': filename})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/files/folder', methods=['POST'])
@login_required
def create_folder_api():
    d = request.json
    if not is_path_allowed(session['username'], d['path']):
        return jsonify({'success': False}), 403
    os.makedirs(d['path'], exist_ok=True)
    log_activity(session['username'], 'server.file.mkdir', d['path'])
    return jsonify({'success': True})

@app.route('/api/files/create', methods=['POST'])
@login_required
def create_file_api():
    d = request.json
    if not is_path_allowed(session['username'], d['path']):
        return jsonify({'success': False}), 403
    with open(d['path'], 'w', encoding='utf-8') as f:
        f.write(d.get('content', ''))
    log_activity(session['username'], 'server.file.create', d['path'])
    return jsonify({'success': True})

@app.route('/api/files/delete', methods=['POST'])
@login_required
def delete_file_api():
    d = request.json
    p = d['path']
    if not is_path_allowed(session['username'], p):
        return jsonify({'success': False}), 403
    if os.path.isdir(p):
        shutil.rmtree(p, ignore_errors=True)
    elif os.path.isfile(p):
        os.remove(p)
    log_activity(session['username'], 'server.file.delete', p)
    return jsonify({'success': True})

@app.route('/api/files/content')
@login_required
def get_file_content():
    p = request.args.get('path')
    if not p or not is_path_allowed(session['username'], p):
        return jsonify({'success': False}), 403
    try:
        with open(p, 'r', encoding='utf-8', errors='ignore') as f:
            log_activity(session['username'], 'server.file.read', p)
            return jsonify({'content': f.read()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/files/save', methods=['POST'])
@login_required
def save_file_api():
    d = request.json
    if not is_path_allowed(session['username'], d['path']):
        return jsonify({'success': False}), 403
    with open(d['path'], 'w', encoding='utf-8') as f:
        f.write(d.get('content', ''))
    log_activity(session['username'], 'server.file.write', d['path'])
    return jsonify({'success': True})

@app.route('/api/files/set-main', methods=['POST'])
@login_required
def set_main_file_api():
    """تعيين ملف كملف التشغيل الأساسي للمستخدم"""
    d = request.json or {}
    filename = d.get('filename', '')
    path = d.get('path', '')
    username = session['username']
    if not filename:
        return jsonify({'success': False, 'error': 'No filename'})
    users = load_users()
    if username == MASTER_USERNAME:
        MASTER_CONFIG['main_file'] = filename
        save_json_file(MASTER_CONFIG_FILE, MASTER_CONFIG)
    elif username in users:
        users[username]['main_file'] = filename
        save_users(users)
    log_activity(username, 'server.file.set-main', filename)
    return jsonify({'success': True, 'main_file': filename})

# ----- تشغيل/إيقاف الملفات -----
@app.route('/api/file/run', methods=['POST'])
@login_required
def run_file_api():
    d = request.json or {}
    filepath = os.path.join(d.get('path',''), d.get('filename',''))
    if not os.path.exists(filepath):
        return jsonify({'success': False, 'error': 'File not found'})
    if not is_path_allowed(session['username'], d.get('path','')):
        return jsonify({'success': False, 'error': 'Forbidden'})
    if d.get('filename', '').lower().endswith('.zip'):
        extract_dir = os.path.join(d['path'], d['filename'].replace('.zip', ''))
        os.makedirs(extract_dir, exist_ok=True)
        main = extract_and_find_main(filepath, extract_dir)
        if main:
            filepath = main
        else:
            return jsonify({'success': False, 'error': 'Main file not found'})
    installed = auto_install_dependencies(filepath)
    cmd = get_run_command(filepath)
    try:
        kwargs = dict(shell=True, cwd=os.path.dirname(filepath),
                      stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                      stderr=subprocess.STDOUT, text=True, bufsize=1)
        if hasattr(os, 'setsid'):
            kwargs['preexec_fn'] = os.setsid
        p = subprocess.Popen(cmd, **kwargs)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
    pid = f"{session['username']}_{d.get('filename','f')}_{int(time.time())}"
    file_processes[pid] = {'process': p, 'filename': d.get('filename',''), 'username': session['username'], 'output': []}
    threading.Thread(target=read_process_output, args=(pid, p), kwargs={'store': file_processes}, daemon=True).start()
    log_activity(session['username'], 'server.file.run', f"{d.get('filename','')} ({pid})")
    return jsonify({'success': True, 'process_id': pid, 'installed_result': installed})

@app.route('/api/file/stop', methods=['POST'])
@login_required
def stop_file_api():
    pid = (request.json or {}).get('process_id')
    if pid in file_processes:
        try:
            if hasattr(os, 'killpg'):
                os.killpg(os.getpgid(file_processes[pid]['process'].pid), signal.SIGKILL)
            else:
                file_processes[pid]['process'].kill()
        except Exception:
            pass
        log_activity(session['username'], 'server.file.stop', pid)
        del file_processes[pid]
    return jsonify({'success': True})

@app.route('/api/file/output/<pid>')
@login_required
def get_file_output_api(pid):
    if pid in file_processes:
        info = file_processes[pid]
        return jsonify({
            'success': True,
            'output': info.get('output', []),
            'is_running': info['process'].poll() is None
        })
    return jsonify({'success': False})

@app.route('/api/file/input', methods=['POST'])
@login_required
def send_file_input_api():
    d = request.json or {}
    pid = d.get('process_id')
    if pid in file_processes:
        try:
            file_processes[pid]['process'].stdin.write(d.get('input','') + '\n')
            file_processes[pid]['process'].stdin.flush()
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})
    return jsonify({'success': True})

@app.route('/api/file/running')
@login_required
def get_running_files_api():
    user    = session['username']
    running = []
    dead    = []
    for pid, info in file_processes.items():
        if info['username'] == user or user == MASTER_USERNAME:
            if info['process'].poll() is None:
                running.append({'process_id': pid, 'filename': info['filename'], 'username': info['username']})
            else:
                dead.append(pid)
    for d in dead:
        file_processes.pop(d, None)
    return jsonify({'success': True, 'running': running})

# ----- تنفيذ أوامر -----
@app.route('/api/exec', methods=['POST'])
@login_required
def execute_command_api():
    d = request.json
    cmd = d['command']
    cwd = d.get('cwd', get_user_path(session['username']))
    log_activity(session['username'], 'server.exec', cmd[:120])
    try:
        r = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True, timeout=60)
        return jsonify({'output': r.stdout + r.stderr, 'success': True})
    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Timeout (60s)', 'success': False})
    except Exception as e:
        return jsonify({'error': str(e), 'success': False})

# ----- العمليات -----
@app.route('/api/process/start', methods=['POST'])
@login_required
def start_process_api():
    d = request.json
    def run():
        kwargs = dict(shell=True, cwd=d.get('cwd', BASE_PATH))
        if hasattr(os, 'setsid'):
            kwargs['preexec_fn'] = os.setsid
        p = subprocess.Popen(d['command'], **kwargs)
        running_processes[d['name']] = {'process': p, 'owner': session.get('username'), 'command': d['command']}
        p.wait()
    threading.Thread(target=run, daemon=True).start()
    log_activity(session['username'], 'server.process.start', d.get('name',''))
    return jsonify({'success': True})

@app.route('/api/process/stop', methods=['POST'])
@login_required
def stop_process_api():
    n = request.json['name']
    if n in running_processes:
        try:
            if hasattr(os, 'killpg'):
                os.killpg(os.getpgid(running_processes[n]['process'].pid), signal.SIGKILL)
            else:
                running_processes[n]['process'].kill()
        except Exception:
            pass
        del running_processes[n]
    log_activity(session['username'], 'server.process.stop', n)
    return jsonify({'success': True})

@app.route('/api/process/stop-all', methods=['POST'])
@login_required
def stop_all_processes_api():
    for p in list(running_processes.values()):
        try:
            if hasattr(os, 'killpg'):
                os.killpg(os.getpgid(p['process'].pid), signal.SIGKILL)
            else:
                p['process'].kill()
        except Exception:
            pass
    running_processes.clear()
    return jsonify({'success': True})

@app.route('/api/process/list')
@login_required
def list_processes_api():
    procs = {}
    for n, i in running_processes.items():
        procs[n] = {'status': 'running' if i['process'].poll() is None else 'stopped', 'command': i['command']}
    return jsonify(procs)

# ----- شبكة / بورتات متعددة (Replit-friendly) -----
@app.route('/api/network/scan', methods=['POST'])
@login_required
def scan_ports_api():
    d = request.json
    out = []
    for p in d.get('ports', []):
        try:
            s = socket.socket()
            s.settimeout(1)
            r = s.connect_ex((d['host'], int(p)))
            out.append({'port': p, 'open': r == 0})
            s.close()
        except Exception:
            out.append({'port': p, 'open': False})
    return jsonify({'results': out})

@app.route('/api/ports/list')
@login_required
def list_ports_api():
    return jsonify({'ports': load_ports()})

@app.route('/api/ports/add', methods=['POST'])
@master_required
def add_port_api():
    d = request.json
    try:
        port = int(d.get('port', 0))
    except Exception:
        return jsonify({'success': False, 'error': 'Invalid port'})
    if port <= 0 or port > 65535:
        return jsonify({'success': False, 'error': 'Invalid port range'})
    ports = load_ports()
    if any(p.get('port') == port for p in ports):
        return jsonify({'success': False, 'error': 'Port already exists'})
    ports.append({'port': port, 'note': d.get('note', ''), 'status': 'idle', 'created': datetime.now().isoformat()})
    save_ports(ports)
    log_activity(session['username'], 'server.port.add', str(port))
    return jsonify({'success': True})

@app.route('/api/ports/delete', methods=['POST'])
@master_required
def del_port_api():
    port = (request.json or {}).get('port')
    ports = [p for p in load_ports() if p.get('port') != port]
    save_ports(ports)
    log_activity(session['username'], 'server.port.delete', str(port))
    return jsonify({'success': True})

# ----- مستخدمي اللوحة -----
@app.route('/api/users/list')
@master_required
def list_panel_users_api():
    users = load_users()
    sessions = load_user_sessions()
    return jsonify({'users': [
        {'username': u,
         'max_sessions': users[u].get('max_sessions', 999) if isinstance(users[u], dict) else 999,
         'max_servers': users[u].get('max_servers', 1) if isinstance(users[u], dict) else 1,
         'main_file': users[u].get('main_file', 'main.py') if isinstance(users[u], dict) else 'main.py',
         'active_sessions': sessions.get(u, 0),
         'expiry': users[u].get('expiry') if isinstance(users[u], dict) else None}
        for u in users
    ]})

@app.route('/api/users/add', methods=['POST'])
@master_required
def add_panel_user_api():
    d = request.json
    uname = d.get('username', '').strip()
    if not uname:
        return jsonify({'success': False, 'error': 'Username required'})
    users = load_users()
    if uname in users:
        return jsonify({'success': False, 'error': 'Username already exists'})
    # حساب تاريخ الانتهاء — أدنى 30 يوم
    expiry_days = max(30, int(d.get('expiry_days', 30) or 30))
    expiry_dt = (datetime.now() + timedelta(days=expiry_days)).isoformat()
    users[uname] = {
        'password': hashlib.sha256(d['password'].encode()).hexdigest(),
        'max_sessions': int(d.get('max_sessions', 999)),
        'max_servers': int(d.get('max_servers', 1)),
        'main_file': d.get('main_file', 'main.py'),
        'created': datetime.now().isoformat(),
        'expiry': expiry_dt
    }
    save_users(users)
    os.makedirs(os.path.join(USERS_FOLDER, uname), exist_ok=True)
    log_activity(session['username'], 'server.user.add', uname)
    return jsonify({'success': True})

@app.route('/api/users/update', methods=['POST'])
@master_required
def update_panel_user_api():
    d = request.json
    users = load_users()
    uname = d.get('username')
    if uname not in users:
        return jsonify({'success': False, 'error': 'User not found'})
    if d.get('password'):
        users[uname]['password'] = hashlib.sha256(d['password'].encode()).hexdigest()
    if d.get('max_servers') is not None:
        users[uname]['max_servers'] = int(d['max_servers'])
    if d.get('main_file') is not None:
        users[uname]['main_file'] = d['main_file']
    if d.get('max_sessions') is not None:
        users[uname]['max_sessions'] = int(d['max_sessions'])
    # تحديث مدة الاشتراك إذا أُرسلت — أدنى 30 يوم
    if d.get('expiry_days') is not None:
        expiry_days = max(30, int(d['expiry_days'] or 30))
        users[uname]['expiry'] = (datetime.now() + timedelta(days=expiry_days)).isoformat()
    save_users(users)
    log_activity(session['username'], 'server.user.update', uname)
    return jsonify({'success': True})

@app.route('/api/users/delete', methods=['POST'])
@master_required
def delete_panel_user_api():
    d = request.json
    users = load_users()
    if d['username'] in users:
        del users[d['username']]
        save_users(users)
        shutil.rmtree(os.path.join(USERS_FOLDER, d['username']), ignore_errors=True)
        log_activity(session['username'], 'server.user.delete', d['username'])
    return jsonify({'success': True})

# ----- الملفات الثابتة -----
@app.route('/static/<filename>')
def serve_static(filename):
    return send_from_directory(BASE_PATH, filename)

# ----- استضافة المواقع والـ API -----
@app.route('/web/<username>/')
@app.route('/web/<username>/<path:filename>')
def serve_user_web(username, filename='index.html'):
    user_path = get_user_path(username)
    # نبحث عن ملف index.html في مجلد المستخدم
    return send_from_directory(user_path, filename)

@app.route('/api-service/<username>/')
@app.route('/api-service/<username>/<path:filename>')
def serve_user_api_files(username, filename='api.json'):
    user_path = get_user_path(username)
    return send_from_directory(user_path, filename)

# ----- الجدولة -----
@app.route('/api/schedules/list')
@login_required
def list_schedules_api():
    return jsonify({'schedules': list(load_schedules().values())})

@app.route('/api/schedules/add', methods=['POST'])
@login_required
def add_schedule_api():
    d = request.json
    sch = load_schedules()
    sid = str(uuid.uuid4())[:8]
    sch[sid] = {'id': sid, 'name': d['name'], 'command': d['command'], 'schedule': d.get('schedule', '* * * * *'), 'owner': session['username']}
    save_schedules(sch)
    log_activity(session['username'], 'server.schedule.add', d['name'])
    return jsonify({'success': True})

# ----- النسخ -----
@app.route('/api/backups/list')
@master_required
def list_backups_api():
    backs = []
    if os.path.exists(BACKUPS_FOLDER):
        for f in os.listdir(BACKUPS_FOLDER):
            if f.endswith('.tar.gz'):
                backs.append({'name': f, 'size': f"{os.path.getsize(os.path.join(BACKUPS_FOLDER, f))/1024**2:.2f} MB"})
    return jsonify({'backups': backs})

@app.route('/api/backups/create', methods=['POST'])
@master_required
def create_backup_api():
    name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.tar.gz"
    try:
        with tarfile.open(os.path.join(BACKUPS_FOLDER, name), 'w:gz') as tar:
            tar.add(BASE_PATH, arcname='backup')
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
    log_activity(session['username'], 'server.backup.create', name)
    return jsonify({'success': True})

# ----- الحزم -----
@app.route('/api/packages/list')
@master_required
def list_packages_api():
    return jsonify(load_packages())

@app.route('/api/packages/install/pip', methods=['POST'])
@master_required
def install_pip_api():
    pkg = request.json['package']
    subprocess.run([sys.executable, '-m', 'pip', 'install', pkg], capture_output=True)
    pkgs = load_packages()
    if pkg not in pkgs.get('pip', []):
        pkgs.setdefault('pip', []).append(pkg)
        save_packages(pkgs)
    log_activity(session['username'], 'server.package.install', pkg)
    return jsonify({'success': True})

# ----- Docker -----
@app.route('/api/docker/list')
@master_required
def list_docker_api():
    out = []
    try:
        r = subprocess.run(['docker', 'ps', '-a', '--format', '{{.Names}}|{{.Status}}'],
                           capture_output=True, text=True)
        for line in (r.stdout or '').strip().split('\n'):
            if line:
                parts = line.split('|')
                if len(parts) >= 2:
                    out.append({'name': parts[0], 'status': parts[1]})
    except Exception:
        pass
    return jsonify({'containers': out})

@app.route('/api/docker/run', methods=['POST'])
@master_required
def run_docker_api():
    d = request.json
    cmd = ['docker', 'run', '-d']
    if d.get('name'): cmd.extend(['--name', d['name']])
    if d.get('ports'):
        for p in d['ports'].split(','):
            cmd.extend(['-p', p.strip()])
    cmd.append(d['image'])
    subprocess.run(cmd, capture_output=True)
    return jsonify({'success': True})

# ----- السجلات -----
@app.route('/api/logs')
@master_required
def get_logs_api():
    if os.path.exists(LOGS_FILE):
        with open(LOGS_FILE, 'r', encoding='utf-8', errors='ignore') as f:
            return jsonify({'logs': f.read()[-50000:]})
    return jsonify({'logs': ''})

@app.route('/api/logs/clear', methods=['POST'])
@master_required
def clear_logs_api():
    with open(LOGS_FILE, 'w') as f:
        f.write(f"[{datetime.now()}] CLEARED\n")
    save_json_file(ACTIVITY_FILE, {'events': []})
    return jsonify({'success': True})

# ----- إعدادات المالك -----
@app.route('/api/master/change-username', methods=['POST'])
@master_required
def change_master_username_api():
    global MASTER_USERNAME
    MASTER_USERNAME = request.json['new_username']
    MASTER_CONFIG['master_username'] = MASTER_USERNAME
    save_json_file(MASTER_CONFIG_FILE, MASTER_CONFIG)
    return jsonify({'success': True})

@app.route('/api/master/change-password', methods=['POST'])
@master_required
def change_master_password_api():
    global MASTER_PASSWORD_HASH
    d = request.json
    if hashlib.sha256(d['current_password'].encode()).hexdigest() == MASTER_PASSWORD_HASH:
        MASTER_PASSWORD_HASH = hashlib.sha256(d['new_password'].encode()).hexdigest()
        MASTER_CONFIG['master_password_hash'] = MASTER_PASSWORD_HASH
        save_json_file(MASTER_CONFIG_FILE, MASTER_CONFIG)
        return jsonify({'success': True})
    return jsonify({'success': False})

@app.route('/api/master/change-port', methods=['POST'])
@master_required
def change_port_api():
    try:
        port = int((request.json or {}).get('port', 3177))
    except Exception:
        return jsonify({'success': False, 'error': 'Invalid port'})
    MASTER_CONFIG['port'] = port
    save_json_file(MASTER_CONFIG_FILE, MASTER_CONFIG)
    threading.Thread(target=lambda: (time.sleep(1), os.execv(sys.executable, [sys.executable] + sys.argv))).start()
    return jsonify({'success': True})

@app.route('/api/master/restart', methods=['POST'])
@master_required
def restart_panel_api():
    log_activity(session['username'], 'server.power.restart', 'Panel restart requested')
    threading.Thread(target=lambda: (time.sleep(1), os.execv(sys.executable, [sys.executable] + sys.argv))).start()
    return jsonify({'success': True})


# =============================================================================
# 15)  API routes قسم المالك (Owner Panel)
# =============================================================================

@app.route('/api/owner/config')
@master_required
def owner_config_get():
    cfg = load_owner_config()
    # لا نرسل التوكن كاملاً للأمان
    safe = dict(cfg)
    safe['telegram_token'] = '***' if cfg.get('telegram_token') else ''
    return jsonify(safe)

@app.route('/api/owner/config/save', methods=['POST'])
@master_required
def owner_config_save():
    d = request.json or {}
    cfg = load_owner_config()
    if 'panel_name' in d:
        cfg['panel_name'] = d['panel_name']
    if 'welcome_msg' in d:
        cfg['welcome_msg'] = d['welcome_msg']
    save_json_file(OWNER_CONFIG_FILE, cfg)
    log_activity(session['username'], 'owner.config.save', 'Panel settings updated')
    return jsonify({'success': True})

@app.route('/api/owner/maintenance', methods=['GET', 'POST'])
@login_required
def owner_maintenance_api():
    if request.method == 'GET':
        return jsonify(load_maintenance())
    if session.get('username') != MASTER_USERNAME:
        return jsonify({'success': False, 'error': 'Master only'}), 403
    d = request.json or {}
    maint = load_maintenance()
    if 'enabled' in d:
        maint['enabled'] = bool(d['enabled'])
    if 'message' in d:
        maint['message'] = d['message']
    save_maintenance(maint)
    log_activity(session['username'], 'owner.maintenance', 'enabled='+str(maint['enabled']))
    return jsonify({'success': True, 'enabled': maint['enabled']})

@app.route('/api/owner/stats')
@master_required
def owner_stats_api():
    users = load_users()
    # عد ملفات ZIP في جميع مجلدات المستخدمين
    zip_count = 0
    try:
        for root, dirs, files in os.walk(USERS_FOLDER):
            for f in files:
                if f.lower().endswith('.zip'):
                    zip_count += 1
        # أيضاً في مجلد BASE_PATH
        for f in os.listdir(BASE_PATH):
            if f.lower().endswith('.zip'):
                zip_count += 1
    except Exception:
        pass
    # عد البوتات النشطة
    active_bots = sum(1 for p in file_processes.values() if p['process'].poll() is None)
    # تحديث الإحصائيات
    stats = {
        'total_users': len(users),
        'total_servers': len(users),
        'active_bots': active_bots,
        'zip_files': zip_count,
        'last_updated': datetime.now().isoformat()
    }
    save_json_file(BOT_STATS_FILE, stats)
    return jsonify(stats)

@app.route('/api/owner/bot/link', methods=['POST'])
@master_required
def owner_bot_link():
    d = request.json or {}
    token = d.get('token', '').strip()
    owner_id = d.get('owner_id', '').strip()
    if not token or not owner_id:
        return jsonify({'success': False, 'error': 'Token and owner ID required'})
    # التحقق من صحة التوكن عبر Telegram API
    try:
        resp = requests.get(f'https://api.telegram.org/bot{token}/getMe', timeout=10)
        data = resp.json()
        if not data.get('ok'):
            return jsonify({'success': False, 'error': data.get('description', 'Invalid token')})
        bot_username = data['result'].get('username', 'unknown')
        cfg = load_owner_config()
        cfg['telegram_token'] = token
        cfg['telegram_owner_id'] = owner_id
        cfg['bot_linked'] = True
        cfg['bot_username'] = bot_username
        save_json_file(OWNER_CONFIG_FILE, cfg)
        log_activity(session['username'], 'owner.bot.link', f'Bot @{bot_username} linked')
        return jsonify({'success': True, 'bot_username': bot_username})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/owner/bot/unlink', methods=['POST'])
@master_required
def owner_bot_unlink():
    cfg = load_owner_config()
    cfg['telegram_token'] = ''
    cfg['telegram_owner_id'] = ''
    cfg['bot_linked'] = False
    cfg['bot_username'] = ''
    save_json_file(OWNER_CONFIG_FILE, cfg)
    log_activity(session['username'], 'owner.bot.unlink', 'Bot unlinked')
    return jsonify({'success': True})

@app.route('/api/owner/bot/action', methods=['POST'])
@master_required
def owner_bot_action():
    # تحقق من أن المستخدم هو المالك فقط
    if session.get('username') != MASTER_USERNAME:
        return jsonify({'success': False, 'error': 'Unauthorized: Master only'}), 403
    d = request.json or {}
    action = d.get('action', '')
    cfg = load_owner_config()
    if not cfg.get('bot_linked') or not cfg.get('telegram_token'):
        return jsonify({'success': False, 'error': 'Bot not linked'}), 403
    token = cfg['telegram_token']
    owner_id = cfg['telegram_owner_id']
    messages = {
        'start': '✅ Bot started via panel',
        'stop': '⏹ Bot stopped via panel',
        'restart': '🔄 Bot restarted via panel'
    }
    msg = messages.get(action, f'Action: {action}')
    try:
        requests.post(f'https://api.telegram.org/bot{token}/sendMessage',
                      json={'chat_id': owner_id, 'text': msg}, timeout=10)
        log_activity(session['username'], f'owner.bot.{action}', msg)
        return jsonify({'success': True, 'message': msg})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/owner/bot/cmd', methods=['POST'])
@master_required
def owner_bot_cmd():
    # تحقق من أن المستخدم هو المالك فقط
    if session.get('username') != MASTER_USERNAME:
        return jsonify({'success': False, 'error': 'Unauthorized: Master only'}), 403
    d = request.json or {}
    cmd = d.get('command', '').strip()
    cfg = load_owner_config()
    if not cfg.get('bot_linked'):
        return jsonify({'success': False, 'error': 'Bot not linked'}), 403
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        output = r.stdout + r.stderr
        # إرسال النتيجة عبر تيليجرام
        token = cfg['telegram_token']
        owner_id = cfg['telegram_owner_id']
        requests.post(f'https://api.telegram.org/bot{token}/sendMessage',
                      json={'chat_id': owner_id, 'text': f'🖥 CMD: {cmd}\n📝 Output:\n{output[:3000]}'}, timeout=10)
        log_activity(session['username'], 'owner.bot.cmd', cmd[:100])
        return jsonify({'success': True, 'output': output})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/owner/zips')
@master_required
def owner_list_zips():
    zips = []
    try:
        # مجلد المستخدمين
        for user_dir in os.listdir(USERS_FOLDER):
            user_path = os.path.join(USERS_FOLDER, user_dir)
            if os.path.isdir(user_path):
                for root, dirs, files in os.walk(user_path):
                    for f in files:
                        if f.lower().endswith('.zip'):
                            fp = os.path.join(root, f)
                            zips.append({
                                'name': f,
                                'user': user_dir,
                                'path': fp,
                                'size': f"{os.path.getsize(fp)/1024:.1f} KB"
                            })
        # مجلد BASE_PATH
        for f in os.listdir(BASE_PATH):
            if f.lower().endswith('.zip'):
                fp = os.path.join(BASE_PATH, f)
                zips.append({'name': f, 'user': 'master', 'path': fp, 'size': f"{os.path.getsize(fp)/1024:.1f} KB"})
    except Exception:
        pass
    return jsonify({'zips': zips})

@app.route('/api/owner/zips/download')
@master_required
def owner_download_zip():
    path = request.args.get('path', '')
    if not path or not os.path.exists(path):
        return jsonify({'success': False, 'error': 'File not found'}), 404
    return send_file(path, as_attachment=True)

@app.route('/api/owner/zips/download-all')
@master_required
def owner_download_all_zips():
    import io
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        try:
            for user_dir in os.listdir(USERS_FOLDER):
                user_path = os.path.join(USERS_FOLDER, user_dir)
                if os.path.isdir(user_path):
                    for root, dirs, files in os.walk(user_path):
                        for f in files:
                            if f.lower().endswith('.zip'):
                                fp = os.path.join(root, f)
                                zf.write(fp, os.path.join(user_dir, f))
            for f in os.listdir(BASE_PATH):
                if f.lower().endswith('.zip'):
                    fp = os.path.join(BASE_PATH, f)
                    zf.write(fp, os.path.join('master', f))
        except Exception:
            pass
    buf.seek(0)
    return send_file(buf, as_attachment=True, download_name='all_zips.zip', mimetype='application/zip')

@app.route('/api/owner/zips/delete', methods=['POST'])
@master_required
def owner_delete_zip():
    path = (request.json or {}).get('path', '')
    if not path or not os.path.exists(path):
        return jsonify({'success': False, 'error': 'File not found'})
    try:
        os.remove(path)
        log_activity(session['username'], 'owner.zip.delete', path)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/owner/announcements')
@login_required
def owner_get_announcements():
    return jsonify(load_announcements())

@app.route('/api/owner/announcements/add', methods=['POST'])
@master_required
def owner_add_announcement():
    d = request.json or {}
    text = d.get('text', '').strip()
    if not text:
        return jsonify({'success': False, 'error': 'Empty text'})
    data = load_announcements()
    data['list'].insert(0, {'text': text, 'time': datetime.now().strftime('%Y-%m-%d %H:%M')})
    data['list'] = data['list'][:50]  # احتفظ بآخر 50
    save_announcements(data)
    log_activity(session['username'], 'owner.announce.add', text[:80])
    return jsonify({'success': True})

@app.route('/api/owner/announcements/delete', methods=['POST'])
@master_required
def owner_delete_announcement():
    d = request.json or {}
    idx = d.get('index', -1)
    data = load_announcements()
    try:
        data['list'].pop(int(idx))
        save_announcements(data)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/owner/broadcast', methods=['POST'])
@master_required
def owner_broadcast():
    d = request.json or {}
    msg = d.get('message', '').strip()
    if not msg:
        return jsonify({'success': False, 'error': 'Empty message'})
    cfg = load_owner_config()
    users = load_users()
    count = 0
    if cfg.get('bot_linked') and cfg.get('telegram_token'):
        token = cfg['telegram_token']
        # إرسال للمالك أولاً
        try:
            requests.post(f'https://api.telegram.org/bot{token}/sendMessage',
                          json={'chat_id': cfg['telegram_owner_id'], 'text': f'📡 Broadcast:\n{msg}'}, timeout=10)
            count += 1
        except Exception:
            pass
    # تسجيل الإعلان أيضاً
    data = load_announcements()
    data['list'].insert(0, {'text': f'[BROADCAST] {msg}', 'time': datetime.now().strftime('%Y-%m-%d %H:%M')})
    save_announcements(data)
    log_activity(session['username'], 'owner.broadcast', msg[:80])
    return jsonify({'success': True, 'count': count})

@app.route('/api/owner/action', methods=['POST'])
@master_required
def owner_action_api():
    action = (request.json or {}).get('action', '')
    try:
        if action == 'clear_all_logs':
            with open(LOGS_FILE, 'w') as f:
                f.write(f"[{datetime.now()}] CLEARED BY OWNER\n")
            save_json_file(ACTIVITY_FILE, {'events': []})
        elif action == 'kick_all_users':
            sessions = load_user_sessions()
            for u in list(sessions.keys()):
                if u != MASTER_USERNAME:
                    sessions[u] = 0
            save_user_sessions(sessions)
        elif action == 'reset_stats':
            save_json_file(BOT_STATS_FILE, {'total_users': 0, 'total_servers': 0, 'active_bots': 0, 'zip_files': 0, 'last_updated': ''})
        elif action == 'restart_panel':
            threading.Thread(target=lambda: (time.sleep(1), os.execv(sys.executable, [sys.executable] + sys.argv))).start()
        log_activity(session['username'], f'owner.action.{action}', '')
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# =============================================================================
# 14)  ميزة Multi-Port: تشغيل Sub-servers على بورتات إضافية
# =============================================================================
def run_extra_port(port, note=""):
    """يشغل Flask sub-server على بورت إضافي يقدم نفس اللوحة."""
    try:
        from flask import Flask as _F
        sub = _F(f"sub_{port}")
        @sub.route('/')
        def _h():
            return f"<h1 style='font-family:sans-serif;color:#29c7d3;background:#1f2933;padding:40px;text-align:center'>𝗢𝗠𝗔𝗥 𝗨𝗡𝗟𝗜𝗠𝗜𝗧𝗘𝗗 𝗩𝗣𝗦— Port {port}</h1><p style='color:#9aa9b3;text-align:center'>{html.escape(note)}</p><p style='text-align:center'><a style='color:#2f6fed' href='/'>Open user app here</a></p>"
        sub.run(host='0.0.0.0', port=port, debug=False, threaded=True, use_reloader=False)
    except Exception as e:
        print(f"[port {port}] failed: {e}")

def start_configured_extra_ports():
    for p in load_ports():
        try:
            threading.Thread(target=run_extra_port, args=(int(p['port']), p.get('note','')), daemon=True).start()
        except Exception:
            pass

# =============================================================================
# التشغيل الرئيسي
# =============================================================================
if __name__ == '__main__':
    print(r"""
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║   🔥  𝗢𝗠𝗔𝗥 𝗨𝗡𝗟𝗜𝗠𝗜𝗧𝗘𝗗 𝗩𝗣𝗦 — Lunes Host LLC Style Panel 🔥              ║
║   # 𝚅𝙿𝚂 𝙾𝙼𝙰𝚁                                              ║
║                                                                  ║
║   Master  : {mu:<48} ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
""".format(mu=MASTER_USERNAME))

    # شغّل بورتات إضافية إن وُجدت
    start_configured_extra_ports()

    port = int(os.environ.get('PORT', MASTER_CONFIG.get('port') or 3177))
    print(f"🌐 Panel: http://0.0.0.0:{port}")
    print(f"   Login: {MASTER_USERNAME} / @xAyOuB (default)")
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)