import re
from sys import stderr
import builtins
from itertools import combinations, compress
from . import IS_VERBOSE, OutColours
from .data import Artist, Track
import helpers.output_helpers as oh


def calculate_avg_word_count(cleaned_recordings: [Track]) -> (int, Exception):
    """

    :param cleaned_recordings:
    :return:
    """
    total_words = 0

    print(oh.header("Calculating average word count..."))

    # Error handling
    if not cleaned_recordings:
        return None, f"{OutColours.FAIL}No lyrics to count!{OutColours.ENDC}"

    for track in cleaned_recordings:
        total_words += track.word_count

    result = total_words // len(cleaned_recordings)

    return result, None


def remove_duplicate_recordings(raw_recordings_data: [Track], artist: Artist) -> [Track]:
    """
    Go through each recording from the data and remove any duplicate tracks.
    :param raw_recordings_data: A list of Track objects.
    :param artist:
    :return: Cleaned list of Track objects for each non-duplicate track
        and a count of how many tracks were removed.
    """
    # Selector list to determine which elements of the raw data we want to keep
    selector = [True] * (len(raw_recordings_data))

    original_length = len(raw_recordings_data)

    print(oh.header("Cleaning duplicate tracks..."))

    # FIXME - Hacky way of getting this to work, loop through each element and check if any other songs have the element
    #   name as a substring, optimise later - bunch of issues with this but lets make a start at least.
    for track, other_track in combinations(raw_recordings_data, 2):
        track_index = raw_recordings_data.index(track)

        # Quick sanity check to see if a track with the wrong artist ID has slipped through the search filters
        if is_non_artist_song(track, artist):
            if selector[track_index]:
                if builtins.IS_VERBOSE:
                    print(oh.fail(f"{track} is not by the artist {artist.name} - removing."))
                selector[track_index] = False
            continue
        else:
            # Check if the track name appears as a sub string in any other track
            #
            # If we have an exact match it's likely a single or EP re-release, in this case
            # we prioritise album tracks
            if other_track.name == track.name:
                # Determine which one to remove:
                # Is one a single with the same name? Remove that one.
                if builtins.IS_VERBOSE:
                    print(oh.cyan(f"Removing re-released track: {other_track}"))
                selector[track_index] = False
                continue
            # If the other track contains the original track, it's
            # likely some sort of re-release or alternate version
            if track.name in other_track.name:
                # Are the words "live", "remix", or "instrumental" in the name? Remove the track
                if is_re_release_or_instrumental(track):
                    selector[track_index] = False
                    if builtins.IS_VERBOSE:
                        print(oh.warning(f"Removing {track}! as it is likely a remix, instrumental, or live version."))
                    continue

    output_data = list(compress(raw_recordings_data, selector))

    # Calculate how many tracks we've removed from the initial list
    new_length = len(output_data)
    tracks_removed = original_length - new_length

    if builtins.IS_VERBOSE:
        print(oh.separator())
        print(f"Original tracklist length = {oh.header(str(original_length))}")
        print(f"New tracklist length = {oh.green(str(new_length))}")
        print(f"Duplicate tracks removed = {oh.warning(str(tracks_removed))}")
        print(oh.separator())

    print(oh.cyan(f"Removed {tracks_removed} duplicates, remixes, or live tracks"))

    return output_data


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
    # Clean the names of the track and release, removing any parentheses
    # and making them lowercase for comparison
    track_name = re.sub("[()]", '', track.name.lower())
    release_name = re.sub("[()]", '', track.release.lower())

    # Split the track and release names into words, we only want whole word instances of these
    # keywords to prevent removing valid song names like "Alive" or "Mixed Up"
    track_name_words = track_name.split(" ")
    release_name_words = release_name.split(" ")
    for keyword in ["live", "mix", "remix", "cut", "take", "master", "mono", "deluxe", "demo", "version", "instrumental", "session", "acoustic"]:
        if keyword in track_name_words or keyword in release_name_words:
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
