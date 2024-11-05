from typing import Union

from fastapi import FastAPI, Request

app = FastAPI()

YOUTUBE_PLAYLIST_URL = "https://www.youtube.com/playlist"

@app.get("/youtube/{_:path}")
def retrieve_playlist_json(request: Request, q: Union[str, None] = None):
    return {"path": YOUTUBE_PLAYLIST_URL,
            "playlist_id": request.url.query}