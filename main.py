#-----create by siam ---#
#------TG: @SIAMKHANXD--#
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
import json
import re
import uuid
import random
import time
import os
import hashlib
import string
import threading
import requests
from concurrent.futures import ThreadPoolExecutor
from flask import Flask

try:
    from curl_cffi import requests as cureq
except ImportError:
    print("\033[91m[!] curl_cffi not found!\033[0m")
    exit()

# ══════════════════════════════════════════════════════════
# BOT TOKEN & SHEET URL HERE
# ══════════════════════════════════════════════════════════
BOT_TOKEN = "9025360567:AAEJ2Jq2FSAVpDOVC3UCPYViQE9-sNI7NSk" 
bot = telebot.TeleBot(BOT_TOKEN)

# PASTE YOUR GOOGLE APPS SCRIPT WEB APP URL HERE
WEB_APP_URL = "https://script.google.com/macros/s/AKfycbz5NvizkYskxUAZy7HzngAHqPrcU687b4mSLgI8s0IYlBUUpoVz_fxbenVCYVOW3H5G/exec"

# ══════════════════════════════════════════════════════════
# FLASK WEB SERVER (To keep Render awake)
# ══════════════════════════════════════════════════════════
app = Flask('')

@app.route('/')
def home():
    return "Bot is alive and running!"

def run_flask():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

# ══════════════════════════════════════════════════════════
# CONSTANTS
# ══════════════════════════════════════════════════════════
FB_REG_BASE = "https://limited.facebook.com"
GRAPHQL_URL = "https://web.facebook.com/api/graphql/"
PROXY_FILE = "proxies.txt" 
file_lock = threading.Lock()

# ══════════════════════════════════════════════════════════
# PROXY & DB
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
    'tr': ('tr-TR,tr;q=0.9,en;q=0.8', 'Europe/Istanbul'), 'in': ('hi-IN,hi;q=0.9,en;q=0.8', 'Asia/Kolkata')
}
CURRENT_LANG_HEADER = "en-US,en;q=0.9"

DEFAULT_FIRST_NAMES = ['Arafat', 'Rakib', 'Sabbir', 'Nayeem', 'Rifat', 'Tanvir', 'Shakib', 'Sajid', 'John', 'David', 'Michael', 'James']
DEFAULT_LAST_NAMES = ['Hossain', 'Ahmed', 'Khan', 'Islam', 'Rahman', 'Sarker', 'Smith', 'Johnson', 'Williams', 'Brown']
GERMAN_FIRST_NAMES = ["Alexander", "Andreas", "Anna", "Anja", "Anke", "Anton", "Armin", "Axel", "Barbara", "Bastian", "Benedikt", "Benjamin", "Bernd", "Birgit", "Björn", "Brigitte", "Bruno", "Carina", "Carla", "Charlotte", "Christian", "Christina", "Christof", "Claudia", "Claus", "Cornelia", "Daniel", "Daniela", "David", "Dennis"]
GERMAN_LAST_NAMES = ["Albrecht", "Arnold", "Bachmann", "Bauer", "Baumann", "Becker", "Beckmann", "Berger", "Bergmann", "Böhm", "Brandt", "Braun", "Brinker", "Brunner", "Busch", "Dietrich", "Dörfler", "Dreher", "Ebert", "Eckert", "Engel", "Esser", "Falk", "Faust", "Fischer", "Fleischer", "Frank", "Franz", "Frey", "Fuchs"]
PORTUGUESE_FIRST_NAMES = ["Miguel", "Arthur", "Gael", "Théo", "Heitor", "Ravi", "Davi", "Bernardo", "Noah", "Gabriel", "Samuel", "Pedro", "Anthony", "Lucas", "Benjamin", "Matheus", "Joaquim", "Nicolas", "Lorenzo", "Henrique", "João", "Rafael", "Enzo", "Murilo", "Benício", "Gustavo", "Guilherme", "Emanuel", "Felipe", "Bryan", "Daniel", "Vitor", "Leonardo", "Bruno", "Thiago", "Vicente", "Carlos", "Eduardo", "André", "Fernando"]
PORTUGUESE_LAST_NAMES = ["Silva", "Santos", "Oliveira", "Souza", "Rodrigues", "Ferreira", "Alves", "Pereira", "Lima", "Gomes", "Costa", "Ribeiro", "Martins", "Carvalho", "Almeida", "Lopes", "Soares", "Fernandes", "Vieira", "Barbosa", "Rocha", "Dias", "Nascimento", "Andrade", "Moreira", "Nunes", "Marques", "Machado", "Mendes", "Freitas"]

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

# ══════════════════════════════════════════════════════════
# GOOGLE SHEET SENDER
# ══════════════════════════════════════════════════════════
def send_to_sheet(uid, cookie, email):
    try:
        payload = {
            "uid": uid,
            "cookie": cookie,
            "mail": email
        }
        # Using requests post to Apps Script Web App
        res = requests.post(WEB_APP_URL, json=payload, timeout=15)
        if res.status_code == 200:
            return True
        return False
    except Exception as e:
        print(f"Sheet Error: {e}")
        return False

# ══════════════════════════════════════════════════════════
# CORE FB LOGIC
# ══════════════════════════════════════════════════════════
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

# ══════════════════════════════════════════════════════════
# TELEGRAM BOT LOGIC
# ══════════════════════════════════════════════════════════
user_states = {}

def get_main_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton('🚀 Create Account'))
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Welcome to FB Auto Creator Bot! 🤖\n\nBot ready. Click below to start.", reply_markup=get_main_menu())

@bot.message_handler(commands=['create'])
@bot.message_handler(func=lambda message: message.text == '🚀 Create Account')
def start_creation(message):
    chat_id = message.chat.id
    user_states[chat_id] = {'step': 'emails'}
    bot.send_message(chat_id, "📧 Paste your list of emails (one per line):", reply_markup=telebot.types.ReplyKeyboardRemove())

@bot.message_handler(func=lambda message: True)
def handle_inputs(message):
    chat_id = message.chat.id
    if chat_id not in user_states: return
    state = user_states[chat_id]

    if state['step'] == 'emails':
        emails = [l.strip() for l in message.text.split('\n') if '@' in l]
        if not emails: return bot.send_message(chat_id, "❌ Invalid format. Send valid emails.")
        state['emails'] = emails
        state['step'] = 'password'
        bot.send_message(chat_id, f"✅ Got {len(emails)} emails.\n🔐 Enter Password:")

    elif state['step'] == 'password':
        state['password'] = message.text.strip()
        state['step'] = 'proxy_mode'
        
        proxy_count = len(load_proxies())
        proxy_text = f"Use Proxy ({proxy_count} Loaded)" if proxy_count > 0 else "Use Proxy (0 Loaded)"
        
        markup = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        markup.add('No Proxy (Direct)', proxy_text)
        bot.send_message(chat_id, "🌐 Select Proxy Mode:", reply_markup=markup)

    elif state['step'] == 'proxy_mode':
        choice = message.text
        if 'No Proxy' in choice:
            state['use_proxy'] = False
            next_step = True
        elif 'Use Proxy' in choice:
            if len(load_proxies()) == 0:
                return bot.send_message(chat_id, "⚠️ No proxies found in proxies.txt! Please add some or select No Proxy.")
            state['use_proxy'] = True
            next_step = True
        else:
            next_step = False
            bot.send_message(chat_id, "❌ Please select from the buttons.")

        if next_step:
            state['step'] = 'name_mode'
            markup = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
            markup.add('Auto Name', 'Custom Name')
            bot.send_message(chat_id, "👤 Select Name Mode:", reply_markup=markup)

    elif state['step'] == 'name_mode':
        if message.text == 'Custom Name':
            state['step'] = 'custom_name'
            bot.send_message(chat_id, "✍️ Send: Firstname Lastname", reply_markup=telebot.types.ReplyKeyboardRemove())
        else:
            state['custom_name'] = None
            state['step'] = 'language'
            show_languages(chat_id)

    elif state['step'] == 'custom_name':
        parts = message.text.strip().split(' ')
        if len(parts) < 2: return bot.send_message(chat_id, "❌ Invalid format. Use: Firstname Lastname")
        state['custom_name'] = (parts[0], " ".join(parts[1:]))
        state['step'] = 'language'
        show_languages(chat_id)

    elif state['step'] == 'language':
        state['lang'] = message.text.strip().lower()[:2]
        state['step'] = None
        
        global CURRENT_LANG_HEADER
        if state['lang'] in LANG_MAP: CURRENT_LANG_HEADER = LANG_MAP[state['lang']][0]
        else: CURRENT_LANG_HEADER = LANG_MAP['us'][0]
        
        proxy_status = "Proxy ON" if state['use_proxy'] else "Direct IP"
        bot.send_message(chat_id, f"⚙️ Starting creation for {len(state['emails'])} accounts ({proxy_status})...", reply_markup=get_main_menu())
        threading.Thread(target=execute_batch, args=(chat_id, state['emails'], state['password'], state['lang'], state['custom_name'], state['use_proxy'])).start()

def show_languages(chat_id):
    markup = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True, row_width=4)
    buttons = [KeyboardButton(code) for code in LANG_MAP.keys()]
    markup.add(*buttons)
    bot.send_message(chat_id, "🌍 Select Language Code:", reply_markup=markup)

def execute_batch(chat_id, emails, password, lang, custom_name, use_proxy):
    success_count = 0
    
    def process_one(email, idx, total):
        nonlocal success_count
        c_fname = custom_name[0] if custom_name else None
        c_lname = custom_name[1] if custom_name else None
        
        status_msg = bot.send_message(chat_id, f"⏳ [{idx}/{total}] Processing: `{email}`", parse_mode='Markdown')
        
        res, err = fb_create_account(email, password, lang, c_fname, c_lname, use_proxy)
        
        if res:
            success_count += 1
            
            # Send to Google Sheet
            sheet_ok = send_to_sheet(res['uid'], res['cookie'], email)
            sheet_status = "✅ Saved to Sheet" if sheet_ok else "⚠️ Sheet Save Failed"
            
            msg = f"✅ **ACCOUNT CREATED!**\n\n📧 Email: `{email}`\n👤 Name: `{res['firstname']} {res['lastname']}`\n🆔 UID: `{res['uid']}`\n🔑 Password: `{password}`\n\n🍪 Cookie: `{res['cookie']}`\n\n{sheet_status}"
            bot.edit_message_text(msg, chat_id=chat_id, message_id=status_msg.message_id, parse_mode='Markdown')
            
            otp_ok = resend_otp(res['session'], res['uid'], res['proxy'])
            bot.send_message(chat_id, f"└─ {'📩 OTP Sent!' if otp_ok else '❌ OTP Failed'} for `{email}`", parse_mode='Markdown')
        else:
            bot.edit_message_text(f"❌ [{idx}/{total}] `{email}` Failed: {err}", chat_id=chat_id, message_id=status_msg.message_id, parse_mode='Markdown')

    with ThreadPoolExecutor(max_workers=len(emails)) as executor:
        futures = [executor.submit(process_one, email, i+1, len(emails)) for i, email in enumerate(emails)]
        for future in futures: future.result()

    bot.send_message(chat_id, f"🎉 **Batch Finished!**\nTotal Success: {success_count}/{len(emails)}\n\n📊 Data sent to Google Sheet.", parse_mode='Markdown')

# ══════════════════════════════════════════════════════════
# START BOTH FLASK & BOT
# ══════════════════════════════════════════════════════════
if __name__ == '__main__':
    t = threading.Thread(target=run_flask)
    t.daemon = True
    t.start()
    
    print("Bot is running...")
    bot.infinity_polling()
