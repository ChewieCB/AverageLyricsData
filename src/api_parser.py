_api_prefix = "https://musicbrainz.org/ws/2"


def build_artist_search_query_url(artist_name: str) -> str:
    """
    Given the name of an artist, build a url to query the API in order to retrieve the artist ID.
    :param artist_name: The name of the artist we're searching for.
    :return: A url string that can be passed to the MusicBrainz API to get the required artist data.
    """
    return f"{_api_prefix}/artist/?query=artist:{artist_name}"


def build_release_lookup_url(artist_id: str) -> str:
    """
    Given the ID of an artist, build a url to pass to the API in order to
    retrieve data on releases by that artist.
    :param artist_id: The id the artist is assigned in the MusicBrains database.
    :return: A url string that can be passed to the MusicBrainz API to get the required release data.
    """
    # The lookup is retrieving release entities matching the artist id - filtering out any non-official
    # or repetitive releases such as bootlegs, remixes, etc. with the `status:official` and `NOT secondarytype:*`
    # query args.
    return f"{_api_prefix}/release-group?query=arid:{artist_id}%20AND%20status:official%20NOT%20secondarytype:*"


def build_track_lookup_url(artist_id: str) -> str:
    """
    Given the ID of a recording, build a url to pass to the API in order to retrieve data
    on the track listing for a given release.
    :param artist_id: The id the artist is assigned in the MusicBrains database.
    :return: A url string that can be passed to the MusicBrainz API to the get the required track list data.
    """
    return f"{_api_prefix}/recording/?query=rgid:{artist_id}%20AND%20status:official%20AND%20video:false%20NOT%20secondary-type:*"

