from diskcache import Cache
import httpx
import os

#from dotenv import load_dotenv
#load_dotenv()

TMDB_POSTER_URL = 'https://image.tmdb.org/t/p/w500'
TMDB_BACK_URL = 'https://image.tmdb.org/t/p/original'
TMDB_API_KEY = os.getenv('TMDB_API_KEY')

# Cache set
tmp_cache = Cache('/tmp/ids')
tmp_cache.clear()
cache_expire_time = 43200 # 12h

async def get_tmdb_data(client: httpx.AsyncClient, imdb_id: str) -> dict:
    url = f"https://api.themoviedb.org/3/find/{imdb_id}"

    params = {
        "external_source": "imdb_id",
        "language": "it-IT",
        "api_key": TMDB_API_KEY
    }

    headers = {
        "accept": "application/json"
    }

    item = tmp_cache.get(imdb_id)

    if item != None:
        return item
    else:
        response = await client.get(url, headers=headers, params=params)

        if response.status_code == 200:
            tmp_cache.set(imdb_id, response.json(), expire=cache_expire_time)
            
        return response.json()