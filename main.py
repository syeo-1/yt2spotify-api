from typing import Union

from fastapi import FastAPI, Request
from api_keys import YOUTUBE_API_KEY, SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET
import requests
import base64
import concurrent.futures

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

# Step 1: Function to get Spotify access token
def get_spotify_token(client_id, client_secret):
    auth_url = 'https://accounts.spotify.com/api/token'
    auth_header = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    headers = {'Authorization': f'Basic {auth_header}'}
    data = {'grant_type': 'client_credentials'}
    response = requests.post(auth_url, headers=headers, data=data)
    return response.json().get('access_token')

# Step 2: Function to search for a track on Spotify
def search_spotify_track(access_token, title):
    search_url = 'https://api.spotify.com/v1/search'
    headers = {'Authorization': f'Bearer {access_token}'}
    params = {'q': title, 'type': 'track', 'limit': 1}
    response = requests.get(search_url, headers=headers, params=params)
    data = response.json()
    
    # Return the first result if it exists
    if data['tracks']['items']:
        items = data['tracks']['items']
        track = items[0]
        # print(items)
        result = []
        for _ in items:
            result.append({
                'spotify_title': track['name'],
                'spotify_artist': track['artists'][0]['name'],
                'spotify_url': track['external_urls']['spotify']
            }
        )
        print(result)
        return {
            'spotify_title': track['name'],
            'spotify_artist': track['artists'][0]['name'],
            'spotify_url': track['external_urls']['spotify']
        }
    return None

# Step 3: Function to search for multiple tracks concurrently
def find_multiple_tracks_concurrently(youtube_titles, client_id, client_secret):
    access_token = get_spotify_token(client_id, client_secret)
    
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_title = {executor.submit(search_spotify_track, access_token, title): title for title in youtube_titles}
        
        results = []
        for future in concurrent.futures.as_completed(future_to_title):
            title = future_to_title[future]
            try:
                spotify_match = future.result()
                if spotify_match:
                    results.append({
                        'youtube_title': title,
                        'spotify_title': spotify_match['spotify_title'],
                        'spotify_artist': spotify_match['spotify_artist'],
                        'spotify_url': spotify_match['spotify_url']
                    })
                else:
                    results.append({
                        'youtube_title': title,
                        'spotify_match': 'No match found'
                    })
            except Exception as e:
                results.append({
                    'youtube_title': title,
                    'error': str(e)
                })
                
    return results

def youtube_to_spotify_track(title, id):
    # check if the song exists via spotify's api
    # if it does exist, try to retrieve the track name for creating the playlist

    # if it does not exist, check the description for a tracklist (use regex)

    # if a tracklist doesn't exist skip for now
    # TODO: if the track doesn't exist on spotify, use youtube-dl to download so can have offline still
    # and use the spotify platform
    pass

@app.get("/youtube/{_:path}")
def retrieve_playlist_json(request: Request, q: Union[str, None] = None):

    # using the playlist id, retrieve names of all the songs
    playlist_id = request.url.query.split('=')[1]
    playlist_videos = get_playlist_videos(YOUTUBE_API_KEY, playlist_id)
    
    # then, check using the spotify api if these songs actually exist
    # for video in playlist_videos:
    matches = find_multiple_tracks_concurrently(
        [video['title'] for video in playlist_videos],
        SPOTIFY_CLIENT_ID,
        SPOTIFY_CLIENT_SECRET
    )

    # how to tell if a match is found on spotify?
    # splitting the youtube title by spaces, regardless of case,
    # two "words" in which at least one alphanumeric character must exist
    # must match either the spotify_artist field or the spotify_title field
        


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