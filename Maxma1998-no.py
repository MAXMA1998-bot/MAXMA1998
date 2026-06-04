import os
import telebot
import logging
import time
import threading
import requests
import io
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

# نظام حماية من الضغط (Rate Limiting)
user_last_call = {}
def is_spaming(user_id):
    last_time = user_last_call.get(user_id, 0)
    if time.time() - last_time < 2: return True
    user_last_call[user_id] = time.time()
    return False

# --- دالة التحميل الشاملة (API) ---
def process_universal_video(message):
    if is_spaming(message.chat.id): return
    url = message.text.strip()
    
    # حماية: فلترة الروابط
    if not any(d in url for d in ['instagram.com', 'facebook.com', 'youtube.com', 'youtu.be', 'tiktok.com']):
        bot.send_message(message.chat.id, "⚠️ رابط غير مدعوم.")
        return

    wait_msg = bot.send_message(message.chat.id, "⏳ جاري التحميل...")
    
    def worker():
        try:
            api_url = "https://api.cobalt.tools/api/json"
            payload = {"url": url, "vCodec": "h264"}
            headers = {"Accept": "application/json", "Content-Type": "application/json"}
            response = requests.post(api_url, json=payload, headers=headers).json()
            
            if response.get("status") == "success":
                bot.send_video(message.chat.id, response.get("url"), caption="✅ تم التحميل بنجاح!")
            else:
                bot.send_message(message.chat.id, "⚠️ فشل التحميل.")
        except Exception as e:
            logging.error(f"Error in video_link: {e}")
            bot.send_message(message.chat.id, "⚠️ حدث خطأ تقني.")
        finally:
            bot.delete_message(message.chat.id, wait_msg.message_id)

    threading.Thread(target=worker).start()

# --- دالة إزالة الخلفية (أداء محسن) ---
def process_remove_bg(message):
    try:
        wait_msg = bot.send_message(message.chat.id, "⚙️ جاري المعالجة...")
        file_id = message.photo[-1].file_id
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        input_image = Image.open(io.BytesIO(downloaded_file))
        input_image.thumbnail((800, 800))
        output_image = remove(input_image)
        
        byte_arr = io.BytesIO()
        output_image.save(byte_arr, format='PNG')
        bot.send_photo(message.chat.id, byte_arr.getvalue())
        bot.delete_message(message.chat.id, wait_msg.message_id)
    except Exception as e:
        logging.error(f"BG Error: {e}")

# --- الربط الأساسي للبوت ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("الاشتراك المجاني", callback_data='free_sub'),
               types.InlineKeyboardButton("اشتراك ماكس ✨", callback_data='max_sub'))
    bot.send_message(message.chat.id, "أهلاً بك في ✨ 𝓜𝓐𝓧 𝓑𝓞𝓞𝓣 ✨", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == 'free_sub':
        # ... (بقية كود الأزرار الخاص بك هنا) ...
        pass
    elif call.data == 'f2':
        msg = bot.send_message(call.message.chat.id, "أرسل رابط الفيديو:")
        bot.register_next_step_handler(msg, process_universal_video)

# --- تشغيل البوت و Flask ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    Thread(target=lambda: Flask('').run(host='0.0.0.0', port=port)).start()
    logging.info("Bot is running...")
    bot.infinity_polling()
