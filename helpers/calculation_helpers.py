import flags
import statistics
import matplotlib.pyplot as plt

from helpers.data import Track, Artist
import helpers.output_helpers as oh


def calculate_output(recordings_with_lyrics: [Track], artist: Artist) -> (int, str):
    """
    For a list of cleaned Track objects with lyrics, calculate the average number of words
    used by the Track's Artist, as well as other statistical values such as standard deviation,
    variance, minimum and maximum values.
    :param recordings_with_lyrics: A list of Track objects with cleaned lyrics attributes.
    :param artist: The Artist object linked to the tracks.
    :return: A tuple containing the average word count as an integer and a string to pass as an error message.
    """
    # Error handling
    if not recordings_with_lyrics:
        return None, oh.fail("No lyrics to count!")

    word_counts = [track.word_count for track in recordings_with_lyrics]

    average_word_count = int(statistics.mean(word_counts))

    std_dev = statistics.pstdev(word_counts)
    variance = statistics.pvariance(word_counts)

    min_length = min(word_counts)
    track_with_min_length = recordings_with_lyrics[word_counts.index(min_length)]

    max_length = max(word_counts)
    track_with_max_length = recordings_with_lyrics[word_counts.index(max_length)]

    print(oh.separator())
    print(oh.bold(f"{artist.name} uses an average of ") + oh.green(f"{average_word_count}") + oh.bold(
        " words in their songs"))
    if flags.SHOW_STATISTICS:
        print("\t - " + oh.blue("Standard deviation") + " of the sample is " + oh.bold(str(std_dev)))
        print("\t - " + oh.cyan("Variance") + " of the sample is " + oh.bold(str(variance)))
        print("\t - The song with the " + oh.cyan("least") + " words was " + oh.bold(
            str(track_with_min_length.name)) + " with " + oh.cyan(str(min_length)) + " words")
        print("\t - The song with the " + oh.header("most") + " words was " + oh.bold(
            str(track_with_max_length.name)) + " with " + oh.header(str(max_length)) + " words")
    print(oh.separator())

    return average_word_count, None


def plot_data(track_data: [Track], average_word_count: int, artist: Artist) -> None:
    """
    Given the cleaned and calculated track data plot a scatter graph of an Artist's songs, with the
    year of release along the x-axis, the number of words in the track along the y-axis, and the
    average number of words plotted as a dashed line across the plot.
    :param track_data: Cleaned list of Track objects.
    :param average_word_count: The average number of words across all tracks.
    :param artist: The Artist object linked to the tracks.
    :return: None.
    """
    xs = []
    ys = []

    tracks_with_lyrics_year_ascending = sorted(
        [track for track in track_data if track.release.date],
        key=lambda x: x.release.date,
        reverse=False,
    )

    # Extract only the years from each track's release date, some tracks only have a year value
    # but all date values should follow a %Y-%m-%d format so we can just slice the first 4 chars
    # to get the year in this case.
    for track in tracks_with_lyrics_year_ascending:
        xs.append(track.release.date[0:4])

    for point in tracks_with_lyrics_year_ascending:
        ys.append(point.word_count)

    fig, ax = plt.subplots()
    ax.set_title(f"Word count of {artist.name} songs over time.")

    # Limit the number of x-ticks so we don't get flooded with date labels
    # and obscure the x-axis for large datasets
    ax.xaxis.set_major_locator(plt.MaxNLocator(12))

    plt.scatter(xs, ys)
    # Plot the average as a dashed black line
    plt.plot([xs[0], xs[-1]], [average_word_count, average_word_count], 'k--')
    plt.show()
