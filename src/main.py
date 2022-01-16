from time import perf_counter
import aiohttp
import asyncio
import api_parser
from data import Artist, Release, Track


async def main():
    # Await a user input for the artist name
    artist_name_query = input("Artist name: ")

    # We use this accept header so the MusicBrainz API will return JSON data instead of XML
    headers = {"Accept": "application/json"}
    async with aiohttp.ClientSession(headers=headers) as session:
        # Get the artist data from the API
        artist_id_url = api_parser.build_artist_search_query_url(artist_name_query)
        artist = await get_artist_data(session, artist_id_url)

        # Get the recording data from the API using the artist ID
        recordings = await get_recordings_data(session, artist)
        print("=" * 32)
        print(f"{artist.name}")
        print("=" * 32)
        print(f"{len(recordings)} tracks.\n")
        # for track in recordings:
        #     print(track)

        # Clean the data by removing any duplicate songs/singles/remixes/re-releases/etc.
        _cleaned_recordings = remove_duplicate_recordings(recordings)


async def get_artist_data(session: aiohttp.ClientSession, url: str) -> Artist:
    """

    :param session:
    :param url:
    :return:
    """
    # Make a query request to the API
    async with session.get(url) as response:
        artist_data = await response.json()

        # If we get no data from the API, show the user an error message and exit.
        if not artist_data or len(artist_data["artists"]) < 0:
            print("No artist found!")
            return

    # Assign the data from the API into an Artist class for later reference
    artist_name = artist_data["artists"][0]["name"]
    artist_id = artist_data["artists"][0]["id"]
    artist_object = Artist(name=artist_name, mb_id=artist_id)

    return artist_object


# async def get_release_data(session: aiohttp.ClientSession, url: str, artist: Artist) -> [Release]:
#     """
#
#     :param session:
#     :param url:
#     :param artist:
#     :return:
#     """
#     async with session.get(url) as response:
#         print(response.status)
#         release_data = await response.json()
#
#         # If we get no data from the API, show the user an error message and exit.
#         if not release_data or len(release_data["release-groups"]) < 0:
#             print("No releases found!")
#             return
#
#     # Assign the data from the API into Release objects for later reference
#     releases = []
#     for _release in release_data["release-groups"]:
#         release_id = _release.get("id")
#         release_title = _release.get("title")
#         release_type = _release.get("primary-type")
#         release_year = _release.get("first-release-date")
#
#         release_object = Release(
#             name=release_title,
#             mb_id=release_id,
#             year=release_year,
#             type=release_type,
#             artist=artist,
#         )
#         releases.append(release_object)
#         print(release_object)
#
#     return releases


async def get_recordings_data(session: aiohttp.ClientSession, artist: Artist) -> [Track]:
    """

    :param session:
    :param url:
    :param artist:
    :return:
    """
    recordings = []
    # Since the MusicBrainz API limits search and browse requests to 100 entries per page, we need to make sequential
    # requests when an artist has more than 100 recordings listed in the database.
    #
    # To do this we offset the request data each iteration based on the number of tracks we know are in the list
    # (from count provided in the data) vs the number of tracks retrieved after each request.
    track_count = 0
    tracks_retrieved = 0

    # While the tracks retrieved is less than the number of tracks in the list, add an offset and make another request
    while track_count == 0 or tracks_retrieved < track_count:
        # Build the url
        recordings_url = api_parser.build_recordings_lookup_url(artist.mb_id, tracks_retrieved)

        # Make a query request to the API
        async with session.get(recordings_url) as response:
            recording_data = await response.json()

        # If we get no data from the API, show the user an error message and exit.
        if not recording_data or len(recording_data["recordings"]) < 0:
            print("No recordings  found!")
            return

        track_count = recording_data.get("count")
        tracks_retrieved += len(recording_data.get("recordings"))

        for track in recording_data["recordings"]:
            _id = track.get("id")
            _title = track.get("title")
            _release_title = track.get("releases")[0].get("title")
            _release_type = track.get("releases")[0].get("release-group").get("primary-type")
            current_track = Track(
                name=_title,
                mb_id=_id,
                release=_release_title,
                release_type=_release_type,
            )
            recordings.append(current_track)

    return recordings

def remove_duplicate_tracks(unpacked_track_data: [str]):
    """
    Go through each track from the data, unpacked into a list, and remove any duplicate tracks.
    :param unpacked_track_data: A list of track titles unpacked from each album, EP, and single.
    :return: Cleaned list of Track objects for each non-duplicate track.
    """
    return []


if __name__ == "__main__":
    timer_start = perf_counter()
    asyncio.run(main())
    timer_stop = perf_counter()
    print(f"Elapsed time: {timer_stop - timer_start}s")
