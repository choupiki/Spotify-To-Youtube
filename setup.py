from setuptools import setup, find_packages

requires = ['spotipy',
            'pandas',
            'numpy',
            'dotenv',
            'flask',
            'html5lib',
            'requests',
            'requests_html',
            'pathlib',
            'beautifulsoup4',
            'google_auth_oauthlib',
            'google.oauth2',
            'googleapiclient',
            'authlib',
            'flask-session'
]


setup(
      name='Spotify_to_yt',
      version='1.0',
      description='App to convert spotify playlist to yt ones',
      author='Oscar Hallman',
      author_email='o.hallman@outlook.com',
      packages=find_packages(),
      include_package_data=True,
      install_requires=requires
)