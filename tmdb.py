from diskcache import Cache
from datetime import timedelta
import httpx
import os
import asyncio
import kitsu

from dotenv import load_dotenv
load_dotenv()

TMDB_POSTER_URL = 'https://image.tmdb.org/t/p/w500'
TMDB_BACK_URL = 'https://image.tmdb.org/t/p/original'
TMDB_API_KEY = os.getenv('TMDB_API_KEY')

# Cache set
tmp_cache = Cache('/tmp/ids')
tmp_cache.clear()
cache_expire_time = timedelta(days=1).total_seconds()
max_retries = 5

async def get_tmdb_data(client: httpx.AsyncClient, id: str, type: str) -> dict:
    params = {
        "external_source": "imdb_id",
        "language": "it-IT",
        "api_key": TMDB_API_KEY
    }

    headers = {
        "accept": "application/json"
    }

    if 'kitsu' in id:
        id = await kitsu.convert_to_imdb(id, type)
    
    url = f"https://api.themoviedb.org/3/find/{id}"
    item = tmp_cache.get(id)

    if item != None:
        return item
    else:
        for attempt in range(1, max_retries + 1):
            response = await client.get(url, headers=headers, params=params)

            if response.status_code == 200:
                tmp_cache.set(id, response.json(), expire=cache_expire_time)
                return response.json()

            elif response.status_code == 429:
                print(response)
                await asyncio.sleep(attempt * 2)

        return {}