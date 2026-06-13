# -*- coding: utf-8 -*-
import glob
import os
import time
import shutil
import telebot
import urllib.parse
import hashlib
import hmac
import requests
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

# مخازن مؤقتة للبيانات الحية القادمة من الكمبيوتر عبر الـ API
LATEST_PC_INTERFACES = []  # لحفظ كروت الشبكة الحقيقية

# --- 2. محرك التشفير والمحاكاة الرياضية للمصافحة ---
class WiFiHandshake:
    def __init__(self, wifi_password: str, ssid: str):
        self.wifi_password = wifi_password
        self.ssid = ssid
        self.PMK = None
        self.PTK = None
        
    def generate_psk(self) -> bytes:
        psk = hashlib.pbkdf2_hmac('sha1', self.wifi_password.encode(), self.ssid.encode(), 4096, dklen=32)
        self.PMK = psk
        return psk
    
    def generate_nonce(self) -> bytes:
        return os.urandom(32)
    
    def compute_ptk(self, aa: bytes, spa: bytes, anonce: bytes, snonce: bytes) -> bytes:
        if not self.PMK: self.generate_psk()
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
            h.update(label); h.update(b'\x00'); h.update(data); h.update(bytes([counter]))
            result += h.digest()
        return result[:length]
    
    def compute_mic(self, data: bytes, tk: bytes) -> bytes:
        mic = hmac.new(tk, data, hashlib.md5).digest()
        return mic[:16]

# --- 3. جدار الحماية والتريث تلقائي (Middleware) ---
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

# --- 4. نظام تنظيف الذاكرة الموقتة للإنتاج ---
def auto_cleanup_job():
    patterns = ["video_*.mp4", "img_*.jpg", "output_*.pdf", "*.tmp"]
    for pattern in patterns:
        for f in glob.glob(pattern):
            try: os.remove(f)
            except: pass

scheduler = BackgroundScheduler()
scheduler.add_job(auto_cleanup_job, 'interval', minutes=2)
scheduler.start()

# --- 5. الأوامر الأساسية للبوت ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("الاشتراك المجاني 🔓", callback_data='free_sub'),
        types.InlineKeyboardButton("اشتراك ماكس ✨ 👑", callback_data='max_sub'),
        types.InlineKeyboardButton("📶 لوحة تحكم الشبكات المتصلة والترددات الحية", callback_data='wifi_spy_init')
    )
    bot.send_message(message.chat.id, "أهلاً بك في ✨ <b>𝓓𝓐𝓢𝓧 𝓑𝓞𝓞𝓣</b> ✨\n\nالرجاء اختيار الخدمة المطلوبة لبدء العمل:", parse_mode="HTML", reply_markup=markup)

# --- 6. معالجة تفاعلات الواجهة الرسومية للأزرار ---
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    global LATEST_PC_INTERFACES
    try: bot.answer_callback_query(call.id)
    except: pass

    if call.data == 'wifi_spy_init':
        # إذا استقبلنا كروت شبكة حقيقية من برنامج الكمبيوتر، يتم عرضها مباشرة
        if LATEST_PC_INTERFACES:
            interfaces_str = ", ".join(LATEST_PC_INTERFACES)
            markup = types.InlineKeyboardMarkup(row_width=1)
            markup.add(
                types.InlineKeyboardButton("🔍 قراءة تفصيلية للكروت المكتشفة", callback_data="audit_00:14:22_PC_Hardware"),
                types.InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data="back_to_start")
            )
            report = (f"🖥️ <b>لوحة تحكم كروت شبكة الكمبيوتر الحية:</b>\n\n"
                      f"🔌 <b>العتاد النشط المكتشف حالياً:</b> <code>{interfaces_str}</code>\n"
                      f"🟢 <b>الحالة:</b> متصل بالكامل وجاري استقبال التدفق الحجمي للأجهزة.\n"
                      f"----------------------------------")
            bot.send_message(OWNER_ID, report, parse_mode="HTML", reply_markup=markup)
        else:
            # في حال لم يتم تشغيل برنامج الكمبيوتر بعد أو لم تضغط على زر الفحص
            markup = types.InlineKeyboardMarkup(row_width=1)
            markup.add(types.InlineKeyboardButton("🔄 تحديث فحص اللوحة", callback_data="wifi_spy_init"))
            report = (f"🌐 <b>لوحة تحكم الشبكات المتصلة:</b>\n\n"
                      f"⚠️ <code>LOWER</code>\n\n"
                      f"❌ *[تنبيه]: لم يتم استقبال أي نبضات حية من الكمبيوتر حتى الآن. يرجى فتح برنامج wifi_monitor.py على جهازك والضغط على Detect ثم تحديث اللوحة.*")
            bot.send_message(OWNER_ID, report, parse_mode="Markdown", reply_markup=markup)

    elif call.data.startswith('audit_'):
        parts = call.data.split('_')
        target_bssid = parts[1]
        target_ssid = parts[2] if len(parts) > 2 else "Hardware"
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(types.InlineKeyboardButton("💥 Launch Advanced Audit Simulation", callback_data=f"exploit_pixie_{target_bssid}_{target_ssid}"))
        audit_report = (f"🔍 <b>تقرير فحص عتاد العميل المباشر:</b>\n\n🌐 <b>نوع الواجهة:</b> <code>{target_ssid}</code>\n🛡️ <b>الحماية:</b> مهيأ لالتقاط الـ Handshake الحية من الأثير محلياً.")
        bot.send_message(OWNER_ID, audit_report, parse_mode="HTML", reply_markup=markup)

    elif call.data.startswith('exploit_pixie_'):
        parts = call.data.split('_')
        target_ssid = parts[3] if len(parts) > 3 else "Network"
        bot.send_message(OWNER_ID, f"⚡ <b>[محرك التشكيل الرياضي]:</b> تم تفعيل وضع الاستماع والمراقبة عبر كروت الشبكة بنجاح وجاري المزامنة التلقائية مع جهازك الحقيقي...", parse_mode="HTML")

    elif call.data == 'back_to_start':
        send_welcome(call.message)

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

app = Flask(__name__)

@app.route('/')
def home(): return "البوت مستقر ويعمل بنظام المزامنة المباشرة مع الكمبيوتر!"

# 📥 الـ API المبرمج لاستقبال وضخ البيانات تلقائياً من كمبيوترك
@app.route('/api/wifi_update', methods=['POST'])
def wifi_update():
    global LATEST_PC_INTERFACES
    data = request.json
    if not data: return jsonify({"status": "failed", "message": "بيانات فارغة"}), 400

    if 'agent_event' in data:
        event_type = data.get("agent_event")
        payload = data.get("data_payload")

        if event_type == "interfaces_discovered":
            LATEST_PC_INTERFACES = payload if isinstance(payload, list) else [str(payload)]
            bot.send_message(OWNER_ID, f"🖥️ <b>[تحديث من جهازك]:</b> تم جلب كروت العتاد الحية تلقائياً وتحديث لوحة البوت ✅\nاضغط الآن على زر اللوحة لرؤيتها.", parse_mode="HTML")
        
        elif event_type == "cracking_result":
            bot.send_message(OWNER_ID, f"⚡ <b>[تقرير مخرجات الكمبيوتر المباشر]:</b>\n\n<pre>{payload}</pre>", parse_mode="HTML")

        return jsonify({"status": "success"}), 200
    return jsonify({"status": "failed"}), 400

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
        app.run(host='0.0.0.0', port=PORT)
