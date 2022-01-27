import asyncio
import aiohttp
import aiohttp.web
import backoff
import musicbrainzngs

import config
from .data_cleanup_helpers import remove_lyrics_credit, remove_duplicate_recordings
from . import api_parser
from .data import Artist, Track, known_releases
import helpers.output_helpers as oh


def get_artist_data(artist_name: str) -> (Artist, str):
    """

    :param artist_name:
    :return:
    """
    from time import perf_counter
    timer_start = perf_counter()

    # Build a url from the artist name
    print(oh.header("Finding artist..."))

    artist_data = musicbrainzngs.search_artists(
        limit=3,
        artist=artist_name,
    ).get('artist-list')

    # If we get no data from the API, return an error message.
    if not artist_data:
        return None, oh.fail("No artist found!")

    # If we get a lot of results from a unique or common artist name (or a fragment of another artist name)
    # then err on the side of caution and ask the user which artist they were looking for.
    # TODO - add a check to determine when this is actually necessary, using the python API for MusicBrainz
    #   has improved search quality drastically.
    artist = select_artist_from_multiple_choices(artist_data)

    # Assign the data from the API into an Artist class for later reference
    artist_name = artist.get("name")
    artist_id = artist.get("id")
    artist_description = artist.get("disambiguation")
    artist_tags = []
    if artist.get("tags"):
        artist_tags = [tag.get("name") for tag in artist.get("tags")]

    artist_object = Artist(
        raw_data=artist_data,
        name=artist_name,
        mb_id=artist_id,
        description=artist_description,
    )
    # Assign the tags outside the constructor since we're setting it as a property so it
    # automatically unpacks each tag into one string for the ease of display.
    artist_object.tags = artist_tags

    timer_stop = perf_counter()

    # Display artist output
    print(oh.separator())
    print(oh.green(artist_object.name))
    if artist_object.description:
        print(oh.bold(artist_object.description))
    if artist_object.tags:
        print(oh.bold(artist_object.tags))
    print(oh.separator())

    if config.PERFORMANCE_TIMING:
        print(oh.blue(f"Artist API request made in {timer_stop - timer_start} seconds"))

    return artist_object, None


def select_artist_from_multiple_choices(artist_data):
    """"""
    if len(artist_data) > 3:
        print(oh.separator(64))
        print(oh.bold("Multiple artists found, please select the correct one:"))
        print(oh.separator(64))

        for count, _artist in enumerate(artist_data[0:b3]):
            # Get the data to display for each choice
            name = _artist.get("name")
            desc = _artist.get("disambiguation")
            tags = []
            if _artist.get("tags"):
                tags = [tag.get("name") for tag in _artist.get("tags")]

            print(f"{count + 1}. {name}")
            if desc:
                print(f"\t{desc}")
            if tags:
                print(f"\t{tags}")
            print(oh.separator(64, True))
        print(oh.separator(64))

        # Prompt the user to pick the most appropriate result
        artist_choice = None
        while True:
            try:
                artist_choice = int(input(""))
                if 0 < artist_choice < 3 + 1:
                    chosen_artist = artist_data[artist_choice - 1]
                    break
                else:
                    raise ValueError
            except ValueError:
                if artist_choice:
                    print(f"`{artist_choice + 1}` is not a valid choice, try again.")
                else:
                    print("Not a valid choice, try again.")
                artist_choice = None
    else:
        chosen_artist = artist_data[0]

    return chosen_artist


request_counter = 0


async def get_recordings_data(session: aiohttp.ClientSession, artist: Artist) -> ([Track], str):
    """

    :param session:
    :param artist:
    :return:
    """
    from time import perf_counter
    timer_start = perf_counter()

    recordings = []
    # Since the MusicBrainz API limits search and browse requests to 100 entries per page, we need to make sequential
    # requests when an artist has more than 100 recordings listed in the database.
    #
    # To do this we offset the request data each iteration based on the number of tracks we know are in the list
    # (from count provided in the data) vs the number of tracks retrieved after each request.
    #
    # FIXME - This is a bit hacky, but we use global vars here to more easily pass these vars between this
    #  function and each individual async function.
    global request_counter
    request_counter = 0
    global track_count
    track_count = 0

    print(oh.header("Finding songs..."))

    # Make an initial request to find the number of tracks
    recordings_url = api_parser.build_recordings_query_url(artist.mb_id, 0)
    recording_data = await make_recordings_request(session, recordings_url)
    if not recording_data:
        return None, oh.fail("No songs found!")

    track_count = recording_data.get("count")

    # If we need to make more than 1 request, batch all requests using asyncio
    if track_count >= 100:
        import math
        requests_to_make = math.ceil(track_count / 100) - 1

        tasks = []
        for i in range(requests_to_make):
            # Make a query request to the lyrics API
            tracks_retrieved = (i + 1) * 100
            url = api_parser.build_recordings_query_url(artist.mb_id, tracks_retrieved)
            tasks.append(asyncio.ensure_future(make_recordings_request(session, url)))

        async_recording_data = await asyncio.gather(*tasks)
        async_recording_data = [i for i in async_recording_data if i]

        # Combine the initial and async data by adding the initial data to the start of the list
        recording_data = [recording_data, *async_recording_data]
        # Combine each request's dict of tracks into one big dict of tracks
        combined_data = []
        for dataset in recording_data:
            for item in dataset.get("recordings"):
                combined_data.append(item)
    else:
        combined_data = recording_data.get("recordings")

    print(f"{len(combined_data)}/{track_count} tracks retrieved")

    # Create a Track object for each item
    for track in combined_data:
        current_track = Track(
            raw_data=track,
        )
        recordings.append(current_track)

    timer_stop = perf_counter()

    print(oh.cyan(f"Found {len(recordings)} tracks"))

    if config.PERFORMANCE_TIMING:
        print(oh.blue(f"{len(recordings)} songs retrieved from API in {request_counter} requests in {timer_stop - timer_start} seconds"))

    return recordings, None


# Use backoff to handle HTTP errors and retry since the optimisation
# speed of the async requests can cause us to hit rate limits
@backoff.on_exception(backoff.expo, aiohttp.web.HTTPException, max_tries=10)
async def make_recordings_request(session: aiohttp.ClientSession, url: str) -> dict:
    """"""
    retry_statuses = [x for x in range(100, 600)]
    retry_statuses.remove(200)
    retry_statuses.remove(429)

    async with session.get(url) as response:
        if response.status in retry_statuses:
            print(oh.warning(f"Response returned status {response.status}, retrying."))
            raise aiohttp.web.HTTPException
        # if "application/json" in response.headers['content-type']:
        recording_data = await response.json()

        global request_counter
        request_counter += 1

        return recording_data


# Use backoff to handle HTTP errors and retry since the async requests can cause us to hit rate limits
@backoff.on_exception(backoff.expo, aiohttp.web.HTTPException, max_tries=10)
async def make_lyrics_request(session: aiohttp.ClientSession, url: str, track: Track) -> Track:
    """"""
    retry_statuses = [x for x in range(100, 600)]
    retry_statuses.remove(200)
    retry_statuses.remove(429)
    retry_statuses.remove(404)

    async with session.get(url) as response:
        if response.status in retry_statuses:
            print(oh.warning(f"{track.name} returned status {response.status}, retrying."))
            raise aiohttp.web.HTTPException

        # Disable the content_type check here since the lyrics API sends text/html for `no lyrics found` responses
        # and application/json for valid responses.
        if "application/json" in response.headers['content-type']:
            lyrics_data = await response.json()
        else:
            # FIXME - this sometimes fails with a 502 error, likely the lyrics API getting overloaded.
            if config.IS_VERBOSE:
                print(oh.fail(f"Can't retrieve lyrics for {track.name}: Response status {response.status}" + response.headers['content-type']))
            return None

        lyrics = lyrics_data.get("lyrics")
        error = lyrics_data.get("error")

        # If we get no lyrics data from the API, show the user an error message and continue
        if error:
            if config.IS_VERBOSE:
                print(oh.fail(f"No lyrics found for {track.name}"))
            return None

        # Remove a common lyrics header this API's sources sometimes have within the lyrics data
        cleaned_lyrics = remove_lyrics_credit(lyrics)

        # Some songs will be instrumental even after filtering (not all instrumental songs have it in the title)
        if cleaned_lyrics.lower().find("instrumental") != -1:
            if config.IS_VERBOSE:
                print(oh.warning(f"{track.name} is an instrumental!"))
            return None

        track.lyrics = cleaned_lyrics

        return track


async def get_song_lyrics(session: aiohttp.ClientSession, cleaned_recordings: [Track], artist: Artist) -> ([Track], str):
    """

    :param session:
    :param cleaned_recordings:
    :param artist:
    :return:
    """
    from time import perf_counter
    timer_start = perf_counter()
    # List to hold async tasks
    tasks = []

    print(oh.header("Finding lyrics..."))

    for track in cleaned_recordings:
        # Make a query request to the lyrics API
        url = api_parser.build_lyrics_url(artist.name, track.name)
        tasks.append(asyncio.ensure_future(make_lyrics_request(session, url, track)))

    recordings_with_lyrics = await asyncio.gather(*tasks)

    timer_stop = perf_counter()

    if config.PERFORMANCE_TIMING:
        print(oh.blue(f"{len(tasks)} lyric API requests made in {timer_stop - timer_start} seconds"))

    # Remove any null values
    recordings_with_lyrics = [i for i in recordings_with_lyrics if i]

    # If we get no data from the API, return an error message.
    if not recordings_with_lyrics:
        return None, oh.fail("No lyrics found!")

    # Display colouring
    found_num = len(recordings_with_lyrics)
    cleaned_num = len(cleaned_recordings)
    found_func = oh.warning

    if found_num == cleaned_num:
        found_func = oh.green
    elif found_num < cleaned_num / 2:
        found_func = oh.fail

    found_lyrics_str = found_func(f"{found_num}")
    cleaned_lyrics_str = oh.green(f"{cleaned_num}")
    print(oh.cyan("Found lyrics for ") + f"{found_lyrics_str}/{cleaned_lyrics_str} " + oh.cyan("tracks"))

    return recordings_with_lyrics, None
