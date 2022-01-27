# TODO - dataclasses would probably work better here for most of these.
#   since dataclasses make hashing easier we could do some sort of hash comparison to compare releases?

known_releases = []


class Artist:
    def __init__(self, raw_data: str, name: str, mb_id: str, description: str):
        """

        :param raw_data: The full JSON data retrieved from the API call.
        :param name: Full or official name of the artist returned by the API search.
        :param mb_id: Artist id string used by the musicbrainz API for lookups.
        """
        self.raw_data = raw_data
        self.name: str = name
        self.mb_id: str = mb_id
        self.description: str = description
        self._tags: str
        self.releases: [Release] = []

    def __str__(self):
        return f"{self.name}"

    @property
    def tags(self):
        return self._tags

    @tags.setter
    def tags(self, value: [str]):
        """Unpack the list of tags into one string."""
        tags_string = ", ".join(value)
        self._tags = tags_string


class Release:
    def __init__(self, raw_data: dict):
        """"""
        self.raw_data = raw_data
        self.name = self.raw_data.get("title")
        self.mb_id = self.raw_data.get("id")
        self.date = self.raw_data.get("date")
        self.release_type = self.raw_data.get("release-group").get("primary-type")
        self.tracks = []

    def __str__(self):
        return f"{self.name} - {self.release_type} ({self.date})"

    def __repr__(self):
        return f"{self.name} - {self.release_type} ({self.date})"


class Track:
    def __init__(self, raw_data: dict):
        """"""
        self.raw_data: dict = raw_data
        self.name: str = self.raw_data.get("title")
        self.mb_id: str = self.raw_data.get("id")
        self.release: Release = self._assign_release()
        #
        self.raw_lyrics_data: str
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

    def _assign_release(self) -> Release:
        release_data = self.raw_data.get("releases")[0]
        release_name = release_data.get("title")
        release_mb_id = release_data.get("id")
        # Check if a Release object exists in known_releases with the same name and mb_id passed to the constructor
        _is_existing_release = False
        new_release = None

        for release in known_releases:
            if release.name == release_name and release.mb_id == release_mb_id:
                _is_existing_release = True
                new_release = release

        # If the release doesn't exist yet, create it
        if not _is_existing_release:
            new_release = Release(raw_data=release_data)
            known_releases.append(new_release)
            # print(new_release)

        # If this track object is not already part of the Release object's track list, add it
        if self not in new_release.tracks:
            new_release.tracks.append(self)

        return new_release
