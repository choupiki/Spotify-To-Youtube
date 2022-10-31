import spotipy
from spotipy.oauth2 import SpotifyOAuth
from flask import Flask, url_for, session, request, redirect, jsonify, render_template, flash
from flask_session import Session
import pandas as pd
import os
from config import Config


def trackList(token_info, playlist_link, opt):
    sp = spotipy.Spotify(auth=token_info['access_token'])
    # playlist_link = input('Playlist Link: ')
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
    if opt==1:
        return df.to_csv('temp_files/playlist_data.csv')
    if opt==2:
        return df.to_csv('temp_files/ref_list.csv')
    else:
        return 'Invalid Entry for Option: opt'


def create_spotify_oauth():
        return SpotifyOAuth(
            client_id=Config.CLIENT_ID,
            client_secret=Config.SECRET_KEY,
            redirect_uri=url_for("redirectPage", _external=True),
            scope='user-library-read'
        )
