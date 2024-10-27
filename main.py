from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import httpx
import tmdb
import base64

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Config CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


addon_meta_url = 'https://94c8cb9f702d-tmdb-addon.baby-beamup.club/%7B%22provide_imdbId%22%3A%22true%22%2C%22language%22%3A%22it-IT%22%7D'


@app.get('/')
@app.get('/configure')
async def configure(request: Request):
    return templates.TemplateResponse("configure.html", {"request": request})


@app.get('/{addon_url}/manifest.json')
async def get_manifest(addon_url):
    addon_url = decode_base64_url(addon_url)
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{addon_url}/manifest.json")
        manifest = response.json()

    manifest['description'] += ' | Tradotto da Toast Translator.'
    manifest['id'] += '.toast'
    manifest['idPrefixes'].append('tmdb')
    if 'meta' not in manifest['resources']:
        manifest['resources'].append('meta')
    return manifest


@app.get('/{addon_url}/catalog/{type}/{query:path}')
async def get_catalog(addon_url, type: str, query: str):
    addon_url = decode_base64_url(addon_url)
    async with httpx.AsyncClient(follow_redirects=True, timeout=10) as client:
        response = await client.get(f"{addon_url}/catalog/{type}/{query}")
        catalog = response.json()

        tasks = [
            tmdb.get_tmdb_data(client, item.get('imdb_id', item.get('id'))) for item in catalog['metas']
        ]
        tmdb_details = await asyncio.gather(*tasks)

    new_catalog = translate_catalog(catalog, tmdb_details)
    return new_catalog


@app.get('/{addon_url}/meta/{type}/{id}.json')
async def get_meta(addon_url, type: str, id: str):
    addon_url = decode_base64_url(addon_url)
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(f"{addon_meta_url}/meta/{type}/{id}.json")
        meta = response.json()
        meta['meta']['id'] = id
    return meta


def extract_imdb_ids(catalog: dict) -> list:
    imdb_ids = []
    for meta in catalog['metas']:
        imdb_ids.append(meta.get('imdb_id', meta.get('id')))
    return imdb_ids


def translate_catalog(original: dict, tmdb_meta: dict) -> dict:
    new_catalog = original
    
    for i, item in enumerate(new_catalog['metas']):
        try:
            type = item['type']
            type_key = 'movie' if type == 'movie' else 'tv'
            detail = tmdb_meta[i][f"{type_key}_results"][0]
        except:
            print('Total skip')
            continue
        try:
            item['name'] = detail['title'] if type == 'movie' else detail['name']
        except:
            print('Name skip')
        try:
            item['description'] = detail['overview']
        except:
            print('Description skip')
        try:
            item['poster'] = tmdb.TMDB_POSTER_URL + detail['poster_path']
        except:
            print('Poster skip')

    return new_catalog


def decode_base64_url(encoded_url):
    padding = '=' * (-len(encoded_url) % 4)
    encoded_url += padding
    decoded_bytes = base64.b64decode(encoded_url)
    return decoded_bytes.decode('utf-8')


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8080)   
