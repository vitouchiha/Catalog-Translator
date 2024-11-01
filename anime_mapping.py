import httpx

anime_mapping_url = 'https://raw.githubusercontent.com/Fribb/anime-lists/refs/heads/master/anime-list-full.json'

def load() -> dict:
    raw_map = httpx.Client().get(anime_mapping_url).json()
    mapping_list = {}

    for item in raw_map:
        kitsu_id = item.get('kitsu_id', None)
        imdb_id = item.get('imdb_id', None)
        if kitsu_id != None and imdb_id != None and 'tt' in imdb_id:
            mapping_list[kitsu_id] = imdb_id

    return mapping_list