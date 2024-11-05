from typing import Union

from fastapi import FastAPI, Request
from api_keys import YOUTUBE_API_KEY
import requests

app = FastAPI()

YOUTUBE_PLAYLIST_URL = "https://www.youtube.com/playlist"

def get_playlist_videos(api_key, playlist_id):
    url = "https://www.googleapis.com/youtube/v3/playlistItems"
    videos = []
    next_page_token = None

    while True:
        params = {
            'part': 'snippet',
            'playlistId': playlist_id,
            'maxResults': 50,
            'pageToken': next_page_token,
            'key': api_key
        }
        response = requests.get(url, params=params)
        data = response.json()

        # Extract video information
        for item in data['items']:
            video_title = item['snippet']['title']
            video_id = item['snippet']['resourceId']['videoId']
            videos.append({'title': video_title, 'id': video_id})

        # Check if there are more pages
        next_page_token = data.get('nextPageToken')
        if not next_page_token:
            break

    return videos

@app.get("/youtube/{_:path}")
def retrieve_playlist_json(request: Request, q: Union[str, None] = None):

    # using the playlist id, retrieve names of all the songs
    playlist_id = request.url.query.split('=')[1]
    playlist_videos = get_playlist_videos(YOUTUBE_API_KEY, playlist_id)
    
    # then, check using the spotify api if these songs actually exist

    # if the song doesn't exist, first check if for the link of each song
        # if it's a self contained playlist, then use a regex to try and
        # retrieve song names for those songs within the compilation

    return playlist_videos


def main():
    # test stuff

    # request playlist videos using api key
    playlist_id = 'PLE0B0LF_HjBV6_G-42PsEiVYGDhLAllfO'
    playlist_videos = get_playlist_videos(YOUTUBE_API_KEY, playlist_id)
    print(playlist_videos)


if __name__ == '__main__':
    main()