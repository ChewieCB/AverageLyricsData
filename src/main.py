from time import perf_counter
import aiohttp
import asyncio
import api_parser
from data import Artist, Release, Track


async def main():
    # Await a user input for the artist name
    artist_name_query = input("Artist name: ")
    print("\n")

    # We use this accept header so the MusicBrainz API will return JSON data instead of XML
    headers = {"Accept": "application/json"}
    async with aiohttp.ClientSession(headers=headers) as session:
        # Get the artist data from the API
        artist_id_url = api_parser.build_artist_search_query_url(artist_name_query)
        artist = await get_artist_data(session, artist_id_url)

        # Get the release data from the API
        artist_release_url = api_parser.build_release_lookup_url(artist.mb_id)
        releases = await get_release_data(session, artist_release_url, artist)

        # Unpack each release into a list of individual tracks
        full_track_list = []
        for release in releases:
            track_list = await get_tracks_from_release(session, release)
            full_track_list.extend(track_list)

        print()
        print(len(full_track_list))
        print()

        # Clean the release data by removing any duplicates
        cleaned_track_list = remove_duplicate_tracks(full_track_list)
        print(cleaned_track_list)


async def get_artist_data(session: aiohttp.ClientSession, url: str) -> Artist:
    """

    :param session:
    :param url:
    :return:
    """
    # Make a query request to the API
    async with session.get(url) as response:
        print(response.status)
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


async def get_release_data(session: aiohttp.ClientSession, url: str, artist: Artist) -> [Release]:
    """

    :param session:
    :param url:
    :param artist:
    :return:
    """
    async with session.get(url) as response:
        print(response.status)
        release_data = await response.json()

        # If we get no data from the API, show the user an error message and exit.
        if not release_data or len(release_data["release-groups"]) < 0:
            print("No releases found!")
            return

    # Assign the data from the API into Release objects for later reference
    releases = []
    for _release in release_data["release-groups"]:
        release_id = _release.get("id")
        release_title = _release.get("title")
        release_type = _release.get("primary-type")
        release_year = _release.get("first-release-date")

        release_object = Release(
            name=release_title,
            mb_id=release_id,
            year=release_year,
            type=release_type,
            artist=artist,
        )
        releases.append(release_object)
        print(release_object)

    return releases


async def get_tracks_from_release(session: aiohttp.ClientSession, release: [Release]) -> [Track]:
    """
    Go through each Release object in the array and collect each individual track into a list.
    :param session: aiohttp.ClientSession: The current aiohttp Session object.
    :param release: A list of Release objects containing data on each release by an artist.
    :return: List of all Track objects within the release data.
    """
    # Build the url for the release
    track_list_url = api_parser.build_track_lookup_url(release.mb_id)

    print(f"\n{release}\n========")

    # Get the track data from the API
    async with session.get(track_list_url) as response:
        # FIXME - this is making way too many requests and is kicking us off the API
        print(response.status)
        if response.status == 503:
            print("Too many requests! We're being rate limited! HTTP Status 503")
        track_data = await response.json()

        # If we get no data from the API, show the user an error message and exit.
        if not track_data.get("recordings"):
            print("No tracks found!")
            exit(0)

    # Iterate over the tracks in the data and create a Track object for each,
    # appending each new object to the return list.
    track_list = []
    for track in track_data.get("recordings"):
        current_track = Track(name=track["title"], mb_id=track["id"], release=release)
        track_list.append(current_track)
        print(current_track)

    print("========")
    return track_list


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
