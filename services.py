import os
import io
import pytesseract
from PIL import Image

# إعداد الصلاحيات
ADMIN_ID = int(os.environ.get('ADMIN_ID', 438077185))

def is_authorized(user_id):
    """التحقق مما إذا كان المستخدم هو الأدمن"""
    return user_id == ADMIN_ID

def convert_photo_to_pdf(bot, message):
    """دالة تحويل الصورة إلى PDF"""
    if not is_authorized(message.chat.id):
        bot.reply_to(message, "❌ عذراً، هذه الخدمة للمشتركين فقط.")
        return
    
    try:
        bot.send_message(message.chat.id, "⏳ جاري التحويل إلى PDF...")
        # الحصول على الصورة بأعلى جودة
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        # فتح الصورة
        image = Image.open(io.BytesIO(downloaded_file))
        
        # حفظ كـ PDF في الذاكرة
        pdf_buffer = io.BytesIO()
        image.save(pdf_buffer, "PDF", resolution=100.0)
        pdf_buffer.seek(0)
        
        # إرسال الملف
        bot.send_document(message.chat.id, pdf_buffer, visible_file_name="converted_image.pdf")
    except Exception as e:
        bot.reply_to(message, f"⚠️ حدث خطأ أثناء التحويل: {str(e)}")

def convert_photo_to_text(bot, message):
    """دالة استخراج النص من الصورة (OCR)"""
    if not is_authorized(message.chat.id):
        bot.reply_to(message, "❌ عذراً، هذه الخدمة للمشتركين فقط.")
        return
    
    try:
        bot.send_message(message.chat.id, "🔍 جاري استخراج النص...")
        # الحصول على الصورة
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        # فتح الصورة باستخدام PIL
        img = Image.open(io.BytesIO(downloaded_file))
        
        # استخراج النص باستخدام pytesseract
        text = pytesseract.image_to_string(img)
        
        if text.strip():
            bot.reply_to(message, f"📝 النص المستخرج:\n\n{text[:3000]}")
        else:
            bot.reply_to(message, "⚠️ لم أتمكن من العثور على أي نص في الصورة.")
            
    except Exception as e:
        bot.reply_to(message, f"⚠️ حدث خطأ أثناء القراءة: {str(e)}")
