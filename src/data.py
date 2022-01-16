

class Artist:
    def __init__(self, name: str, mb_id: str):
        """

        :param name: Full or official name of the artist returned by the API search.
        :param mb_id: Artist id string used by the musicbrainz API for lookups.
        """
        self.name: str = name
        self.mb_id: str = mb_id
        self.releases: [Release] = []


class Release:
    def __init__(self, name: str, mb_id: str, year: str, type: str, artist: Artist):
        """

        :param name:
        :param mb_id:
        :param artist:
        :param year:
        """
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
    def __init__(self, name: str, mb_id: str, release: str, release_type: str):
        """

        :param name:
        :param mb_id:
        :param release:
        """
        self.name = name
        self.mb_id = mb_id
        self.release = release
        self.release_type = release_type
        self.lyrics: str

    def __str__(self):
        return f"{self.release}: {self.name}"

    def __repr__(self):
        return f"{self.release}: {self.name}"

