import instaloader
import yt_dlp
import img2pdf
import os

# تهيئة انستالودر
L = instaloader.Instaloader(download_videos=True, download_pictures=True, save_metadata=False)


def get_insta_media(username):
    url = f"https://www.instagram.com/stories/{username}/"
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'format': 'best',
        'outtmpl': 'story_%(id)s.mp4',
        # إضافة هذه السطور لتقليل احتمالية طلب تسجيل الدخول
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=True)
            return info.get('requested_downloads', [])
        except Exception as e:
            # إذا فشل التحميل، هذا يعني أن الحساب برايفت أو يتطلب تسجيل دخول إجباري
            print(f"فشل التحميل: {e}")
            return []


def download_video_service(url):
    ydl_opts = {'format': 'best', 'outtmpl': 'video.mp4', 'noplaylist': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

def convert_to_pdf(image_path, pdf_path):
    with open(pdf_path, "wb") as f:
        f.write(img2pdf.convert(image_path))
