from unittest import TestCase
from unittest.mock import patch
import requests
from helpers.api_parser import build_recordings_query_url, build_lyrics_url, sanitise_url_string


class TestAPISetup(TestCase):
    """
    Base class to reduce repetitive setup of sessions for API call tests.

    This way we can separate each API parser function into its own TestCase
    with slightly less boilerplate.
    """
    def setUp(self) -> None:
        """Create a session object we can make requests and check responses with."""
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/json"})
        # These attributes are virtual - either set by the child class, or set within make_API_call()
        self.query_url = None
        self.response = None
        self.response_data = None

    def make_API_call(self) -> None:
        """
        Helper method to abstract out API calls for each test case.

        This prevents removes any session/request code from the unit tests and
        lets us focus more on what each test is asserting.
        """
        # Error handling in case of no url being set.
        if not self.query_url:
            raise NotImplementedError()

        # Make the response within a context manager to ensure the session is closed correctly
        with self.session:
            self.response = self.session.get(self.query_url)

        if self.response.status_code == 200:
            # We are using a JSON header in the session so we need to convert the string to a JSON dict
            self.response_data = self.response.json()

    def test_API_call_returns_a_valid_response(self):
        """Assert that the url generated for the API call returns a valid response object."""
        # Skip this test for the base class, we only want to run this in the inherited classes.
        if not self.query_url:
            return

        self.assertIsNotNone(self.response)
        self.assertEqual(self.response.status_code, 200)


class TestRecordingsQueryGeneration(TestAPISetup):
    def setUp(self) -> None:
        super().setUp()
        # This is the artist ID for Nine Inch Nails, the artist has a lot of secondary releases, demos, etc.
        self.query_url = build_recordings_query_url("b7ffd2af-418f-4be2-bdd1-22f8b48613da")
        self.make_API_call()

        self.recordings = self.response_data.get("recordings")

    def test_query_returns_only_official_releases(self):
        """Assert that only official recordings are released, we don't want any bootlegs or demos in our data."""
        for recording in self.recordings:
            first_release = recording.get("releases")[0]
            status = first_release.get("status")
            self.assertTrue(status, "Official")

    def test_query_returns_no_videos(self):
        """Assert that the recording data doesn't contain any video entries."""
        for recording in self.recordings:
            is_video = recording.get("video")
            # The `video` value in recording data can be truthy or null so we check
            # that the value != True to prevent false positives.
            self.assertFalse(is_video, True)

    def test_query_data_is_primary_releases_only(self):
        """
        Assert that the recording data doesn't contain any secondary release objects,
        e.g. live albums, compilations, demos, remixes.
        """
        for recording in self.recordings:
            secondary_type = recording.get("releases")[0].get("release-group").get("secondary-types")
            self.assertIsNone(secondary_type)


class TestLyricsAPICallGeneration(TestAPISetup):
    def setUp(self) -> None:
        super().setUp()

    def test_api_call_returns_lyrics_with_valid_inputs(self):
        """Given an artist and song title known to be valid in the API, assert that passing
        these args to `build_lyrics_url` and making a request returns the expected lyrics."""
        self.query_url = build_lyrics_url("Napalm Death", "You Suffer")
        self.make_API_call()
        self.test_API_call_returns_a_valid_response()

        self.lyrics = self.response_data.get("lyrics")
        self.assertEqual(
            self.lyrics,
            "You suffer...\r\nBut why?"
        )

    def test_api_call_returns_error_with_invalid_inputs(self):
        """Given an artist/song input known to be invalid, assert that passing these
        ars to `build_lyrics_url` and making a request returns a handled error."""
        # FIXME
        self.query_url = build_lyrics_url("Not A Band", "Invalid Song")
        self.make_API_call()
        self.assertFalse(
            self.test_API_call_returns_a_valid_response()
        )

        # self.lyrics = self.response_data.get("lyrics")
        self.assertEqual(
            self.response_data,
            {"error": "No lyrics found"}
        )

    def test_api_call_handles_empty_input(self):
        """"""
        # FIXME
        self.query_url = build_lyrics_url("Not A Band", "")
        self.make_API_call()
        self.test_API_call_returns_a_valid_response()

    @patch("helpers.api_parser.sanitise_url_string")
    def test_sanitise_url_string_called_on_build_lyrics(self, mock_sanitise_method) -> None:
        """Assert that the method `sanitise_url_string` is called when the `build_lyrics_url`
        method is called with valid arguments."""
        build_lyrics_url("TestArtist", "TestTitle")
        mock_sanitise_method.assert_called()

    def test_sanitise_url_string_escapes_characters(self):
        """Assert that the passing an unescaped string to `sanitise_url_string
        returns a cleaned and properly escaped url string."""
        dirty_url = """only.thi's--should" b;e | vIsib/?l!e"  """
        cleaned_url = "only.thi%27s--should%22%20b%3Be%20%7C%20vIsib %3Fl%21e%22%20%20"
        self.assertEqual(sanitise_url_string(dirty_url), cleaned_url)

