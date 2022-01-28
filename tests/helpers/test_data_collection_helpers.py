import aiohttp
import asynctest
from asynctest import CoroutineMock, patch
import musicbrainzngs

import helpers.data
import helpers.output_helpers as oh
from helpers.data import Artist, Track
from helpers.data_collection_helpers import get_artist_data, get_recordings_data


class TestGetArtistData(asynctest.TestCase):

    async def setUp(self) -> None:
        # Setting a useragent is required to use the python API
        musicbrainzngs.set_useragent("LyricsCounterTest", "0.1")

    # Search MusicBrainz API for the Artist data
    @patch('musicbrainzngs.search_artists')
    def test_no_data_returns_error(self, mock_artist_search_query) -> None:
        """Assert that when get_artist_data retrieves no data from the API it returns an expected error message."""
        # Since we can't call the musicbrainz search method without arguments,
        # we mock it to ensure we get an empty dataset.
        mock_artist_search_query.return_value = {}

        artist_data = get_artist_data("")
        self.assertEqual(artist_data, (None, oh.fail("No artist found!")))

    @patch('flags.MAX_SEARCH_RESULTS', 1)
    def test_returns_valid_data(self) -> None:
        """Assert that a known input returns an Artist object with the expected attributes."""
        artist_data, _error = get_artist_data("The Dillinger Escape Plan")
        self.assertEqual(artist_data.name, "The Dillinger Escape Plan")
        self.assertEqual(artist_data.mb_id, "1bc41dff-5397-4c53-bb50-469d2c277197")

    # Prompt the user to choose an Artist if many results are returned
    @patch('helpers.data_collection_helpers.select_artist_from_multiple_choices')
    @patch('flags.MAX_SEARCH_RESULTS', 5)
    def test_data_with_many_results_prompt_user_for_input(self, mock_select_method) -> None:
        """Assert that when the data returned has more than 1 result for the artist query
        the user is prompted to choose between the artists."""
        _artist_data = get_artist_data("A")
        self.assertEqual(mock_select_method.call_count, 1)

    @patch('flags.MAX_SEARCH_RESULTS', 3)
    @patch('helpers.output_helpers.fail', side_effect=[None, Exception("Raise an exception to break the input loop.")])
    def test_invalid_prompt_input_returns_error(self, mock_fail) -> None:
        """Assert that given an invalid input by the user when prompted to choose an artist, the input prompt
         is repeated after outputting an error message."""
        # Invalid positive range
        with patch('builtins.input', return_value="5"):
            with self.assertRaises(Exception):
                _artist_data, _error = get_artist_data("Elvis")
            mock_fail.assert_any_call("`5` is not a valid choice, try again.")
        # Invalid negative range
        with patch('builtins.input', return_value="-7"):
            with self.assertRaises(Exception):
                _artist_data, _error = get_artist_data("Elvis")
            mock_fail.assert_any_call("`-7` is not a valid choice, try again.")
        # Invalid null input
        with patch('builtins.input', return_value=""):
            with self.assertRaises(Exception):
                _artist_data, _error = get_artist_data("Elvis")
            mock_fail.assert_any_call("Not a valid choice, try again.")

    @patch('flags.MAX_SEARCH_RESULTS', 3)
    @patch('builtins.input', return_value="2")
    def test_valid_prompt_input(self, _mock_input) -> None:
        """Assert that a valid input by the user when prompted to choose an artist is accepted and
        continues execution with the correct Artist data."""
        artist_data, _error = get_artist_data("Elvis")
        self.assertEqual(artist_data.name, "Elvis Costello")

    # Build an Artist object from the data returned from the API
    @patch('flags.MAX_SEARCH_RESULTS', 1)
    def test_artist_object_instantiated(self) -> None:
        """Assert that a valid Artist object is created."""
        artist_data, _error = get_artist_data("The Dillinger Escape Plan")
        self.assertIsInstance(artist_data, Artist)


class TestGetSongData(asynctest.TestCase):

    async def setUp(self) -> None:
        # Setting a useragent is required to use the python API
        musicbrainzngs.set_useragent("LyricsCounterTest", "0.1")
        self.session = aiohttp.ClientSession(headers={"Accept": "application/json"})

    # Search API for tracks by Artist
    async def test_valid_response(self) -> None:
        """Assert that a known valid query does not return an error, and returns a list
        of Track objects with the expected length."""
        artist, _error = get_artist_data("Archspire")
        song_data = await get_recordings_data(self.session, artist)
        self.assertNotEqual(song_data, (None, oh.fail("No songs found!")))
        self.assertEqual(len(song_data[0]), 30)
        for item in song_data[0]:
            self.assertIsInstance(item, Track)

    @patch('helpers.data_collection_helpers.make_recordings_request')
    @patch('aiohttp.ClientSession.get')
    async def test_no_data_returns_error(self, mock_get, mock_make_recordings_request) -> None:
        """Assert that when get_artist_data retrieves no data from the API it returns an expected error message."""
        # Mock an invalid response from the API
        mock_make_recordings_request.return_value = {}
        #
        # We need to change the return value attributes within the __aenter__ method here because
        # within the function we're testing the ClientSession object is used with a context manager.
        mock_get.return_value.__aenter__.return_value.json = CoroutineMock()
        mock_get.return_value.__aenter__.return_value.json.return_value = {}

        with patch('helpers.api_parser.build_recordings_query_url'):
            song_data = await get_recordings_data(self.session, Artist("", "", "", ""))
        self.assertEqual(song_data, (None, oh.fail("No songs found!")))

    # Collect all tracks by Artist in batches of 100 per request
    @patch('helpers.data_collection_helpers.track_count', 30)
    @patch('helpers.api_parser.build_recordings_query_url')
    @patch('aiohttp.ClientSession.get')
    async def test_artists_with_less_than_100_songs_only_make_1_request(
            self,
            mock_get,
            mock_build_url,
    ) -> None:
        """Assert that for a known artist with less than 100 songs on the MusicBrainz database,
        only one request is made."""
        # We need to change the return value attributes within the __aenter__ method here because
        # within the function we're testing the ClientSession object is used with a context manager.
        mock_get.return_value.__aenter__.return_value.json = CoroutineMock()
        # Set the session to return a similar dict to the reponses we expect, with a low count so only one
        # request will be made.
        mock_get.return_value.__aenter__.return_value.json.return_value = {"count": 30, "recordings": {}}
        mock_build_url.return_value = ""

        artist, _error = get_artist_data("Archspire")
        _recording_data, _error = await get_recordings_data(self.session, artist)

        self.assertEqual(helpers.data_collection_helpers.request_counter, 1)

    @patch('helpers.data_collection_helpers.track_count', 30)
    @patch('helpers.api_parser.build_recordings_query_url')
    @patch('aiohttp.ClientSession.get')
    async def test_large_track_lists_make_the_expected_number_of_requests(
            self,
            mock_get,
            mock_build_url,
    ) -> None:
        """For an artist with more than 100 songs, we loop and increment the offset until we have
        all the songs from teh database. Assert that the number of requests made is equal to
        the total number of tracks / 100."""
        # We need to change the return value attributes within the __aenter__ method here because
        # within the function we're testing the ClientSession object is used with a context manager.
        mock_get.return_value.__aenter__.return_value.json = CoroutineMock()
        # Set the session to return a similar dict to the reponses we expect, with a low count so only one
        # request will be made.
        mock_get.return_value.__aenter__.return_value.json.return_value = {"count": 350, "recordings": {}}
        mock_build_url.return_value = ""

        artist, _error = get_artist_data("Archspire")
        _recording_data, _error = await get_recordings_data(self.session, artist)

        self.assertEqual(helpers.data_collection_helpers.request_counter, 4)

    async def test_all_tracks_retrieved(self) -> None:
        """Assert the number of Track objects instantiated for the Artist is equal to
        the track count given in the data."""
        artist, _error = get_artist_data("Beck")
        recording_data, _error = await get_recordings_data(self.session, artist)
        self.assertEqual(
            helpers.data_collection_helpers.track_count,
            len(recording_data)
        )

    async def tearDown(self) -> None:
        # Close the session once we're done testing to prevent a memory leak
        await self.session.close()
