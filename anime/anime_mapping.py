import httpx

# Map for IDs
anime_mapping_url = 'https://raw.githubusercontent.com/Fribb/anime-lists/refs/heads/master/anime-list-full.json'

# Map for season/episode
anime_db_map_url = 'https://raw.githubusercontent.com/Kometa-Team/Anime-IDs/master/anime_ids.json'


def load_kitsu_map() -> dict:
    """
    Mappa per convertire un id kitsu in un id imdb
    """
    raw_map = httpx.Client().get(anime_mapping_url).json()
    mapping_list = {}

    for item in raw_map:
        kitsu_id = item.get('kitsu_id', None)
        imdb_id = item.get('imdb_id', None)
        if kitsu_id != None and imdb_id != None and 'tt' in imdb_id:
            mapping_list[kitsu_id] = imdb_id

    return mapping_list


def load_mal_map() -> dict:
    """
    Mappa per convertire un id mal in un id imdb
    """
    raw_map = httpx.Client().get(anime_mapping_url).json()
    mapping_list = {}

    for item in raw_map:
        mal_id = item.get('mal_id', None)
        imdb_id = item.get('imdb_id', None)
        if mal_id != None and imdb_id != None and 'tt' in imdb_id:
            mapping_list[mal_id] = imdb_id

    return mapping_list


def load_imdb_map() -> dict:
    """
    Genera una mappa con chiavi imdb_id con al suo interno:
    Tutti gli id corrispondenti di kitsu, animeDB e MAL.
    Serve per incorporare tutti le stagioni in un unico id (imdb)
    """

    raw_map = httpx.Client().get(anime_mapping_url).json()
    anidb_map = httpx.Client().get(anime_db_map_url).json()
    map = {}

    for item in raw_map:

        imdb_id: str | None = item.get('imdb_id')

        if imdb_id != None:
            kitsu_id: str | None = item.get('kitsu_id')
            anidb_id: str | None  = item.get('anidb_id')
            mal_id: str | None  = item.get('mal_id')

            # Create
            if imdb_id not in map:
                map[imdb_id] = {
                    "kitsu_ids": [],
                    "anidb_ids": [],
                    "mal_ids": []
                }
                
            # Update
            if kitsu_id != None and anidb_id != None:
                kitsu_id, anidb_id = str(kitsu_id), str(anidb_id)
                map[imdb_id]['anidb_ids'].append(anidb_id)
                map[imdb_id]['kitsu_ids'].append({
                    kitsu_id: {
                        "season": anidb_map[anidb_id].get('tvdb_season'),
                        "epoffset": anidb_map[anidb_id].get('tvdb_epoffset')
                    }
                })

            if mal_id != None:
                mal_id = str(mal_id)
                map[imdb_id]['mal_ids'].append(mal_id)

    return map


def load_kitsu_to_anidb_map():
    """
    Genera una mappa da chiave valore kitsu id -> anime db id
    """
    raw_map = httpx.Client().get(anime_mapping_url).json()
    map = {}

    for item in raw_map:
        kitsu_id = item.get('kitsu_id', None)
        anidb_id = item.get('anidb_id', None)

        if kitsu_id != None and anidb_id != None:
            map[kitsu_id] = anidb_id
    
    return map


def load_anidb_map():
    map = httpx.Client().get(anime_db_map_url).json()
    return map

if __name__ == '__main__':
    imdb_map = load_imdb_map()
    anidb_map = load_anidb_map()
    print(len(imdb_map))

    titans = imdb_map['tt21209876']
    #print(anidb_map["9541"])
    print(titans)
    """
    kitsu_anidb_map = load_kitsu_to_anidb_map()
    anidb_map = load_anidb_map()

    kitsu_id = 41982
    print(kitsu_anidb_map[kitsu_id])
    item = anidb_map[str(kitsu_anidb_map[kitsu_id])]
    print(item)
    """

"""
{'livechart_id': 754, 'thetvdb_id': 267440, 'anime-planet_id': 'attack-on-titan-2nd-season', 'imdb_id': 'tt2560140', 'anisearch_id': 10082, 'themoviedb_id': 1429, 'anidb_id': 10944, 'kitsu_id': 8671, 'mal_id': 25777, 'type': 'TV', 'notify.moe_id': 'jh2JpFimg', 'anilist_id': 20958}   
{'livechart_id': 2737, 'thetvdb_id': 267440, 'anime-planet_id': 'attack-on-titan-3rd-season', 'imdb_id': 'tt2560140', 'anisearch_id': 12550, 'themoviedb_id': 1429, 'anidb_id': 13241, 'kitsu_id': 13569, 'mal_id': 35760, 'type': 'TV', 'notify.moe_id': '_7O42FiiR', 'anilist_id': 99147} 
{'livechart_id': 3558, 'thetvdb_id': 267440, 'anime-planet_id': 'attack-on-titan-3rd-season-part-ii', 'imdb_id': 'tt2560140', 'anisearch_id': 13942, 'themoviedb_id': 1429, 'anidb_id': 14444, 'kitsu_id': 41982, 'mal_id': 38524, 'type': 'TV', 'notify.moe_id': 'k8I25a-ig', 'anilist_id': 104578}
{'livechart_id': 9491, 'thetvdb_id': 267440, 'anime-planet_id': 'attack-on-titan-the-final-season', 'imdb_id': 'tt2560140', 'anisearch_id': 14484, 'themoviedb_id': 1429, 'anidb_id': 14977, 'kitsu_id': 42422, 'mal_id': 40028, 'type': 'TV', 'notify.moe_id': 'drmaMJIZg', 'anilist_id': 110277}
{'livechart_id': 11174, 'thetvdb_id': 267440, 'anime-planet_id': 'attack-on-titan-the-final-season-the-final-chapters', 'imdb_id': 'tt2560140', 'anisearch_id': 17265, 'themoviedb_id': 1429, 'anidb_id': 17303, 'kitsu_id': 46038, 'mal_id': 51535, 'type': 'SPECIAL', 'notify.moe_id': 'ii
{'livechart_id': 10487, 'thetvdb_id': 267440, 'anime-planet_id': 'attack-on-titan-the-final-season-part-ii', 'imdb_id': 'tt2560140', 'anisearch_id': 16103, 'themoviedb_id': 1429, 'anidb_id': 16177, 'kitsu_id': 44240, 'mal_id': 48583, 'type': 'TV', 'notify.moe_id': 'g9nvf6wMR', 'anilist_id': 131681}
"""