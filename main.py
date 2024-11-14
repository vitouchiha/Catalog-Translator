from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from datetime import timedelta
from diskcache import Cache
from deepmerge import Merger
import asyncio
import httpx
import tmdb
import kitsu
import base64

translator_version = 'v0.0.4'
FORCE_PREFIX = False
FORCE_META = False

# Cache set
tmp_cache = Cache('/tmp/meta')
tmp_cache.clear()
cache_expire_time = timedelta(hours=12).total_seconds()


# Merger
meta_merger = Merger(
    [(dict, "merge")],
    ["override"],
    ["override"]
)

# Videos Merger
def merge_lists_on_id(list1, list2):
    combined = list1 + list2
    merged_dict = {}
    translate_list = []

    for item in combined:
        if item['id'] not in merged_dict:
            translate_list.append(item['id'])
        else:
            translate_list.remove(item['id'])

        merged_dict[item['id']] = item

    print(translate_list)
    return list(merged_dict.values())


# Starts keep alive HF
@asynccontextmanager
async def lifespan(app: FastAPI):
    #asyncio.create_task(keep_alive_loop())
    print('Started')
    yield
    print('Shutdown')

app = FastAPI(lifespan=lifespan)
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


# Config CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

stremio_headers = {
    'connection': 'keep-alive', 
    'user-agent': 'Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) QtWebEngine/5.15.2 Chrome/83.0.4103.122 Safari/537.36 StremioShell/4.4.168', 
    'accept': '*/*', 
    'origin': 'https://app.strem.io', 
    'sec-fetch-site': 'cross-site', 
    'sec-fetch-mode': 'cors', 
    'sec-fetch-dest': 'empty', 
    'accept-encoding': 'gzip, deflate, br'
}

addon_meta_url = 'https://94c8cb9f702d-tmdb-addon.baby-beamup.club/%7B%22provide_imdbId%22%3A%22true%22%2C%22language%22%3A%22it-IT%22%7D'
cinemeta_url = 'https://v3-cinemeta.strem.io'


async def keep_alive_loop():
    while True:
        update_time = timedelta(days=1, hours=23, minutes=55).total_seconds()
        await asyncio.sleep(update_time)
        async with httpx.AsyncClient() as client:
            await client.get(f"http://localhost:8080/keep_alive")

@app.get('/keep_alive')
async def keep_alive():
    print('Keep Alive: updated.')
    return "OK"


@app.get('/', response_class=HTMLResponse)
@app.get('/configure', response_class=HTMLResponse)
async def configure(request: Request):
    return templates.TemplateResponse("configure.html", {"request": request})


@app.get('/{addon_url}/{skip_poster}/manifest.json')
async def get_manifest(addon_url):
    addon_url = decode_base64_url(addon_url)
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(f"{addon_url}/manifest.json")
        manifest = response.json()

    is_translated = manifest.get('translated', False)
    if not is_translated:
        manifest['translated'] = True
        manifest['name'] += ' 🇮🇹'

        if 'description' in manifest:
            manifest['description'] += f" | Tradotto da Toast Translator. {translator_version}"
        else:
            manifest['description'] = f"Tradotto da Toast Translator. {translator_version}"
    
    if FORCE_PREFIX:
        if 'idPrefixes' in manifest:
            if 'tmdb:' not in manifest['idPrefixes']:
                manifest['idPrefixes'].append('tmdb:')
            if 'tt' not in manifest['idPrefixes']:
                manifest['idPrefixes'].append('tt')

    if FORCE_META:
        if 'meta' not in manifest['resources']:
            manifest['resources'].append('meta')

    return manifest


@app.get('/{addon_url}/{skip_poster}/catalog/{type}/{path:path}')
async def get_catalog(addon_url, type: str, skip_poster: str, path: str):

    # Cinemeta last-videos
    if 'last-videos' in path:
        return RedirectResponse(f"{cinemeta_url}/catalog/{type}/{path}")

    addon_url = decode_base64_url(addon_url)
    async with httpx.AsyncClient(follow_redirects=True, timeout=20) as client:
        response = await client.get(f"{addon_url}/catalog/{type}/{path}")
        catalog = response.json()

        if 'metas' in catalog:
            if type == 'anime':
                await remove_duplicates(catalog)
            tasks = [
                tmdb.get_tmdb_data(client, item.get('imdb_id', item.get('id')), item['type']) for item in catalog['metas']
            ]
            tmdb_details = await asyncio.gather(*tasks)
        else:
            return {}

    new_catalog = translate_catalog(catalog, tmdb_details, skip_poster)
    return new_catalog


@app.get('/{addon_url}/{skip_poster}/meta/{type}/{id}.json')
async def get_meta(addon_url, type: str, id: str):
    addon_url = decode_base64_url(addon_url)
    async with httpx.AsyncClient(follow_redirects=True, timeout=20) as client:

        # Get from cache
        meta = tmp_cache.get(id)

        # Not in cache
        if meta == None:
            # Handle imdb ids
            if 'tt' in id:
                tasks = [
                    client.get(f"{addon_meta_url}/meta/{type}/{id}.json"),
                    client.get(f"{cinemeta_url}/meta/{type}/{id}.json")
                ]
                metas = await asyncio.gather(*tasks)
                tmdb_meta, cinemeta_meta = metas[0].json(), metas[1].json()
                
                # Not empty tmdb meta
                if len(tmdb_meta['meta']) > 0:
                    merged_videos = merge_lists_on_id(cinemeta_meta.get('meta', {}).get('videos', []), tmdb_meta.get('meta', {}).get('videos', []))
                    meta = meta_merger.merge(cinemeta_meta, tmdb_meta)
                    meta['meta']['videos'] = merged_videos
                else:
                    meta = cinemeta_meta

            # Handle kitsu ids
            elif 'kitsu' in id:
                # Try convert kitsu to imdb
                imdb_id, is_converted = await kitsu.convert_to_imdb(id, type)

                if is_converted:
                    response = await client.get(f"{addon_meta_url}/meta/{type}/{imdb_id}.json")
                    meta = response.json()
                    if type == 'movie':
                        meta['meta']['behaviorHints']['defaultVideoId'] = id
                    elif type == 'series':
                        videos = kitsu.parse_meta_videos(meta['meta']['videos'], imdb_id)
                        meta['meta']['videos'] = videos
                else:
                    # Get meta from kitsu addon
                    response = await client.get(f"{kitsu.kitsu_addon_url}/meta/{type}/{id.replace(':','%3A')}.json")
                    meta = response.json()

        meta['meta']['id'] = id
        tmp_cache.set(id, meta, expire=cache_expire_time)
        return meta


# Subs redirect
@app.get('/{addon_url}/{skip_poster}/subtitles/{path:path}')
async def get_subs(addon_url, path: str):
    addon_url = decode_base64_url(addon_url)
    return RedirectResponse(f"{addon_url}/subtitles/{path}")

# Stream redirect
@app.get('/{addon_url}/{skip_poster}/stream/{path:path}')
async def get_subs(addon_url, path: str):
    addon_url = decode_base64_url(addon_url)
    return RedirectResponse(f"{addon_url}/stream/{path}")


def translate_catalog(original: dict, tmdb_meta: dict, skip_poster) -> dict:
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
            if skip_poster == "0":
                item['poster'] = tmdb.TMDB_POSTER_URL + detail['poster_path']
        except:
            print('Poster skip')
        try:
            item['background'] = tmdb.TMDB_BACK_URL + detail['backdrop_path']
        except:
            print("Background skip")

    return new_catalog


def decode_base64_url(encoded_url):
    padding = '=' * (-len(encoded_url) % 4)
    encoded_url += padding
    decoded_bytes = base64.b64decode(encoded_url)
    return decoded_bytes.decode('utf-8')


async def remove_duplicates(catalog) -> None:
    unique_items = []
    seen_ids = set()
    
    for item in catalog['metas']:
        if 'kitsu' in item['id']:
            item['imdb_id'], is_converted = await kitsu.convert_to_imdb(item['id'], item['type'])

        if item['imdb_id'] not in seen_ids:
            unique_items.append(item)
            seen_ids.add(item['imdb_id'])

    catalog['metas'] = unique_items


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8080)   
