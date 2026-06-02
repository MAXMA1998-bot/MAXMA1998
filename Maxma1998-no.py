import os
import telebot
from telebot import types
from flask import Flask
from threading import Thread

# جلب التوكن من Railway
TOKEN = os.environ.get('TOKEN')
bot = telebot.TeleBot(TOKEN)

# 1. كود الترحيب مع الأزرار الرئيسية
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton("الاشتراك المجاني", callback_data='free_sub')
    btn2 = types.InlineKeyboardButton("اشتراك ماكس ✨", callback_data='max_sub')
    markup.add(btn1, btn2)
    
    welcome_text = "أهلاً بك في ✨ 𝓜𝓐𝓧 𝓑𝓞𝓞𝓣 ✨\n\nكيف يمكنني مساعدتك اليوم؟"
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup)

# 2. معالج ضغطات الأزرار (هنا يتم الدمج)
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    # حالة زر الاشتراك المجاني
    if call.data == 'free_sub':
        markup = types.InlineKeyboardMarkup(row_width=2)
        btns = [
            types.InlineKeyboardButton("مجاني 1", callback_data='f1'),
            types.InlineKeyboardButton("مجاني 2", callback_data='f2'),
            types.InlineKeyboardButton("مجاني 3", callback_data='f3'),
            types.InlineKeyboardButton("مجاني 5", callback_data='f5')
        ]
        markup.add(*btns)
        bot.edit_message_text("اختر الخدمة المجانية المطلوبة:", 
                              call.message.chat.id, call.message.message_id, reply_markup=markup)

    # حالة زر اشتراك ماكس
    elif call.data == 'max_sub':
        markup = types.InlineKeyboardMarkup(row_width=2)
        # إنشاء 20 زر باستخدام حلقة تكرار
        btns = [types.InlineKeyboardButton(f"ماكس {i}", callback_data=f'max_{i}') for i in range(1, 21)]
        markup.add(*btns)
        bot.edit_message_text("اختر خدمة ماكس المطلوبة:", 
                              call.message.chat.id, call.message.message_id, reply_markup=markup)
    
    # هنا يمكنك إضافة 'else' للرد إذا ضغط المستخدم على زر (مثال: ماكس 1)
    else:
        bot.answer_callback_query(call.id, f"تم اختيار: {call.data}")

# --- كود الاستيقاظ الدائم (Keep Alive) ---
app = Flask('')
@app.route('/')
def home():
    return "البوت يعمل الآن!"

def run():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

def keep_alive():
    t = Thread(target=run)
    t.start()

if __name__ == "__main__":
    keep_alive()
    bot.infinity_polling()
