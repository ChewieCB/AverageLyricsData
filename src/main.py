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

        print("=" * 32)
        print(f"{artist.name}")
        print("=" * 32)

        # Get the recording data from the API using the artist ID
        recordings = await get_recordings_data(session, artist)
        print(f"\n{len(recordings)} tracks.\n")

        # Clean the data by removing any duplicate songs/singles/remixes/re-releases/etc.
        cleaned_recordings = remove_duplicate_recordings(recordings, artist)

        # For each song we have, get the lyrics and store them in the class
        await get_song_lyrics(session, cleaned_recordings, artist)


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
    artist_object = Artist(raw_data=artist_data, name=artist_name, mb_id=artist_id)

    return artist_object


async def get_recordings_data(session: aiohttp.ClientSession, artist: Artist) -> [Track]:
    """

    :param session:
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
        # FIXME - not getting all album data for some reason? Alpha/Omega don't show up :/
        recordings_url = api_parser.build_recordings_query_url(artist.mb_id, tracks_retrieved)

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
                raw_data=track,
                name=_title,
                mb_id=_id,
                release=_release_title,
                release_type=_release_type,
            )
            recordings.append(current_track)

    return recordings


async def get_song_lyrics(session: aiohttp.ClientSession, cleaned_recordings: [Track], artist: Artist) -> None:
    """

    :param session:
    :param cleaned_recordings:
    :param artist:
    :return:
    """
    # TODO - optimise async calls here to increase speed
    for track in cleaned_recordings:
        # Make a query request to the lyrics API
        url = api_parser.build_lyrics_url(artist.name, track.name)
        async with session.get(url) as response:
            # Workaround status check to prevent crashes
            # TODO: This is likely an issue with uncommon characters or escape sequences
            #  being passed in the artist name or song title, implement the cleaning method
            #  to negate this as much as possible.
            if response.status != 200:
                print(f"Bad response {response.status} for {track.name} - Skipping.")
                continue
            lyrics_data = await response.json()

        # If we get no lyrics data from the API, show the user an error message and continue
        if lyrics_data == {'error': 'No lyrics found'}:
            print(f"No lyrics found for {track.name}")
            continue
        # Some songs will be instrumental even after filtering (not all instrumental songs have it in the title)
        elif lyrics_data == "[Instrumental]":
            print(f"{track.name}is an instrumental!")
            continue

        # Remove a known header from the lyrics, we don't want this muddying the word count
        lyrics = lyrics_data.get("lyrics")
        cleaned_lyrics = remove_lyrics_credit(lyrics)

        track.lyrics = cleaned_lyrics
        print(f"{track.name} has {track.word_count} words.")


def remove_duplicate_recordings(raw_recordings_data: [Track], artist: Artist) -> [Track]:
    """
    Go through each recording from the data and remove any duplicate tracks.
    :param raw_recordings_data: A list of Track objects.
    :param artist:
    :return: Cleaned list of Track objects for each non-duplicate track.
    """
    local_recording_data = raw_recordings_data
    original_length = len(local_recording_data)

    # Hacky shit way of getting this to work, loop through each element and check if any other songs have the element
    # name as a substring, optimise later - bunch of issues with this buy lets make a start at least.
    for track in local_recording_data:
        # Quick sanity check to see if a track with the wrong artist ID has slipped through the search filters
        if is_non_artist_song(track, artist):
            print(f"{track} is not by the artist {artist.name} - removing.")
            local_recording_data.remove(track)
            continue

        # Are the words "live", "remix", or "instrumental" in the name? Remove the track.
        # FIXME - still not getting all of them, few DGD instrumental albums slipping through
        if is_re_release_or_instrumental(track):
            print(f"Removing {track}! as it is likely a remix, instrumental, or live version.")
            local_recording_data.remove(track)
            continue

        # Check if the track name appears as a sub string in any other track
        for other_track in local_recording_data:
            # Don't check against yourself
            if local_recording_data.index(other_track) == local_recording_data.index(track):
                continue

            # If we have an exact match it's likely a single or EP re-release, in this case we prioritise album tracks
            elif other_track.name == track.name:
                # Determine which one to remove:
                # Is one a single with the same name? Remove that one.
                if other_track.release_type == "Single":
                    print(f"Removing album single: {other_track}")
                    local_recording_data.remove(other_track)
                elif other_track.release_type == "EP":
                    print(f"Removing re-released EP track: {other_track}")
                    local_recording_data.remove(other_track)

    print("=" * 32)
    print(f"Original tracklist length = {original_length}")
    new_length = len(local_recording_data)
    print(f"New tracklist length = {new_length}")
    print(f"Duplicate tracks removed = {original_length - new_length}")
    print("=" * 32)

    return local_recording_data


def is_non_artist_song(track: Track, artist: Artist) -> bool:
    """
    Helper method to detect songs not by the chosen artist that have slipped through the API search filter.
    :param track:
    :param artist:
    :return:
    """
    track_artist_id = track.raw_data.get("artist-credit")[0].get("artist").get("id")
    if track_artist_id != artist.mb_id:
        return True
    return False


def is_re_release_or_instrumental(track: Track) -> bool:
    """
    Helper method to detect songs re-released as live or remixed versions,
    and instrumental tracks we don't need to find lyrics for.
    :param track:
    :return:
    """
    # FIXME - refine this, it's removing partial matches that could be valid songs.
    for keyword in ["live", "mix", "deluxe", "instrumental", "session"]:
        if track.name.lower().find(keyword) != -1 or track.release.lower().find(keyword) != -1:
            return True
    return False


def remove_lyrics_credit(lyrics: str) -> str:
    """
    Helper method to remove known header lines that are returned for some songs on the lyrics API.
    :param lyrics:
    :return:
    """
    local_lyrics = lyrics
    # The header line is in French and runs up until the first \r\n escape sequence, so we look for the
    # start of this substring and trim up until the escape sequence.
    if local_lyrics.lower().find("paroles de la chanson") != -1:
        first_escape_index = local_lyrics.index("\r\n")
        local_lyrics = local_lyrics[first_escape_index:]

    return local_lyrics


if __name__ == "__main__":
    timer_start = perf_counter()
    asyncio.run(main())
    timer_stop = perf_counter()
    print(f"Elapsed time: {timer_stop - timer_start}s")
