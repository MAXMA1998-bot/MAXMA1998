
# قائمة المشتركين (يمكن لاحقاً ربطها بقاعدة بيانات)
AUTHORIZED_USERS = [int(os.environ.get('ADMIN_ID', 438077185))] 

def is_authorized(user_id):
    # هنا يمكنك إضافة قائمة ID المشتركين أو التحقق من قاعدة بيانات
    return user_id in AUTHORIZED_USERS

def convert_photo_to_pdf(bot, message):
    if not is_authorized(message.chat.id):
        bot.reply_to(message, "❌ عذراً، هذه الخدمة للمشتركين فقط.")
        return
    # ... (بقية كود التحويل) ...
