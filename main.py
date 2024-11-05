from typing import Union

from fastapi import FastAPI, Request

app = FastAPI()

YOUTUBE_PLAYLIST_URL = "https://www.youtube.com/playlist"

@app.get("/youtube/{_:path}")
def retrieve_playlist_json(request: Request, q: Union[str, None] = None):

    # using the playlist id, retrieve names of all the songs
    
    # then, check using the spotify api if these songs actually exist

    # if the song doesn't exist, first check if for the link of each song
        # if it's a self contained playlist, then use a regex to try and
        # retrieve song names for those songs within the compilation

    return {"path": YOUTUBE_PLAYLIST_URL,
            "playlist_id": request.url.query}