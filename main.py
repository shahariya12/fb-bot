#-----create by siam ---#
#------TG: @SIAMKHANXD--#
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
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
import requests
import io
import openpyxl
from concurrent.futures import ThreadPoolExecutor
from flask import Flask, request, jsonify, send_file, render_template_string, session, redirect, url_for
from supabase import create_client, Client

try:
    from curl_cffi import requests as cureq
except ImportError:
    print("\033[91m[!] curl_cffi not found!\033[0m")
    exit()

# ══════════════════════════════════════════════════════════
# CONFIG
# ══════════════════════════════════════════════════════════
BOT_TOKEN_1 = "9050767452:AAHto41auReAVjqJnzOeGKjbEW2Zue67oWQ"
BOT_TOKEN_2 = "9141516064:AAEB9HzrjlTY0WVu3DLSw87ncOVfWRBKejg"
ADMIN_ID = "6408202140"
WEB_PASSWORD = "SOHAV_ADMIN"

SUPABASE_URL = "https://plojfqqvqnddxibaxrqr.supabase.co"
SUPABASE_KEY = "sb_publishable_TkViojZqhR4ViRLfwEZpqg_TgKTE3Ps"

try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    print(f"Supabase Connection Error: {e}")

bot1 = telebot.TeleBot(BOT_TOKEN_1)
bot2 = telebot.TeleBot(BOT_TOKEN_2)

# ══════════════════════════════════════════════════════════
# GLOBALS
# ══════════════════════════════════════════════════════════
IS_RUNNING = False
CANCEL_EVENT = threading.Event()
CURRENT_BATCH_ID = 0
CURRENT_BATCH_NUMBER = None
WEB_LOGS = []
WEB_STATE = {"total": 0, "success": 0, "current": 0, "batch_number": None}

PROXY_COUNTRY = "fr"
CHECKPOINT_RETRY_POOL = {}
LAST_BATCH_CONFIG = {}

def add_web_log(msg, color="white"):
    global WEB_LOGS
    t = datetime.datetime.now().strftime("%H:%M:%S")
    WEB_LOGS.append({"time": t, "msg": msg, "color": color})
    if len(WEB_LOGS) > 100: WEB_LOGS.pop(0)

def load_proxies():
    try:
        res = supabase.table("proxies").select("proxy_str").execute()
        return [item['proxy_str'] for item in res.data]
    except Exception as e:
        print(f"Proxy Load Error: {e}")
        return []

def parse_proxy(proxy_str):
    try:
        p = proxy_str.split(':')
        if len(p) == 4:
            ip, port, user, pwd = p
            if PROXY_COUNTRY and '_cr.' in user:
                user = re.sub(r'_cr\.[a-zA-Z]+', f'_cr.{PROXY_COUNTRY}', user)
            return {'http': f'http://{user}:{pwd}@{ip}:{port}', 'https': f'http://{user}:{pwd}@{ip}:{port}'}
        elif len(p) == 3:
            ip, port, user = p
            if PROXY_COUNTRY and '_cr.' in user:
                user = re.sub(r'_cr\.[a-zA-Z]+', f'_cr.{PROXY_COUNTRY}', user)
            return {'http': f'http://{user}@{ip}:{port}', 'https': f'http://{user}@{ip}:{port}'}
        elif len(p) == 2:
            return {'http': f'http://{p[0]}:{p[1]}', 'https': f'http://{p[0]}:{p[1]}'}
    except:
        pass
    return None

def get_next_batch_number():
    max_b = 0
    for tbl in ("accounts", "failed_accounts"):
        try:
            res = supabase.table(tbl).select("batch_id").order("batch_id", desc=True).limit(1).execute()
            if res.data and res.data[0].get('batch_id') is not None:
                max_b = max(max_b, res.data[0]['batch_id'])
        except Exception as e:
            print(f"Batch fetch error ({tbl}): {e}")
    if max_b > 0:
        return max_b + 1
    return int(time.time()) % 100000

def fetch_all_rows(table, columns):
    out = []
    offset = 0
    while True:
        try:
            r = supabase.table(table).select(columns).range(offset, offset + 999).execute()
        except Exception as e:
            print(f"Pagination error ({table}): {e}")
            break
        if not r.data: break
        out.extend(r.data)
        if len(r.data) < 1000: break
        offset += 1000
    return out

# ══════════════════════════════════════════════════════════
# USER AGENTS
# ══════════════════════════════════════════════════════════
ANDROID_USER_AGENTS = [
    "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/156.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.6422.147 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.113 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12; SM-A525F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.6312.118 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 11; M2101K6G) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.119 Mobile Safari/537.36"
]
IOS_USER_AGENTS = [
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1"
]

# ══════════════════════════════════════════════════════════
# FLASK SETUP
# ══════════════════════════════════════════════════════════
app = Flask('')
app.secret_key = "SOHAV_SECRET_KEY_123"

FB_REG_BASE = "https://limited.facebook.com"
GRAPHQL_URL = "https://web.facebook.com/api/graphql/"
AUTH_FILE = "authorized_users.txt"

def load_auth_users():
    if os.path.exists(AUTH_FILE):
        with open(AUTH_FILE, 'r') as f:
            return [line.strip() for line in f if line.strip()]
    return []

def save_auth_user(user_id):
    users = load_auth_users()
    if str(user_id) not in users:
        with open(AUTH_FILE, 'a') as f: f.write(f"{user_id}\n")

def remove_auth_user(user_id):
    users = load_auth_users()
    if str(user_id) in users:
        users.remove(str(user_id))
        with open(AUTH_FILE, 'w') as f:
            for u in users: f.write(f"{u}\n")

def is_authorized(chat_id):
    if str(chat_id) == ADMIN_ID: return True
    return str(chat_id) in load_auth_users()

# ══════════════════════════════════════════════════════════
# MANUAL READER API
# ══════════════════════════════════════════════════════════
def get_code_via_api(combo, code_type="facebook"):
    try:
        parts = combo.split('|')
        if len(parts) < 4:
            return None, "Invalid combo (need 4 parts)"
        payload = {
            "email": parts[0].strip(),
            "refresh_token": parts[2].strip(),
            "client_id": parts[3].strip(),
            "type": code_type
        }
        headers = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}
        res = requests.post("https://tools.dongvanfb.net/api/get_code_oauth2", json=payload, headers=headers, timeout=10)
        if res.status_code == 200:
            rj = res.json()
            if rj.get("status") is True and "code" in rj:
                return rj["code"], None
            return None, str(rj.get("message", rj.get("content", "No code found")))
        return None, f"API Error: {res.status_code}"
    except Exception as e:
        return None, str(e)

# ══════════════════════════════════════════════════════════
# AUTO OTP FETCHER (2 HOURS) - FORCED FACEBOOK ONLY
# ══════════════════════════════════════════════════════════
def fetch_otp_from_hotmail(email_addr, full_combo, chat_id=None):
    deadline = time.time() + (2 * 60 * 60)
    while time.time() < deadline:
        if CANCEL_EVENT.wait(timeout=5):
            return
        code, error = get_code_via_api(full_combo, code_type="facebook")
        if code:
            try:
                supabase.table("otps").insert({"email": email_addr, "code": code}).execute()
            except Exception as e:
                print(f"Supabase OTP Error: {e}")
            if chat_id:
                try:
                    bot1.send_message(chat_id, f"📩 **AUTO OTP for `{email_addr}`**\n\n🔑 `{code}`", parse_mode='Markdown')
                except: pass
            return

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

DEFAULT_FIRST_NAMES = ['Arafat', 'Rakib', 'Sabbir', 'Nayeem', 'Rifat', 'Tanvir', 'Shakib', 'Sajid', 'John', 'David', 'Michael', 'James']
DEFAULT_LAST_NAMES = ['Hossain', 'Ahmed', 'Khan', 'Islam', 'Rahman', 'Sarker', 'Smith', 'Johnson', 'Williams', 'Brown']
GERMAN_FIRST_NAMES = ["Alexander", "Andreas", "Anna", "Anja", "Anke", "Anton", "Armin", "Axel", "Barbara", "Bastian", "Benedikt", "Benjamin", "Bernd", "Birgit", "Björn", "Brigitte", "Bruno", "Carina", "Carla", "Charlotte", "Christian", "Christina", "Christof", "Claudia", "Claus", "Cornelia", "Daniel", "Daniela", "David", "Dennis"]
GERMAN_LAST_NAMES = ["Albrecht", "Arnold", "Bachmann", "Bauer", "Baumann", "Becker", "Beckmann", "Berger", "Bergmann", "Böhm", "Brandt", "Braun", "Brinker", "Brunner", "Busch", "Dietrich", "Dörfler", "Dreher", "Ebert", "Eckert", "Engel", "Esser", "Falk", "Faust", "Fischer", "Fleischer", "Frank", "Franz", "Frey", "Fuchs"]
PORTUGUESE_FIRST_NAMES = ["Miguel", "Arthur", "Gael", "Théo", "Heitor", "Ravi", "Davi", "Bernardo", "Noah", "Gabriel", "Samuel", "Pedro", "Anthony", "Lucas", "Benjamin", "Matheus", "Joaquim", "Nicolas", "Lorenzo", "Henrique", "João", "Rafael", "Enzo", "Murilo", "Benício", "Gustavo", "Guilherme", "Emanuel", "Felipe", "Bryan", "Daniel", "Vitor", "Leonardo", "Bruno", "Thiago", "Vicente", "Carlos", "Eduardo", "André", "Fernando"]
PORTUGUESE_LAST_NAMES = ["Silva", "Santos", "Oliveira", "Souza", "Rodrigues", "Ferreira", "Alves", "Pereira", "Lima", "Gomes", "Costa", "Ribeiro", "Martins", "Carvalho", "Almeida", "Lopes", "Soares", "Fernandes", "Vieira", "Barbosa", "Rocha", "Dias", "Nascimento", "Andrade", "Moreira", "Nunes", "Marques", "Machado", "Mendes", "Freitas"]
FRENCH_FIRST_NAMES = ["Jean", "Pierre", "Michel", "André", "Philippe", "Louis", "Nicolas", "François", "Alain", "Julien", "Bernard", "Marcel", "Daniel", "Paul", "Gérard", "Robert", "Patrick", "Henri", "Jacques", "Claude", "Éric", "Christian", "Georges", "René", "Pascal", "David", "Olivier", "Laurent", "Stéphane", "Thierry", "Thomas", "Sébastien", "Alexandre", "Vincent", "Christophe", "Maxime", "Jérôme", "Frédéric", "Xavier", "Fabrice", "Mathieu", "Antoine", "Romain", "Benjamin", "Guillaume", "Damien", "Yves", "Hugo", "Lucas", "Jules", "Léo", "Gabriel", "Raphaël", "Arthur", "Nathan", "Ethan", "Enzo", "Mathis", "Noah", "Tom"]
FRENCH_LAST_NAMES = ["Martin", "Bernard", "Thomas", "Petit", "Robert", "Richard", "Durand", "Dubois", "Moreau", "Laurent", "Simon", "Michel", "Lefebvre", "Leroy", "Roux", "David", "Bertrand", "Morel", "Fournier", "Girard", "Bonnet", "Dupont", "Lambert", "Fontaine", "Rousseau", "Vincent", "Muller", "Lefevre", "Faure", "Andre", "Mercier", "Blanc", "Guerin", "Boyer", "Garnier", "Chevalier", "Francois", "Legrand", "Gauthier", "Garcia", "Perrin", "Robin", "Clement", "Morin", "Nicolas", "Henry", "Roussel", "Mathieu", "Gautier", "Masson", "Marchand", "Duval", "Denis", "Dumont", "Marie", "Lemaire", "Noel", "Meyer", "Dufour", "Meunier"]

SCREEN_PROFILES = [(390, 844, 3.0), (393, 852, 3.0), (428, 926, 3.0), (430, 932, 3.0), (375, 812, 3.0)]

def build_fingerprint(os_type="ios"):
    if os_type == "android":
        ua = random.choice(ANDROID_USER_AGENTS); imp = "chrome120"
    else:
        ua = random.choice(IOS_USER_AGENTS); imp = "safari15_5"
    sw, sh, _ = random.choice(SCREEN_PROFILES)
    return {
        "impersonate": imp,
        "pringer": hashlib.sha256(f"{ua}-{sw}x{sh}-{uuid.uuid4()}".encode()).hexdigest()[:32],
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
    if CANCEL_EVENT.is_set(): return {}, ""
    steps = ["https://www.facebook.com/", f"{FB_REG_BASE}/reg/?cid=103"]
    collected, last_lsd = {}, "AdS-QY2mYrCcHP7sVf7ynTA6vTc"
    for url in steps:
        if CANCEL_EVENT.is_set(): return {}, ""
        try:
            r = session.get(url, headers=fp["headers"], impersonate=fp["impersonate"], proxies=proxy, timeout=10)
            if CANCEL_EVENT.wait(timeout=random.uniform(1.5, 3.5)): return {}, ""
            collected.update(session.cookies.get_dict())
            m = re.search(r'"LSD",\[\],\{"token":"([^"]+)"', r.text)
            if m: last_lsd = m.group(1)
        except:
            if CANCEL_EVENT.wait(timeout=1): return {}, ""
    return collected, last_lsd

def fb_create_account(email, password, lang_code, custom_fname, custom_lname, proxy_dict, os_type):
    if CANCEL_EVENT.is_set(): return (None, 'CANCELLED')
    session = cureq.Session()
    fp = build_fingerprint(os_type)
    cookies_warm, lsd_token = warmup_session(session, fp, proxy_dict)
    if CANCEL_EVENT.is_set(): return (None, 'CANCELLED')
    if CANCEL_EVENT.wait(timeout=random.uniform(2.0, 4.0)):
        return (None, 'CANCELLED')

    reg_fp = build_fingerprint(os_type)
    try:
        r = session.get(f"{FB_REG_BASE}/reg/?cid=103", headers=reg_fp["headers"], impersonate=reg_fp["impersonate"], proxies=proxy_dict, timeout=10)
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
            'field_names[0]': 'firstname', 'firstname': firstname, 'lastname': lastname,
            'field_names[1]': 'birthday_wrapper',
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
            'referer': f"{FB_REG_BASE}/reg/?cid=103", 'x-fb-lsd': lsd,
            "Cookie": build_cookie_header(cookies_warm)
        })
        if CANCEL_EVENT.wait(timeout=random.uniform(3.0, 6.0)):
            return (None, 'CANCELLED')
        r = session.post(f"{FB_REG_BASE}/reg/submit/?app_id=103&multi_step_form=1",
                         headers=headers, data=data, impersonate=reg_fp["impersonate"], proxies=proxy_dict, timeout=30)
    except:
        return (None, 'POST_FAIL')

    cookies = session.cookies.get_dict()
    uid = cookies.get('c_user')
    if uid:
        merged = dict(cookies_warm); merged.update(cookies)
        return ({
            'firstname': firstname, 'lastname': lastname, 'email': email,
            'password': password, 'uid': uid,
            'cookie': build_cookie_header(merged), 'session': session, 'proxy': proxy_dict
        }, None)
    body = r.text.lower()
    if 'checkpoint' in body: return (None, 'CHECKPOINT')
    if 'already' in body: return (None, 'TAKEN')
    return (None, 'FAILED')

def resend_otp(session, uid, proxy):
    try:
        r = session.get("https://web.facebook.com/confirmemail.php?next=undefined", proxies=proxy, timeout=10)
        lsd = re.search(r'"LSD",\[\],\{"token":"([^"]+)"', r.text)
        lsd = lsd.group(1) if lsd else ""
        dtsg = re.search(r'"DTSGInitialData",\[\],\{"token":"([^"]+)"', r.text) or re.search(r'name="fb_dtsg"\s+value="([^"]+)"', r.text)
        fb_dtsg = dtsg.group(1) if dtsg else ""
        if not lsd or not fb_dtsg: return False
        headers = {'host': 'web.facebook.com', 'content-type': 'application/x-www-form-urlencoded', 'x-fb-lsd': lsd, 'origin': 'https://web.facebook.com'}
        variables = json.dumps({"input": {"actor_id": str(uid), "client_mutation_id": str(uuid.uuid4()), "machine_id": ""}}, separators=(',', ':'))
        data = {'av': str(uid), '__user': str(uid), 'fb_dtsg': fb_dtsg, 'lsd': lsd, 'variables': variables, 'doc_id': '9554972464608847'}
        res = session.post(GRAPHQL_URL, headers=headers, data=data, proxies=proxy, timeout=15)
        return (res.status_code == 200 and "errors" not in res.text)
    except: return False

# ══════════════════════════════════════════════════════════
# BATCH EXECUTION
# ══════════════════════════════════════════════════════════
def execute_batch(chat_id, email_data_list, password, lang, custom_name, hotmail_name, use_proxy, os_type, is_web=False):
    global IS_RUNNING, WEB_STATE, CURRENT_BATCH_ID, CURRENT_BATCH_NUMBER

    CURRENT_BATCH_ID += 1
    my_batch_id = CURRENT_BATCH_ID
    my_batch_number = get_next_batch_number()
    CURRENT_BATCH_NUMBER = my_batch_number

    IS_RUNNING = True
    CANCEL_EVENT.clear()
    success_count = 0; fail_count = 0
    WEB_STATE["total"] = len(email_data_list)
    WEB_STATE["success"] = 0
    WEB_STATE["batch_number"] = my_batch_number

    proxies = load_proxies() if use_proxy else []
    proxy_dicts = []
    if use_proxy:
        if not proxies:
            if not is_web and chat_id:
                bot1.send_message(chat_id, "⚠️ Proxies selected but database is empty!")
            IS_RUNNING = False
            return
        random.shuffle(proxies)
        for i in range(len(email_data_list)):
            proxy_dicts.append(parse_proxy(proxies[i % len(proxies)]))
    else:
        proxy_dicts = [None] * len(email_data_list)

    def process_one(item, idx, total):
        nonlocal success_count, fail_count
        if CANCEL_EVENT.is_set() or my_batch_id != CURRENT_BATCH_ID: return
        WEB_STATE["current"] = idx
        email = item['email']; full_combo = item['full_combo']

        is_hotmail = any(d in email.lower() for d in ["@hotmail.", "@outlook.", "@live.", "@msn."])
        c_fname, c_lname = None, None
        if is_hotmail and hotmail_name:
            p = hotmail_name.split(' ', 1); c_fname = p[0]; c_lname = p[1] if len(p) > 1 else "User"
        elif not is_hotmail and custom_name:
            p = custom_name.split(' ', 1); c_fname = p[0]; c_lname = p[1] if len(p) > 1 else "User"

        assigned_proxy = proxy_dicts[idx - 1]
        proxy_ip = list(assigned_proxy.values())[0].split('@')[-1] if assigned_proxy else "Direct IP"

        status_msg = None
        if not is_web and chat_id:
            status_msg = bot1.send_message(chat_id, f"⏳ [{idx}/{total}] B#{my_batch_number}: `{email}`\n🔌 `{proxy_ip}`", parse_mode='Markdown')
        else:
            add_web_log(f"[B{my_batch_number}][{idx}/{total}] {email} (Proxy: {proxy_ip})", "cyan")

        res, err = fb_create_account(email, password, lang, c_fname, c_lname, assigned_proxy, os_type)
        if CANCEL_EVENT.is_set() or my_batch_id != CURRENT_BATCH_ID: return

        if res:
            success_count += 1; WEB_STATE["success"] = success_count
            try:
                supabase.table("accounts").insert({
                    "email": email, "password": password, "uid": res['uid'],
                    "cookie": res['cookie'], "full_combo": full_combo,
                    "batch_id": my_batch_number
                }).execute()
            except Exception as e:
                print(f"Supabase Save Error: {e}")

            msg_text = f"✅ **SUCCESS** (B#{my_batch_number})\n📧 `{email}`\n🔌 `{proxy_ip}`"
            if not is_web and chat_id:
                bot1.edit_message_text(msg_text, chat_id=chat_id, message_id=status_msg.message_id, parse_mode='Markdown')
            else:
                add_web_log(f"[+] B{my_batch_number} SUCCESS: {email}", "green")

            resend_otp(res['session'], res['uid'], res['proxy'])
            threading.Thread(target=fetch_otp_from_hotmail, args=(email, full_combo, chat_id if not is_web else None)).start()
        else:
            if err == 'CANCELLED': return
            fail_count += 1
            try:
                supabase.table("failed_accounts").insert({
                    "full_combo": full_combo, "reason": err, "batch_id": my_batch_number
                }).execute()
            except Exception as e:
                print(f"Supabase Error: {e}")

            fail_text = f"❌ `{email}` Failed: {err} (B#{my_batch_number})\n🔌 `{proxy_ip}`"
            if not is_web and chat_id:
                bot1.edit_message_text(fail_text, chat_id=chat_id, message_id=status_msg.message_id, parse_mode='Markdown')
                if err == 'CHECKPOINT':
                    rid = str(uuid.uuid4())[:8]
                    CHECKPOINT_RETRY_POOL[rid] = {"email": email, "full_combo": full_combo}
                    mk = InlineKeyboardMarkup()
                    mk.add(InlineKeyboardButton("🔄 Try Again", callback_data=f"retry_chk_{rid}"))
                    bot1.send_message(chat_id, f"⚠️ **CHECKPOINT DETECTED**\n📧 `{email}`\n\nClick below to retry.", reply_markup=mk, parse_mode='Markdown')
            else:
                add_web_log(fail_text, "red")

    # Limit maximum concurrent workers to 20
    workers = min(len(email_data_list), 20)
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(process_one, item, i+1, len(email_data_list)) for i, item in enumerate(email_data_list)]
        for future in futures: future.result()

    if my_batch_id != CURRENT_BATCH_ID: return

    IS_RUNNING = False
    if CANCEL_EVENT.is_set():
        finish_msg = f"🛑 **Batch #{my_batch_number} Cancelled!**\n✅ Success: {success_count}\n❌ Failed: {fail_count}"
    else:
        finish_msg = f"🎉 **Batch #{my_batch_number} Finished!**\n✅ Success: {success_count}\n❌ Failed: {fail_count}\n\n👉 _/start to open menu_"

    if not is_web and chat_id:
        bot1.send_message(chat_id, finish_msg, parse_mode='Markdown', reply_markup=get_main_menu_1(chat_id))
    else:
        add_web_log(f"Finished! B#{my_batch_number} — Success: {success_count}, Failed: {fail_count}", "yellow")

# ══════════════════════════════════════════════════════════
# CSV HELPERS
# ══════════════════════════════════════════════════════════
def _write_csv(header, rows):
    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_ALL)
    writer.writerow(header)
    for row in rows: writer.writerow(row)
    mem = io.BytesIO()
    mem.write(output.getvalue().encode('utf-8'))
    mem.seek(0)
    return mem

# ══════════════════════════════════════════════════════════
# WEB TEMPLATES
# ══════════════════════════════════════════════════════════
LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Login</title>
<style>
body { font-family: -apple-system, sans-serif; background: #0f172a; color: white; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; padding: 20px; box-sizing: border-box; }
.card { background: #1e293b; padding: 30px 20px; border-radius: 16px; width: 100%; max-width: 350px; text-align: center; }
h2 { margin-top: 0; color: #38bdf8; }
input { width: 100%; padding: 14px; margin: 15px 0; background: #0f172a; border: 1px solid #334155; border-radius: 10px; color: white; font-size: 16px; box-sizing: border-box; }
button { width: 100%; padding: 14px; background: #0ea5e9; color: white; border: none; border-radius: 10px; font-weight: bold; font-size: 16px; cursor: pointer; }
.error { color: #f87171; margin-top: 10px; }
</style></head><body>
<div class="card"><h2>🔒 Login</h2>
<form method="POST"><input type="password" name="password" placeholder="Password" required><button>Unlock</button></form>
{% if error %}<p class="error">{{ error }}</p>{% endif %}</div>
</body></html>
"""

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>SOHAV Creator App</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background: #0f172a; color: #e2e8f0; margin: 0; padding-bottom: 80px; }
        .header { background: #1e293b; padding: 15px 20px; position: sticky; top: 0; z-index: 100; display: flex; justify-content: space-between; align-items: center; }
        .header h1 { font-size: 18px; margin: 0; color: #38bdf8; }
        .header button { background: none; border: none; color: #38bdf8; font-size: 20px; cursor: pointer; }
        .status-bar { padding: 10px 20px; font-size: 13px; font-weight: bold; text-align: center; background: #334155; }
        .content { padding: 20px; }
        .card { background: #1e293b; padding: 15px; border-radius: 12px; margin-bottom: 15px; }
        label { display: block; font-size: 13px; color: #94a3b8; margin-bottom: 8px; font-weight: 600; }
        textarea, select, input { width: 100%; padding: 12px; background: #0f172a; border: 1px solid #334155; border-radius: 8px; color: white; font-size: 15px; margin-bottom: 12px; box-sizing: border-box; }
        textarea { resize: vertical; min-height: 100px; }
        .btn { width: 100%; padding: 14px; background: #0ea5e9; color: white; border: none; border-radius: 10px; font-weight: bold; font-size: 16px; cursor: pointer; }
        .btn.stop { background: #ef4444; display: none; }
        .btn:active { opacity: 0.8; }
        .btn-row { display: flex; gap: 10px; margin-top: 10px; }
        .btn-row .btn { flex: 1; font-size: 13px; padding: 10px; }
        .btn-row .btn.success { background: #10b981; }
        .btn-row .btn.failed { background: #ef4444; }
        #otp-container { display: none; }
        .otp-list-item { display: flex; justify-content: space-between; align-items: center; background: #0f172a; padding: 10px; border-radius: 8px; margin-bottom: 8px; border-left: 4px solid #10b981; }
        .otp-code { font-family: monospace; font-size: 18px; font-weight: bold; color: #4ade80; letter-spacing: 2px; }
        .otp-email { font-size: 11px; color: #94a3b8; display: block; margin-bottom: 4px; }
        .copy-btn { background: #0ea5e9; color: white; border: none; border-radius: 6px; padding: 6px 12px; font-size: 12px; font-weight: bold; cursor: pointer; }
        .del-btn { background: #ef4444; color: white; border: none; border-radius: 6px; padding: 6px 12px; font-size: 12px; font-weight: bold; cursor: pointer; }
        #logs { background: #000; height: 200px; overflow-y: auto; padding: 10px; border-radius: 8px; font-family: monospace; font-size: 12px; border: 1px solid #334155; margin-top: 15px; color: #ccc; }
        .cyan { color: #22d3ee; } .green { color: #4ade80; } .red { color: #f87171; } .yellow { color: #fbbf24; } .white { color: #e2e8f0; }
        .batch-item { background: #0f172a; padding: 10px; border-radius: 8px; margin-bottom: 8px; border-left: 4px solid #0ea5e9; }
        .batch-item.old { border-left-color: #f59e0b; }
        .batch-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
        .batch-num { font-weight: bold; color: #38bdf8; }
        .batch-num.old { color: #f59e0b; }
        .batch-counts { font-size: 11px; color: #94a3b8; }
        .bottom-nav { position: fixed; bottom: 0; width: 100%; background: #1e293b; display: flex; border-top: 1px solid #334155; }
        .nav-item { flex: 1; text-align: center; padding: 15px 0; color: #94a3b8; font-size: 12px; text-decoration: none; font-weight: bold; }
        .nav-item.active { color: #0ea5e9; }
        .hidden { display: none !important; }
    </style>
</head>
<body>
    <div class="header"><h1>🚀 Creator App</h1><button onclick="window.location.reload()">🔄</button></div>
    <div class="status-bar" id="status">Status: Idle</div>
    <div class="content">
        <div id="otp-container">
            <div class="card">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
                    <label style="color:#4ade80; margin-bottom:0;">📩 Recent OTPs</label>
                    <button class="del-btn" onclick="deleteOTPs()">🗑 Delete All</button>
                </div>
                <div id="otp-list"></div>
            </div>
        </div>
        <div id="mainForm">
        
            <div class="card" style="border-left: 4px solid #8b5cf6;">
                <label>📥 Email Pool (Add Combos)</label>
                <textarea id="poolCombos" placeholder="email|password|refresh_token|client_id&#10;(Paste 1 or 1000 combos here)"></textarea>
                <div class="btn-row">
                    <button class="btn" onclick="addToPool()" style="background:#8b5cf6;">📥 Add to Pool</button>
                    <button class="btn" onclick="deleteFromPool()" style="background:#ef4444;">🗑 Delete</button>
                </div>
                <div id="poolResult" style="margin-top:10px; font-size:14px; font-weight:bold; color:#4ade80; word-wrap:break-word;"></div>
            </div>

            <div class="card">
                <label>Emails / Combos</label>
                <textarea id="emails" placeholder="email|password|refresh_token|client_id"></textarea>
                <label>OS Mode</label>
                <select id="osMode"><option value="ios">iOS (Safari)</option><option value="android">Android (Chrome)</option></select>
                <label>Password Mode</label>
                <select id="passMode" onchange="togglePass()"><option value="fix">Fix Password (SOHAVdd)</option><option value="custom">Custom Password</option></select>
                <input type="text" id="customPass" placeholder="Custom Password" style="display:none;">
                <label>Proxy Mode</label>
                <select id="proxyMode"><option value="no">No Proxy</option><option value="yes">Use Proxy</option></select>
                <label>Name Mode (.com)</label>
                <select id="nameMode" onchange="toggleName()"><option value="auto">Auto Name</option><option value="custom">Custom Name</option></select>
                <input type="text" id="customName" placeholder="Firstname Lastname" style="display:none;">
                <label>Hotmail Reader Name</label>
                <input type="text" id="hotmailName" placeholder="Firstname Lastname (optional)">
                <label>Language</label>
                <select id="lang"><option value="de">German</option><option value="fr">French</option><option value="br">Portuguese</option><option value="us">English</option></select>
                <button class="btn" id="startBtn" onclick="startBatch()">▶ START</button>
                <button class="btn stop" id="stopBtn" onclick="stopBatch()">🛑 STOP</button>
            </div>
            <div class="card">
                <label>📦 Batch Downloads</label>
                <div id="batchList" style="max-height: 400px; overflow-y: auto;">
                    <p style="color:#94a3b8; font-size:12px;">Loading...</p>
                </div>
            </div>
            <div class="card">
                <label>📥 Download ALL</label>
                <div class="btn-row">
                    <a href="/download/success" class="btn success" style="text-decoration:none; text-align:center;">✅ All Success</a>
                    <a href="/download/failed" class="btn failed" style="text-decoration:none; text-align:center;">❌ All Failed</a>
                </div>
            </div>
            <div id="logs"></div>
            <div class="card" style="margin-top:15px;">
                <label>📩 Bulk Hotmail Reader</label>
                <select id="readerType">
                    <option value="facebook">Facebook</option><option value="all">All</option><option value="instagram">Instagram</option>
                    <option value="twitter">Twitter</option><option value="tiktok">TikTok</option><option value="google">Google</option>
                </select>
                <textarea id="readerCombo" placeholder="email|pass|refresh_token|client_id (one per line)"></textarea>
                <button class="btn" onclick="readHotmail()" style="background:#8b5cf6;">🔍 Read Inboxes</button>
                <div id="readerResult" style="margin-top:10px; font-size:12px; max-height:300px; overflow-y:auto; background:#0f172a; padding:10px; border-radius:8px; display:none; border:1px solid #334155;"></div>
            </div>
        </div>
    </div>
    <div class="bottom-nav">
        <a href="#" class="nav-item active" id="nav-home" onclick="showHome(event)">🏠 Home</a>
        <a href="#" class="nav-item" id="nav-otp" onclick="showOTP(event)">📩 OTP</a>
        <a href="#" class="nav-item" onclick="window.location.reload()">🔄</a>
        <a href="/logout" class="nav-item" style="color:#ef4444;">🚪 Logout</a>
    </div>
<script>
    function togglePass() { document.getElementById('customPass').style.display = document.getElementById('passMode').value === 'custom' ? 'block' : 'none'; }
    function toggleName() { document.getElementById('customName').style.display = document.getElementById('nameMode').value === 'custom' ? 'block' : 'none'; }
    function showHome(e) { if(e) e.preventDefault(); document.getElementById('mainForm').classList.remove('hidden'); document.getElementById('otp-container').classList.add('hidden'); document.getElementById('nav-home').classList.add('active'); document.getElementById('nav-otp').classList.remove('active'); }
    function showOTP(e) { if(e) e.preventDefault(); document.getElementById('mainForm').classList.add('hidden'); document.getElementById('otp-container').classList.remove('hidden'); document.getElementById('nav-otp').classList.add('active'); document.getElementById('nav-home').classList.remove('active'); fetchOTPs(); }
    function copyCode(code) { navigator.clipboard.writeText(code).then(() => alert("Copied: " + code)); }
    async function deleteOTPs() { if(!confirm("Delete all OTPs?")) return; await fetch('/api/delete_otps', { method: 'POST' }); fetchOTPs(); }

    async function fetchOTPs() {
        const res = await fetch('/api/otps');
        const otps = await res.json();
        const list = document.getElementById('otp-list');
        if (otps.length > 0) {
            list.innerHTML = otps.map(o => `<div class="otp-list-item"><div><span class="otp-email">${o.email}</span><span class="otp-code">${o.code}</span></div><button class="copy-btn" onclick="copyCode('${o.code}')">Copy</button></div>`).join('');
        } else { list.innerHTML = `<p style="color:#94a3b8; font-size:12px; text-align:center;">No OTPs.</p>`; }
    }

    async function loadBatches() {
        const res = await fetch('/api/batches');
        const batches = await res.json();
        const c = document.getElementById('batchList');
        if (!batches || batches.length === 0) { c.innerHTML = `<p style="color:#94a3b8; font-size:12px;">No batches yet.</p>`; return; }
        c.innerHTML = batches.map(b => {
            const isOld = b.batch_id === 0;
            const label = isOld ? '📜 Old (Batch #0)' : `Batch #${b.batch_id}`;
            return `
            <div class="batch-item ${isOld ? 'old' : ''}">
                <div class="batch-header">
                    <span class="batch-num ${isOld ? 'old' : ''}">${label}</span>
                    <span class="batch-counts">✅ ${b.success} &nbsp; ❌ ${b.failed}</span>
                </div>
                <div class="btn-row" style="margin-top:0;">
                    <a href="/download/success/${b.batch_id}" class="btn success" style="padding:8px; font-size:12px; text-decoration:none; text-align:center;">✅ CSV</a>
                    <a href="/download/failed/${b.batch_id}" class="btn failed" style="padding:8px; font-size:12px; text-decoration:none; text-align:center;">❌ CSV</a>
                    <button onclick="deleteBatch(${b.batch_id})" class="btn" style="padding:8px; font-size:12px; background:#dc2626; border:none;">🗑 Del</button>
                </div>
            </div>`;
        }).join('');
    }

    async function deleteBatch(bid) {
        if(!confirm(`Are you sure you want to DELETE ALL accounts from Batch #${bid}?`)) return;
        const res = await fetch(`/api/batch/delete/${bid}`, { method: 'POST' });
        const data = await res.json();
        if(data.status === 'success') { alert("Batch deleted!"); loadBatches(); }
        else alert("Error: " + data.msg);
    }

    async function addToPool() {
        const raw = document.getElementById('poolCombos').value.trim();
        if (!raw) return alert("Paste combos first!");
        const combos = raw.split('\\n').map(c => c.trim()).filter(c => c);
        
        document.getElementById('poolResult').innerText = "⏳ Saving...";
        const res = await fetch('/api/pool/add', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ combos: combos })
        });
        const data = await res.json();
        if(data.status === 'success') {
            document.getElementById('poolResult').innerText = "✅ Serials: " + data.serials.join(', ');
            document.getElementById('poolCombos').value = '';
        } else {
            document.getElementById('poolResult').innerText = "❌ Error: " + data.msg;
        }
    }

    async function deleteFromPool() {
        const serialsStr = prompt("Enter Serial Numbers to delete (e.g. 1, 2, 5) OR type 'all' to delete ALL unused emails:");
        if (!serialsStr) return;
        
        if (serialsStr.toLowerCase() === 'all') {
            if (!confirm("Are you sure you want to delete ALL unused emails in the pool?")) return;
            document.getElementById('poolResult').innerText = "⏳ Deleting all unused...";
            const res = await fetch('/api/pool/delete', {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ delete_all: true })
            });
            const data = await res.json();
            document.getElementById('poolResult').innerText = data.status === 'success' ? "✅ Deleted all unused emails from pool." : "❌ Error: " + data.msg;
            return;
        }

        const serials = serialsStr.split(/[,\s]+/).map(s => parseInt(s.trim())).filter(n => !isNaN(n));
        if (serials.length === 0) return alert("Invalid serial numbers.");
        
        if (!confirm(`Delete ${serials.length} serial(s) from database?`)) return;

        document.getElementById('poolResult').innerText = "⏳ Deleting...";
        const res = await fetch('/api/pool/delete', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ serials: serials })
        });
        const data = await res.json();
        if(data.status === 'success') {
            document.getElementById('poolResult').innerText = `✅ Deleted ${data.deleted_count} serial(s).`;
        } else {
            document.getElementById('poolResult').innerText = "❌ Error: " + data.msg;
        }
    }

    async function startBatch() {
        const rawEmails = document.getElementById('emails').value.trim();
        if (!rawEmails) return alert("Enter emails!");
        document.getElementById('logs').innerHTML = '';
        document.getElementById('startBtn').style.display = 'none';
        document.getElementById('stopBtn').style.display = 'block';
        await fetch('/api/start', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                emails: rawEmails.split('\\n').map(e => e.trim()).filter(e => e),
                os_mode: document.getElementById('osMode').value,
                pass_mode: document.getElementById('passMode').value,
                custom_pass: document.getElementById('customPass').value,
                proxy_mode: document.getElementById('proxyMode').value,
                name_mode: document.getElementById('nameMode').value,
                custom_name: document.getElementById('customName').value,
                hotmail_name: document.getElementById('hotmailName').value,
                lang: document.getElementById('lang').value
            })
        });
    }
    async function stopBatch() { if (!confirm("Stop process?")) return; await fetch('/api/stop', { method: 'POST' }); document.getElementById('stopBtn').style.display = 'none'; }
    async function readHotmail() {
        const raw = document.getElementById('readerCombo').value.trim();
        if(!raw) return alert("Enter combos");
        const codeType = document.getElementById('readerType').value;
        const combos = raw.split('\\n').map(c => c.trim()).filter(c => c);
        const div = document.getElementById('readerResult');
        div.style.display = 'block';
        div.innerHTML = `<p style="color:#fbbf24;">⏳ Fetching ${codeType.toUpperCase()} for ${combos.length}...</p>`;
        const res = await fetch('/api/hotmail_reader', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ combos, type: codeType }) });
        const rd = await res.json();
        if(rd.status === 'success') {
            div.innerHTML = rd.results.map(acc => {
                let h = `<div style="margin-bottom:12px; border-left:3px solid #8b5cf6; padding-left:10px;"><div style="color:#a78bfa; font-weight:bold; font-size:13px;">${acc.email}</div>`;
                if (acc.status === 'success') {
                    h += acc.data.length === 0 ? `<div style="color:#64748b; font-size:11px; font-style:italic;">No code.</div>` :
                        acc.data.map(m => `<div style="display:flex; justify-content:space-between; margin-top:4px; background:#1e293b; padding:6px; border-radius:6px;"><span style="color:#4ade80; font-weight:bold; letter-spacing:2px;">${m.otp}</span><button class="copy-btn" onclick="copyCode('${m.otp}')">Copy</button></div>`).join('');
                } else h += `<div style="color:#ef4444; font-size:11px;">❌ ${acc.msg}</div>`;
                return h + `</div>`;
            }).join('');
        } else div.innerHTML = `<p style="color:#ef4444;">❌ ${rd.msg}</p>`;
    }

    setInterval(async () => {
        const res = await fetch('/api/status');
        const data = await res.json();
        if (data.is_running) {
            document.getElementById('status').innerText = `⚙️ Running B#${data.batch_number} (${data.success}/${data.total})`;
            document.getElementById('status').style.background = '#0ea5e9';
            document.getElementById('startBtn').style.display = 'none';
            document.getElementById('stopBtn').style.display = 'block';
        } else {
            document.getElementById('status').innerText = "🟢 Status: Idle";
            document.getElementById('status').style.background = '#334155';
            document.getElementById('startBtn').style.display = 'block';
            document.getElementById('stopBtn').style.display = 'none';
        }
        const logs = document.getElementById('logs');
        if (data.logs.length > 0) {
            logs.innerHTML = data.logs.map(l => `<div class="${l.color}">[${l.time}] ${l.msg}</div>`).join('');
            logs.scrollTop = logs.scrollHeight;
        }
        if (!document.getElementById('otp-container').classList.contains('hidden')) fetchOTPs();
        loadBatches();
    }, 3000);
</script>
</body></html>
"""

# ══════════════════════════════════════════════════════════
# WEB ROUTES
# ══════════════════════════════════════════════════════════
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('password') == WEB_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('home'))
        return render_template_string(LOGIN_TEMPLATE, error="Wrong Password")
    return render_template_string(LOGIN_TEMPLATE)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/')
def home():
    if not session.get('logged_in'): return redirect(url_for('login'))
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/status')
def get_status():
    if not session.get('logged_in'): return jsonify({"error": "Unauthorized"}), 401
    return jsonify({"is_running": IS_RUNNING, "success": WEB_STATE["success"], "total": WEB_STATE["total"],
                    "batch_number": WEB_STATE.get("batch_number"), "logs": WEB_LOGS})

@app.route('/api/batch/delete/<int:batch_id>', methods=['POST'])
def api_batch_delete(batch_id):
    if not session.get('logged_in'): return jsonify({"error": "Unauthorized"}), 401
    try:
        supabase.table("accounts").delete().eq("batch_id", batch_id).execute()
        supabase.table("failed_accounts").delete().eq("batch_id", batch_id).execute()
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "msg": str(e)}), 500

@app.route('/api/pool/add', methods=['POST'])
def api_pool_add():
    if not session.get('logged_in'): return jsonify({"error": "Unauthorized"}), 401
    data = request.json
    combos = data.get('combos', [])
    added_serials = []
    
    for c in combos:
        parts = c.split('|')
        if len(parts) < 4: continue
        email = parts[0].strip()
        if '@' not in email: continue
        
        try:
            res = supabase.table("email_pool").insert({
                "email": email, 
                "password": parts[1].strip(), 
                "refresh_token": parts[2].strip(), 
                "client_id": parts[3].strip(), 
                "full_combo": c
            }).execute()
            if res.data:
                added_serials.append(str(res.data[0]['id']))
        except Exception as e:
            print(f"Pool insert error: {e}")
            
    if not added_serials:
        return jsonify({"status": "error", "msg": "No valid combos found (need email|pass|token|id)"})
        
    return jsonify({"status": "success", "serials": added_serials})

@app.route('/api/pool/delete', methods=['POST'])
def api_pool_delete():
    if not session.get('logged_in'): return jsonify({"error": "Unauthorized"}), 401
    data = request.json
    
    try:
        if data.get('delete_all'):
            res = supabase.table("email_pool").delete().eq("is_used", False).execute()
            return jsonify({"status": "success", "deleted_count": len(res.data)})
        
        serials = data.get('serials', [])
        if not serials:
            return jsonify({"status": "error", "msg": "No serials provided"})
            
        res = supabase.table("email_pool").delete().in_("id", serials).execute()
        return jsonify({"status": "success", "deleted_count": len(res.data)})
    except Exception as e:
        return jsonify({"status": "error", "msg": str(e)}), 500

@app.route('/api/otps')
def get_otps():
    if not session.get('logged_in'): return jsonify({"error": "Unauthorized"}), 401
    try:
        r = supabase.table("otps").select("email, code").order("created_at", desc=True).limit(50).execute()
        return jsonify(r.data)
    except: return jsonify([])

@app.route('/api/delete_otps', methods=['POST'])
def api_delete_otps():
    if not session.get('logged_in'): return jsonify({"error": "Unauthorized"}), 401
    try:
        supabase.table("otps").delete().neq("id", 0).execute()
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "msg": str(e)}), 500

@app.route('/api/batches')
def api_batches():
    if not session.get('logged_in'): return jsonify({"error": "Unauthorized"}), 401
    try:
        acc = fetch_all_rows("accounts", "batch_id")
        fail = fetch_all_rows("failed_accounts", "batch_id")

        counts = {}
        for row in acc:
            b = row.get('batch_id')
            if b is None: continue
            counts.setdefault(b, {"success": 0, "failed": 0})["success"] += 1
        for row in fail:
            b = row.get('batch_id')
            if b is None: continue
            counts.setdefault(b, {"success": 0, "failed": 0})["failed"] += 1

        result = [{"batch_id": k, "success": v["success"], "failed": v["failed"]}
                  for k, v in sorted(counts.items(), reverse=True)]
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/start', methods=['POST'])
def api_start():
    global IS_RUNNING, WEB_LOGS
    if not session.get('logged_in'): return jsonify({"error": "Unauthorized"}), 401
    if IS_RUNNING: return jsonify({"error": "Already running"}), 400
    data = request.json
    raw = data.get('emails', [])
    if not raw: return jsonify({"error": "No emails"}), 400
    edl = []
    for line in raw:
        e = line.split('|')[0].strip()
        if '@' in e: edl.append({"email": e, "full_combo": line})
    if not edl: return jsonify({"error": "No valid emails"}), 400
    if data['pass_mode'] == 'fix':
        tz = datetime.timezone(datetime.timedelta(hours=6))
        password = f"SOHAV{datetime.datetime.now(tz).day}"
    else:
        password = data.get('custom_pass', '')
        if not password: return jsonify({"error": "Password required"}), 400
    WEB_LOGS = []
    add_web_log(f"Starting {len(edl)} accounts...", "cyan")
    threading.Thread(target=execute_batch, args=(
        None, edl, password, data.get('lang', 'us'),
        data.get('custom_name', '') if data.get('name_mode') == 'custom' else '',
        data.get('hotmail_name', '').strip(),
        data['proxy_mode'] == 'yes', data.get('os_mode', 'ios'), True
    )).start()
    return jsonify({"status": "started"})

@app.route('/api/stop', methods=['POST'])
def api_stop():
    global IS_RUNNING, CURRENT_BATCH_ID
    if not session.get('logged_in'): return jsonify({"error": "Unauthorized"}), 401
    CANCEL_EVENT.set()
    IS_RUNNING = False
    CURRENT_BATCH_ID += 1
    add_web_log("🛑 Stop requested...", "red")
    return jsonify({"status": "stopping"})

@app.route('/api/hotmail_reader', methods=['POST'])
def api_hotmail_reader():
    if not session.get('logged_in'): return jsonify({"error": "Unauthorized"}), 401
    data = request.json
    combos = data.get('combos', [])
    code_type = data.get('type', 'facebook')
    if not combos: return jsonify({"status": "error", "msg": "No combos"})
    results = []
    def process_combo(combo):
        email_addr = combo.split('|')[0] if len(combo.split('|')) > 0 else combo
        code, error = get_code_via_api(combo, code_type=code_type)
        if error: return {"email": email_addr, "status": "error", "msg": error}
        msgs = [{"otp": code}] if code else []
        return {"email": email_addr, "status": "success", "data": msgs}
    with ThreadPoolExecutor(max_workers=5) as ex:
        futures = [ex.submit(process_combo, c) for c in combos]
        for f in futures: results.append(f.result())
    return jsonify({"status": "success", "results": results})

# ─── DOWNLOADS ───────────────────────────────────────────
@app.route('/download/success')
def download_success():
    if not session.get('logged_in'): return redirect(url_for('login'))
    try:
        rows = fetch_all_rows("accounts", "uid, password, cookie, full_combo")
        if not rows: return "No Data", 404
        out = [[x.get('uid'), x.get('password'), x.get('cookie'), x.get('full_combo')] for x in rows]
        mem = _write_csv(['UID', 'PASSWORD', 'COOKIE', 'FULL_MAIL'], out)
        return send_file(mem, as_attachment=True, download_name="all_success.csv", mimetype='text/csv')
    except Exception as e: return f"Error: {e}", 500

@app.route('/download/failed')
def download_failed():
    if not session.get('logged_in'): return redirect(url_for('login'))
    try:
        rows = fetch_all_rows("failed_accounts", "full_combo, reason")
        if not rows: return "No Data", 404
        out = [[x.get('full_combo'), x.get('reason')] for x in rows]
        mem = _write_csv(['FULL_MAIL', 'REASON'], out)
        return send_file(mem, as_attachment=True, download_name="all_failed.csv", mimetype='text/csv')
    except Exception as e: return f"Error: {e}", 500

@app.route('/download/success/<int:batch_id>')
def download_success_batch(batch_id):
    if not session.get('logged_in'): return redirect(url_for('login'))
    try:
        rows = []
        offset = 0
        while True:
            r = supabase.table("accounts").select("uid, password, cookie, full_combo") \
                .eq("batch_id", batch_id).range(offset, offset + 999).execute()
            if not r.data: break
            rows.extend(r.data)
            if len(r.data) < 1000: break
            offset += 1000
        if not rows: return "No data for this batch", 404
        out = [[x.get('uid'), x.get('password'), x.get('cookie'), x.get('full_combo')] for x in rows]
        mem = _write_csv(['UID', 'PASSWORD', 'COOKIE', 'FULL_MAIL'], out)
        return send_file(mem, as_attachment=True, download_name=f"batch_{batch_id}_success.csv", mimetype='text/csv')
    except Exception as e: return f"Error: {e}", 500

@app.route('/download/failed/<int:batch_id>')
def download_failed_batch(batch_id):
    if not session.get('logged_in'): return redirect(url_for('login'))
    try:
        rows = []
        offset = 0
        while True:
            r = supabase.table("failed_accounts").select("full_combo, reason") \
                .eq("batch_id", batch_id).range(offset, offset + 999).execute()
            if not r.data: break
            rows.extend(r.data)
            if len(r.data) < 1000: break
            offset += 1000
        if not rows: return "No data for this batch", 404
        out = [[x.get('full_combo'), x.get('reason')] for x in rows]
        mem = _write_csv(['FULL_MAIL', 'REASON'], out)
        return send_file(mem, as_attachment=True, download_name=f"batch_{batch_id}_failed.csv", mimetype='text/csv')
    except Exception as e: return f"Error: {e}", 500

# ══════════════════════════════════════════════════════════
# BOT 1 (CREATOR)
# ══════════════════════════════════════════════════════════
user_states = {}

def get_main_menu_1(chat_id):
    m = ReplyKeyboardMarkup(resize_keyboard=True)
    m.add(KeyboardButton('🚀 Create Account'))
    m.add(KeyboardButton('🔢 Create from Serial'))
    m.add(KeyboardButton('📩 Hotmail Reader'), KeyboardButton('🔄 Retry Checkpoints'))
    if IS_RUNNING: m.add(KeyboardButton('🛑 Stop Process'))
    if str(chat_id) == ADMIN_ID:
        m.add(KeyboardButton('⚙️ Admin Panel'), KeyboardButton('🔌 Proxies'))
    return m

@bot1.message_handler(commands=['start'])
def send_welcome_1(message):
    chat_id = message.chat.id
    if not is_authorized(chat_id): return bot1.reply_to(message, "⛔ Access Denied!")
    bot1.reply_to(message, f"Welcome!\n🆔 `{chat_id}`", reply_markup=get_main_menu_1(chat_id), parse_mode='Markdown')

@bot1.message_handler(func=lambda m: m.text == '🛑 Stop Process')
def stop_process(message):
    global IS_RUNNING, CURRENT_BATCH_ID
    CANCEL_EVENT.set(); IS_RUNNING = False; CURRENT_BATCH_ID += 1
    user_states[message.chat.id] = {}
    bot1.send_message(message.chat.id, "🛑 Stopping...", reply_markup=get_main_menu_1(message.chat.id))

@bot1.message_handler(func=lambda m: m.text == '🔌 Proxies')
def proxy_menu(message):
    if str(message.chat.id) != ADMIN_ID: return
    m = ReplyKeyboardMarkup(resize_keyboard=True)
    m.add(KeyboardButton('➕ Add Proxy'), KeyboardButton('👀 View Proxies'))
    m.add(KeyboardButton('🗑 Clear Proxies'), KeyboardButton('🌍 Proxy Country'))
    m.add(KeyboardButton('🔙 Back to Menu'))
    bot1.send_message(message.chat.id, f"🔌 **Proxy Manager**\nTotal: `{len(load_proxies())}`\nCurrent Country: `{PROXY_COUNTRY}`", reply_markup=m, parse_mode='Markdown')

@bot1.message_handler(func=lambda m: m.text == '🌍 Proxy Country')
def proxy_country_menu(message):
    if str(message.chat.id) != ADMIN_ID: return
    countries = ['us', 'bd', 'in', 'fr', 'de', 'br', 'id', 'ru', 'gb', 'ca']
    mk = InlineKeyboardMarkup()
    row = []
    for c in countries:
        row.append(InlineKeyboardButton(c.upper(), callback_data=f"set_pc_{c}"))
    for i in range(0, len(row), 3):
        mk.row(*row[i:i+3])
    bot1.send_message(message.chat.id, f"Select Proxy Country (Current: {PROXY_COUNTRY}):", reply_markup=mk)

@bot1.callback_query_handler(func=lambda call: call.data.startswith('set_pc_'))
def set_proxy_country_cb(call):
    global PROXY_COUNTRY
    PROXY_COUNTRY = call.data.split('_')[2]
    bot1.answer_callback_query(call.id, f"Country set to {PROXY_COUNTRY.upper()}")
    bot1.edit_message_text(f"✅ Proxy Country updated to: `{PROXY_COUNTRY.upper()}`", call.message.chat.id, call.message.message_id, parse_mode='Markdown')

@bot1.message_handler(func=lambda m: m.text == '➕ Add Proxy')
def add_proxy(message):
    if str(message.chat.id) != ADMIN_ID: return
    user_states[message.chat.id] = {'step': 'adding_proxy'}
    bot1.send_message(message.chat.id, "Paste proxies (ip:port or ip:port:user:pass)", reply_markup=ReplyKeyboardRemove())

@bot1.message_handler(func=lambda m: user_states.get(m.chat.id, {}).get('step') == 'adding_proxy')
def save_proxy(message):
    chat_id = message.chat.id
    lines = [l.strip() for l in message.text.split('\n') if ':' in l]
    if not lines: return bot1.send_message(chat_id, "❌ No valid proxy")
    added = 0
    for line in lines:
        try:
            supabase.table("proxies").insert({"proxy_str": line}).execute()
            added += 1
        except: pass
    user_states[chat_id] = {}
    bot1.send_message(chat_id, f"✅ Added {added}", reply_markup=get_main_menu_1(chat_id))

@bot1.message_handler(func=lambda m: m.text == '👀 View Proxies')
def view_proxies(message):
    if str(message.chat.id) != ADMIN_ID: return
    p = load_proxies()
    if not p: return bot1.send_message(message.chat.id, "❌ None")
    t = "🔌 **Proxies:**\n\n" + "\n".join([f"`{x}`" for x in p[:20]])
    if len(p) > 20: t += f"\n...and {len(p)-20} more."
    bot1.send_message(message.chat.id, t, parse_mode='Markdown')

@bot1.message_handler(func=lambda m: m.text == '🗑 Clear Proxies')
def clear_proxies(message):
    if str(message.chat.id) != ADMIN_ID: return
    try:
        supabase.table("proxies").delete().neq("proxy_str", "___SOMETHING_IMPOSSIBLE___").execute()
        bot1.send_message(message.chat.id, "✅ All proxies deleted.", reply_markup=get_main_menu_1(message.chat.id))
    except Exception as e: 
        bot1.send_message(message.chat.id, f"Err: {e}", reply_markup=get_main_menu_1(message.chat.id))

@bot1.message_handler(func=lambda m: m.text == '🔙 Back to Menu')
def back_to_menu(message):
    user_states[message.chat.id] = {}
    bot1.send_message(message.chat.id, "Main Menu:", reply_markup=get_main_menu_1(message.chat.id))

@bot1.message_handler(func=lambda m: m.text == '⚙️ Admin Panel')
def admin_panel(message):
    if str(message.chat.id) != ADMIN_ID: return
    user_states[message.chat.id] = {'step': 'admin_panel'}
    m = ReplyKeyboardMarkup(resize_keyboard=True)
    m.add(KeyboardButton('➕ Add User'), KeyboardButton('➖ Remove User'))
    m.add(KeyboardButton('👥 List Users'), KeyboardButton('🔙 Back to Menu'))
    bot1.send_message(message.chat.id, "⚙️ **Admin Panel**", reply_markup=m, parse_mode='Markdown')

@bot1.message_handler(func=lambda m: m.text == '📩 Hotmail Reader')
def hotmail_reader_menu(message):
    chat_id = message.chat.id
    if not is_authorized(chat_id): return
    user_states[chat_id] = {'step': 'reader_type'}
    m = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    m.add('Facebook', 'All (Any Code)'); m.add('Instagram', 'Google'); m.add('🔙 Cancel')
    bot1.send_message(chat_id, "📩 Code Type:", reply_markup=m)

@bot1.message_handler(commands=['create'])
@bot1.message_handler(func=lambda m: m.text == '🚀 Create Account')
def start_creation(message):
    chat_id = message.chat.id
    if not is_authorized(chat_id): return
    if IS_RUNNING: return bot1.send_message(chat_id, "⚠️ Running!")
    user_states[chat_id] = {'step': 'emails'}
    bot1.send_message(chat_id, "📧 **Paste emails** OR **Send a .xlsx / .txt / .csv file** containing combos:", reply_markup=ReplyKeyboardRemove(), parse_mode='Markdown')

@bot1.message_handler(func=lambda m: m.text == '🔢 Create from Serial')
def start_serial_creation(message):
    chat_id = message.chat.id
    if not is_authorized(chat_id): return
    if IS_RUNNING: return bot1.send_message(chat_id, "⚠️ Running!")
    user_states[chat_id] = {'step': 'serial_input'}
    bot1.send_message(chat_id, "🔢 **Paste Serial Numbers:**\n\n(Ex: `1, 2, 5` or `1-5` or one per line)", parse_mode='Markdown', reply_markup=ReplyKeyboardRemove())

@bot1.message_handler(func=lambda m: m.text == '🔄 Retry Checkpoints')
def retry_checkpoints_menu(message):
    chat_id = message.chat.id
    try:
        res = supabase.table("failed_accounts").select("full_combo").eq("reason", "CHECKPOINT").limit(10).execute()
        if not res.data: return bot1.send_message(chat_id, "✅ No checkpoint accounts in database!")
        
        mk = InlineKeyboardMarkup()
        for row in res.data:
            full_combo = row['full_combo']
            email = full_combo.split('|')[0]
            rid = str(uuid.uuid4())[:8]
            CHECKPOINT_RETRY_POOL[rid] = {"email": email, "full_combo": full_combo}
            mk.add(InlineKeyboardButton(f"🔄 {email}", callback_data=f"retry_chk_{rid}"))
        bot1.send_message(chat_id, "🔄 **Checkpoint Retry List:**", reply_markup=mk, parse_mode='Markdown')
    except Exception as e:
        bot1.send_message(chat_id, f"Err: {e}")

@bot1.callback_query_handler(func=lambda call: call.data.startswith('retry_chk_'))
def retry_checkpoint_cb(call):
    rid = call.data.split('_')[2]
    if rid in CHECKPOINT_RETRY_POOL:
        mk = InlineKeyboardMarkup()
        mk.row(InlineKeyboardButton("📱 iOS", callback_data=f"retry_os_{rid}_ios"), InlineKeyboardButton("🤖 Android", callback_data=f"retry_os_{rid}_android"))
        bot1.edit_message_text("📱 **Select OS for Retry:**", call.message.chat.id, call.message.message_id, reply_markup=mk, parse_mode='Markdown')
    else:
        bot1.answer_callback_query(call.id, "Expired.", show_alert=True)

@bot1.callback_query_handler(func=lambda call: call.data.startswith('retry_os_'))
def retry_os_cb(call):
    parts = call.data.split('_')
    rid = parts[2]
    os_type = parts[3]
    if rid not in CHECKPOINT_RETRY_POOL:
        return bot1.answer_callback_query(call.id, "Expired.", show_alert=True)
    
    CHECKPOINT_RETRY_POOL[rid]['os_type'] = os_type
    
    mk = InlineKeyboardMarkup()
    langs = ['us', 'bd', 'de', 'fr', 'br', 'id']
    row = []
    for l in langs:
        row.append(InlineKeyboardButton(l.upper(), callback_data=f"retry_lang_{rid}_{l}"))
    for i in range(0, len(row), 3):
        mk.row(*row[i:i+3])
        
    bot1.edit_message_text(f"🌍 **Select Language for Retry ({os_type.upper()}):**", call.message.chat.id, call.message.message_id, reply_markup=mk, parse_mode='Markdown')

@bot1.callback_query_handler(func=lambda call: call.data.startswith('retry_lang_'))
def retry_lang_cb(call):
    parts = call.data.split('_')
    rid = parts[2]
    lang = parts[3]
    
    if rid not in CHECKPOINT_RETRY_POOL:
        return bot1.answer_callback_query(call.id, "Expired.", show_alert=True)
        
    item = CHECKPOINT_RETRY_POOL.pop(rid)
    chat_id = call.message.chat.id
    
    cfg = LAST_BATCH_CONFIG.get(chat_id, {
        'password': 'SOHAV17', 'custom_name': '', 'use_proxy': True, 'os_type': 'ios'
    })
    
    os_type = item.get('os_type', cfg['os_type'])
    
    bot1.edit_message_text(f"🔄 Retrying `{item['email']}` with {os_type.upper()} | {lang.upper()}...", chat_id, call.message.message_id, parse_mode='Markdown')
    threading.Thread(target=execute_batch, args=(
        chat_id, [{"email": item['email'], "full_combo": item['full_combo']}],
        cfg['password'], lang, cfg['custom_name'], "",
        cfg['use_proxy'], os_type, False
    )).start()

def process_extracted_emails(chat_id, edl):
    if not edl:
        user_states[chat_id] = {}
        return bot1.send_message(chat_id, "❌ No valid emails found. Please try again.", reply_markup=get_main_menu_1(chat_id))
    st = user_states[chat_id]
    st['email_data_list'] = edl
    st['step'] = 'os_mode'
    m = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    m.add('iOS', 'Android'); m.add('🔙 Cancel')
    bot1.send_message(chat_id, f"✅ {len(edl)} emails found.\n📱 OS:", reply_markup=m)

@bot1.message_handler(content_types=['document'])
def handle_document(message):
    chat_id = message.chat.id
    if not is_authorized(chat_id): return
    if chat_id not in user_states or user_states[chat_id].get('step') != 'emails': 
        return bot1.reply_to(message, "⚠️ Please click '🚀 Create Account' first.")
        
    file_info = bot1.get_file(message.document.file_id)
    downloaded_file = bot1.download_file(file_info.file_path)
    
    file_name = message.document.file_name.lower()
    edl = []
    
    try:
        if file_name.endswith('.xlsx'):
            wb = openpyxl.load_workbook(io.BytesIO(downloaded_file), read_only=True, data_only=True)
            ws = wb.active
            for row in ws.iter_rows(values_only=True):
                row_data = [str(cell).strip() for cell in row if cell is not None]
                if not row_data: continue
                
                if len(row_data) >= 4:
                    combo = "|".join(row_data[:4])
                elif len(row_data) == 1:
                    combo = row_data[0]
                else:
                    combo = "|".join(row_data)
                    
                if '@' in combo:
                    email = combo.split('|')[0].strip() if '|' in combo else combo.strip()
                    if '@' in email:
                        edl.append({"email": email, "full_combo": combo})
        elif file_name.endswith('.txt') or file_name.endswith('.csv'):
            text = downloaded_file.decode('utf-8', errors='ignore')
            lines = [l.strip() for l in text.split('\n') if l.strip()]
            for l in lines:
                e = l.split('|')[0].strip() if '|' in l else l.split(',')[0].strip()
                if '@' in e:
                    combo = l.replace(',', '|') if ',' in l and '|' not in l else l
                    edl.append({"email": e, "full_combo": combo})
        else:
            return bot1.reply_to(message, "❌ Unsupported file format. Send .xlsx, .txt, or .csv")
            
        process_extracted_emails(chat_id, edl)
    except Exception as e:
        bot1.send_message(chat_id, f"❌ Error reading file: {e}")
        user_states[chat_id] = {}

@bot1.message_handler(func=lambda m: True)
def handle_inputs(message):
    chat_id = message.chat.id
    if not is_authorized(chat_id): return
    if chat_id not in user_states: return
    st = user_states[chat_id]

    if st['step'] == 'admin_panel':
        if message.text == '➕ Add User':
            st['step'] = 'admin_add_user'
            bot1.send_message(chat_id, "✍️ Enter User ID to authorize:", reply_markup=ReplyKeyboardRemove())
        elif message.text == '➖ Remove User':
            st['step'] = 'admin_remove_user'
            bot1.send_message(chat_id, "✍️ Enter User ID to remove:", reply_markup=ReplyKeyboardRemove())
        elif message.text == '👥 List Users':
            users = load_auth_users()
            bot1.send_message(chat_id, "👥 **Authorized Users:**\n\n" + "\n".join([f"`{u}`" for u in users]), parse_mode='Markdown', reply_markup=get_main_menu_1(chat_id))
            user_states[chat_id] = {}
        else:
            bot1.send_message(chat_id, "❌ Invalid choice.", reply_markup=get_main_menu_1(chat_id))
            user_states[chat_id] = {}

    elif st['step'] == 'admin_add_user':
        try:
            save_auth_user(message.text.strip())
            bot1.send_message(chat_id, f"✅ User `{message.text.strip()}` added!", parse_mode='Markdown', reply_markup=get_main_menu_1(chat_id))
        except Exception as e:
            bot1.send_message(chat_id, f"❌ Error: {e}", reply_markup=get_main_menu_1(chat_id))
        user_states[chat_id] = {}

    elif st['step'] == 'admin_remove_user':
        try:
            remove_auth_user(message.text.strip())
            bot1.send_message(chat_id, f"✅ User `{message.text.strip()}` removed!", parse_mode='Markdown', reply_markup=get_main_menu_1(chat_id))
        except Exception as e:
            bot1.send_message(chat_id, f"❌ Error: {e}", reply_markup=get_main_menu_1(chat_id))
        user_states[chat_id] = {}

    elif st['step'] == 'reader_type':
        t = message.text.lower()
        if 'facebook' in t: st['reader_type'] = 'facebook'
        elif 'all' in t: st['reader_type'] = 'all'
        elif 'instagram' in t: st['reader_type'] = 'instagram'
        elif 'google' in t: st['reader_type'] = 'google'
        elif 'cancel' in t:
            del user_states[chat_id]
            return bot1.send_message(chat_id, "Cancelled.", reply_markup=get_main_menu_1(chat_id))
        else: return bot1.send_message(chat_id, "❌ From buttons.")
        st['step'] = 'hotmail_reader'
        bot1.send_message(chat_id, f"✅ {st['reader_type'].upper()}.\nPaste combos:", reply_markup=ReplyKeyboardRemove())

    elif st['step'] == 'emails':
        lines = [l.strip() for l in message.text.split('\n') if l.strip()]
        edl = []
        for l in lines:
            e = l.split('|')[0].strip()
            if '@' in e: edl.append({"email": e, "full_combo": l})
        process_extracted_emails(chat_id, edl)

    elif st['step'] == 'serial_input':
        text = message.text.strip()
        serial_set = set()
        tokens = re.split(r'[,\s\n]+', text)
        for t in tokens:
            if not t: continue
            if '-' in t:
                try:
                    s, e = map(int, t.split('-'))
                    serial_set.update(range(s, e+1))
                except: pass
            else:
                try: serial_set.add(int(t))
                except: pass
                
        if not serial_set:
            return bot1.send_message(chat_id, "❌ No valid serials found. Try again (ex: 1, 2, 3).")
            
        try:
            serials_list = list(serial_set)
            res = supabase.table("email_pool").select("*").in_("id", serials_list).eq("is_used", False).execute()
            
            if not res.data:
                return bot1.send_message(chat_id, "❌ Serial(s) not found or already used in database.")
                
            edl = []
            fetched_ids = []
            for row in res.data:
                edl.append({"email": row['email'], "full_combo": row['full_combo']})
                fetched_ids.append(row['id'])
                
            supabase.table("email_pool").update({"is_used": True}).in_("id", fetched_ids).execute()
            
            st['email_data_list'] = edl
            st['step'] = 'os_mode'
            m = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
            m.add('iOS', 'Android'); m.add('🔙 Cancel')
            bot1.send_message(chat_id, f"✅ Found {len(edl)} emails from serials.\n📱 OS:", reply_markup=m)
            
        except Exception as e:
            return bot1.send_message(chat_id, f"❌ DB Error: {e}")

    elif st['step'] == 'hotmail_reader':
        lines = [l.strip() for l in message.text.split('\n') if l.strip()]
        ct = st.get('reader_type', 'facebook')
        bot1.send_message(chat_id, f"⏳ Fetching {ct.upper()} for {len(lines)}...", reply_markup=get_main_menu_1(chat_id))
        def bulk(combos):
            res = []
            for c in combos:
                if CANCEL_EVENT.is_set(): res.append("🛑 Cancelled."); break
                ea = c.split('|')[0] if len(c.split('|')) > 0 else c
                code, err = get_code_via_api(c, code_type=ct)
                if code: res.append(f"✅ `{ea}` — `{code}`")
                elif err: res.append(f"❌ `{ea}` — {err}")
                else: res.append(f"⚠️ `{ea}` — No Code")
            out = f"📩 **{ct.upper()}:**\n\n" + "\n".join(res)
            for i in range(0, len(out), 4000):
                bot1.send_message(chat_id, out[i:i+4000], parse_mode='Markdown')
        threading.Thread(target=bulk, args=(lines,)).start()

    elif st['step'] == 'os_mode':
        t = message.text.lower()
        if 'ios' in t: st['os_type'] = 'ios'
        elif 'android' in t: st['os_type'] = 'android'
        elif 'cancel' in t:
            del user_states[chat_id]
            return bot1.send_message(chat_id, "Cancelled.", reply_markup=get_main_menu_1(chat_id))
        else: return bot1.send_message(chat_id, "❌ From buttons.")
        st['step'] = 'password_mode'
        m = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        m.add('Fix Password (SOHAVdd)', 'Custom Password'); m.add('🔙 Cancel')
        bot1.send_message(chat_id, "🔐 Password:", reply_markup=m)

    elif st['step'] == 'password_mode':
        if 'Fix Password' in message.text:
            tz = datetime.timezone(datetime.timedelta(hours=6))
            st['password'] = f"SOHAV{datetime.datetime.now(tz).day}"
            st['step'] = 'proxy_mode'
            bot1.send_message(chat_id, f"✅ `{st['password']}`", parse_mode='Markdown', reply_markup=ReplyKeyboardRemove())
            show_proxy_menu(chat_id)
        elif 'Custom Password' in message.text:
            st['step'] = 'custom_password'
            bot1.send_message(chat_id, "✍️ Enter Password:", reply_markup=ReplyKeyboardRemove())
        elif 'Cancel' in message.text:
            del user_states[chat_id]
            return bot1.send_message(chat_id, "Cancelled.", reply_markup=get_main_menu_1(chat_id))
        else: bot1.send_message(chat_id, "❌ From buttons.")

    elif st['step'] == 'custom_password':
        st['password'] = message.text.strip()
        st['step'] = 'proxy_mode'
        bot1.send_message(chat_id, "✅ Set.", reply_markup=ReplyKeyboardRemove())
        show_proxy_menu(chat_id)

    elif st['step'] == 'proxy_mode':
        if 'No Proxy' in message.text: st['use_proxy'] = False; go = True
        elif 'Use Proxy' in message.text:
            if len(load_proxies()) == 0: return bot1.send_message(chat_id, "⚠️ No proxies!")
            st['use_proxy'] = True; go = True
        elif 'Cancel' in message.text:
            del user_states[chat_id]
            return bot1.send_message(chat_id, "Cancelled.", reply_markup=get_main_menu_1(chat_id))
        else: go = False; bot1.send_message(chat_id, "❌ From buttons.")
        if go:
            st['step'] = 'name_mode_com'
            m = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
            m.add('Auto Name', 'Custom Name'); m.add('🔙 Cancel')
            bot1.send_message(chat_id, "👤 Name Mode (.com):", reply_markup=m)

    elif st['step'] == 'name_mode_com':
        if message.text == 'Custom Name':
            st['step'] = 'custom_name_com'
            bot1.send_message(chat_id, "✍️ .com Name: First Last", reply_markup=ReplyKeyboardRemove())
        elif 'Cancel' in message.text:
            del user_states[chat_id]
            return bot1.send_message(chat_id, "Cancelled.", reply_markup=get_main_menu_1(chat_id))
        else:
            st['custom_name'] = ''
            st['step'] = 'language'
            show_languages(chat_id)

    elif st['step'] == 'custom_name_com':
        st['custom_name'] = message.text.strip()
        st['step'] = 'language'
        show_languages(chat_id)

    elif st['step'] == 'language':
        if 'Cancel' in message.text:
            del user_states[chat_id]
            return bot1.send_message(chat_id, "Cancelled.", reply_markup=get_main_menu_1(chat_id))
        st['lang'] = message.text.strip().lower()[:2]
        start_batch_from_state(chat_id, st)

def show_proxy_menu(chat_id):
    n = len(load_proxies())
    m = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    m.add('No Proxy (Direct)', f"Use Proxy ({n} Loaded)"); m.add('🔙 Cancel')
    bot1.send_message(chat_id, "🌐 Proxy:", reply_markup=m)

def show_languages(chat_id):
    m = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True, row_width=4)
    m.add(*[KeyboardButton(c) for c in LANG_MAP.keys()]); m.add(KeyboardButton('🔙 Cancel'))
    bot1.send_message(chat_id, "🌍 Language:", reply_markup=m)

def start_batch_from_state(chat_id, st):
    global CURRENT_LANG_HEADER, LAST_BATCH_CONFIG
    lang = st['lang']
    CURRENT_LANG_HEADER = LANG_MAP.get(lang, LANG_MAP['us'])[0]
    st['step'] = None
    
    # Save config for retries
    LAST_BATCH_CONFIG[chat_id] = {
        'password': st['password'],
        'lang': lang,
        'custom_name': st['custom_name'],
        'hotmail_name': "",
        'use_proxy': st['use_proxy'],
        'os_type': st['os_type']
    }
    
    bot1.send_message(chat_id, f"⚙️ {len(st['email_data_list'])} accounts | Lang: {lang.upper()} | OS: {st['os_type'].upper()}...", reply_markup=ReplyKeyboardRemove())
    threading.Thread(target=execute_batch, args=(
        chat_id, st['email_data_list'], st['password'], lang,
        st['custom_name'], "",
        st['use_proxy'], st['os_type'], False
    )).start()

# ══════════════════════════════════════════════════════════
# BOT 2 (DOWNLOAD + BATCH)
# ══════════════════════════════════════════════════════════
def get_main_menu_2(chat_id):
    m = ReplyKeyboardMarkup(resize_keyboard=True)
    m.add(KeyboardButton('📩 OTP List'))
    m.add(KeyboardButton('🗑 Delete OTPs'))
    m.add(KeyboardButton('📦 Batch Downloads'))
    m.add(KeyboardButton('📁 Download ALL Success'), KeyboardButton('❌ Download ALL Failed'))
    return m

@bot2.message_handler(commands=['start'])
def send_welcome_2(message):
    chat_id = message.chat.id
    if not is_authorized(chat_id): return bot2.reply_to(message, "⛔ Access Denied!")
    bot2.reply_to(message, "Download Bot 📁", reply_markup=get_main_menu_2(chat_id))

@bot2.message_handler(func=lambda m: m.text == '📩 OTP List')
def show_otps(message):
    chat_id = message.chat.id
    if not is_authorized(chat_id): return
    try:
        r = supabase.table("otps").select("email, code").order("created_at", desc=True).limit(50).execute()
        if not r.data: return bot2.send_message(chat_id, "❌ No OTPs.")
        msg = "📩 **Recent OTPs:**\n\n"
        for o in r.data: msg += f"`{o['email']}` — `{o['code']}`\n"
        bot2.send_message(chat_id, msg, parse_mode='Markdown')
    except Exception as e: bot2.send_message(chat_id, f"Err: {e}")

@bot2.message_handler(func=lambda m: m.text == '🗑 Delete OTPs')
def delete_otps_bot(message):
    if not is_authorized(message.chat.id): return
    try:
        supabase.table("otps").delete().neq("id", 0).execute()
        bot2.send_message(message.chat.id, "✅ All OTPs deleted.")
    except Exception as e: bot2.send_message(message.chat.id, f"Err: {e}")

@bot2.message_handler(commands=['getcsv'])
@bot2.message_handler(func=lambda m: m.text == '📁 Download ALL Success')
def send_csv_all(message):
    if not is_authorized(message.chat.id): return
    try:
        rows = fetch_all_rows("accounts", "uid, password, cookie, full_combo")
        if not rows: return bot2.send_message(message.chat.id, "❌ No Data.")
        out = [[x.get('uid'), x.get('password'), x.get('cookie'), x.get('full_combo')] for x in rows]
        mem = _write_csv(['UID', 'PASSWORD', 'COOKIE', 'FULL_MAIL'], out)
        bot2.send_document(message.chat.id, mem, visible_file_name="all_success.csv", caption="All Success")
    except Exception as e: bot2.send_message(message.chat.id, f"Err: {e}")

@bot2.message_handler(commands=['getfailed'])
@bot2.message_handler(func=lambda m: m.text == '❌ Download ALL Failed')
def send_failed_all(message):
    if not is_authorized(message.chat.id): return
    try:
        rows = fetch_all_rows("failed_accounts", "full_combo, reason")
        if not rows: return bot2.send_message(message.chat.id, "❌ No Data.")
        out = [[x.get('full_combo'), x.get('reason')] for x in rows]
        mem = _write_csv(['FULL_MAIL', 'REASON'], out)
        bot2.send_document(message.chat.id, mem, visible_file_name="all_failed.csv", caption="All Failed")
    except Exception as e: bot2.send_message(message.chat.id, f"Err: {e}")

@bot2.message_handler(func=lambda m: m.text == '📦 Batch Downloads')
def batch_menu_bot(message):
    chat_id = message.chat.id
    if not is_authorized(chat_id): return
    try:
        acc = fetch_all_rows("accounts", "batch_id, created_at")
        fail = fetch_all_rows("failed_accounts", "batch_id, created_at")
        counts = {}
        dates = {}
        
        for row in acc:
            b = row.get('batch_id')
            if b is None: continue
            counts.setdefault(b, {"s": 0, "f": 0})["s"] += 1
            if b not in dates and row.get('created_at'):
                dates[b] = row['created_at'][:10] # YYYY-MM-DD
                
        for row in fail:
            b = row.get('batch_id')
            if b is None: continue
            counts.setdefault(b, {"s": 0, "f": 0})["f"] += 1
            if b not in dates and row.get('created_at'):
                dates[b] = row['created_at'][:10]
                
        if not counts: return bot2.send_message(chat_id, "❌ No batches yet.")
        
        today_str = datetime.datetime.now().strftime("%Y-%m-%d")
        
        mk = InlineKeyboardMarkup()
        has_today = False
        for bn in sorted(counts.keys(), reverse=True):
            b_date = dates.get(bn, "Unknown")
            if b_date == today_str:
                c = counts[bn]
                label = f"Batch #{bn} — ✅{c['s']} ❌{c['f']}"
                mk.add(InlineKeyboardButton(label, callback_data=f"bi_{bn}"))
                has_today = True
                
        if not has_today:
            mk.add(InlineKeyboardButton("No batches today.", callback_data="none"))
            
        mk.add(InlineKeyboardButton("📅 Previous Days", callback_data="b_days"))
        bot2.send_message(chat_id, "📦 **Today's Batches:**", reply_markup=mk, parse_mode='Markdown')
    except Exception as e: bot2.send_message(chat_id, f"Err: {e}")

@bot2.callback_query_handler(func=lambda c: c.data == "b_days")
def batch_days_cb(call):
    try:
        acc = fetch_all_rows("accounts", "batch_id, created_at")
        dates = set()
        for row in acc:
            if row.get('created_at'): dates.add(row['created_at'][:10])
            
        today_str = datetime.datetime.now().strftime("%Y-%m-%d")
        prev_dates = sorted([d for d in dates if d < today_str], reverse=True)[:14] # last 14 days
        
        if not prev_dates:
            return bot2.answer_callback_query(call.id, "No previous days found.", show_alert=True)
            
        mk = InlineKeyboardMarkup()
        for d in prev_dates:
            mk.add(InlineKeyboardButton(f"📅 {d}", callback_data=f"b_date_{d}"))
        mk.add(InlineKeyboardButton("🔙 Back", callback_data="b_today"))
        
        bot2.edit_message_text("📅 **Select Previous Day:**", call.message.chat.id, call.message.message_id, reply_markup=mk)
    except Exception as e:
        bot2.answer_callback_query(call.id, f"Err: {e}", show_alert=True)

@bot2.callback_query_handler(func=lambda c: c.data == "b_today")
def batch_today_cb(call):
    call.message.text = "📦 Batch Downloads"
    batch_menu_bot(call.message)

@bot2.callback_query_handler(func=lambda c: c.data.startswith("b_date_"))
def batch_date_cb(call):
    d_str = call.data.replace("b_date_", "")
    try:
        acc = fetch_all_rows("accounts", "batch_id, created_at")
        fail = fetch_all_rows("failed_accounts", "batch_id, created_at")
        counts = {}
        
        for row in acc:
            if row.get('created_at', '').startswith(d_str):
                b = row.get('batch_id')
                if b: counts.setdefault(b, {"s": 0, "f": 0})["s"] += 1
                
        for row in fail:
            if row.get('created_at', '').startswith(d_str):
                b = row.get('batch_id')
                if b: counts.setdefault(b, {"s": 0, "f": 0})["f"] += 1
                
        if not counts:
            return bot2.answer_callback_query(call.id, "No batches on this day.", show_alert=True)
            
        mk = InlineKeyboardMarkup()
        for bn in sorted(counts.keys(), reverse=True):
            c = counts[bn]
            label = f"Batch #{bn} — ✅{c['s']} ❌{c['f']}"
            mk.add(InlineKeyboardButton(label, callback_data=f"bi_{bn}"))
        mk.add(InlineKeyboardButton("🔙 Back", callback_data="b_days"))
        
        bot2.edit_message_text(f"📦 **Batches for {d_str}:**", call.message.chat.id, call.message.message_id, reply_markup=mk)
    except Exception as e:
        bot2.answer_callback_query(call.id, f"Err: {e}", show_alert=True)

@bot2.callback_query_handler(func=lambda c: c.data.startswith("bi_"))
def batch_info_cb(call):
    bn = int(call.data.split("_")[1])
    mk = InlineKeyboardMarkup()
    mk.add(InlineKeyboardButton("✅ Success CSV", callback_data=f"bs_{bn}"), InlineKeyboardButton("❌ Failed CSV", callback_data=f"bf_{bn}"))
    mk.add(InlineKeyboardButton("🗑 Delete Batch", callback_data=f"bd_{bn}"))
    mk.add(InlineKeyboardButton("🔙 Back", callback_data="b_today"))
    label = f"Batch #{bn}"
    bot2.edit_message_text(f"📦 **{label}** — choose download:", call.message.chat.id, call.message.message_id, reply_markup=mk, parse_mode='Markdown')

@bot2.callback_query_handler(func=lambda c: c.data.startswith("bs_") or c.data.startswith("bf_"))
def batch_dl_cb(call):
    parts = call.data.split("_")
    is_s = parts[0] == "bs"
    bn = int(parts[1])
    chat_id = call.message.chat.id
    try:
        rows = []
        offset = 0
        tbl = "accounts" if is_s else "failed_accounts"
        cols = "uid, password, cookie, full_combo" if is_s else "full_combo, reason"
        while True:
            r = supabase.table(tbl).select(cols).eq("batch_id", bn).range(offset, offset + 999).execute()
            if not r.data: break
            rows.extend(r.data)
            if len(r.data) < 1000: break
            offset += 1000
        if not rows: return bot2.answer_callback_query(call.id, "No data.", show_alert=True)

        if is_s:
            out = [[x.get('uid'), x.get('password'), x.get('cookie'), x.get('full_combo')] for x in rows]
            hdr = ['UID', 'PASSWORD', 'COOKIE', 'FULL_MAIL']; fn = f"batch_{bn}_success.csv"; cap = f"Batch #{bn} — Success"
        else:
            out = [[x.get('full_combo'), x.get('reason')] for x in rows]
            hdr = ['FULL_MAIL', 'REASON']; fn = f"batch_{bn}_failed.csv"; cap = f"Batch #{bn} — Failed"
        mem = _write_csv(hdr, out)
        bot2.send_document(chat_id, mem, visible_file_name=fn, caption=cap)
        bot2.answer_callback_query(call.id, "Sent!")
    except Exception as e:
        bot2.answer_callback_query(call.id, f"Err: {e}", show_alert=True)

@bot2.callback_query_handler(func=lambda c: c.data.startswith("bd_"))
def batch_del_cb(call):
    bn = int(call.data.split("_")[1])
    try:
        supabase.table("accounts").delete().eq("batch_id", bn).execute()
        supabase.table("failed_accounts").delete().eq("batch_id", bn).execute()
        bot2.answer_callback_query(call.id, f"Batch #{bn} Deleted Successfully!", show_alert=True)
        bot2.delete_message(call.message.chat.id, call.message.message_id)
    except Exception as e:
        bot2.answer_callback_query(call.id, f"Err: {e}", show_alert=True)

@bot2.callback_query_handler(func=lambda c: c.data == "bb")
def batch_back_cb(call):
    call.message.text = '📦 Batch Downloads'
    batch_menu_bot(call.message)

# ══════════════════════════════════════════════════════════
# START
# ══════════════════════════════════════════════════════════
if __name__ == '__main__':
    t1 = threading.Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080))))
    t1.daemon = True
    t1.start()
    t2 = threading.Thread(target=bot2.infinity_polling)
    t2.daemon = True
    t2.start()
    print("Running...")
    bot1.infinity_polling()
