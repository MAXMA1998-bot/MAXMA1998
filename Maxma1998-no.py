import os
import telebot
from flask import Flask
from threading import Thread
import services # هذا الملف موجود عندك بالفعل

TOKEN = os.environ.get('TOKEN')
bot = telebot.TeleBot(TOKEN)

# إعداد خادم الويب لـ Railway
app = Flask('')
@app.route('/')
def home(): return "البوت يعمل!"

def run_web():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))

# تشغيل الخادم
Thread(target=run_web).start()

# --- معالجة الأزرار ---
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    # تمرير 'bot' و 'call.message' للملف الآخر
    if call.data == 'to_pdf':
        services.convert_photo_to_pdf(bot, call.message)
    elif call.data == 'to_text':
        services.convert_photo_to_text(bot, call.message)

bot.infinity_polling()
