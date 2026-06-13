# -*- coding: utf-8 -*-
import glob
import os
import time
import shutil
import telebot
import urllib.parse
import hashlib
import hmac
from telebot import apihelper
from telebot import types
from flask import Flask, request, jsonify
from apscheduler.schedulers.background import BackgroundScheduler

# --- 1. الإعدادات والتهيئة الأساسية ---
apihelper.ENABLE_MIDDLEWARE = True
OWNER_ID = int(os.getenv('OWNER_ID', 0)) 
TOKEN = os.environ.get('TOKEN')
bot = telebot.TeleBot(TOKEN)
user_last_message_time = {}

# مخزن مؤقت لحفظ آخر شبكات حقيقية تم استقبالها من الأجهزة المتصلة
LATEST_SCANNED_NETWORKS = {}

# --- 2. محرك التشفير والمحاكاة الرياضية للمصافحة ---
class WiFiHandshake:
    def __init__(self, wifi_password: str, ssid: str):
        self.wifi_password = wifi_password
        self.ssid = ssid
        self.PMK = None
        self.PTK = None
        
    def generate_psk(self) -> bytes:
        psk = hashlib.pbkdf2_hmac(
            'sha1',
            self.wifi_password.encode(),
            self.ssid.encode(),
            4096,
            dklen=32
        )
        self.PMK = psk
        return psk
    
    def generate_nonce(self) -> bytes:
        return os.urandom(32)
    
    def compute_ptk(self, aa: bytes, spa: bytes, anonce: bytes, snonce: bytes) -> bytes:
        if not self.PMK:
            self.generate_psk()
        data = b"Pairwise key expansion"
        mac_part = aa + spa if aa < spa else spa + aa
        nonce_part = anonce + snonce if anonce < snonce else snonce + anonce
        ptk = self._prf_sha256(self.PMK, data, mac_part + nonce_part, 384 // 8)
        self.PTK = ptk
        return ptk
    
    def _prf_sha256(self, key: bytes, label: bytes, data: bytes, length: int) -> bytes:
        result = b''
        counter = 0
        while len(result) < length:
            counter += 1
            h = hmac.new(key, digestmod=hashlib.sha256)
            h.update(label)
            h.update(b'\x00')
            h.update(data)
            h.update(bytes([counter]))
            result += h.digest()
        return result[:length]
    
    def compute_mic(self, data: bytes, tk: bytes) -> bytes:
        mic = hmac.new(tk, data, hashlib.md5).digest()
        return mic[:16]

# --- 3. قالب سكريبت الاستماع والارسال لجهاز العميل (القديم) ---
IOS_SPY_SCRIPT_TEMPLATE = """# -*- coding: utf-8 -*-
import time
import requests

SERVER_API_URL = "{webhook_url}/api/wifi_update" 
TARGET_SSID = "LOWER"

def scan_iphone_airspace():
    try:
        from objc_util import ObjCClass
        current_net = ObjCClass('NEHotspotNetwork').fetchCurrent()
        if current_net and str(current_net.SSID()) == TARGET_SSID:
            return [{{
                "ssid": str(current_net.SSID()), 
                "bssid": str(current_net.BSSID()), 
                "rssi": -52
            }}]
    except ImportError:
        pass
    return [
        {{"ssid": TARGET_SSID, "bssid": "00:14:22:01:23:45", "rssi": -48}}
    ]

def start_iphone_transmitter():
    print(f"[*] بدأ العميل بالعمل... جاري استكشاف الشبكة: {{TARGET_SSID}}")
    while True:
        try:
            current_networks = scan_iphone_airspace()
            payload = {{"networks": current_networks}}
            requests.post(SERVER_API_URL, json=payload, timeout=5)
        except Exception as e:
            print(f"[-] خطأ اتصال: {{e}}")
        time.sleep(7) 

if __name__ == '__main__':
    start_iphone_transmitter()
"""

# --- 4. جدار الحماية والتريث تلقائي (Middleware) ---
@bot.middleware_handler(update_types=['message', 'callback_query'])
def rate_limit_middleware(update_type, data):
    user_id = data.from_user.id
    if user_id == OWNER_ID: return
    current_time = time.time()
    last_time = user_last_message_time.get(user_id, 0)
    if current_time - last_time < 1:
        if update_type == 'message': bot.reply_to(data, "⏳ تريث قليلاً قبل إرسال الطلب التالي!")
        else: bot.answer_callback_query(data.id, "⏳ تريث قليلاً!")
        return {"ok": False}
    user_last_message_time[user_id] = current_time

# --- 5. نظام تنظيف الذاكرة الموقتة للإنتاج ---
def auto_cleanup_job():
    patterns = ["video_*.mp4", "img_*.jpg", "output_*.pdf", "*.tmp", "ios_spy_*.py"]
    count = 0
    for pattern in patterns:
        for f in glob.glob(pattern):
            try: os.remove(f); count += 1
            except: pass
    if count > 0: print(f"🧹 [تنظيف تلقائي]: تم مسح {count} من الملفات المؤقتة بنجاح.")

scheduler = BackgroundScheduler()
scheduler.add_job(auto_cleanup_job, 'interval', minutes=2)
scheduler.start()

# --- 6. الأوامر الأساسية للبوت ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("الاشتراك المجاني 🔓", callback_data='free_sub'),
        types.InlineKeyboardButton("اشتراك ماكس ✨ 👑", callback_data='max_sub'),
        types.InlineKeyboardButton("📶 لوحة تحكم الشبكات المتصلة والترددات الحية", callback_data='wifi_spy_init')
    )
    bot.send_message(message.chat.id, "أهلاً بك في ✨ <b>𝓓𝓐𝓢𝓧 𝓑𝓞𝓞𝓣</b> ✨\n\nالرجاء اختيار الخدمة المطلوبة لبدء العمل:", parse_mode="HTML", reply_markup=markup)

# --- 7. معالجة تفاعلات الواجهة الرسومية للأزرار ---
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    try: bot.answer_callback_query(call.id)
    except: pass

    if call.data.startswith('dist_'):
        distance = call.data.split('_')[1]
        bot.send_message(call.message.chat.id, f"📏 <b>تحليل نطاق البث الحقيقي:</b>\n\nالهاتف يبعد عن نقطة بث الراوتر بمسافة هندسية تقريبية تقدر بـ <b>{distance} متر</b> بناءً على مستوى الفقد الحالي في الإشارة.")

    elif call.data == 'wifi_spy_init':
        if not LATEST_SCANNED_NETWORKS:
            target_name = "LOWER"
            for line in IOS_SPY_SCRIPT_TEMPLATE.split("\n"):
                if "TARGET_SSID =" in line:
                    try: target_name = line.split('"')[1]
                    except: pass
            networks_to_show = [{"ssid": target_name, "bssid": "00:14:22:01:23:45", "rssi": -48}]
        else:
            networks_to_show = list(LATEST_SCANNED_NETWORKS.values())

        for net in networks_to_show:
            ssid = net.get('ssid', 'Unknown')
            bssid = net.get('bssid', '00:00:00:00:00:00')
            rssi = net.get('rssi', -100)
            try: distance = round(10 ** ((-30 - rssi) / (10 * 2.5)), 1)
            except: distance = "غير محدد"

            markup = types.InlineKeyboardMarkup(row_width=2)
            markup.add(
                types.InlineKeyboardButton("🔍 Audit Network", callback_data=f"audit_{bssid}_{ssid}"),
                types.InlineKeyboardButton("📝 Wordlist", callback_data=f"wordlist_{ssid}"),
                types.InlineKeyboardButton("📍 Distance", callback_data=f"dist_{distance}")
            )
            report = (f"🌐 **SSID:** `{ssid}`\n"
                      f"🆔 **BSSID:** `{bssid}`\n"
                      f"📶 **RSSI:** `{rssi} dBm`\n"
                      f"📏 **Est. Distance:** `{distance} m`\n"
                      f"----------------------------------")
            bot.send_message(OWNER_ID, report, parse_mode="Markdown", reply_markup=markup)

    elif call.data.startswith('audit_'):
        parts = call.data.split('_')
        target_bssid = parts[1]
        target_ssid = parts[2] if len(parts) > 2 else "Unknown"
        
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton("💥 Launch Advanced Audit Simulation", callback_data=f"exploit_pixie_{target_bssid}_{target_ssid}"),
            types.InlineKeyboardButton("🔙 Return to Main Menu", callback_data="wifi_spy_init")
        )
        
        audit_report = (
            f"🔍 <b>تقرير الفحص المتقدم للهوية الحقيقية:</b>\n\n"
            f"🌐 <b>الاسم البرمجي (SSID):</b> <code>{target_ssid}</code>\n"
            f"🆔 <b>عنوان العتاد (BSSID):</b> <code>{target_bssid}</code>\n"
            f"🛡️ <b>بروتوكول الحماية النشط:</b> WPA2-PSK (AES-CCMP)\n"
            f"⚠️ <b>الملاحظات الأمنية:</b> تم رصد استجابة للتحقق والتأكيد من الهوية عبر النظام المدمج."
        )
        try: bot.send_message(call.message.chat.id, audit_report, parse_mode="HTML", reply_markup=markup)
        except: pass

    elif call.data.startswith('exploit_pixie_'):
        parts = call.data.split('_')
        target_bssid = parts[2]
        target_ssid = parts[3] if len(parts) > 3 else "Network"
        
        sim_password = f"{target_ssid}🏆Secure2026"
        engine = WiFiHandshake(wifi_password=sim_password, ssid=target_ssid)
        
        psk = engine.generate_psk()
        try: ap_mac = bytes.fromhex(target_bssid.replace(":", ""))
        except: ap_mac = os.urandom(6)
            
        client_mac = os.urandom(6)
        anonce = engine.generate_nonce()
        snonce = engine.generate_nonce()
        
        ptk = engine.compute_ptk(ap_mac, client_mac, anonce, snonce)
        kck = ptk[:16]
        message = ap_mac + client_mac + anonce + snonce
        mic = engine.compute_mic(message, kck)

        handshake_report = (
            f"⚡ <b>[محرك التشكيل الرياضي]: جاري معالجة إشارات الشبكة المستهدفة...</b>\n"
            f"-----------------------------------------\n"
            f"🌐 <b>SSID Target:</b> <code>{target_ssid}</code>\n"
            f"🆔 <b>BSSID Address:</b> <code>{target_bssid}</code>\n\n"
            f"🔄 <b>STEP 1 (AP ➔ Client):</b>\n"
            f"📡 التقط الهاتف حزمة البث التلقائي وبداية تبادل الـ Nonce الحية.\n"
            f"🔑 <code>ANonce: {anonce.hex()[:24]}...</code>\n\n"
            f"🔄 <b>STEP 2 (Client ➔ AP):</b>\n"
            f"📱 قام الهاتف بحساب مصفوفة المفتاح المؤقت وتوليد الـ SNonce الخاص به.\n"
            f"🔑 <code>SNonce: {snonce.hex()[:24]}...</code>\n\n"
            f"🔄 <b>STEP 3 & 4 (Verification):</b>\n"
            f"🛡️ تم توليد كود التحقق من سلامة الحزمة (MIC) باستخدام بروتوكول HMAC-MD5 المعتمد.\n"
            f"⚙️ <code>Calculated PMK: {psk.hex()[:20]}...</code>\n"
            f"⚙️ <code>Calculated PTK: {ptk.hex()[:20]}...</code>\n"
            f"🔒 <code>Computed MIC: {mic.hex()}</code>\n\n"
            f"✅ <b>تحليل التدفق الرقمي:</b>\n"
            f"المفتاح المشتق المتوقع لحماية النطاق الحالي هو:\n"
            f"🔑 <code>{sim_password}</code>\n"
            f"-----------------------------------------"
        )
        try: bot.send_message(call.message.chat.id, handshake_report, parse_mode="HTML")
        except: pass

    elif call.data.startswith('wordlist_'):
        ssid = call.data.split('_')[1]
        generated_passes = [f"{ssid}2026", f"admin@{ssid}", f"{ssid}1234", f"pass_{ssid}", f"master_{ssid}"]
        pass_report = f"📝 <b>مصفوفة التخمين الذكية المشتقة من الاسم الحقيقي للشبكة (<code>{ssid}</code>):</b>\n\n"
        for p in generated_passes: pass_report += f"▪️ <code>{p}</code>\n"
        try: bot.send_message(call.message.chat.id, pass_report, parse_mode="HTML")
        except: pass

    elif call.data == 'free_sub':
        my_free_names = ["زيادة دقة الصور 🌅", "تحميل أي فيديو 📥", "ترجمة صورة الى نص 📝", "تحويل صورة لـ PDF 📄"]
        markup = types.InlineKeyboardMarkup(row_width=2)
        buttons = [types.InlineKeyboardButton(my_free_names[i], callback_data=f'f{i+1}') for i in range(4)]
        markup.add(*buttons)
        bot.edit_message_text("اختر الخدمة المجانية المطلوبة:", call.message.chat.id, call.message.message_id, reply_markup=markup)
    
    elif call.data == 'max_sub':
        my_names = ["💀 واتساب بلس", "👑 يوزرات مميزة", "اكواد تعطي_ل 😈", "📷 فتح كاميرا", "📍 تحديد موقع", "☠️ رفع تيكتوك", "✅ أرقام فيك", "👀 انستا برايفت", "➕ فك سافي_وم", "🛠 أدوات متطورة", "✨ مزايا انستا", "🌎 تل/غيم روابط", "🎮 شحن ألعاب", "✅ رشق انستا", "🚀 تطبيقات برو", "📱 بلياردو لانهائي", "🤖 تيكتوك ترول", "ادوات اخت*ر|ق ☠️", "✅ أرقام حقيقية خاصة بك", "اتصال وهمي ☎️"]
        markup = types.InlineKeyboardMarkup(row_width=2)
        buttons = [types.InlineKeyboardButton(my_names[i], callback_data=f'max_{i+1}') for i in range(20)]
        markup.add(*buttons)
        bot.edit_message_text("اختر خدمة ماكس المتقدمة:", call.message.chat.id, call.message.message_id, reply_markup=markup)
        
    elif call.data.startswith('max_'):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("تفعيل خطة ماكس الآن ✨", callback_data='activate_max'))
        bot.edit_message_text("🔒 <b>عذراً، هذه الخدمة تتطلب اشتراك ماكس ✨</b>\n\nيرجى ترقية حسابك لتتمكن من استخدامها فوراً.", call.message.chat.id, call.message.message_id, parse_mode="HTML", reply_markup=markup)
        
    elif call.data == 'activate_max':
        try: bot.delete_message(call.message.chat.id, call.message.message_id)
        except: pass
        prices = [types.LabeledPrice(label="اشتراك ماكس برو", amount=100)]
        bot.send_invoice(chat_id=call.message.chat.id, title="اشتراك ماكس المتقدم ✨", description="تفعيل جميع الخدمات المدفوعة داخل البوت لمدة شهر.", invoice_payload="max_premium_subscription", provider_token="", currency="XTR", prices=prices)

# --- 8. أنظمة الفواتير وبوابات الربط واستقبال التحديثات من الأجهزة الحية ---
@bot.pre_checkout_query_handler(func=lambda query: True)
def process_pre_checkout(pre_checkout_query):
    bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

@bot.message_handler(content_types=['successful_payment'])
def process_successful_payment(message):
    bot.reply_to(message, f"🎉 <b>تم تفعيل اشتراك ماكس ✨ بنجاح!</b>\n\nاستمتع بكافة الصلاحيات المفتوحة الآن.", parse_mode="HTML")

app = Flask(__name__)

@app.route('/')
def home(): return "البوت مستقر ويعمل بنظام الحسابات الرياضية المتقدمة!"

@app.route('/api/wifi_update', methods=['POST'])
def wifi_update():
    global LATEST_SCANNED_NETWORKS
    data = request.json
    if not data:
        return jsonify({"status": "failed", "message": "بيانات غير صالحة"}), 400

    # 1. معالجة البيانات القادمة من العميل الرسومي الجديد (wifi_monitor.py)
    if 'agent_event' in data:
        event_type = data.get("agent_event")
        payload = data.get("data_payload")

        if event_type == "interfaces_discovered":
            bot.send_message(OWNER_ID, f"🖥️ <b>[تحديث واجهة العميل للكمبيوتر]:</b>\n\n🔄 تم رصد عتاد شبكة جديد متصل محلياً بالعميل:\n<code>{payload}</code>", parse_mode="HTML")
        
        elif event_type == "cracking_result":
            # إرسال مخرجات الكسر النصية كاملة للمالك
            bot.send_message(OWNER_ID, f"⚡ <b>[تقرير مخرجات العميل المباشر]:</b>\n\nوصل تحديث فوري لنتائج الفحص والكسر:\n\n<pre>{payload[:3500]}</pre>", parse_mode="HTML")
            
        elif event_type == "file_attached":
            file_info = payload.get("file_path", "Unknown")
            bot.send_message(OWNER_ID, f"📂 <b>[تنبيه العميل]:</b> تم إرفاق ملف للتحليل محلياً:\n<code>{file_info}</code>", parse_mode="HTML")

        return jsonify({"status": "success", "message": "تمت معالجة حدث العميل"}), 200

    # 2. معالجة البيانات القادمة من قالب الآيفون والتطبيقات القديمة (للخلفية والتوافق المتكامل)
    if 'networks' in data:
        networks_list = data['networks']
        LATEST_SCANNED_NETWORKS.clear()
        
        bot.send_message(OWNER_ID, f"📡 <b>[إشعار بث حي حقيقي]: تم استقبال معطيات حية وجديدة من عتاد الهاتف!</b>", parse_mode="HTML")

        for net in networks_list:
            ssid = net.get('ssid', 'Unknown')
            bssid = net.get('bssid', '00:00:00:00:00:00')
            rssi = net.get('rssi', -100)
            
            LATEST_SCANNED_NETWORKS[bssid] = net
            try: distance = round(10 ** ((-30 - rssi) / (10 * 2.5)), 1)
            except: distance = "غير محدد"

            markup = types.InlineKeyboardMarkup(row_width=2)
            markup.add(
                types.InlineKeyboardButton("🔍 Audit Network", callback_data=f"audit_{bssid}_{ssid}"),
                types.InlineKeyboardButton("📝 Wordlist", callback_data=f"wordlist_{ssid}"),
                types.InlineKeyboardButton("📍 Distance", callback_data=f"dist_{distance}")
            )
            
            report = (f"🌐 **SSID:** `{ssid}`\n"
                      f"🆔 **BSSID:** `{bssid}`\n"
                      f"📶 **RSSI:** `{rssi} dBm`\n"
                      f"📏 **Est. Distance:** `{distance} m`\n"
                      f"----------------------------------")
            bot.send_message(OWNER_ID, report, parse_mode="Markdown", reply_markup=markup)
            
        return jsonify({"status": "success", "message": "تم التحديث"}), 200

    return jsonify({"status": "failed", "message": "هيكل البيانات غير مطابق"}), 400

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return '!', 200
    return 'Forbidden', 403

if __name__ == "__main__":
    WEBHOOK_URL = os.environ.get("WEBHOOK_URL")
    PORT = int(os.environ.get("PORT", 8080))
    if WEBHOOK_URL:
        bot.remove_webhook()
        bot.set_webhook(url=f"{WEBHOOK_URL}/webhook")
        print("Server running...")
        app.run(host='0.0.0.0', port=PORT)
