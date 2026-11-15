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
from concurrent.futures import ThreadPoolExecutor
from flask import Flask, request, jsonify, send_file, render_template_string, session, redirect, url_for
from supabase import create_client, Client

try:
    from curl_cffi import requests as cureq
except ImportError:
    print("\033[91m[!] curl_cffi not found!\033[0m")
    exit()

# ══════════════════════════════════════════════════════════
# CONFIGURATIONS & DATABASE (Ekhane Supabase Link Boshao)
# ══════════════════════════════════════════════════════════
BOT_TOKEN_1 = "9025360567:AAEJ2Jq2FSAVpDOVC3UCPYViQE9-sNI7NSk"
BOT_TOKEN_2 = "9028640496:AAG8y-z28g98sjYfEjLC5yanhhA-YgP9zHQ"
ADMIN_ID = "6408202140"
WEB_PASSWORD = "SOHAV_ADMIN"

SUPABASE_URL = "https://plojfqqvqnddxibaxrqr.supabase.co/rest/v1/" # <-- Tomar Project URL
SUPABASE_KEY = "your-anon-key" # <-- Tomar anon key

try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    print(f"Supabase Connection Error: {e}")

bot1 = telebot.TeleBot(BOT_TOKEN_1)
bot2 = telebot.TeleBot(BOT_TOKEN_2)

# ══════════════════════════════════════════════════════════
# GLOBAL VARIABLES
# ══════════════════════════════════════════════════════════
IS_RUNNING = False
CANCEL_FLAG = False
WEB_OTPS = []

# ══════════════════════════════════════════════════════════
# 50 ANDROID USER-AGENTS
# ══════════════════════════════════════════════════════════
ANDROID_USER_AGENTS = [
    "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/156.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.6422.147 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.113 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12; SM-A525F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.6312.118 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 11; M2101K6G) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.119 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.6167.165 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.6478.122 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; CPH2447) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.6422.147 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12; V2134) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.113 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 11; RMX3085) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.6312.118 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 10; Redmi Note 8 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.119 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; SM-F946B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.6533.103 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; Pixel 6a) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.6478.122 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.6422.147 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 11; moto g(60)) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.113 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 10; Nokia G20) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.6312.118 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; SM-S928B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.6613.88 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; 2201117TG) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.6533.103 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12; CPH2387) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.6478.122 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 11; V2307) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.6422.147 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 10; SM-A515F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.113 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; Pixel Fold) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.6668.81 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; SM-A546B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.6613.88 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12; 23021RAAEG) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.6533.103 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 11; TECNO KE5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.6478.122 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 10; Infinix X6811) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.6422.147 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; SM-S911B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.6723.58 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; Pixel 7 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.6668.81 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12; RMX3741) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.6613.88 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 11; CPH2499) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.6533.103 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 10; SM-M325F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.6478.122 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; SM-G996B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.6778.39 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; 220333QNY) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.6723.58 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12; V2225) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.6668.81 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 11; moto g84 5G) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.6613.88 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 10; Pixel 4a) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.6533.103 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; SM-A346E) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.6834.79 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; SM-S911U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.6778.39 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12; Nokia X20) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.6723.58 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 11; Infinix X6837) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.6668.81 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 10; TECNO LH7n) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.6613.88 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.6943.42 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; SM-A145F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.6834.79 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12; Redmi Note 11) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.6778.39 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 11; CPH2461) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.6723.58 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 10; SM-A135F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.6668.81 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; SM-M515F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.6998.135 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; V2307) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.6943.42 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12; RMX3630) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.6834.79 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 11; moto g(30)) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.6778.39 Mobile Safari/537.36"
]

# ══════════════════════════════════════════════════════════
# FLASK WEB SERVER SETUP
# ══════════════════════════════════════════════════════════
app = Flask('')
app.secret_key = "SOHAV_SECRET_KEY_123"
WEB_LOGS = []
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
PROXY_FILE = "proxies.txt" 
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
# HOTMAIL OTP AUTO-FETCHER
# ══════════════════════════════════════════════════════════
def fetch_otp_from_hotmail(email_addr, refresh_token, client_id, chat_id=None):
    global CANCEL_FLAG
    for attempt in range(2400): 
        if CANCEL_FLAG: return
        time.sleep(3)
        try:
            token_res = requests.post("https://login.microsoftonline.com/common/oauth2/v2.0/token", data={
                "client_id": client_id,
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "scope": "https://graph.microsoft.com/.default offline_access"
            }, timeout=10)
            
            access_token = token_res.json().get("access_token")
            if not access_token: continue

            msg_res = requests.get(
                "https://graph.microsoft.com/v1.0/me/messages?$top=10&$orderby=receivedDateTime%20desc&$select=subject,body,receivedDateTime,from",
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=10
            )
            
            messages = msg_res.json().get("value", [])
            for msg in messages:
                body = msg.get("body", {}).get("content", "")
                subject = msg.get("subject", "")
                sender = msg.get("from", {}).get("emailAddress", {}).get("address", "")
                
                if "facebook" in sender.lower() or "facebook" in subject.lower() or "code" in subject.lower():
                    clean_body = re.sub(r'<[^>]+>', ' ', body)
                    match = re.search(r'\b(\d{5})\b', clean_body)
                    if not match: match = re.search(r'\b(\d{6})\b', clean_body)

                    if match:
                        code = match.group(1)
                        
                        # Save to Supabase
                        try:
                            supabase.table("otps").insert({
                                "email": email_addr,
                                "code": code
                            }).execute()
                        except Exception as e:
                            print(f"Supabase OTP Error: {e}")

                        # Add to Web List
                        WEB_OTPS.append({"email": email_addr, "code": code})
                        add_web_log(f"OTP FOUND: {code} for {email_addr}", "green")
                        
                        if chat_id: 
                            bot1.send_message(chat_id, f"📩 **OTP FOUND for `{email_addr}`**\n\n🔑 Code: `{code}`\n\n_Copied from Hotmail inbox!_", parse_mode='Markdown')
                        return 
        except Exception:
            pass

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

IOS_USER_AGENTS = [
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1"
]
SCREEN_PROFILES = [(390, 844, 3.0), (393, 852, 3.0), (428, 926, 3.0), (430, 932, 3.0), (375, 812, 3.0)]

def build_fingerprint(os_type="ios"):
    if os_type == "android":
        ua = random.choice(ANDROID_USER_AGENTS)
        impersonate = "chrome120"
    else:
        ua = random.choice(IOS_USER_AGENTS)
        impersonate = "safari15_5"

    sw, sh, dpr = random.choice(SCREEN_PROFILES)
    pringer_hash = hashlib.sha256(f"{ua}-{sw}x{sh}-{uuid.uuid4()}".encode()).hexdigest()[:32]
    
    return {
        "impersonate": impersonate, "pringer": pringer_hash,
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

def fb_create_account(email, password, lang_code, custom_fname, custom_lname, use_proxy, os_type):
    session = cureq.Session()
    proxy = get_random_proxy() if use_proxy else None
    
    fp = build_fingerprint(os_type)
    cookies_warm, lsd_token = warmup_session(session, fp, proxy)
    time.sleep(random.uniform(2.0, 4.0))

    reg_fp = build_fingerprint(os_type)
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

def execute_batch(chat_id, email_data_list, password, lang, custom_name, use_proxy, os_type, is_web=False):
    global IS_RUNNING, WEB_STATE, CANCEL_FLAG
    IS_RUNNING = True
    CANCEL_FLAG = False
    success_count = 0; fail_count = 0
    WEB_STATE["total"] = len(email_data_list); WEB_STATE["success"] = 0
    
    def process_one(item, idx, total):
        nonlocal success_count, fail_count
        if CANCEL_FLAG: return
        WEB_STATE["current"] = idx
        email = item['email']; full_combo = item['full_combo']
        c_fname = custom_name[0] if custom_name else None; c_lname = custom_name[1] if custom_name else None
        
        status_msg = None
        if not is_web and chat_id: status_msg = bot1.send_message(chat_id, f"⏳ [{idx}/{total}] Processing: `{email}`", parse_mode='Markdown')
        else: add_web_log(f"[{idx}/{total}] Processing: {email}", "cyan")
        
        res, err = fb_create_account(email, password, lang, c_fname, c_lname, use_proxy, os_type)
        
        if res:
            success_count += 1; WEB_STATE["success"] = success_count
            
            # Save to Supabase
            try:
                supabase.table("accounts").insert({
                    "email": email,
                    "password": password,
                    "uid": res['uid'],
                    "cookie": res['cookie'],
                    "full_combo": full_combo
                }).execute()
            except Exception as e:
                print(f"Supabase Save Error: {e}")
            
            msg_text = f"✅ **ACCOUNT CREATED!**\n\n📧 Email: `{email}`"
            
            if not is_web and chat_id: bot1.edit_message_text(msg_text, chat_id=chat_id, message_id=status_msg.message_id, parse_mode='Markdown')
            else: add_web_log(f"[+] SUCCESS: {email}", "green")
            
            resend_otp(res['session'], res['uid'], res['proxy'])
            
            combo_parts = full_combo.split('|')
            if len(combo_parts) >= 4:
                refresh_token = combo_parts[2].strip()
                client_id = combo_parts[3].strip()
                threading.Thread(target=fetch_otp_from_hotmail, args=(email, refresh_token, client_id, chat_id if not is_web else None)).start()
        else:
            fail_count += 1
            
            # Save to Supabase
            try:
                supabase.table("failed_accounts").insert({
                    "full_combo": full_combo,
                    "reason": err
                }).execute()
            except Exception as e:
                print(f"Supabase Error: {e}")

            fail_text = f"❌ `{email}` Failed: {err}"
            if not is_web and chat_id: bot1.edit_message_text(fail_text, chat_id=chat_id, message_id=status_msg.message_id, parse_mode='Markdown')
            else: add_web_log(fail_text, "red")

    with ThreadPoolExecutor(max_workers=len(email_data_list)) as executor:
        futures = [executor.submit(process_one, item, i+1, len(email_data_list)) for i, item in enumerate(email_data_list)]
        for future in futures: future.result()

    IS_RUNNING = False
    if CANCEL_FLAG:
        finish_msg = f"🛑 **Batch Cancelled!**\n\n✅ Total Success: {success_count}\n❌ Total Failed: {fail_count}"
    else:
        finish_msg = f"🎉 **Batch Finished!**\n\n✅ Total Success: {success_count}\n❌ Total Failed: {fail_count}\n\n👉 _Type /start to open menu again._"
    
    if not is_web and chat_id: 
        bot1.send_message(chat_id, finish_msg, parse_mode='Markdown', reply_markup=get_main_menu_1(chat_id))
    else: 
        add_web_log(f"Finished! Success: {success_count}, Failed: {fail_count}", "yellow")

# ══════════════════════════════════════════════════════════
# WEB DASHBOARD
# ══════════════════════════════════════════════════════════
LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>SOHAV App Login</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background: #0f172a; color: white; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; padding: 20px; box-sizing: border-box; }
        .card { background: #1e293b; padding: 30px 20px; border-radius: 16px; width: 100%; max-width: 350px; box-shadow: 0 10px 25px rgba(0,0,0,0.5); text-align: center; }
        h2 { margin-top: 0; color: #38bdf8; font-size: 24px; }
        input { width: 100%; padding: 14px; margin: 15px 0; background: #0f172a; border: 1px solid #334155; border-radius: 10px; color: white; font-size: 16px; box-sizing: border-box; }
        button { width: 100%; padding: 14px; background: #0ea5e9; color: white; border: none; border-radius: 10px; font-weight: bold; font-size: 16px; cursor: pointer; }
        button:active { background: #0284c7; }
        .error { color: #f87171; font-size: 14px; margin-top: 10px; }
    </style>
</head>
<body>
    <div class="card">
        <h2>🔒 Login</h2>
        <form method="POST">
            <input type="password" name="password" placeholder="Enter Password" required>
            <button type="submit">Unlock App</button>
        </form>
        {% if error %}<p class="error">{{ error }}</p>{% endif %}
    </div>
</body>
</html>
"""

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <meta name="theme-color" content="#0f172a">
    <title>SOHAV Creator App</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background: #0f172a; color: #e2e8f0; margin: 0; padding-bottom: 80px; }
        .header { background: #1e293b; padding: 15px 20px; position: sticky; top: 0; z-index: 100; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); }
        .header h1 { font-size: 18px; margin: 0; color: #38bdf8; }
        .status-bar { padding: 10px 20px; font-size: 13px; font-weight: bold; text-align: center; background: #334155; color: white; }
        .content { padding: 20px; }
        .card { background: #1e293b; padding: 15px; border-radius: 12px; margin-bottom: 15px; }
        label { display: block; font-size: 13px; color: #94a3b8; margin-bottom: 8px; font-weight: 600; }
        textarea, select, input { width: 100%; padding: 12px; background: #0f172a; border: 1px solid #334155; border-radius: 8px; color: white; font-size: 15px; margin-bottom: 12px; box-sizing: border-box; }
        textarea { resize: vertical; min-height: 100px; }
        .btn { width: 100%; padding: 14px; background: #0ea5e9; color: white; border: none; border-radius: 10px; font-weight: bold; font-size: 16px; cursor: pointer; }
        .btn.stop { background: #ef4444; display: none; }
        .btn:active { opacity: 0.8; }
        .btn-row { display: flex; gap: 10px; margin-top: 10px; }
        .btn-row .btn { flex: 1; font-size: 14px; padding: 12px; }
        .btn-row .btn.success { background: #10b981; }
        .btn-row .btn.failed { background: #ef4444; }
        
        #otp-container { display: none; background: #064e3b; border: 1px solid #10b981; padding: 15px; border-radius: 12px; margin-bottom: 15px; }
        .otp-item { display: flex; justify-content: space-between; align-items: center; background: #0f172a; padding: 10px; border-radius: 8px; margin-bottom: 8px; border-left: 4px solid #10b981; }
        .otp-code { font-family: monospace; font-size: 18px; font-weight: bold; color: #4ade80; letter-spacing: 2px; }
        .otp-email { font-size: 11px; color: #94a3b8; display: block; margin-bottom: 4px; }
        .copy-btn { background: #0ea5e9; color: white; border: none; border-radius: 6px; padding: 6px 12px; font-size: 12px; font-weight: bold; cursor: pointer; }
        .copy-btn:active { background: #0284c7; }

        #logs { background: #000; height: 200px; overflow-y: auto; padding: 10px; border-radius: 8px; font-family: monospace; font-size: 12px; border: 1px solid #334155; margin-top: 15px; color: #ccc; }
        .log-line { margin-bottom: 4px; }
        .cyan { color: #22d3ee; } .green { color: #4ade80; } .red { color: #f87171; } .yellow { color: #fbbf24; } .white { color: #e2e8f0; }
        
        .bottom-nav { position: fixed; bottom: 0; width: 100%; background: #1e293b; display: flex; border-top: 1px solid #334155; padding-bottom: env(safe-area-inset-bottom); }
        .nav-item { flex: 1; text-align: center; padding: 15px 0; color: #94a3b8; font-size: 12px; text-decoration: none; font-weight: bold; }
        .nav-item.active { color: #0ea5e9; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 Creator App</h1>
        <span style="font-size:12px; color:#94a3b8;">v2.3</span>
    </div>
    <div class="status-bar" id="status">Status: Idle</div>

    <div class="content" id="mainForm">
    
        <div id="otp-container">
            <label style="color:#4ade80; margin-bottom:10px;">📩 Recent OTPs</label>
            <div id="otp-list"></div>
        </div>

        <div class="card">
            <label>Emails / Combos</label>
            <textarea id="emails" placeholder="email|password|refresh_token|client_id"></textarea>

            <label>OS Mode</label>
            <select id="osMode">
                <option value="ios">iOS (Safari)</option>
                <option value="android">Android (Chrome)</option>
            </select>

            <label>Password Mode</label>
            <select id="passMode" onchange="togglePass()">
                <option value="fix">Fix Password (SOHAVdd)</option>
                <option value="custom">Custom Password</option>
            </select>
            <input type="text" id="customPass" placeholder="Enter Custom Password" style="display:none;">

            <label>Proxy Mode</label>
            <select id="proxyMode">
                <option value="no">No Proxy (Direct)</option>
                <option value="yes">Use Proxy (Auto)</option>
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

            <button class="btn" id="startBtn" onclick="startBatch()">▶ START PROCESS</button>
            <button class="btn stop" id="stopBtn" onclick="stopBatch()">🛑 STOP PROCESS</button>
        </div>

        <div class="card">
            <label>Downloads (From Cloud)</label>
            <div class="btn-row">
                <a href="/download/success" class="btn success" style="text-decoration:none; text-align:center;">📁 Success CSV</a>
                <a href="/download/failed" class="btn failed" style="text-decoration:none; text-align:center;">❌ Failed CSV</a>
            </div>
        </div>

        <label style="margin-top:10px;">Live Logs</label>
        <div id="logs"></div>
    </div>

    <div class="bottom-nav">
        <a href="#" class="nav-item active">🏠 Home</a>
        <a href="#" class="nav-item" onclick="window.location.reload()">🔄 Refresh</a>
        <a href="/logout" class="nav-item" style="color:#ef4444;">🚪 Logout</a>
    </div>

<script>
    function togglePass() {
        document.getElementById('customPass').style.display = document.getElementById('passMode').value === 'custom' ? 'block' : 'none';
    }
    function toggleName() {
        document.getElementById('customName').style.display = document.getElementById('nameMode').value === 'custom' ? 'block' : 'none';
    }

    function copyCode(code) {
        navigator.clipboard.writeText(code).then(() => {
            alert("Code Copied: " + code);
        }).catch(err => {
            console.error('Failed to copy: ', err);
        });
    }

    async function startBatch() {
        const rawEmails = document.getElementById('emails').value.trim();
        if (!rawEmails) return alert("Please enter emails!");
        
        const osMode = document.getElementById('osMode').value;
        const passMode = document.getElementById('passMode').value;
        const customPass = document.getElementById('customPass').value;
        const proxyMode = document.getElementById('proxyMode').value;
        const nameMode = document.getElementById('nameMode').value;
        const customName = document.getElementById('customName').value;
        const lang = document.getElementById('lang').value;

        document.getElementById('logs').innerHTML = '';
        document.getElementById('startBtn').style.display = 'none';
        document.getElementById('stopBtn').style.display = 'block';
        document.getElementById('otp-container').style.display = 'none';
        document.getElementById('otp-list').innerHTML = '';

        const res = await fetch('/api/start', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                emails: rawEmails.split('\\n').map(e => e.trim()).filter(e => e),
                os_mode: osMode,
                pass_mode: passMode,
                custom_pass: customPass,
                proxy_mode: proxyMode,
                name_mode: nameMode,
                custom_name: customName,
                lang: lang
            })
        });
    }

    async function stopBatch() {
        if (!confirm("Are you sure you want to stop the process?")) return;
        await fetch('/api/stop', { method: 'POST' });
        document.getElementById('stopBtn').style.display = 'none';
    }

    let isRunning = false;

    setInterval(async () => {
        const res = await fetch('/api/status');
        const data = await res.json();
        
        isRunning = data.is_running;

        if (data.is_running) {
            document.getElementById('status').innerText = `⚙️ Running (${data.success}/${data.total})`;
            document.getElementById('status').style.background = '#0ea5e9';
            document.getElementById('startBtn').style.display = 'none';
            document.getElementById('stopBtn').style.display = 'block';
        } else {
            document.getElementById('status').innerText = "🟢 Status: Idle";
            document.getElementById('status').style.background = '#334155';
            document.getElementById('startBtn').style.display = 'block';
            document.getElementById('stopBtn').style.display = 'none';
        }

        const logsDiv = document.getElementById('logs');
        if (data.logs.length > 0) {
            logsDiv.innerHTML = data.logs.map(l => `<div class="log-line ${l.color}">[${l.time}] ${l.msg}</div>`).join('');
            logsDiv.scrollTop = logsDiv.scrollHeight;
        }

        const otpRes = await fetch('/api/otps');
        const otps = await otpRes.json();
        
        if (otps.length > 0) {
            document.getElementById('otp-container').style.display = 'block';
            const otpList = document.getElementById('otp-list');
            otpList.innerHTML = otps.map(o => `
                <div class="otp-item">
                    <div>
                        <span class="otp-email">${o.email}</span>
                        <span class="otp-code">${o.code}</span>
                    </div>
                    <button class="copy-btn" onclick="copyCode('${o.code}')">Copy</button>
                </div>
            `).join('');
        }
    }, 3000);
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
    return jsonify({"is_running": IS_RUNNING, "success": WEB_STATE["success"], "total": WEB_STATE["total"], "logs": WEB_LOGS})

@app.route('/api/otps')
def get_otps():
    if not session.get('logged_in'): return jsonify({"error": "Unauthorized"}), 401
    return jsonify(WEB_OTPS)

@app.route('/api/start', methods=['POST'])
def api_start():
    global IS_RUNNING, WEB_LOGS, WEB_OTPS, CANCEL_FLAG
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
    os_mode = data.get('os_mode', 'ios')
    
    WEB_LOGS = [] 
    WEB_OTPS = []
    CANCEL_FLAG = False
    add_web_log(f"Starting process for {len(email_data_list)} accounts...", "cyan")
    threading.Thread(target=execute_batch, args=(None, email_data_list, password, lang, custom_name, use_proxy, os_mode, True)).start()
    return jsonify({"status": "started"})

@app.route('/api/stop', methods=['POST'])
def api_stop():
    global CANCEL_FLAG
    if not session.get('logged_in'): return jsonify({"error": "Unauthorized"}), 401
    CANCEL_FLAG = True
    add_web_log("🛑 Stop requested by user...", "red")
    return jsonify({"status": "stopping"})

@app.route('/download/success')
def download_success():
    if not session.get('logged_in'): return redirect(url_for('login'))
    
    try:
        response = supabase.table("accounts").select("uid, password, cookie, full_combo").execute()
        data = response.data
        if not data: return "No Data Found", 404
        
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['UID', 'PASSWORD', 'COOKIE', 'FULL_MAIL'])
        for row in data:
            writer.writerow([row.get('uid'), row.get('password'), row.get('cookie'), row.get('full_combo')])
        
        mem = io.BytesIO()
        mem.write(output.getvalue().encode('utf-8-sig'))
        mem.seek(0)
        return send_file(mem, as_attachment=True, download_name="success_accounts.csv", mimetype='text/csv')
    except Exception as e:
        return f"Error: {e}", 500

@app.route('/download/failed')
def download_failed():
    if not session.get('logged_in'): return redirect(url_for('login'))
    
    try:
        response = supabase.table("failed_accounts").select("full_combo, reason").execute()
        data = response.data
        if not data: return "No Data Found", 404
        
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['FULL_MAIL', 'REASON'])
        for row in data:
            writer.writerow([row.get('full_combo'), row.get('reason')])
        
        mem = io.BytesIO()
        mem.write(output.getvalue().encode('utf-8-sig'))
        mem.seek(0)
        return send_file(mem, as_attachment=True, download_name="failed_accounts.csv", mimetype='text/csv')
    except Exception as e:
        return f"Error: {e}", 500

# ══════════════════════════════════════════════════════════
# BOT 1 LOGIC (MAIN BOT - CREATOR)
# ══════════════════════════════════════════════════════════
user_states = {}

def get_main_menu_1(chat_id):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton('🚀 Create Account'))
    if IS_RUNNING: markup.add(KeyboardButton('🛑 Stop Process'))
    if str(chat_id) == ADMIN_ID: markup.add(KeyboardButton('⚙️ Admin Panel'))
    return markup

@bot1.message_handler(commands=['start'])
def send_welcome_1(message):
    chat_id = message.chat.id
    if not is_authorized(chat_id): return bot1.reply_to(message, "⛔ **Access Denied!**")
    bot1.reply_to(message, f"Welcome!\n🆔 `{chat_id}`", reply_markup=get_main_menu_1(chat_id), parse_mode='Markdown')

@bot1.message_handler(func=lambda message: message.text == '🛑 Stop Process')
def stop_process(message):
    global CANCEL_FLAG
    CANCEL_FLAG = True
    bot1.send_message(message.chat.id, "🛑 **Stopping...**", reply_markup=ReplyKeyboardRemove())

@bot1.message_handler(commands=['create'])
@bot1.message_handler(func=lambda message: message.text == '🚀 Create Account')
def start_creation(message):
    chat_id = message.chat.id
    if not is_authorized(chat_id): return
    if IS_RUNNING: return bot1.send_message(chat_id, "⚠️ Process running!")
    user_states[chat_id] = {'step': 'emails'}
    bot1.send_message(chat_id, "📧 Paste emails:", reply_markup=ReplyKeyboardRemove())

@bot1.message_handler(func=lambda message: True)
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
                
        if not email_data_list: return bot1.send_message(chat_id, "❌ Invalid format.")
        state['email_data_list'] = email_data_list
        auto_lang = get_lang_from_email(email_data_list[0]['email'])
        state['auto_lang'] = auto_lang
        state['step'] = 'os_mode'
        
        msg = f"✅ Got {len(email_data_list)} emails."
        if auto_lang: msg += f"\n(Auto Language: {auto_lang.upper()})"
        
        markup = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        markup.add('iOS', 'Android')
        markup.add('🔙 Cancel')
        bot1.send_message(chat_id, msg + "\n📱 Select OS Mode:", reply_markup=markup)

    elif state['step'] == 'os_mode':
        text = message.text.lower()
        if 'ios' in text: state['os_type'] = 'ios'
        elif 'android' in text: state['os_type'] = 'android'
        elif 'cancel' in text:
            del user_states[chat_id]
            return bot1.send_message(chat_id, "Cancelled.", reply_markup=get_main_menu_1(chat_id))
        else: return bot1.send_message(chat_id, "❌ Select OS from buttons.")
        
        state['step'] = 'password_mode'
        markup = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        markup.add('Fix Password (SOHAVdd)', 'Custom Password')
        markup.add('🔙 Cancel')
        bot1.send_message(chat_id, "🔐 Select Password Mode:", reply_markup=markup)

    elif state['step'] == 'password_mode':
        if 'Fix Password' in message.text:
            tz = datetime.timezone(datetime.timedelta(hours=6))
            state['password'] = f"SOHAV{datetime.datetime.now(tz).day}"
            state['step'] = 'proxy_mode'
            bot1.send_message(chat_id, f"✅ Fixed Pass: `{state['password']}`", parse_mode='Markdown', reply_markup=ReplyKeyboardRemove())
            show_proxy_menu(chat_id)
        elif 'Custom Password' in message.text:
            state['step'] = 'custom_password'
            bot1.send_message(chat_id, "✍️ Enter Custom Password:", reply_markup=telebot.types.ReplyKeyboardRemove())
        elif 'Cancel' in message.text:
            del user_states[chat_id]
            return bot1.send_message(chat_id, "Cancelled.", reply_markup=get_main_menu_1(chat_id))
        else: bot1.send_message(chat_id, "❌ Select from buttons.")

    elif state['step'] == 'custom_password':
        state['password'] = message.text.strip()
        state['step'] = 'proxy_mode'
        bot1.send_message(chat_id, f"✅ Custom Pass set.", reply_markup=ReplyKeyboardRemove())
        show_proxy_menu(chat_id)

    elif state['step'] == 'proxy_mode':
        choice = message.text
        if 'No Proxy' in choice: state['use_proxy'] = False; next_step = True
        elif 'Use Proxy' in choice:
            if len(load_proxies()) == 0: return bot1.send_message(chat_id, "⚠️ No proxies found!")
            state['use_proxy'] = True; next_step = True
        elif 'Cancel' in choice:
            del user_states[chat_id]
            return bot1.send_message(chat_id, "Cancelled.", reply_markup=get_main_menu_1(chat_id))
        else: next_step = False; bot1.send_message(chat_id, "❌ Select from buttons.")

        if next_step:
            state['step'] = 'name_mode'
            markup = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
            markup.add('Auto Name', 'Custom Name')
            markup.add('🔙 Cancel')
            bot1.send_message(chat_id, "👤 Select Name Mode:", reply_markup=markup)

    elif state['step'] == 'name_mode':
        if message.text == 'Custom Name':
            state['step'] = 'custom_name'
            bot1.send_message(chat_id, "✍️ Send: Firstname Lastname", reply_markup=ReplyKeyboardRemove())
        elif 'Cancel' in message.text:
            del user_states[chat_id]
            return bot1.send_message(chat_id, "Cancelled.", reply_markup=get_main_menu_1(chat_id))
        else:
            state['custom_name'] = None
            if state.get('auto_lang'): state['lang'] = state['auto_lang']; start_batch_from_state(chat_id, state)
            else: state['step'] = 'language'; show_languages(chat_id)

    elif state['step'] == 'custom_name':
        parts = message.text.strip().split(' ')
        if len(parts) < 2: return bot1.send_message(chat_id, "❌ Invalid format.")
        state['custom_name'] = (parts[0], " ".join(parts[1:]))
        if state.get('auto_lang'): state['lang'] = state['auto_lang']; start_batch_from_state(chat_id, state)
        else: state['step'] = 'language'; show_languages(chat_id)

    elif state['step'] == 'language':
        if 'Cancel' in message.text:
            del user_states[chat_id]
            return bot1.send_message(chat_id, "Cancelled.", reply_markup=get_main_menu_1(chat_id))
        state['lang'] = message.text.strip().lower()[:2]
        start_batch_from_state(chat_id, state)

def show_proxy_menu(chat_id):
    proxy_count = len(load_proxies())
    proxy_text = f"Use Proxy ({proxy_count} Loaded)" if proxy_count > 0 else "Use Proxy (0 Loaded)"
    markup = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add('No Proxy (Direct)', proxy_text)
    markup.add('🔙 Cancel')
    bot1.send_message(chat_id, "🌐 Select Proxy Mode:", reply_markup=markup)

def show_languages(chat_id):
    markup = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True, row_width=4)
    buttons = [KeyboardButton(code) for code in LANG_MAP.keys()]
    markup.add(*buttons)
    markup.add(KeyboardButton('🔙 Cancel'))
    bot1.send_message(chat_id, "🌍 Select Language:", reply_markup=markup)

def start_batch_from_state(chat_id, state):
    global CURRENT_LANG_HEADER
    lang = state['lang']
    if lang in LANG_MAP: CURRENT_LANG_HEADER = LANG_MAP[lang][0]
    else: CURRENT_LANG_HEADER = LANG_MAP['us'][0]
    
    state['step'] = None
    proxy_status = "Proxy ON" if state['use_proxy'] else "Direct IP"
    os_status = state['os_type'].upper()
    
    bot1.send_message(chat_id, f"⚙️ Starting for {len(state['email_data_list'])} accounts ({proxy_status} | Lang: {lang.upper()} | OS: {os_status})...\n\n👇 *Please wait...*", parse_mode='Markdown', reply_markup=ReplyKeyboardRemove())
    threading.Thread(target=execute_batch, args=(chat_id, state['email_data_list'], state['password'], lang, state['custom_name'], state['use_proxy'], state['os_type'], False)).start()


# ══════════════════════════════════════════════════════════
# BOT 2 LOGIC (DOWNLOAD BOT + OTP LIST)
# ══════════════════════════════════════════════════════════
def get_main_menu_2(chat_id):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton('📩 OTP List'))
    markup.add(KeyboardButton('📁 Download Success'), KeyboardButton('❌ Download Failed'))
    if str(chat_id) == ADMIN_ID: markup.add(KeyboardButton('📊 Stats'))
    return markup

@bot2.message_handler(commands=['start'])
def send_welcome_2(message):
    chat_id = message.chat.id
    if not is_authorized(chat_id): return bot2.reply_to(message, "⛔ **Access Denied!**")
    bot2.reply_to(message, "Welcome to Download Bot! 📁", reply_markup=get_main_menu_2(chat_id))

@bot2.message_handler(func=lambda message: message.text == '📩 OTP List')
def show_otps(message):
    chat_id = message.chat.id
    if not is_authorized(chat_id): return
    
    try:
        response = supabase.table("otps").select("email, code").order("id", desc=True).limit(20).execute()
        data = response.data
        if not data:
            return bot2.send_message(chat_id, "❌ No OTPs found yet.")
            
        msg = "📩 **Recent OTPs:**\n\n"
        for o in data:
            msg += f"`{o['email']}` - `{o['code']}`\n"
            
        bot2.send_message(chat_id, msg, parse_mode='Markdown')
    except Exception as e:
        bot2.send_message(chat_id, f"Error: {e}")

@bot2.message_handler(commands=['getcsv'])
@bot2.message_handler(func=lambda message: message.text == '📁 Download Success')
def send_csv_2(message):
    chat_id = message.chat.id
    if not is_authorized(chat_id): return
    
    try:
        response = supabase.table("accounts").select("uid, password, cookie, full_combo").execute()
        data = response.data
        if not data: return bot2.send_message(chat_id, "❌ No Data.")
        
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['UID', 'PASSWORD', 'COOKIE', 'FULL_MAIL'])
        for row in data:
            writer.writerow([row.get('uid'), row.get('password'), row.get('cookie'), row.get('full_combo')])
            
        mem = io.BytesIO()
        mem.write(output.getvalue().encode('utf-8-sig'))
        mem.seek(0)
        bot2.send_document(chat_id, mem, visible_file_name="success.csv", caption="Here is your SUCCESS CSV.")
    except Exception as e:
        bot2.send_message(chat_id, f"Error: {e}")

@bot2.message_handler(commands=['getfailed'])
@bot2.message_handler(func=lambda message: message.text == '❌ Download Failed')
def send_failed_csv_2(message):
    chat_id = message.chat.id
    if not is_authorized(chat_id): return
    
    try:
        response = supabase.table("failed_accounts").select("full_combo, reason").execute()
        data = response.data
        if not data: return bot2.send_message(chat_id, "❌ No Data.")
        
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['FULL_MAIL', 'REASON'])
        for row in data:
            writer.writerow([row.get('full_combo'), row.get('reason')])
            
        mem = io.BytesIO()
        mem.write(output.getvalue().encode('utf-8-sig'))
        mem.seek(0)
        bot2.send_document(chat_id, mem, visible_file_name="failed.csv", caption="Here is your FAILED CSV.")
    except Exception as e:
        bot2.send_message(chat_id, f"Error: {e}")


# ══════════════════════════════════════════════════════════
# START FLASK & BOTH BOTS
# ══════════════════════════════════════════════════════════
if __name__ == '__main__':
    t1 = threading.Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080))))
    t1.daemon = True
    t1.start()

    t2 = threading.Thread(target=bot2.infinity_polling)
    t2.daemon = True
    t2.start()

    print("App Server & Bots running with Supabase...")
    bot1.infinity_polling()
