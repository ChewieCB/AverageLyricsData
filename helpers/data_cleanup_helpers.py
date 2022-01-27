import re
import config

from .data import Artist, Track, known_releases
import helpers.output_helpers as oh


def remove_duplicate_recordings(raw_recordings_data: [Track], artist: Artist) -> [Track]:
    """
    Go through each recording from the data and remove any duplicate tracks.
    :param raw_recordings_data: A list of Track objects.
    :param artist:
    :return: Cleaned list of Track objects for each non-duplicate track
        and a count of how many tracks were removed.
    """
    original_length = len(raw_recordings_data)

    output_data = raw_recordings_data.copy()

    print(oh.header("Cleaning duplicate tracks..."))

    # Loop over every recording we have
    for recording in raw_recordings_data:
        # Quick sanity check to see if a track with the wrong artist ID has slipped through the search filters
        if is_non_artist_song(recording, artist):
            if config.IS_VERBOSE:
                if config.IS_VERBOSE:
                    print(oh.fail(f"{recording} is not by the artist {artist.name} - removing."))
                if recording in output_data:
                    output_data.remove(recording)
                    remove_from_releases(recording)
            continue

        # Split the song name into a list of words so we can use the
        # first word as the substring to find similar tracks
        search_term = recording.name

        # Find any recordings with similar names
        similar_recordings = []
        for track in raw_recordings_data:
            substring = track.name.find(search_term)
            if substring != -1:
                if track.mb_id == recording.mb_id:
                    continue
                else:
                    similar_recordings.append(track)

        # Look for instrumental, live, remix, etc. track variants
        if similar_recordings:
            for sim in similar_recordings:
                start_substr = sim.name.find(search_term)
                end_substr = start_substr + len(search_term)
                if is_re_release_or_instrumental(sim):
                    if config.IS_VERBOSE:
                        print(oh.warning(f"Removing {sim}! as it is likely a remix, instrumental, or live version."))
                    if sim in output_data:
                        output_data.remove(sim)
                        remove_from_releases(sim)
                    continue
                else:
                    # If we have an exact match it's likely a single or EP re-release, in this case
                    # we prioritise album tracks
                    if sim.name == recording.name:
                        # Determine which one to remove:
                        # Is one a single with the same name? Remove that one.
                        if config.IS_VERBOSE:
                            print(oh.cyan(f"Removing re-released track: {sim}"))
                            if sim in output_data:
                                output_data.remove(sim)
                                remove_from_releases(sim)
                        continue

    # Calculate how many tracks we've removed from the initial list
    new_length = len(output_data)
    tracks_removed = original_length - new_length

    if config.IS_VERBOSE:
        print(oh.separator())
        print(f"Original tracklist length = {oh.header(str(original_length))}")
        print(f"New tracklist length = {oh.green(str(new_length))}")
        print(f"Duplicate tracks removed = {oh.warning(str(tracks_removed))}")
        print(oh.separator())

    print(oh.cyan(f"Removed {tracks_removed} duplicates, remixes, or live tracks"))

    return output_data


def remove_from_releases(track: Track) -> None:
    """"""
    for release in known_releases:
        if track in release.tracks:
            # print(oh.fail(f"Removed {track.name} from {release.name} tracklist!"))
            release.tracks.remove(track)
            if len(release.tracks) == 0:
                known_releases.remove(release)


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
    # Clean the names of the track and release, removing any parentheses
    # and making them lowercase for comparison
    track_name = re.sub("[()]", '', track.name.lower())
    release_name = re.sub("[()]", '', track.release.name.lower())

    # Split the track and release names into words, we only want whole word instances of these
    # keywords to prevent removing valid song names like "Alive" or "Mixed Up"
    track_name_words = track_name.split(" ")
    release_name_words = release_name.split(" ")
    for keyword in ["live", "mix", "remix", "cut", "take", "master", "mono", "deluxe", "demo", "version", "instrumental", "session", "acoustic", "rehearsal", "5.1"]:
        if keyword in track_name_words:
            return True
        elif keyword in release_name_words:
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
