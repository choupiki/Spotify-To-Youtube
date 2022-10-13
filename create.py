import pandas as pd
from flask import Flask, url_for, session, request, redirect
from authlib.integrations.flask_client import OAuth
import app.app
from googleapiclient.discovery import build
import os


# oAuth Setup
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=Config.YT_CLIENT_ID,
    client_secret=Config.YT_SECRET_KEY,
    access_token_url='https://accounts.google.com/o/oauth2/token',
    access_token_params=None,
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    authorize_params=None,
    api_base_url='https://www.googleapis.com/oauth2/v1/',
    userinfo_endpoint='https://openidconnect.googleapis.com/v1/userinfo',  # This is only needed if using openId to fetch user info
    client_kwargs={'scope': 'openid email profile'},
)

# Flask routes
@app.route('/yt')
def ythome():
    return 'ythome'

@app.route('/ytlogin')
def ytLogin():
    google = oauth.create_client('google')
    redirect_uri = url_for('ytauth', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/ytauth')
def ytAuth():
    google = oauth.create_client('google')
    token = google.authorize_access_token()
    resp = google.get('userinfo')
    userinfo = resp.json()
    user = oauth.google.userinfo()
    session['profile'] = user_info
    return redirect(url_for('yt', _external=True))




# Disable OAuthlib's HTTPS verification when running locally.
# *DO NOT* leave this option enabled in production.
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

#pd.from_dict(playlist_dict)
youtube = build('youtube', 'v3', developerKey=Config.YT_CLIENT_ID)

request = youtube.playlist().list(
    part='statistics',
    mine=True
)

response = request.execute()

youtube.close()
