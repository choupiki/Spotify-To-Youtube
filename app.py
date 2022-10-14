from flask import Flask, url_for, session, request, redirect, jsonify, render_template, flash
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from config import Config
import time
from authlib.integrations.flask_client import OAuth
from googleapiclient.discovery import build
import pandas as pd
import os
import google_auth_oauthlib
import google.oauth2


app = Flask(__name__)

app.config.from_object(Config)
TOKEN_INFO = 'token_info'
YT_TOKEN_INFO = 'yt token info'

@app.route('/')
def login():
    sp_oauth = create_spotify_oauth()
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)


@app.route('/redirect')
def redirectPage():
    sp_oauth = create_spotify_oauth()
    session.clear()
    code = request.args.get('code')
    token_info = sp_oauth.get_access_token(code)
    session[TOKEN_INFO] = token_info
    return redirect(url_for("playlistSelect", _external=True))

@app.route('/playlistselect')
def playlistSelect():
    flash("Please enter the link for the Spotify playlist you wish to convert: ")
    return render_template("playlistselect.html")

@app.route('/getTracks', methods=["POST", "GET"])
def getTracks():
    try:
        token_info = get_token()
    except:
        print('Not logged in')
        return redirect(url_for('login', _external=False))
    
    sp = spotipy.Spotify(auth=token_info['access_token'])
    playlist_link = request.form['playlist_link']
    #]playlist_link = input('Playlist Link: ')
    # playlist_link = 'https://open.spotify.com/playlist/5A8qAM27k3KvDaIyJ97HER?si=080d4a4c1a6a4b81'
    playlist_uri = playlist_link.split("/")[-1].split("?")[0]
    track_uris = []
    track_names = []
    artist_names = []
    albums = []
    
    for track in sp.playlist_tracks(playlist_uri)["items"]:
        #URI
        track_uris.append(track["track"]["uri"]) 
        #Track name
        track_names.append(track["track"]["name"])    
        #Name, popularity, genre
        artist_names.append(track["track"]["artists"][0]["name"])    
        #Album
        albums.append(track["track"]["album"]["name"])
    
    playlist_dict = {
        "URIs": track_uris,
        "Track": track_names,
        "Artists": artist_names,
        "Albums": albums
    }
    
    
    df = pd.DataFrame.from_dict(playlist_dict)
    print(df)
    os.makedirs('temp_files', exist_ok=True)  
    df.to_csv('temp_files/playlist_data.csv')
    
    return redirect(url_for('ytLogin', _external=True))
    #return render_template("getTracks.html")

def get_token():
    token_info = session.get(TOKEN_INFO, None)
    if not token_info:
        raise "exception"
    now = int(time.time()) 
    is_expired = token_info['expires_at'] - now < 60 
    if (is_expired):
        sp_oauth = create_spotify_oauth()
        token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
    return token_info


def create_spotify_oauth():
        return SpotifyOAuth(
            client_id=Config.CLIENT_ID,
            client_secret=Config.SECRET_KEY,
            redirect_uri=url_for("redirectPage", _external=True),
            scope='user-library-read'
        )

# Youtube Execution
# When running locally, disable OAuthlib's HTTPs verification.
# ACTION ITEM for developers:
#     When running in production *do not* leave this option enabled.
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'
scopes = ["https://www.googleapis.com/auth/userinfo.profile",
          "https://www.googleapis.com/auth/userinfo.email",
          "https://www.googleapis.com/auth/youtube openid"]

# Flask routes
@app.route('/yt')
def yt():
    return 'yt'

@app.route('/ytlogin')
def ytLogin():
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        'service.json',
        scopes=scopes)
    flow.redirect_uri = url_for('ytAuth', _external=True)
    auth_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true')
    session['state'] = state
    return redirect(auth_url)


@app.route('/ytauth')
def ytAuth():
    state = session['state']
    
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        'service.json', 
         scopes=scopes, 
         state=state)
    flow.redirect_uri = url_for('ytAuth', _external=True)
    
    auth_response = request.url
    flow.fetch_token(authorization_response=auth_response)
    
    credentials = flow.credentials
    session['credentials'] = credentials_to_dict(credentials)
    
    return redirect(url_for('playlistName', _external=True))

@app.route('/nameplaylist')
def playlistName():
    flash("What would you like to call your Youtube playlist? ")
    return render_template("playlistname.html")

@app.route('/create_yt_playlist', methods=["POST", "GET"])
def mkPlaylist():
    # Check authorized
    if 'credentials' not in session:
        return redirect('ytAuth')
    # Fetch credentials 
    credentials = google.oauth2.credentials.Credentials(
        **session['credentials'])
    # Instantiate playlist data
    playlist_title = request.form['playlist_name']
    #playlist_title = input('Name new playlist: ')
    songs_df = pd.read_csv('temp_files/playlist_data.csv')
    song_title = songs_df['Track'][0]
    artist = songs_df['Artists'][0]
    print(song_title)
    print(artist)
    
    # Call functions
    mkList_resp = mkList(credentials, playlist_title)
    playlistId = mkList_resp['id']
    # Add videos to above created playlist
    for i in range(len(songs_df['Track'])):
        iter_response = popList(credentials, playlistId, songs_df['Track'][i], songs_df['Artists'][i])
        print(iter_response)
    print(str(i) + "Tracks added")
    
    #response = listVids(credentials)
    # Save Creds again
    
    session['credentials'] = credentials_to_dict(credentials)

    #return jsonify(**response)
    return 'complete!'



def listVids(credentials):
    youtube = build('youtube', 'v3', credentials=credentials)

    request = youtube.playlistItems().list(
        part='snippet',
        playlistId='PL11reovxTQ5tgpOAlMzvV2sgOqsVPbO9a'

    )

    response = request.execute()
    print(response)
    youtube.close()
    return response


def mkList(credentials, title):
    youtube = build('youtube', 'v3', credentials=credentials)

    request = youtube.playlists().insert(
        part='snippet',
        body={
            'snippet': {
                'title': title,
                'description': "Playlist converted from Spotify account by Sp2Yt"
                }
              }
    )
    response = request.execute()
    print(response["snippet"]["localized"])
    youtube.close()
    return response

def popList(credentials, playlistId, song_title, artist):
    # SetUp youtube var
    youtube = build('youtube', 'v3', credentials=credentials)
    
    # Create search request for youtube
    search_req = youtube.search().list(
        q = song_title + ' ' + artist,
        part="snippet",
        type = 'video'
        )
    search_resp = search_req.execute()
    # Add to playlist request
    top_vid = search_resp['items'][0]
    videoId = top_vid['id']['videoId']
    # Add top video result to playlist
    add_req = youtube.playlistItems().insert(
        part='snippet',
        body={'snippet': {
        'playlistId': playlistId,
        'resourceId': {"kind": "youtube#video",  
        'videoId': videoId}
        }  }  
    )
    add_resp = add_req.execute()
    print(add_resp)
    youtube.close()
    return 'popListResponse'




def credentials_to_dict(credentials):
  return {'token': credentials.token,
          'refresh_token': credentials.refresh_token,
          'token_uri': credentials.token_uri,
          'client_id': credentials.client_id,
          'client_secret': credentials.client_secret,
          'scopes': credentials.scopes}

