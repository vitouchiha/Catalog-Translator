import httpx
import os

#from dotenv import load_dotenv
#load_dotenv()

TMDB_POSTER_URL = 'https://image.tmdb.org/t/p/w500'
TMDB_BACK_URL = 'https://image.tmdb.org/t/p/original'
TMDB_API_KEY = os.getenv('TMDB_API_KEY')

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

    response = await client.get(url, headers=headers, params=params)
    return response.json()