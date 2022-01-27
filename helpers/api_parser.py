from urllib.parse import quote

_api_prefix = "https://musicbrainz.org/ws/2"


def build_recordings_query_url(artist_id: str, offset: int = 0) -> str:
    """
    Given the ID of an artist, build a url to pass to the API in order to retrieve data
    on recordings/tracks released by that artist.
    :param artist_id: The id the artist is assigned in the MusicBrains database.
    :param offset: The API limits our data to return at most 100 items per request, so for large numbers of recordings
        we can get around this by adding an offset to retrieve items later in the list - starting at the offset index.
    :return: A url string that can be passed to the MusicBrainz API to the get the required track list data.
    """
    return f"{_api_prefix}/recording/?query=arid:{artist_id}%20AND%20status:official%20AND%20video:false%20NOT%20secondarytype:*&limit=100&offset={offset}"


def build_lyrics_url(artist_name: str, song_title: str) -> str:
    """
    Given an artist name and a song title, build a url to pass to the lyrics API
    to retrieve data on the lyrics for the given song.
    :param artist_name:
    :param song_title:
    :return:
    """
    cleaned_artist_name = sanitise_url_string(artist_name)
    cleaned_title = sanitise_url_string(song_title)
    return f"https://api.lyrics.ovh/v1/{cleaned_artist_name}/{cleaned_title}"


def sanitise_url_string(input_url: str) -> str:
    """
    Remove any dangerous or unsupported characters from an artist or song name
    as it could change the behaviour of our requests.
    :param input_url: The raw url string to be cleaned.
    :return: A version of the input string with any special characters escaped and
        any backslashes removed.
    """
    # Escape any special characters
    output_url = quote(input_url)
    # Remove any slashes
    output_url = output_url.replace("/", " ")

    return output_url
