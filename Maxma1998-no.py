import os
import services

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    user_id = call.message.chat.id
    
    # التحقق من الاشتراك قبل تنفيذ أي خدمة
    if not services.is_authorized(user_id):
        bot.answer_callback_query(call.id, "غير مشترك!")
        bot.send_message(user_id, "⚠️ يجب عليك الاشتراك في خدمة 'ماكس' لاستخدام هذه الميزة.")
        return

    # إذا كان مشتركاً، ينفذ الأوامر
    if call.data == 'to_pdf':
        services.convert_photo_to_pdf(bot, call.message)
    elif call.data == 'to_text':
        services.convert_photo_to_text(bot, call.message)
