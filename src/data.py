# TODO - dataclasses would probably work better here for most of these.


class Artist:
    def __init__(self, raw_data: str, name: str, mb_id: str):
        """

        :param raw_data: The full JSON data retrieved from the API call.
        :param name: Full or official name of the artist returned by the API search.
        :param mb_id: Artist id string used by the musicbrainz API for lookups.
        """
        self.raw_data = raw_data
        self.name: str = name
        self.mb_id: str = mb_id
        self.releases: [Release] = []


class Release:
    def __init__(self, raw_data: str, name: str, mb_id: str, year: str, type: str, artist: Artist):
        """

        :param name:
        :param mb_id:
        :param artist:
        :param year:
        """
        self.raw_data = raw_data
        self.name = name
        self.mb_id = mb_id
        self.artist = artist
        self.year = year
        self.type = type

    def __str__(self):
        return f"{self.year}: {self.name} ({self.type})"

    def __repr__(self):
        return f"{self.year}: {self.name} ({self.type})"


class Track:
    def __init__(self, raw_data: str, name: str, mb_id: str, release: str, release_type: str):
        """

        :param name:
        :param mb_id:
        :param release:
        """
        self.raw_data = raw_data
        self.name = name
        self.mb_id = mb_id
        self.release = release
        self.release_type = release_type
        self._lyrics: str
        self.word_count: int = 0

    def __str__(self):
        return f"{self.release}: {self.name}"

    def __repr__(self):
        return f"{self.release}: {self.name}"

    @property
    def lyrics(self):
        """ """
        return self._lyrics

    @lyrics.setter
    def lyrics(self, value):
        self._lyrics = value

        # When we set the lyrics for a track, calculate the number of words in the lyrics as well.
        if self.lyrics:
            # Trim the escape characters off of the text and replace them with spaces for easier counting.
            escaped_lyrics = self.lyrics.replace("\n", " ").replace("\r", " ")
            self.word_count = len(escaped_lyrics.split(" "))

