from flask import Flask, url_for, session, request, redirect, jsonify, render_template, flash
from flask_session import Session
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
import random 
import re
import spotifyAuxFunctions as spauxfn
import youtubeAuxFunctions as ytauxfn

app = Flask(__name__)
app.config.from_object(Config)
Session(app)
TOKEN_INFO = 'token_info'
YT_TOKEN_INFO = 'yt token info'

@app.route('/')
def login():
    sp_oauth = spauxfn.create_spotify_oauth()
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)


@app.route('/redirect')
def redirectPage():
    sp_oauth = spauxfn.create_spotify_oauth()
    session.clear()
    code = request.args.get('code')
    token_info = sp_oauth.get_access_token(code)
    session[TOKEN_INFO] = token_info
    return redirect(url_for("playlistSelect", _external=True))

@app.route('/playlistselect')
def playlistSelect():
    flash("Please enter the link for the Spotify playlist you wish to convert: ")
    return render_template("playlistselect.html")

@app.route('/retryplaylistselect')
def retryplaylistSelect():
    flash("Invalid URL. Please try enter valid Spotify URL")
    return render_template("retryplaylistselect.html")

@app.route('/getTracks', methods=["POST", "GET"])
def getTracks():
    try:
        token_info = get_token()
    except:
        print('Not logged in')
        return redirect(url_for('login', _external=False))
    
    ref_list= 'https://open.spotify.com/playlist/5ZqLP6lOzeimIVbl3ol35m?si=3bf9e243579a40fa'
    spauxfn.trackList(token_info=token_info, playlist_link=ref_list, opt=2)
    validate_url = re.search("^https:\/\/[a-z]+\.spotify\.com", request.form['playlist_link'])
    if not validate_url == None:
        spauxfn.trackList(token_info=token_info, playlist_link=validate_url.string, opt=1)
        return redirect(url_for('ytLogin', _external=True))
    else:
        return redirect(url_for('retryplaylistSelect', _external=True))     
    
def get_token():
    token_info = session.get(TOKEN_INFO, None)
    if not token_info:
        raise "exception"
    now = int(time.time()) 
    is_expired = token_info['expires_at'] - now < 60 
    if (is_expired):
        sp_oauth = spauxfn.create_spotify_oauth()
        token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
    return token_info

# Youtube Execution
# When running locally, disable OAuthlib's HTTPs verification.
# ACTION ITEM for developers:
#     When running in production *do not* leave this option enabled.
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'
scopes = ["https://www.googleapis.com/auth/userinfo.profile",
          "https://www.googleapis.com/auth/userinfo.email",
          "https://www.googleapis.com/auth/youtube openid"]


# Google Flask routes
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
    session['playlistId'] = playlistId
    # Add videos to above created playlist
    for i in range(len(songs_df['Track'])):
        iter_response = popList(credentials, playlistId, songs_df['Track'][i], songs_df['Artists'][i])
        print(iter_response)
    print(str(i) + "Tracks added")
    
    """response = listVids(credentials)"""
    # Save Creds again
    
    session['credentials'] = credentials_to_dict(credentials)

    #return jsonify(**response)
    return redirect(url_for('completePage', _external=True))


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
                'privacyStatus': 'public',
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
    #print(add_resp)
    youtube.close()
    return add_resp["snippet"]["title"]

def credentials_to_dict(credentials):
  return {'token': credentials.token,
          'refresh_token': credentials.refresh_token,
          'token_uri': credentials.token_uri,
          'client_id': credentials.client_id,
          'client_secret': credentials.client_secret,
          'scopes': credentials.scopes}
  
def findRandomVideo(song_df):
    credentials = google.oauth2.credentials.Credentials(
    **session['credentials'])
    youtube = build('youtube', 'v3', credentials=credentials)
    rand = random.randint(0, len(song_df['Track'])-1)
    song_title = song_df['Track'][rand]
    artist = song_df['Artists'][rand]
    # Create search request for YT
    search_req = youtube.search().list(
    q = song_title + ' ' + artist,
    part="snippet",
    type = 'video'
    )
    search_resp = search_req.execute()
    # Add to playlist request
    top_vid = search_resp['items'][0]
    videoId = top_vid['id']['videoId']
    return videoId

@app.route("/endpage", methods=["POST", "GET"])
def completePage():
    static_songs_df = pd.read_csv('temp_files/ref_list.csv')
    static_video_id = findRandomVideo(song_df=static_songs_df)
    playlistId = session.get('playlistId', 'Unable')
    flash("Press button if you wish to convert another", "form")
    flash('https://youtube.com/embed/' + str(static_video_id), "static_link")
    flash('https://youtube.com/embed/playlist?list=' + str(playlistId), "link")
    os.remove("temp_files/playlist_data"+".csv")
    return render_template("endpage.html")

if __name__ == "__main__":
    app.run()
