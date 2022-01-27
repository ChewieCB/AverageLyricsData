import asyncio
import aiohttp
import builtins
import musicbrainzngs

from . import MAX_SEARCH, OutColours
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
        limit=builtins.MAX_SEARCH,
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

    if builtins.PERFORMANCE_TIMING:
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
    request_counter = 0
    track_count = 0
    tracks_retrieved = 0

    print(oh.header("Finding songs..."))
    # While the tracks retrieved is less than the number of tracks in the list, add an offset and make another request
    # TODO - refactor this to be non-blocking for large discographies (Elvis, The Beatles)
    while track_count == 0 or tracks_retrieved < track_count:
        # Build the url
        # TODO - Using the MusicBrainz python API yields more results but it's harder to make async
        recordings_url = api_parser.build_recordings_query_url(artist.mb_id, tracks_retrieved)

        # Make a query request to the API
        # TODO - add error handling to determine when we've hit a request limit instead of a general crash
        async with session.get(recordings_url) as response:
            recording_data = await response.json()

        # If we get data without any recordings data it's likely that
        # the track count  is divisible by 100, so we break here.
        if not recording_data.get("recordings"):
            break
        # If we get no data at all from the API, return an error message.
        elif not recording_data or len(recording_data["recordings"]) == 0:
            return None, oh.fail("No songs found!")

        track_count = recording_data.get("count")
        tracks_retrieved += len(recording_data.get("recordings"))

        for track in recording_data["recordings"]:
            current_track = Track(
                raw_data=track,
            )
            recordings.append(current_track)

        request_counter += 1

    timer_stop = perf_counter()

    print(oh.cyan(f"Found {len(recordings)} tracks"))

    if builtins.PERFORMANCE_TIMING:
        print(oh.blue(f"{len(recordings)} songs retrieved from API in {request_counter} requests in {timer_stop - timer_start} seconds"))

    return recordings, None


async def make_lyrics_request(session: aiohttp.ClientSession, url: str, track: Track) -> Track:
    """"""
    async with session.get(url) as response:
        # Disable the content_type check here since the lyrics API sends text/html for `no lyrics found` responses
        # and application/json for valid responses.
        if "application/json" in response.headers['content-type']:
            lyrics_data = await response.json()
        else:
            # FIXME - this sometimes fails with a 502 error, likely the lyrics API getting overloaded.
            if builtins.IS_VERBOSE:
                print(oh.fail(f"Can't retrieve lyrics for {track.name}: Response status {response.status}" + response.headers['content-type']))
            return None

        lyrics = lyrics_data.get("lyrics")
        error = lyrics_data.get("error")

        # If we get no lyrics data from the API, show the user an error message and continue
        if error:
            if builtins.IS_VERBOSE:
                print(oh.fail(f"No lyrics found for {track.name}"))
            return None

        # Remove a common lyrics header this API's sources sometimes have within the lyrics data
        cleaned_lyrics = remove_lyrics_credit(lyrics)

        # Some songs will be instrumental even after filtering (not all instrumental songs have it in the title)
        if cleaned_lyrics.lower().find("instrumental") != -1:
            if builtins.IS_VERBOSE:
                print(oh.warning(f"{track.name} is an instrumental!"))
            return None

        track.lyrics = cleaned_lyrics

        if builtins.IS_VERBOSE:
            print(f"{track.name} has {track.word_count} words.")

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
    if builtins.PERFORMANCE_TIMING:
        print(oh.blue(f"{len(tasks)} lyric API requests made in {timer_stop - timer_start} seconds"))

    # Remove any null values
    recordings_with_lyrics = [i for i in recordings_with_lyrics if i]

    # If we get no data from the API, return an error message.
    if not recordings_with_lyrics:
        return None, f"{OutColours.FAIL}No lyrics found!{OutColours.ENDC}"

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
