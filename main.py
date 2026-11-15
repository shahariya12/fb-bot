#-----create by siam ---#
#------TG: @SIAMKHANXD--#
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
import json
import re
import uuid
import random
import time
import os
import hashlib
import string
import threading
import csv
import datetime
from concurrent.futures import ThreadPoolExecutor
from flask import Flask, request, jsonify, send_file, render_template_string, session, redirect, url_for

try:
    from curl_cffi import requests as cureq
except ImportError:
    print("\033[91m[!] curl_cffi not found!\033[0m")
    exit()

# ══════════════════════════════════════════════════════════
# SETTINGS (Ekhane tomar details boshao)
# ══════════════════════════════════════════════════════════
BOT_TOKEN = "9025360567:AAEJ2Jq2FSAVpDOVC3UCPYViQE9-sNI7NSk" 
ADMIN_ID = "6408202140" # <--- Tomar Telegram ID ekhane boshao
WEB_PASSWORD = "SOHAV_ADMIN"
bot = telebot.TeleBot(BOT_TOKEN)

# Auth File for Resellers
AUTH_FILE = "authorized_users.txt"

def load_auth_users():
    if os.path.exists(AUTH_FILE):
        with open(AUTH_FILE, 'r') as f:
            return [line.strip() for line in f if line.strip()]
    return []

def save_auth_user(user_id):
    users = load_auth_users()
    if str(user_id) not in users:
        with open(AUTH_FILE, 'a') as f:
            f.write(f"{user_id}\n")

def remove_auth_user(user_id):
    users = load_auth_users()
    if str(user_id) in users:
        users.remove(str(user_id))
        with open(AUTH_FILE, 'w') as f:
            for u in users:
                f.write(f"{u}\n")

def is_authorized(chat_id):
    if str(chat_id) == ADMIN_ID: return True
    return str(chat_id) in load_auth_users()

# ══════════════════════════════════════════════════════════
# FLASK WEB SERVER SETUP
# ══════════════════════════════════════════════════════════
app = Flask('')
app.secret_key = "SOHAV_SECRET_KEY_123"
WEB_LOGS = []
IS_RUNNING = False
WEB_STATE = {"total": 0, "success": 0, "current": 0}

def add_web_log(msg, color="white"):
    global WEB_LOGS
    t = datetime.datetime.now().strftime("%H:%M:%S")
    WEB_LOGS.append({"time": t, "msg": msg, "color": color})
    if len(WEB_LOGS) > 100: WEB_LOGS.pop(0)

# ══════════════════════════════════════════════════════════
# CONSTANTS & FILES
# ══════════════════════════════════════════════════════════
FB_REG_BASE = "https://limited.facebook.com"
GRAPHQL_URL = "https://web.facebook.com/api/graphql/"
CSV_FILE = "fb_accounts.csv"
FAILED_CSV_FILE = "failed_accounts.csv"
PROXY_FILE = "proxies.txt" 

file_lock = threading.Lock()

# ══════════════════════════════════════════════════════════
# DOMAIN TO LANGUAGE MAP
# ══════════════════════════════════════════════════════════
DOMAIN_LANG_MAP = {
    '.de': 'de', '.fr': 'fr', '.uk': 'gb', '.br': 'br', '.es': 'es', '.mx': 'mx',
    '.it': 'it', '.ru': 'ru', '.in': 'in', '.pk': 'pk', '.bd': 'bd', '.id': 'id',
    '.tr': 'tr', '.ph': 'ph', '.ng': 'ng', '.eg': 'eg', '.za': 'za', '.ca': 'ca',
    '.au': 'au', '.nl': 'nl', '.pl': 'pl', '.se': 'se', '.vn': 'vn', '.th': 'th'
}

def get_lang_from_email(email_str):
    email = email_str.split('|')[0].strip()
    domain = email.split('@')[-1].lower() if '@' in email else ""
    if domain.endswith('.com'): return None 
    for tld, lang in DOMAIN_LANG_MAP.items():
        if domain.endswith(tld): return lang
    return None

# ══════════════════════════════════════════════════════════
# CSV SAVERS
# ══════════════════════════════════════════════════════════
def save_to_csv(uid, cookie, full_combo):
    try:
        with file_lock:
            file_exists = os.path.isfile(CSV_FILE)
            with open(CSV_FILE, mode='a', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                if not file_exists or os.path.getsize(CSV_FILE) == 0:
                    writer.writerow(['UID', 'COOKIE', 'MAIL_COMBO'])
                writer.writerow([uid, cookie, full_combo])
        return True
    except Exception as e: return False

def save_failed_to_csv(full_combo, reason):
    try:
        with file_lock:
            file_exists = os.path.isfile(FAILED_CSV_FILE)
            with open(FAILED_CSV_FILE, mode='a', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                if not file_exists or os.path.getsize(FAILED_CSV_FILE) == 0:
                    writer.writerow(['MAIL_COMBO', 'REASON'])
                writer.writerow([full_combo, reason])
        return True
    except Exception as e: return False

def get_csv_stats():
    success = 0; failed = 0
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, 'r', encoding='utf-8-sig') as f: success = sum(1 for line in f) - 1
    if os.path.exists(FAILED_CSV_FILE):
        with open(FAILED_CSV_FILE, 'r', encoding='utf-8-sig') as f: failed = sum(1 for line in f) - 1
    return max(0, success), max(0, failed)

# ══════════════════════════════════════════════════════════
# PROXY & CORE LOGIC
# ══════════════════════════════════════════════════════════
def load_proxies():
    if os.path.exists(PROXY_FILE):
        with open(PROXY_FILE, 'r') as f:
            return [l.strip() for l in f if l.strip() and ':' in l]
    return []

def get_random_proxy():
    proxies = load_proxies()
    if not proxies: return None
    p = random.choice(proxies).split(':')
    if len(p) == 4: return {'http': f'http://{p[2]}:{p[3]}@{p[0]}:{p[1]}', 'https': f'http://{p[2]}:{p[3]}@{p[0]}:{p[1]}'}
    elif len(p) == 2: return {'http': f'http://{p[0]}:{p[1]}', 'https': f'http://{p[0]}:{p[1]}'}
    return None

LANG_MAP = {
    'us': ('en-US,en;q=0.9', 'America/New_York'), 'gb': ('en-GB,en;q=0.9', 'Europe/London'),
    'de': ('de-DE,de;q=0.9,en;q=0.8', 'Europe/Berlin'), 'bd': ('bn-BD,bn;q=0.9,en;q=0.8', 'Asia/Dhaka'),
    'id': ('id-ID,id;q=0.9,en;q=0.8', 'Asia/Jakarta'), 'fr': ('fr-FR,fr;q=0.9,en;q=0.8', 'Europe/Paris'),
    'es': ('es-ES,es;q=0.9,en;q=0.8', 'Europe/Madrid'), 'mx': ('es-MX,es;q=0.9,en;q=0.8', 'America/Mexico_City'),
    'br': ('pt-BR,pt;q=0.9,en;q=0.8', 'America/Sao_Paulo'), 'ru': ('ru-RU,ru;q=0.9,en;q=0.8', 'Europe/Moscow'),
    'it': ('it-IT,it;q=0.9,en;q=0.8', 'Europe/Rome'), 'ar': ('ar-SA,ar;q=0.9,en;q=0.8', 'Asia/Riyadh'),
    'pk': ('ur-PK,ur;q=0.9,en;q=0.8', 'Asia/Karachi'), 'ph': ('en-PH,en;q=0.9', 'Asia/Manila'),
    'tr': ('tr-TR,tr;q=0.9,en;q=0.8', 'Europe/Istanbul'), 'in': ('hi-IN,hi;q=0.9,en;q=0.8', 'Asia/Kolkata'),
    'ng': ('en-NG,en;q=0.9', 'Africa/Lagos'), 'eg': ('ar-EG,ar;q=0.9,en;q=0.8', 'Africa/Cairo'),
    'za': ('en-ZA,en;q=0.9', 'Africa/Johannesburg'), 'ca': ('en-CA,en;q=0.9', 'America/Toronto'),
    'au': ('en-AU,en;q=0.9', 'Australia/Sydney'), 'nl': ('nl-NL,nl;q=0.9,en;q=0.8', 'Europe/Amsterdam'),
    'pl': ('pl-PL,pl;q=0.9,en;q=0.8', 'Europe/Warsaw'), 'se': ('sv-SE,sv;q=0.9,en;q=0.8', 'Europe/Stockholm'),
    'vn': ('vi-VN,vi;q=0.9,en;q=0.8', 'Asia/Ho_Chi_Minh'), 'th': ('th-TH,th;q=0.9,en;q=0.8', 'Asia/Bangkok')
}
CURRENT_LANG_HEADER = "en-US,en;q=0.9"

# NAME LISTS
DEFAULT_FIRST_NAMES = ['Arafat', 'Rakib', 'Sabbir', 'Nayeem', 'Rifat', 'Tanvir', 'Shakib', 'Sajid', 'John', 'David', 'Michael', 'James']
DEFAULT_LAST_NAMES = ['Hossain', 'Ahmed', 'Khan', 'Islam', 'Rahman', 'Sarker', 'Smith', 'Johnson', 'Williams', 'Brown']
GERMAN_FIRST_NAMES = ["Alexander", "Andreas", "Anna", "Anja", "Anke", "Anton", "Armin", "Axel", "Barbara", "Bastian", "Benedikt", "Benjamin", "Bernd", "Birgit", "Björn", "Brigitte", "Bruno", "Carina", "Carla", "Charlotte", "Christian", "Christina", "Christof", "Claudia", "Claus", "Cornelia", "Daniel", "Daniela", "David", "Dennis"]
GERMAN_LAST_NAMES = ["Albrecht", "Arnold", "Bachmann", "Bauer", "Baumann", "Becker", "Beckmann", "Berger", "Bergmann", "Böhm", "Brandt", "Braun", "Brinker", "Brunner", "Busch", "Dietrich", "Dörfler", "Dreher", "Ebert", "Eckert", "Engel", "Esser", "Falk", "Faust", "Fischer", "Fleischer", "Frank", "Franz", "Frey", "Fuchs"]
PORTUGUESE_FIRST_NAMES = ["Miguel", "Arthur", "Gael", "Théo", "Heitor", "Ravi", "Davi", "Bernardo", "Noah", "Gabriel", "Samuel", "Pedro", "Anthony", "Lucas", "Benjamin", "Matheus", "Joaquim", "Nicolas", "Lorenzo", "Henrique", "João", "Rafael", "Enzo", "Murilo", "Benício", "Gustavo", "Guilherme", "Emanuel", "Felipe", "Bryan", "Daniel", "Vitor", "Leonardo", "Bruno", "Thiago", "Vicente", "Carlos", "Eduardo", "André", "Fernando"]
PORTUGUESE_LAST_NAMES = ["Silva", "Santos", "Oliveira", "Souza", "Rodrigues", "Ferreira", "Alves", "Pereira", "Lima", "Gomes", "Costa", "Ribeiro", "Martins", "Carvalho", "Almeida", "Lopes", "Soares", "Fernandes", "Vieira", "Barbosa", "Rocha", "Dias", "Nascimento", "Andrade", "Moreira", "Nunes", "Marques", "Machado", "Mendes", "Freitas"]
FRENCH_FIRST_NAMES = ["Jean", "Pierre", "Michel", "André", "Philippe", "Louis", "Nicolas", "François", "Alain", "Julien", "Bernard", "Marcel", "Daniel", "Paul", "Gérard", "Robert", "Patrick", "Henri", "Jacques", "Claude", "Éric", "Christian", "Georges", "René", "Pascal", "David", "Olivier", "Laurent", "Stéphane", "Thierry", "Thomas", "Sébastien", "Alexandre", "Vincent", "Christophe", "Maxime", "Jérôme", "Frédéric", "Xavier", "Fabrice", "Mathieu", "Antoine", "Romain", "Benjamin", "Guillaume", "Damien", "Yves", "Hugo", "Lucas", "Jules", "Léo", "Gabriel", "Raphaël", "Arthur", "Nathan", "Ethan", "Enzo", "Mathis", "Noah", "Tom"]
FRENCH_LAST_NAMES = ["Martin", "Bernard", "Thomas", "Petit", "Robert", "Richard", "Durand", "Dubois", "Moreau", "Laurent", "Simon", "Michel", "Lefebvre", "Leroy", "Roux", "David", "Bertrand", "Morel", "Fournier", "Girard", "Bonnet", "Dupont", "Lambert", "Fontaine", "Rousseau", "Vincent", "Muller", "Lefevre", "Faure", "Andre", "Mercier", "Blanc", "Guerin", "Boyer", "Garnier", "Chevalier", "Francois", "Legrand", "Gauthier", "Garcia", "Perrin", "Robin", "Clement", "Morin", "Nicolas", "Henry", "Roussel", "Mathieu", "Gautier", "Masson", "Marchand", "Duval", "Denis", "Dumont", "Marie", "Lemaire", "Noel", "Meyer", "Dufour", "Meunier"]

USER_AGENTS = [
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1"
]
SCREEN_PROFILES = [(390, 844, 3.0), (393, 852, 3.0), (428, 926, 3.0), (430, 932, 3.0), (375, 812, 3.0)]

def build_fingerprint():
    ua = random.choice(USER_AGENTS)
    sw, sh, dpr = random.choice(SCREEN_PROFILES)
    pringer_hash = hashlib.sha256(f"{ua}-{sw}x{sh}-{uuid.uuid4()}".encode()).hexdigest()[:32]
    return {
        "impersonate": "safari15_5", "pringer": pringer_hash,
        "headers": {
            "User-Agent": ua, "Accept-Language": CURRENT_LANG_HEADER,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "sec-fetch-site": "same-origin", "sec-fetch-mode": "navigate", "sec-fetch-dest": "document",
        }
    }

def build_cookie_header(cookies):
    order = ['datr', 'sb', 'm_pixel_ratio', 'wd', 'c_user', 'fr', 'xs']
    parts = [f"{k}={cookies[k]}" for k in order if k in cookies]
    parts.extend(f"{k}={v}" for k, v in cookies.items() if k not in order)
    return '; '.join(parts)

def warmup_session(session, fp, proxy):
    steps = ["https://www.facebook.com/", f"{FB_REG_BASE}/reg/?cid=103"]
    collected, last_lsd = {}, "AdS-QY2mYrCcHP7sVf7ynTA6vTc"
    for url in steps:
        try:
            r = session.get(url, headers=fp["headers"], impersonate=fp["impersonate"], proxies=proxy, timeout=20)
            time.sleep(random.uniform(1.5, 3.5))
            collected.update(session.cookies.get_dict())
            m = re.search(r'"LSD",\[\],\{"token":"([^"]+)"', r.text)
            if m: last_lsd = m.group(1)
        except: time.sleep(1)
    return collected, last_lsd

def fb_create_account(email, password, lang_code, custom_fname, custom_lname, use_proxy):
    session = cureq.Session()
    proxy = get_random_proxy() if use_proxy else None
    
    fp = build_fingerprint()
    cookies_warm, lsd_token = warmup_session(session, fp, proxy)
    time.sleep(random.uniform(2.0, 4.0))

    reg_fp = build_fingerprint()
    try:
        r = session.get(f"{FB_REG_BASE}/reg/?cid=103", headers=reg_fp["headers"], impersonate=reg_fp["impersonate"], proxies=proxy, timeout=20)
        m = re.search(r'"LSD",\[\],\{"token":"([^"]+)"', r.text)
        lsd = m.group(1) if m else lsd_token
        
        if custom_fname and custom_lname: firstname, lastname = custom_fname, custom_lname
        elif lang_code == 'de': firstname, lastname = random.choice(GERMAN_FIRST_NAMES), random.choice(GERMAN_LAST_NAMES)
        elif lang_code == 'br': firstname, lastname = random.choice(PORTUGUESE_FIRST_NAMES), random.choice(PORTUGUESE_LAST_NAMES)
        elif lang_code == 'fr': firstname, lastname = random.choice(FRENCH_FIRST_NAMES), random.choice(FRENCH_LAST_NAMES)
        else: firstname, lastname = random.choice(DEFAULT_FIRST_NAMES), random.choice(DEFAULT_LAST_NAMES)
        
        data = {
            'ccp': '2', 'reg_instance': str(uuid.uuid4()).replace('-', '')[:24],
            'submission_request': 'true', 'reg_impression_id': str(uuid.uuid4()),
            'field_names[0]': 'firstname', 'firstname': firstname,
            'lastname': lastname, 'field_names[1]': 'birthday_wrapper',
            'birthday_day': str(random.randint(1, 28)), 'birthday_month': str(random.randint(1, 12)), 'birthday_year': str(random.randint(1995, 2005)),
            'field_names[2]': 'reg_email__', 'reg_email__': email,
            'field_names[3]': 'sex', 'sex': str(random.choice(['1', '2'])), 
            'field_names[4]': 'reg_passwd__', 'reg_passwd__': password,
            'submit': 'Sign up', 'lsd': lsd, 'jazoest': '24979', '__req': '7', '__fmt': '1',
        }

        headers = dict(reg_fp["headers"])
        headers.update({
            'Content-Type': 'application/x-www-form-urlencoded', 'x-response-format': 'JSONStream',
            'x-asbd-id': '359341', 'x-requested-with': 'XMLHttpRequest', 'origin': FB_REG_BASE,
            'referer': f"{FB_REG_BASE}/reg/?cid=103", 'x-fb-lsd': lsd, "Cookie": build_cookie_header(cookies_warm)
        })

        time.sleep(random.uniform(3.0, 6.0))
        r = session.post(f"{FB_REG_BASE}/reg/submit/?app_id=103&multi_step_form=1", headers=headers, data=data, impersonate=reg_fp["impersonate"], proxies=proxy, timeout=30)
    except Exception as e:
        return (None, f'POST_FAIL (Check Proxy/Net)')

    cookies = session.cookies.get_dict()
    uid = cookies.get('c_user')
    if uid:
        merged = dict(cookies_warm); merged.update(cookies)
        return ({'firstname': firstname, 'lastname': lastname, 'email': email, 'password': password, 'uid': uid, 'cookie': build_cookie_header(merged), 'session': session, 'proxy': proxy}, None)
    
    body = r.text.lower()
    if 'checkpoint' in body: return (None, 'CHECKPOINT (Use Proxy / Change Email)')
    if 'already' in body: return (None, 'TAKEN (Email exists)')
    return (None, 'FAILED')

def resend_otp(session, uid, proxy):
    try:
        r = session.get("https://web.facebook.com/confirmemail.php?next=undefined", proxies=proxy, timeout=20)
        lsd = re.search(r'"LSD",\[\],\{"token":"([^"]+)"', r.text)
        lsd = lsd.group(1) if lsd else ""
        dtsg = re.search(r'"DTSGInitialData",\[\],\{"token":"([^"]+)"', r.text) or re.search(r'name="fb_dtsg"\s+value="([^"]+)"', r.text)
        fb_dtsg = dtsg.group(1) if dtsg else ""
        
        if not lsd or not fb_dtsg: return False
        headers = {'host': 'web.facebook.com', 'content-type': 'application/x-www-form-urlencoded', 'x-fb-lsd': lsd, 'origin': 'https://web.facebook.com'}
        variables = json.dumps({"input": {"actor_id": str(uid), "client_mutation_id": str(uuid.uuid4()), "machine_id": ""}}, separators=(',', ':'))
        data = {'av': str(uid), '__user': str(uid), 'fb_dtsg': fb_dtsg, 'lsd': lsd, 'variables': variables, 'doc_id': '9554972464608847'}
        res = session.post(GRAPHQL_URL, headers=headers, data=data, proxies=proxy, timeout=20)
        return (res.status_code == 200 and "errors" not in res.text)
    except Exception: return False

def execute_batch(chat_id, email_data_list, password, lang, custom_name, use_proxy, is_web=False):
    global IS_RUNNING, WEB_STATE
    IS_RUNNING = True
    success_count = 0; fail_count = 0
    WEB_STATE["total"] = len(email_data_list); WEB_STATE["success"] = 0
    
    def process_one(item, idx, total):
        nonlocal success_count, fail_count
        WEB_STATE["current"] = idx
        email = item['email']; full_combo = item['full_combo']
        c_fname = custom_name[0] if custom_name else None; c_lname = custom_name[1] if custom_name else None
        
        status_msg = None
        if not is_web and chat_id: status_msg = bot.send_message(chat_id, f"⏳ [{idx}/{total}] Processing: `{email}`", parse_mode='Markdown')
        else: add_web_log(f"[{idx}/{total}] Processing: {email}", "cyan")
        
        res, err = fb_create_account(email, password, lang, c_fname, c_lname, use_proxy)
        
        if res:
            success_count += 1; WEB_STATE["success"] = success_count
            csv_ok = save_to_csv(res['uid'], res['cookie'], full_combo)
            csv_status = "✅ Saved to CSV" if csv_ok else "⚠️ CSV Save Failed"
            msg_text = f"✅ **ACCOUNT CREATED!**\n\n📧 Email Combo: `{full_combo}`\n👤 Name: `{res['firstname']} {res['lastname']}`\n🆔 UID: `{res['uid']}`\n🔑 FB Password: `{password}`\n\n🍪 Cookie: `{res['cookie']}`\n\n{csv_status}"
            
            if not is_web and chat_id: bot.edit_message_text(msg_text, chat_id=chat_id, message_id=status_msg.message_id, parse_mode='Markdown')
            else: add_web_log(f"[+] SUCCESS: {email} | UID: {res['uid']}", "green")
            resend_otp(res['session'], res['uid'], res['proxy'])
        else:
            fail_count += 1
            save_failed_to_csv(full_combo, err)
            fail_text = f"❌ `{email}` Failed: {err}"
            if not is_web and chat_id: bot.edit_message_text(fail_text, chat_id=chat_id, message_id=status_msg.message_id, parse_mode='Markdown')
            else: add_web_log(fail_text, "red")

    with ThreadPoolExecutor(max_workers=len(email_data_list)) as executor:
        futures = [executor.submit(process_one, item, i+1, len(email_data_list)) for i, item in enumerate(email_data_list)]
        for future in futures: future.result()

    IS_RUNNING = False
    finish_msg = f"🎉 **Batch Finished!**\n\n✅ Total Success: {success_count}\n❌ Total Failed: {fail_count}\n\n👉 _Type /start to open menu again._"
    
    # Keyboard Remove & Only Show Result
    if not is_web and chat_id: 
        bot.send_message(chat_id, finish_msg, parse_mode='Markdown', reply_markup=ReplyKeyboardRemove())
    else: 
        add_web_log(f"Finished! Success: {success_count}, Failed: {fail_count}", "yellow")

# ══════════════════════════════════════════════════════════
# WEB DASHBOARD
# ══════════════════════════════════════════════════════════
LOGIN_TEMPLATE = """
<!DOCTYPE html><html><body style="background:#0f172a; color:white; text-align:center; padding-top:100px; font-family:sans-serif;">
<h2>🔒 Admin Login</h2>
<form method="POST">
    <input type="password" name="password" placeholder="Enter Password" style="padding:10px; border-radius:5px; border:none;"><br><br>
    <button type="submit" style="padding:10px 20px; background:#0ea5e9; border:none; color:white; border-radius:5px; font-weight:bold;">LOGIN</button>
</form>
{% if error %}<p style="color:red;">{{ error }}</p>{% endif %}
</body></html>
"""

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>FB Auto Creator Admin</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0f172a; color: #e2e8f0; padding: 20px; margin: 0; }
        .container { max-width: 800px; margin: auto; background: #1e293b; padding: 20px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.5); }
        h2 { color: #38bdf8; text-align: center; }
        label { font-size: 14px; color: #94a3b8; margin-bottom: 5px; display: block; }
        textarea, input, select { width: 100%; padding: 10px; margin-bottom: 15px; background: #0f172a; color: #e2e8f0; border: 1px solid #334155; border-radius: 6px; box-sizing: border-box; }
        .btn { width: 100%; padding: 12px; background: #0ea5e9; color: white; border: none; border-radius: 6px; font-weight: bold; cursor: pointer; font-size: 16px; }
        .btn:hover { background: #0284c7; }
        .btn:disabled { background: #475569; cursor: not-allowed; }
        .btn-row { display: flex; gap: 10px; margin-bottom: 15px; }
        .btn-row a { flex: 1; text-align: center; padding: 10px; background: #10b981; color: white; text-decoration: none; border-radius: 6px; font-weight: bold; }
        .btn-row a.fail { background: #ef4444; }
        #logs { background: #0f172a; height: 300px; overflow-y: auto; padding: 10px; border-radius: 6px; font-family: monospace; font-size: 13px; border: 1px solid #334155; }
        .log-line { margin-bottom: 4px; }
        .cyan { color: #22d3ee; } .green { color: #4ade80; } .red { color: #f87171; } .yellow { color: #fbbf24; } .white { color: #e2e8f0; }
        .status-bar { background: #334155; padding: 10px; border-radius: 6px; margin-bottom: 15px; font-weight: bold; text-align: center; }
    </style>
</head>
<body>
<div class="container">
    <h2>🚀 Admin Dashboard</h2>
    <div class="status-bar" id="status">Status: Idle</div>

    <label>Emails / Combos (One per line)</label>
    <textarea id="emails" rows="4" placeholder="email|password|refresh_token|client_id&#10;email2@domain.com"></textarea>

    <label>Password Mode</label>
    <select id="passMode" onchange="togglePass()">
        <option value="fix">Fix Password (SOHAVdd)</option>
        <option value="custom">Custom Password</option>
    </select>
    <input type="text" id="customPass" placeholder="Enter Custom Password" style="display:none;">

    <label>Proxy Mode</label>
    <select id="proxyMode">
        <option value="no">No Proxy (Direct)</option>
        <option value="yes">Use Proxy (Auto from file)</option>
    </select>

    <label>Name Mode</label>
    <select id="nameMode" onchange="toggleName()">
        <option value="auto">Auto Name</option>
        <option value="custom">Custom Name</option>
    </select>
    <input type="text" id="customName" placeholder="Firstname Lastname" style="display:none;">

    <label>Language</label>
    <select id="lang">
        <option value="de">German (DE)</option>
        <option value="fr">French (FR)</option>
        <option value="br">Portuguese (BR)</option>
        <option value="us">English (US)</option>
    </select>

    <button class="btn" id="startBtn" onclick="startBatch()">START PROCESS</button>

    <div class="btn-row" style="margin-top: 15px;">
        <a href="/download/success">Download Success CSV</a>
        <a href="/download/failed" class="fail">Download Failed CSV</a>
    </div>

    <label style="margin-top: 15px;">Live Logs</label>
    <div id="logs"></div>
</div>

<script>
    function togglePass() {
        document.getElementById('customPass').style.display = document.getElementById('passMode').value === 'custom' ? 'block' : 'none';
    }
    function toggleName() {
        document.getElementById('customName').style.display = document.getElementById('nameMode').value === 'custom' ? 'block' : 'none';
    }

    async function startBatch() {
        const rawEmails = document.getElementById('emails').value.trim();
        if (!rawEmails) return alert("Please enter emails!");
        
        const passMode = document.getElementById('passMode').value;
        const customPass = document.getElementById('customPass').value;
        const proxyMode = document.getElementById('proxyMode').value;
        const nameMode = document.getElementById('nameMode').value;
        const customName = document.getElementById('customName').value;
        const lang = document.getElementById('lang').value;

        document.getElementById('startBtn').disabled = true;
        document.getElementById('logs').innerHTML = '';

        const res = await fetch('/api/start', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                emails: rawEmails.split('\\n').map(e => e.trim()).filter(e => e),
                pass_mode: passMode,
                custom_pass: customPass,
                proxy_mode: proxyMode,
                name_mode: nameMode,
                custom_name: customName,
                lang: lang
            })
        });
        
        if (!res.ok) {
            alert("Error starting batch");
            document.getElementById('startBtn').disabled = false;
        }
    }

    setInterval(async () => {
        const res = await fetch('/api/status');
        const data = await res.json();
        
        if (data.is_running) {
            document.getElementById('status').innerText = `Status: Running (${data.success}/${data.total})`;
        } else {
            document.getElementById('status').innerText = "Status: Idle";
            document.getElementById('startBtn').disabled = false;
        }

        const logsDiv = document.getElementById('logs');
        if (data.logs.length > 0) {
            logsDiv.innerHTML = data.logs.map(l => `<div class="log-line ${l.color}">[${l.time}] ${l.msg}</div>`).join('');
            logsDiv.scrollTop = logsDiv.scrollHeight;
        }
    }, 2000);
</script>
</body>
</html>
"""

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('password') == WEB_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('home'))
        return render_template_string(LOGIN_TEMPLATE, error="Wrong Password")
    return render_template_string(LOGIN_TEMPLATE)

@app.route('/')
def home():
    if not session.get('logged_in'): return redirect(url_for('login'))
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/status')
def get_status():
    if not session.get('logged_in'): return jsonify({"error": "Unauthorized"}), 401
    return jsonify({"is_running": IS_RUNNING, "success": WEB_STATE["success"], "total": WEB_STATE["total"], "logs": WEB_LOGS})

@app.route('/api/start', methods=['POST'])
def api_start():
    global IS_RUNNING, WEB_LOGS
    if not session.get('logged_in'): return jsonify({"error": "Unauthorized"}), 401
    if IS_RUNNING: return jsonify({"error": "Already running"}), 400
    
    data = request.json
    raw_emails = data.get('emails', [])
    if not raw_emails: return jsonify({"error": "No emails"}), 400
    
    email_data_list = []
    for line in raw_emails:
        email = line.split('|')[0].strip()
        if '@' in email: email_data_list.append({"email": email, "full_combo": line})
    
    if not email_data_list: return jsonify({"error": "No valid emails"}), 400
    
    if data['pass_mode'] == 'fix':
        tz = datetime.timezone(datetime.timedelta(hours=6))
        password = f"SOHAV{datetime.datetime.now(tz).day}"
    else:
        password = data.get('custom_pass', '')
        if not password: return jsonify({"error": "Password required"}), 400

    use_proxy = data['proxy_mode'] == 'yes'
    custom_name = None
    if data['name_mode'] == 'custom' and data.get('custom_name'):
        parts = data['custom_name'].split(' ')
        if len(parts) >= 2: custom_name = (parts[0], " ".join(parts[1:]))
        
    lang = data.get('lang', 'us')
    WEB_LOGS = [] 
    add_web_log(f"Starting process for {len(email_data_list)} accounts...", "cyan")
    threading.Thread(target=execute_batch, args=(None, email_data_list, password, lang, custom_name, use_proxy, True)).start()
    return jsonify({"status": "started"})

@app.route('/download/success')
def download_success():
    if not session.get('logged_in'): return redirect(url_for('login'))
    if os.path.exists(CSV_FILE): return send_file(CSV_FILE, as_attachment=True)
    return "File not found", 404

@app.route('/download/failed')
def download_failed():
    if not session.get('logged_in'): return redirect(url_for('login'))
    if os.path.exists(FAILED_CSV_FILE): return send_file(FAILED_CSV_FILE, as_attachment=True)
    return "File not found", 404

# ══════════════════════════════════════════════════════════
# TELEGRAM BOT LOGIC
# ══════════════════════════════════════════════════════════
user_states = {}

def get_main_menu(chat_id):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton('🚀 Create Account'))
    markup.add(KeyboardButton('📁 Download Success'), KeyboardButton('❌ Download Failed'))
    if str(chat_id) == ADMIN_ID:
        markup.add(KeyboardButton('⚙️ Admin Panel'))
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    if not is_authorized(chat_id):
        return bot.reply_to(message, "⛔ **Access Denied!**\n\nYou are not authorized to use this bot. Please contact the admin to get access.")
    
    # Show User ID on start
    bot.reply_to(message, f"Welcome to FB Auto Creator Bot! 🤖\n\n🆔 **Your Telegram ID:** `{chat_id}`\n\nBot ready. Click below to start.", reply_markup=get_main_menu(chat_id), parse_mode='Markdown')

@bot.message_handler(commands=['adduser'])
def add_user(message):
    if str(message.chat.id) != ADMIN_ID: return
    try:
        user_id = message.text.split(' ')[1]
        save_auth_user(user_id)
        bot.reply_to(message, f"✅ User `{user_id}` has been granted access!", parse_mode='Markdown')
    except IndexError:
        bot.reply_to(message, "Usage: `/adduser 123456789`", parse_mode='Markdown')

@bot.message_handler(commands=['removeuser'])
def remove_user(message):
    if str(message.chat.id) != ADMIN_ID: return
    try:
        user_id = message.text.split(' ')[1]
        remove_auth_user(user_id)
        bot.reply_to(message, f"✅ User `{user_id}` access revoked!", parse_mode='Markdown')
    except IndexError:
        bot.reply_to(message, "Usage: `/removeuser 123456789`", parse_mode='Markdown')

@bot.message_handler(commands=['users'])
def list_users(message):
    if str(message.chat.id) != ADMIN_ID: return
    users = load_auth_users()
    if not users: return bot.reply_to(message, "No authorized users yet.")
    msg = "👥 **Authorized Users:**\n" + "\n".join([f"- `{u}`" for u in users])
    bot.reply_to(message, msg, parse_mode='Markdown')

@bot.message_handler(commands=['admin'])
@bot.message_handler(func=lambda message: message.text == '⚙️ Admin Panel')
def admin_panel(message):
    chat_id = message.chat.id
    if str(chat_id) != ADMIN_ID: return bot.reply_to(message, "❌ You are not an admin.")
        
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton('📊 Stats'), KeyboardButton('🔌 Proxy Count'))
    markup.add(KeyboardButton('🗑 Clear Success CSV'), KeyboardButton('🗑 Clear Failed CSV'))
    markup.add(KeyboardButton('🔙 Back to Menu'))
    bot.send_message(chat_id, "⚙️ **Admin Panel**\nSelect an option:", reply_markup=markup, parse_mode='Markdown')

@bot.message_handler(func=lambda message: message.text in ['📊 Stats', '🔌 Proxy Count', '🗑 Clear Success CSV', '🗑 Clear Failed CSV', '🔙 Back to Menu'])
def admin_actions(message):
    chat_id = message.chat.id
    if str(chat_id) != ADMIN_ID: return
    
    if message.text == '📊 Stats':
        success, failed = get_csv_stats()
        bot.send_message(chat_id, f"📊 **Bot Statistics**\n\n✅ Total Success: {success}\n❌ Total Failed: {failed}", reply_markup=ReplyKeyboardRemove())
    elif message.text == '🔌 Proxy Count':
        bot.send_message(chat_id, f"🔌 Loaded Proxies: {len(load_proxies())}", reply_markup=ReplyKeyboardRemove())
    elif message.text == '🗑 Clear Success CSV':
        if os.path.exists(CSV_FILE): os.remove(CSV_FILE)
        bot.send_message(chat_id, "✅ Success CSV Cleared!", reply_markup=ReplyKeyboardRemove())
    elif message.text == '🗑 Clear Failed CSV':
        if os.path.exists(FAILED_CSV_FILE): os.remove(FAILED_CSV_FILE)
        bot.send_message(chat_id, "✅ Failed CSV Cleared!", reply_markup=ReplyKeyboardRemove())
    elif message.text == '🔙 Back to Menu':
        bot.send_message(chat_id, "Back to main menu.", reply_markup=get_main_menu(chat_id))

@bot.message_handler(commands=['getcsv'])
@bot.message_handler(func=lambda message: message.text == '📁 Download Success')
def send_csv(message):
    chat_id = message.chat.id
    if not is_authorized(chat_id): return
    if os.path.exists(CSV_FILE):
        try:
            with open(CSV_FILE, 'rb') as f: bot.send_document(chat_id, f, caption="Here is your SUCCESS accounts CSV.")
        except Exception as e: bot.send_message(chat_id, f"Error reading file: {e}")
    else: bot.send_message(chat_id, "❌ No Success CSV found. Create accounts first!")

@bot.message_handler(commands=['getfailed'])
@bot.message_handler(func=lambda message: message.text == '❌ Download Failed')
def send_failed_csv(message):
    chat_id = message.chat.id
    if not is_authorized(chat_id): return
    if os.path.exists(FAILED_CSV_FILE):
        try:
            with open(FAILED_CSV_FILE, 'rb') as f: bot.send_document(chat_id, f, caption="Here is your FAILED accounts CSV.")
        except Exception as e: bot.send_message(chat_id, f"Error reading file: {e}")
    else: bot.send_message(chat_id, "❌ No Failed CSV found. Everything might be successful!")

@bot.message_handler(commands=['create'])
@bot.message_handler(func=lambda message: message.text == '🚀 Create Account')
def start_creation(message):
    chat_id = message.chat.id
    if not is_authorized(chat_id): return
    if IS_RUNNING: return bot.send_message(chat_id, "⚠️ A process is already running! Please wait.")
    user_states[chat_id] = {'step': 'emails'}
    bot.send_message(chat_id, "📧 Paste your emails or combos (one per line):", reply_markup=ReplyKeyboardRemove())

@bot.message_handler(func=lambda message: True)
def handle_inputs(message):
    chat_id = message.chat.id
    if not is_authorized(chat_id): return
    if chat_id not in user_states: return
    state = user_states[chat_id]

    if state['step'] == 'emails':
        raw_lines = [l.strip() for l in message.text.split('\n') if l.strip()]
        email_data_list = []
        for line in raw_lines:
            email = line.split('|')[0].strip()
            if '@' in email: email_data_list.append({"email": email, "full_combo": line})
                
        if not email_data_list: return bot.send_message(chat_id, "❌ Invalid format. Send valid emails.")
        state['email_data_list'] = email_data_list
        auto_lang = get_lang_from_email(email_data_list[0]['email'])
        state['auto_lang'] = auto_lang
        state['step'] = 'password_mode'
        msg = f"✅ Got {len(email_data_list)} emails."
        if auto_lang: msg += f"\n(Auto Language detected: {auto_lang.upper()})"
        markup = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        markup.add('Fix Password (SOHAVdd)', 'Custom Password')
        bot.send_message(chat_id, msg + "\n🔐 Select Password Mode:", reply_markup=markup)

    elif state['step'] == 'password_mode':
        if 'Fix Password' in message.text:
            tz = datetime.timezone(datetime.timedelta(hours=6))
            state['password'] = f"SOHAV{datetime.datetime.now(tz).day}"
            state['step'] = 'proxy_mode'
            bot.send_message(chat_id, f"✅ Fixed Password set to: `{state['password']}`", parse_mode='Markdown', reply_markup=ReplyKeyboardRemove())
            show_proxy_menu(chat_id)
        elif 'Custom Password' in message.text:
            state['step'] = 'custom_password'
            bot.send_message(chat_id, "✍️ Enter your Custom Password:", reply_markup=ReplyKeyboardRemove())
        else: bot.send_message(chat_id, "❌ Please select from the buttons.")

    elif state['step'] == 'custom_password':
        state['password'] = message.text.strip()
        state['step'] = 'proxy_mode'
        bot.send_message(chat_id, f"✅ Custom Password set.", reply_markup=ReplyKeyboardRemove())
        show_proxy_menu(chat_id)

    elif state['step'] == 'proxy_mode':
        choice = message.text
        if 'No Proxy' in choice: state['use_proxy'] = False; next_step = True
        elif 'Use Proxy' in choice:
            if len(load_proxies()) == 0: return bot.send_message(chat_id, "⚠️ No proxies found in proxies.txt! Please add some or select No Proxy.")
            state['use_proxy'] = True; next_step = True
        else: next_step = False; bot.send_message(chat_id, "❌ Please select from the buttons.")

        if next_step:
            state['step'] = 'name_mode'
            markup = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
            markup.add('Auto Name', 'Custom Name')
            bot.send_message(chat_id, "👤 Select Name Mode:", reply_markup=markup)

    elif state['step'] == 'name_mode':
        if message.text == 'Custom Name':
            state['step'] = 'custom_name'
            bot.send_message(chat_id, "✍️ Send: Firstname Lastname", reply_markup=ReplyKeyboardRemove())
        else:
            state['custom_name'] = None
            if state.get('auto_lang'): state['lang'] = state['auto_lang']; start_batch_from_state(chat_id, state)
            else: state['step'] = 'language'; show_languages(chat_id)

    elif state['step'] == 'custom_name':
        parts = message.text.strip().split(' ')
        if len(parts) < 2: return bot.send_message(chat_id, "❌ Invalid format. Use: Firstname Lastname")
        state['custom_name'] = (parts[0], " ".join(parts[1:]))
        if state.get('auto_lang'): state['lang'] = state['auto_lang']; start_batch_from_state(chat_id, state)
        else: state['step'] = 'language'; show_languages(chat_id)

    elif state['step'] == 'language':
        state['lang'] = message.text.strip().lower()[:2]
        start_batch_from_state(chat_id, state)

def show_proxy_menu(chat_id):
    proxy_count = len(load_proxies())
    proxy_text = f"Use Proxy ({proxy_count} Loaded)" if proxy_count > 0 else "Use Proxy (0 Loaded)"
    markup = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add('No Proxy (Direct)', proxy_text)
    bot.send_message(chat_id, "🌐 Select Proxy Mode:", reply_markup=markup)

def show_languages(chat_id):
    markup = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True, row_width=4)
    buttons = [KeyboardButton(code) for code in LANG_MAP.keys()]
    markup.add(*buttons)
    bot.send_message(chat_id, "🌍 Select Language Code:", reply_markup=markup)

def start_batch_from_state(chat_id, state):
    global CURRENT_LANG_HEADER
    lang = state['lang']
    if lang in LANG_MAP: CURRENT_LANG_HEADER = LANG_MAP[lang][0]
    else: CURRENT_LANG_HEADER = LANG_MAP['us'][0]
    
    state['step'] = None
    proxy_status = "Proxy ON" if state['use_proxy'] else "Direct IP"
    bot.send_message(chat_id, f"⚙️ Starting creation for {len(state['email_data_list'])} accounts ({proxy_status} | Lang: {lang.upper()})...\n\n👇 *Please wait, results will appear below.*", parse_mode='Markdown', reply_markup=ReplyKeyboardRemove())
    threading.Thread(target=execute_batch, args=(chat_id, state['email_data_list'], state['password'], lang, state['custom_name'], state['use_proxy'], False)).start()

# ══════════════════════════════════════════════════════════
# START BOTH FLASK & BOT
# ══════════════════════════════════════════════════════════
if __name__ == '__main__':
    t = threading.Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080))))
    t.daemon = True
    t.start()
    
    print("Bot & Web Dashboard is running...")
    bot.infinity_polling()
