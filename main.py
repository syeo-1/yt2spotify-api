from typing import Union

from fastapi import FastAPI, Request
from api_keys import YOUTUBE_API_KEY, SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET
import requests
import base64
import concurrent.futures
import re
import string
from unidecode import unidecode
import unicodedata

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

def get_video_description(video_id, api_key):
    url = f"https://www.googleapis.com/youtube/v3/videos?part=snippet&id={video_id}&key={api_key}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if data['items']:
            description = data['items'][0]['snippet']['description']
            return description
        else:
            return "Video not found."
    else:
        return f"Error: {response.status_code}"
    
def get_spotify_token(client_id, client_secret):
    auth_url = 'https://accounts.spotify.com/api/token'
    auth_header = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    headers = {'Authorization': f'Basic {auth_header}'}
    data = {'grant_type': 'client_credentials'}
    response = requests.post(auth_url, headers=headers, data=data)
    return response.json().get('access_token')

def artist_collab_edit(youtube_artist_name):
    '''check if artist is of format <name x name>
    spotify will be of format <name, name>'''
    # pattern = re.compile('^(\w+)[\sx\s][name\sx\s]*(\w+)$')
    # if pattern.match(youtube_artist_name):
    return ', '.join(youtube_artist_name.split(' x '))
    # else:
    #     return youtube_artist_name

def youtube_track_match_found_on_spotify(title, track):
    split_title = title.split('-')
    data = {
        'spotify_title': track['name'],
        'spotify_artist': track['artists'][0]['name'],
        'spotify_url': track['external_urls']['spotify']
    }
    youtube_artist_name = unicodedata.normalize('NFC', split_title[0].strip().lower()).replace("’", "'")
    youtube_track_name = unicodedata.normalize('NFC', split_title[1].strip().lower()).replace("’", "'")

    spotify_artist_name = unicodedata.normalize('NFC', data['spotify_artist'].lower()).replace("’", "'")
    spotify_track_name = unicodedata.normalize('NFC', data['spotify_title'].lower()).replace("’", "'")


     

    # if 'don' in spotify_track_name:
    #     print(repr(spotify_artist_name))
    #     print(repr(spotify_track_name))
    #     print(repr(youtube_artist_name))
    #     print(repr(youtube_track_name))

    # youtube_artist_name = artist_collab_edit(youtube_artist_name)
    # print(f'artist name post edit: {youtube_artist_name}')
    # if spotify_artist_name == youtube_artist_name:
    #     print('asdf')
    # else:
    #     print('diff!!')
    # for i in range(len(spotify_artist_name)):
    #     if spotify_artist_name[i] != youtube_artist_name[i]:
    #         pass
            # print(i)
            # print(spotify_artist_name[i])
            # print(youtube_artist_name[i])
    # print(len(spotify_artist_name))
    # print(len(youtube_artist_name))
    # if spotify_track_name == youtube_track_name:
    #     print('awrbaweb') 

    if (((youtube_artist_name in spotify_artist_name or spotify_artist_name in youtube_artist_name) and 
        (youtube_track_name in spotify_track_name or spotify_track_name in youtube_track_name)) or
        (youtube_track_name == spotify_track_name and youtube_artist_name == spotify_artist_name)):
        print('awklebawjbb hehehehehe')
        return True
    if len(youtube_artist_name.split(', ')) > 1: # more than 1 artist
        artists = youtube_artist_name.split(', ')
        if (any(artist in spotify_artist_name for artist in artists) and
            (youtube_track_name in spotify_track_name or spotify_track_name in youtube_track_name)):
            print('awklebawjbb blahblah')
            return True
        
    # if 'rook1e' in youtube_artist_name:
    #     print('***')
    #     print(spotify_track_name)
    #     print(spotify_artist_name)
    #     print(title)
    #     print('***')

    return False

def get_youtube_video_description_tracklist(video_description):
    matches = re.findall(r'\[?\d{1,2}:\d{2}\]?\s.*', video_description)
    if all('[' in track for track in matches) and all (']' in track for track in matches):
        return [track[7:] for track in matches] 
    else:
        track_names = [track[6:] for track in matches]
        return track_names

def get_proper_track_from_spotify_search(search_json, track_title, access_token):
    '''check for closest match in track title to returned search query result. gives back
    the index with the closest match'''
    # if 'rook1e' in track_title:
    #     print('0000000000')
    #     print(search_json['tracks']['items'])
    #     print('0000000000')

    tracks = search_json['tracks']['items']
    print(f'len tracks is {len(tracks)}')

    for i, track in enumerate(tracks):
        print(track['name'])
        print(track['artists'][0]['name'])
        if youtube_track_match_found_on_spotify(track_title, track):
            return i
    return -1




# Step 2: Function to search for a track on Spotify
def search_spotify_track(access_token, video):
    video_description = get_video_description(video['id'], YOUTUBE_API_KEY)
    compilation_tracklist = get_youtube_video_description_tracklist(video_description)

    print(len(compilation_tracklist))

    if len(compilation_tracklist) > 0:
        print(f'compilation detected!!')
        result_tracklist = []
        for track_title in compilation_tracklist:
            search_url = 'https://api.spotify.com/v1/search'
            headers = {'Authorization': f'Bearer {access_token}'}

            # make sure track title has the artist
            if len(track_title.split('-')) != 2:
                # print(track_title)
                artist = video['title'].split('-')[0]
                track_title = artist + '- ' + track_title

            print()

                # print(track_title)
            # if 'kokoro' in track_title:
                # print(track_title)
            # params = {'q': track_title, 'type': 'track', 'limit': 1}
            title_split = track_title.split(' - ')
            if len(title_split) == 1:
                continue
            print('aawioeufhioawuefboiawuebfoiauweb')
            print(title_split)
            artist = unidecode(title_split[0].lower().translate(str.maketrans('', '', string.punctuation)))
            track_name = unidecode(title_split[1].lower().translate(str.maketrans('', '', string.punctuation)))
            search_query = f'track:{track_name} artist:{artist}'
            print(search_query)
            # params = {'q': track_title, 'type': 'track', 'limit': 20}
            params = {'q': search_query, 'type': 'track', 'limit': 20}
            # exit(0)
            response = requests.get(search_url, headers=headers, params=params)
            data = response.json()
            track_title_split = track_title.split(' - ')
            only_track_title = track_title_split[1].lower()
            # print(only_track_title)
            # print(len(data['tracks']['items']))
            # if len(data['tracks']['items']) == 0 or not any(only_track_title in track['name'] for track in data['tracks']['items']):
            if len(data['tracks']['items']) == 0:
                # try searching only for the track name to at least get a more general search
                print(f'nothing found!!! doing more general search for {track_title}')
                # search_url = 'https://api.spotify.com/v1/search'
                # headers = {'Authorization': f'Bearer {access_token}'}
                only_track_title = track_title.split(' - ')[1].lower()
                print(only_track_title)
                params = {'q': only_track_title, 'type': 'track', 'limit': 20, 'market': None}
                response = requests.get(search_url, headers=headers, params=params)
                data = response.json()
                tracks = data['tracks']['items']
                for track in tracks:
                    print(track['name'])
                    print(track['artists'][0]['name'])
                    print('==========')
                # exit(0)
                # print(f'new tracks: {tracks}')

            
            # print(len(tracks))
            # get the proper json piece from search query
            matching_track_index = get_proper_track_from_spotify_search(data, track_title, access_token)
            print(f'matchin index is {matching_track_index}')

            # if 'kokoro' in track_title:
            #     print("+++++++++++++++++++")
            #     for track in data['tracks']['items']:
            #         filter = track['name']
            #         # print('===')
            #         print(filter)
            #     print("+++++++++++++++++++")
            #     # exit(0)

            if matching_track_index > -1:
                items = data['tracks']['items']
                track = items[matching_track_index]

                result_tracklist.append(
                    {
                        'spotify_title': track['name'],
                        'spotify_artist': track['artists'][0]['name'],
                        'spotify_url': track['external_urls']['spotify'],
                        'spotify_uri': track['uri']
                    }
                )
            else:
                # print(f'no match found on spotify for {track_title} in compilation')
                pass
                # print(f'compilation tracklist: {compilation_tracklist}')
                # exit(0)
        # print(result_tracklist)
        return result_tracklist
    else:
        # single song

        search_url = 'https://api.spotify.com/v1/search'
        headers = {'Authorization': f'Bearer {access_token}'}
        title = video['title']

        # try advanced search
        title_split = title.split(' - ')
        artist = unidecode(title_split[0].lower().translate(str.maketrans('', '', string.punctuation)))
        track_name = unidecode(title_split[1].lower().translate(str.maketrans('', '', string.punctuation)))
        search_query = f'track:{track_name} artist:{artist}'
        print(search_query)

        params = {'q': search_query, 'type': 'track', 'limit': 10, 'market': 'SE'}
        response = requests.get(search_url, headers=headers, params=params)
        data = response.json()



        
        # Return the first result if it exists
        if data['tracks']['items']:
            items = data['tracks']['items']
            track = items[0]
            # print(items)
            # print(data['tracks'])
            # print(track)
            result = []
            for _ in items:
                result.append({
                    'spotify_title': track['name'],
                    'spotify_artist': track['artists'][0]['name'],
                    'spotify_url': track['external_urls']['spotify'],
                    'spotify_uri': track['uri']
                }
            )
            print(result)
            if youtube_track_match_found_on_spotify(title, track):
                # print('track match found on spotify!')
                return {
                    'spotify_title': track['name'],
                    'spotify_artist': track['artists'][0]['name'],
                    'spotify_url': track['external_urls']['spotify'],
                    'spotify_uri': track['uri']
                }
    
    return None

# Step 3: Function to search for multiple tracks concurrently
def find_multiple_tracks_concurrently(playlist_videos, client_id, client_secret):
    access_token = get_spotify_token(client_id, client_secret)

    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_title = {executor.submit(search_spotify_track, access_token, video): video for video in playlist_videos}
        
        results = []
        for future in concurrent.futures.as_completed(future_to_title):
            title = future_to_title[future]
            try:
                spotify_match = future.result()
                # print(type(spotify_match))
                if type(spotify_match) is dict and spotify_match:
                    results.append({
                        'youtube_title': title,
                        'spotify_title': spotify_match['spotify_title'],
                        'spotify_artist': spotify_match['spotify_artist'],
                        'spotify_url': spotify_match['spotify_url'],
                        'spotify_uri': spotify_match['spotify_uri']
                    })
                elif type(spotify_match) == list and len(spotify_match) > 0:
                    # print(f'before: {len(results)}')
                    results.extend(spotify_match)
                    # print(f'after: {len(results)}')
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



@app.get("/youtube/{_:path}")
def retrieve_playlist_json(request: Request, q: Union[str, None] = None):

    # using the playlist id, retrieve names of all the songs
    playlist_id = request.url.query.split('=')[1]
    playlist_videos = get_playlist_videos(YOUTUBE_API_KEY, playlist_id)

    # http://127.0.0.1:8000/youtube/https://www.youtube.com/playlist?list=PLE0B0LF_HjBV6_G-42PsEiVYGDhLAllfO
    
    # then, check using the spotify api if these songs actually exist
    # for video in playlist_videos:

    # matches = find_multiple_tracks_concurrently(
    #     [video['title'] for video in playlist_videos],
    #     SPOTIFY_CLIENT_ID,
    #     SPOTIFY_CLIENT_SECRET
    # )
    matches = find_multiple_tracks_concurrently(
        playlist_videos,
        SPOTIFY_CLIENT_ID,
        SPOTIFY_CLIENT_SECRET
    )
    # how to tell if a match is found on spotify?

    # TODO: i should be checking the description first to see if it's a compilation
    # and then trying to find the trackname on spotify!
    # splitting the youtube title by spaces, regardless of case,
    # two "words" in which at least one alphanumeric character must exist
    # must match either the spotify_artist field or the spotify_title field
        


    # if the song doesn't exist, first check if for the link of each song
        # if it's a self contained playlist, then use a regex to try and
        # retrieve song names for those songs within the compilation

    return matches


def main():
    # test stuff

    # request playlist videos using api key
    playlist_id = 'PLE0B0LF_HjBV6_G-42PsEiVYGDhLAllfO'
    playlist_videos = get_playlist_videos(YOUTUBE_API_KEY, playlist_id)
    # print(playlist_videos)


if __name__ == '__main__':
    main()