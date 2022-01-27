from sys import stderr
from time import perf_counter
import argparse
import aiohttp
import asyncio
import musicbrainzngs

import config
from helpers.data_collection_helpers import get_artist_data, get_recordings_data, get_song_lyrics
from helpers.data_cleanup_helpers import remove_duplicate_recordings
from helpers.calculation_helpers import calculate_output, plot_data


async def main():
    """"""
    # Await a user input for the artist name
    artist_name_query = input("Enter artist name: ")

    timer_start = perf_counter()

    # We use this accept header so the MusicBrainz API will return JSON data instead of XML
    headers = {"Accept": "application/json"}
    async with aiohttp.ClientSession(headers=headers) as session:
        # Get the artist data from the API
        artist, err = get_artist_data(artist_name_query)
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
        average_word_count, err = calculate_output(recordings_with_lyrics, artist)
        if handle_error(err):
            return

        timer_stop = perf_counter()

        if config.PERFORMANCE_TIMING:
            print(f"Elapsed time: {timer_stop - timer_start}s\n\n")

        if config.SHOW_GRAPH:
            plot_data(recordings_with_lyrics, artist)


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
    # Setting a useragent is required to use the python API
    musicbrainzngs.set_useragent("LyricsCounter", "0.1")

    # Setup arguments
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-v", "--verbose",
        help="modify output verbosity",
        action="store_true",
        default=False
    )
    parser.add_argument(
        "-p", "--performance",
        help="show performance timings for elements of the program",
        action="store_true",
        default=False
    )
    parser.add_argument(
        "-s", "--statistics",
        help="output more detailed statistics such as standard deviation, variance, and min/max values",
        action="store_true",
        default=False
    )
    parser.add_argument(
        "-g", "--graph",
        help="show graph output of data",
        action="store_true",
        default=False
    )
    # TODO - add arg to compare 2 artists

    args = parser.parse_args()

    # Set the global config flags
    config.IS_VERBOSE = args.verbose
    config.PERFORMANCE_TIMING = args.performance
    config.SHOW_STATISTICS = args.statistics
    config.SHOW_GRAPH = args.graph

    # Main program
    asyncio.run(main())
