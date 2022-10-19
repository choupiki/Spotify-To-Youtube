from os import environ, path
from dotenv import load_dotenv

"""Flask Config"""

basdir = path.abspath(path.dirname('spotify_to_yt'))
load_dotenv(path.join(basdir, '.env'))
# print(path.join(basdir, '.env'))
class Config:
    """Base Config"""
    # Cookie 
    SESSION_TYPE = 'filesystem'
    SESSION_SECRET_KEY = environ.get('SESSION_SECRET_KEY')
    # Spotify
    CLIENT_ID = environ.get('CLIENT_ID')
    SESSION_COOKIE_NAME = environ.get('SESSION_COOKIE_NAME')
    SECRET_KEY = environ.get('SECRET_KEY')
    # Youtube
    YT_CLIENT_ID = environ.get('YT_CLIENT_ID')
    YT_SECRET_KEY = environ.get('YT_SECRET_KEY')
    OAUTHLIB_INSECURE_TRANSPORT = environ.get('OAUTHLIB_INSECURE_TRANSPORT')
