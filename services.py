import instaloader
import yt_dlp
import img2pdf
import os

# تهيئة انستالودر
L = instaloader.Instaloader(download_videos=True, download_pictures=True, save_metadata=False)

def get_insta_data(username):
    L.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    profile = instaloader.Profile.from_username(L.context, username)
    return L.get_stories(userids=[profile.userid])

def download_video_service(url):
    ydl_opts = {
        'format': 'best',
        'outtmpl': 'video.mp4',
        'noplaylist': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

def convert_to_pdf(image_path, pdf_path):
    with open(pdf_path, "wb") as f:
        f.write(img2pdf.convert(image_path))
