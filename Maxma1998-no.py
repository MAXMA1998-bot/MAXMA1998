import os
import telebot
from flask import Flask
from threading import Thread
import services

TOKEN = os.environ.get('TOKEN')
bot = telebot.TeleBot(TOKEN)

# --- إعداد Flask ---
app = Flask('')
@app.route('/')
def home(): return "البوت يعمل!"

# هذه الدالة لتشغيل الويب فقط
def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# تشغيل الويب في خلفية (Thread)
Thread(target=run_web).start()

# --- معالجة الأزرار ---
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == 'to_pdf':
        services.convert_photo_to_pdf(bot, call.message)
    elif call.data == 'to_text':
        services.convert_photo_to_text(bot, call.message)

# --- تشغيل البوت ---
# البوت يعمل هنا في الخط الأساسي، والويب يعمل في Thread
if __name__ == "__main__":
    print("البوت بدأ العمل...")
    bot.infinity_polling()
