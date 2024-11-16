import tmdb
import asyncio
import httpx

async def translate_with_api(client: httpx.AsyncClient, text: str, source='en', target='it') -> str:
    api_url = 'https://trans.zillyhuhn.com/translate'

    payload = {
        "q": text,
        "source": source,
        "target": target,
        "format": "text",
        "alternatives": 0,
    }

    response = await client.post(api_url, data=payload)
    translated_text = response.json().get('translatedText', '')
    return translated_text


def translate_catalog(original: dict, tmdb_meta: dict, skip_poster) -> dict:
    new_catalog = original
    for i, item in enumerate(new_catalog['metas']):
        try:
            type = item['type']
            type_key = 'movie' if type == 'movie' else 'tv'
            detail = tmdb_meta[i][f"{type_key}_results"][0]
        except: pass
        else:
            try: item['name'] = detail['title'] if type == 'movie' else detail['name']
            except: pass
            try: item['description'] = detail['overview']
            except: pass
            try: item['background'] = tmdb.TMDB_BACK_URL + detail['backdrop_path']
            except: pass
            if skip_poster == "0":
                try: item['poster'] = tmdb.TMDB_POSTER_URL + detail['poster_path']
                except: pass


    return new_catalog


async def translate_episodes(client: httpx.AsyncClient, original_episodes: list[dict]):
    translate_index = []
    tasks = []
    new_episodes = original_episodes

    # Select not translated episodes
    for i, episode in enumerate(original_episodes):
        if 'tvdb_id' in episode:
            tasks.append(tmdb.get_tmdb_data(client, episode['tvdb_id'], "tvdb_id"))
            translate_index.append(i)

    translations = await asyncio.gather(*tasks)

    # Translate episodes 
    for i, t_index in enumerate(translate_index):
        try: detail = translations[i][f"tv_episode_results"][0]
        except: pass
        else:
            try: new_episodes[t_index]['name'] = detail['name']
            except: pass
            try: new_episodes[t_index]['overview'] = detail['overview']
            except: pass
            try: new_episodes[t_index]['thumbnail'] = tmdb.TMDB_BACK_URL + detail['still_path']
            except: pass

    return new_episodes