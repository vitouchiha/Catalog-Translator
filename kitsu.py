from diskcache import Cache
import httpx
import anime_mapping

kitsu_addon_url = 'https://anime-kitsu.strem.fun'

# Cache load
kitsu_cache = Cache('/tmp/kitsu_ids')
kitsu_cache.clear()
imdb_map = anime_mapping.load()
for kitsu_id, imdb_id in imdb_map.items():
    kitsu_cache.set(f"kitsu:{kitsu_id}", imdb_id)


async def convert_to_imdb(kitsu_id: str, type: str) -> str:
    imdb_id = kitsu_cache.get(kitsu_id)

    if imdb_id == None:
        async with httpx.AsyncClient(follow_redirects=True, timeout=20) as client:
            response = await client.get(f"{kitsu_addon_url}/meta/{type}/{kitsu_id.replace(':','%3A')}.json")
            try:
                imdb_id = response.json()['meta']['imdb_id']

            except:
                # If imdb_id not found save kitsu_id as imdb_id (better performance)
                imdb_id = kitsu_id
                return kitsu_id
            
            finally:
                kitsu_cache.set(kitsu_id, imdb_id)

    return imdb_id