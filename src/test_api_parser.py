from unittest import TestCase
import requests
from api_parser import build_artist_search_query_url, build_recordings_query_url, build_lyrics_url


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
        # These attributes are either set by the child class, or set within make_API_call()
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


class TestArtistQueryGeneration(TestAPISetup):
    def setUp(self) -> None:
        """"""
        super().setUp()
        # Generate a valid url for an artist that we know should work
        self.query_url = build_artist_search_query_url("The Beatles")
        self.make_API_call()

        self.artist_name = self.response_data.get("artists")[0].get("name")

    def test_query_returns_correct_artist(self):
        """
        Check that the artist returned from the API query is the one we intended.

        This is ultimately dependent on the MusicBrainz database since we're taking the
        top result of their search algorithm, but we need to at least check that we get
        the expected result for more well-known artists we know work.
        """
        self.assertEqual(self.artist_name, "The Beatles")


class TestRecordingsQueryGeneration(TestAPISetup):
    def setUp(self) -> None:
        """"""
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
        """"""
        super().setUp()

        self.query_url = build_lyrics_url("The Dillinger Escape Plan", "One of Us is the Killer")
        self.make_API_call()

        self.lyrics = self.response_data.get("lyrics")

    def test_api_call_returns_lyrics(self):
        """"""
        self.assertNotEqual(self.lyrics, "No lyrics found")

    def test_api_call_cleans_string_inputs(self):
        """"""
        # TODO
        pass

