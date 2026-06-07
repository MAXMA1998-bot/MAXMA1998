import os
import requests

# استدعاء مفتاح API من متغيرات البيئة في Railway
API_KEY = os.getenv("TMDB_API_KEY")
BASE_URL = "https://api.themoviedb.org/3"

def get_movie_results(query):
    """جلب قائمة بالأفلام المطابقة للبحث"""
    url = f"{BASE_URL}/search/movie"
    params = {"api_key": API_KEY, "query": query, "language": "ar-AR"}
    try:
        response = requests.get(url, params=params).json()
        return response.get('results', [])[:5]
    except:
        return []

def get_movie_full_details(movie_id):
    """جلب تفاصيل الفيلم الواحد"""
    url = f"{BASE_URL}/movie/{movie_id}"
    params = {"api_key": API_KEY, "language": "ar-AR"}
    try:
        response = requests.get(url, params=params).json()
        return response
    except:
        return None
