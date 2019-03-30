from os import getenv as getenv

import spotipy
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyClientCredentials

from app.music.music import LinkType, LinkInfo, EntityType
from app.music.streaming_service import StreamingServiceParser

# Spotify client init
load_dotenv()
client_credentials_manager = SpotifyClientCredentials(client_id=getenv(
    'SPOTIFY_CLIENT_ID'), client_secret=getenv('SPOTIFY_CLIENT_SECRET'))
spotipy_client = spotipy.Spotify(
    client_credentials_manager=client_credentials_manager)


class SpotifyParser(StreamingServiceParser):
    """Parser class that helps to identify which type of Spotify link is"""

    def get_link_type(self, url):
        """Resolves the Spotify link type"""
        if 'artist' in url:
            return LinkType.ARTIST
        elif 'album' in url:
            return LinkType.ALBUM
        elif 'track' in url:
            return LinkType.TRACK
        return None

    def search_link(self, query, entity_type):
        """
        Searches for a list of coincidences in Spotify
        :param query: query string term
        :param entity_type: EntityType
        :return: list of results
        """
        search_result = spotipy_client.search(query, type=entity_type)

        if entity_type == EntityType.ARTIST.value:
            search_result = search_result['artists']['items']
        elif entity_type == EntityType.ALBUM.value:
            search_result = search_result['albums']['items']
        elif entity_type == EntityType.TRACK.value:
            search_result = search_result['tracks']['items']

        return search_result

    def get_link_info(self, url, link_type):
        """
        Resolves the name and the genre of the artist/album/track from a link
        Artist: 'spotify:artist:id'
        Album: 'spotify:album:id'
        Track: 'spotify:track:id'
        """
        # Gets the entity id from the Spotify link:
        # https://open.spotify.com/album/*1yXlpa0dqoQCfucRNUpb8N*?si=GKPFOXTgRq2SLEE-ruNfZQ
        entity_id = self.get_entity_id_from_url(url)
        link_info = LinkInfo(link_type=link_type)
        if link_type == LinkType.ARTIST:
            uri = f'spotify:artist:{entity_id}'
            artist = spotipy_client.artist(uri)
            link_info.artist = artist['name']
            link_info.genre = artist['genres'][0] if len(
                artist['genres']) > 0 else None

        elif link_type == LinkType.ALBUM:
            uri = f'spotify:album:{entity_id}'
            album = spotipy_client.album(uri)
            link_info.album = album['name']
            link_info.artist = album['artists'][0]['name']
            if len(album['genres']) > 0:
                link_info.genre = album['genres'][0]
            else:
                album_artist = spotipy_client.artist(album['artists'][0]['id'])
                link_info.genre = album_artist['genres'][0] if len(
                    album_artist['genres']) > 0 else None

        elif link_type == LinkType.TRACK:
            uri = f'spotify:track:{entity_id}'
            track = spotipy_client.track(uri)
            link_info.track = track['name']
            link_info.album = track['album']['name']
            link_info.artist = track['artists'][0]['name']
            track_artist = spotipy_client.artist(track['artists'][0]['id'])
            link_info.genre = track_artist['genres'][0] if len(
                track_artist['genres']) > 0 else None

        return link_info

    def get_entity_id_from_url(self, url):
        return url[url.rfind('/') + 1:]

    def clean_url(self, url):
        """Receives a Spotify url and returns it cleaned"""
        if url.rfind('?') > -1:
            return url[:url.rfind('?')]
        return url

    def is_valid_url(self, url):
        """Check if a message contains a Spotify Link"""
        return 'open.spotify.com' in url
