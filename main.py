from sys import stderr
from time import perf_counter
import argparse
import aiohttp
import asyncio
# import musicbrainzngs
import helpers.output_helpers as oh
from helpers.data_collection_helpers import get_artist_data, get_recordings_data, get_song_lyrics
from helpers.data_cleanup_helpers import remove_duplicate_recordings, calculate_avg_word_count


async def main():
    """"""
    # Await a user input for the artist name
    artist_name_query = input("Artist name: ")

    # We use this accept header so the MusicBrainz API will return JSON data instead of XML
    headers = {"Accept": "application/json"}
    async with aiohttp.ClientSession(headers=headers) as session:
        # Get the artist data from the API
        artist, err = await get_artist_data(session, artist_name_query)
        if handle_error(err):
            return

        # Get the recording data from the API using the artist ID
        recordings, err = await get_recordings_data(session, artist)
        if handle_error(err):
            return

        # Clean the data by removing any duplicate songs/singles/remixes/re-releases/etc.
        cleaned_recordings = remove_duplicate_recordings(recordings, artist)

        # For each song we have, get the lyrics and store them in the class
        recordings_with_lyrics, err = await get_song_lyrics(session, cleaned_recordings, artist)
        if handle_error(err):
            return

        # Calculate the average number of words over all lyrics we retrieved
        average_number_of_words, err = calculate_avg_word_count(recordings_with_lyrics)
        if handle_error(err):
            return

        print(oh.separator())
        print(oh.bold(f"{artist.name} uses an average of ") + oh.green(f"{average_number_of_words}") + oh.bold(" words in their songs."))
        print(oh.separator())


def handle_error(err: str) -> bool:
    """
    If we raise an error, output to stderr and return True.
    :param err: The error message to display.
    :return: Whether or not we should exit the main method.
    """
    #
    if err:
        print(err, file=stderr)
        return True
    return False


if __name__ == "__main__":
    # Setup arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", help="modify output verbosity", action="store_true")
    parser.add_argument("-s", "--search-number", help="the maximum number of results shown if multiple likely artists are found", type=int)

    args = parser.parse_args()
    # Set the global flags
    # FIXME - these flags don't work :/
    import helpers
    helpers.IS_VERBOSE = args.verbose
    helpers.MAX_SEARCH = args.search_number

    # Main program loop
    while True:
        timer_start = perf_counter()
        asyncio.run(main())
        timer_stop = perf_counter()
        print(f"Elapsed time: {timer_stop - timer_start}s\n\n")
