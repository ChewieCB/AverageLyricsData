import builtins
import statistics
import matplotlib.pyplot as plt

from helpers.data import Track, Artist
import helpers.output_helpers as oh


def calculate_output(recordings_with_lyrics: [Track], artist: Artist) -> (int, str):
    """"""
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
    if builtins.SHOW_STATISTICS:
        print("\t - " + oh.blue("Standard deviation") + " of the sample is " + oh.bold(str(std_dev)))
        print("\t - " + oh.cyan("Variance") + " of the sample is " + oh.bold(str(variance)))
        print("\t - The song with the " + oh.cyan("least") + " words was " + oh.bold(
            str(track_with_min_length.name)) + " with " + oh.cyan(str(min_length)) + " words")
        print("\t - The song with the " + oh.header("most") + " words was " + oh.bold(
            str(track_with_max_length.name)) + " with " + oh.header(str(max_length)) + " words")
    print(oh.separator())

    return average_word_count, None


def plot_data(track_data: [Track], artist: Artist) -> None:
    """"""
    xs = []
    ys = []

    tracks_with_lyrics_year_ascending = sorted(
        [track for track in track_data if track.release.date],
        key=lambda x: x.release.date,
        reverse=False,
    )

    # for track in tracks_with_lyrics_year_ascending:
    #     print(track.name, track.release.date)

    for point in tracks_with_lyrics_year_ascending:
        xs.append(point.release.date)
        ys.append(point.word_count)

    # TODO - Format x-ticks to use only the year value
    # from datetime import datetime
    # print(xs)
    # try:
    #     year_xticks = [datetime.strptime(item, "%Y-%m-%d").year for item in xs]

    fig, ax = plt.subplots()
    ax.set_title(f"Word count of {artist.name} songs over time.")
    plt.scatter(xs, ys)
    plt.show()
