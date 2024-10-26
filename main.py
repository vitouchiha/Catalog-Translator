from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import httpx
import tmdb

app = FastAPI()

# Config CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


addon_url = 'https://v3-cinemeta.strem.io'
addon_meta_url = 'https://94c8cb9f702d-tmdb-addon.baby-beamup.club/%7B%22provide_imdbId%22%3A%22true%22%2C%22language%22%3A%22it-IT%22%7D'

@app.get('/')
async def index():
    return 'OK'


@app.get('/manifest.json')
async def get_manifest():
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{addon_url}/manifest.json")
        manifest = response.json()

    manifest['description'] += ' | Tradotto da Toast Translator.'
    manifest['id'] += '.toast'
    return manifest


@app.get('/catalog/{type}/{query:path}')
async def get_catalog(type: str, query: str):
    async with httpx.AsyncClient(follow_redirects=True, timeout=10) as client:
        response = await client.get(f"{addon_url}/catalog/{type}/{query}")
        catalog = response.json()

        tasks = [tmdb.get_tmdb_data(client, item.get('imdb_id', item.get('id'))) for item in catalog['metas']]
        tmdb_details = await asyncio.gather(*tasks)

    new_catalog = translate_catalog(catalog, tmdb_details, type)

    return new_catalog


@app.get('/meta/{type}/{query:path}')
async def get_meta(type: str, query: str):
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(f"{addon_meta_url}/meta/{type}/{query}")
        meta = response.json()
    return meta


def extract_imdb_ids(catalog: dict) -> list:
    imdb_ids = []
    for meta in catalog['metas']:
        imdb_ids.append(meta.get('imdb_id', meta.get('id')))
    return imdb_ids

def translate_catalog(original: dict, tmdb_meta: dict, type: str) -> dict:
    new_catalog = original
    type_key = 'movie' if type == 'movie' else 'tv'
    print(type_key)

    for i, item in enumerate(new_catalog['metas']):
        try:
            detail = tmdb_meta[i][f"{type_key}_results"][0]
            item['name'] = detail['title'] if type == 'movie' else detail['name']
            item['description'] = detail['overview']
            item['poster'] = tmdb.TMDB_POSTER_URL + detail['poster_path']
        except:
            continue

    return new_catalog


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8080)   