import json
from pathlib import Path

import httpx

from gamelib.config import settings

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / 'data'
FILE_PATH = DATA_DIR / 'steam_library.json'

LIBRARY_URL = 'https://api.steampowered.com/IPlayerService/GetOwnedGames/v1/'

steam_id = settings.STEAM_ID
api_key = settings.STEAM_API_KEY

if not api_key:
    raise ValueError('STEAM_API_KEY is required but missing.')

if not steam_id:
    raise ValueError('STEAM_ID is required but missing.')

query_params = {
    'key': api_key,
    'steamid': steam_id,
    'include_appinfo': 1,
    'include_played_free_games': 1,
    'format': 'json'
}

response = httpx.get(LIBRARY_URL, params=query_params)

try:
    response.raise_for_status()
except httpx.HTTPStatusError as exc:
    raise SystemExit(
        f'API returned status code: {exc.response.status_code}'
    ) from None

data = response.json()

games = data.get('response', {}).get('games', [])

DATA_DIR.mkdir(parents=True, exist_ok=True)

with open(FILE_PATH, 'w', encoding='utf-8') as f:
    json.dump(games, f, ensure_ascii=False, indent=2)
