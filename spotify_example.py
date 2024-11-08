import requests
import base64
import concurrent.futures

from api_keys import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, YOUTUBE_API_KEY
import re

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

def youtube_track_match_found_on_spotify(title, track):
    split_title = title.split()
    data = {
        'spotify_title': track['name'],
        'spotify_artist': track['artists'][0]['name'],
        'spotify_url': track['external_urls']['spotify']
    }    
    print(split_title)
    print(data)

    for youtube_word in split_title:
        if not youtube_word.isalnum():
            continue
        elif (youtube_word.lower() in data['spotify_title'].lower() or 
            youtube_word.lower() in data['spotify_artist'].lower()):
            return True
    return False

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
        # print(data['tracks'])
        result = []
        for _ in items:
            result.append({
                'spotify_title': track['name'],
                'spotify_artist': track['artists'][0]['name'],
                'spotify_url': track['external_urls']['spotify'],
                'spotify_uri': track['uri']
            }
        )
        if youtube_track_match_found_on_spotify(title, track):
            print('track match found on spotify!')
            return {
                'spotify_title': track['name'],
                'spotify_artist': track['artists'][0]['name'],
                'spotify_url': track['external_urls']['spotify'],
                'spotify_uri': track['uri']
            }
        else:
            # check if it's a compilation by using the video description
            # and looking for a tracklist
            pass
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
                        'spotify_url': spotify_match['spotify_url'],
                        'spotify_uri': spotify_match['spotify_uri']
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


def main():
    # lofi_video_id = 'TwWmfyKInKo'
    # lofi_video_description = get_video_description(lofi_video_id, YOUTUBE_API_KEY)
    # # print(lofi_video_description.split('\n'))
    # matches = re.findall(r'\d{2}:\d{2}\s.*', lofi_video_description)
    # # print(matches)
    # matches_tracklist = [track[6:] for track in matches]
    # print(matches_tracklist)

    ######
    # playlist_videos = get_playlist_videos(YOUTUBE_API_KEY, 'PLE0B0LF_HjBV6_G-42PsEiVYGDhLAllfO')
    # print(playlist_videos)
    ######
    # exit(0)
    # Example usage
    client_id = SPOTIFY_CLIENT_ID
    client_secret = SPOTIFY_CLIENT_SECRET
    youtube_titles = [
        'lofty - in my head (ft. Ayeon)',
        'Letskey - Delicate',
        'Lofty - Caught Feelings',
        '🍩 Donut Shop [Lofi / JazzHop / Sleepy Vibes]',
        'A.L.I.S.O.N - Subtract',
        "Jordy Chandra - Coffee Evening"
    ]  #Replace with actual titles
    matches = find_multiple_tracks_concurrently(youtube_titles, client_id, client_secret)

    # Print results
    for match in matches:
        if 'spotify_url' in match:
            print(f"Found on Spotify: {match['youtube_title']} -> {match['spotify_title']} by {match['spotify_artist']} ({match['spotify_uri']})")
        else:
            print(f"No match found on Spotify for: {match['youtube_title']}")


if __name__ == '__main__':
    main()
