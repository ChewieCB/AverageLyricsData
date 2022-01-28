# LyricsAvg
LyricsAvg is a CLI app to calculate the average number of words for a musical artist based on a name input.

## Installation
LyricsAvg should come pre-built for **Linux**, you can find the executable in this repo's `releases`.

#### If you need to build LyricsAvg for another OS then you can run the following:

Make sure you have `pyinstaller` installed on your local Python environment (`pip install pyinstaller`).

From the repository root run `pyinstaller main.py -n lyrics_avg --onefile` to build an executable file within `dist/`.

## Usage
LyricsAvg can be executed with default arguments by running `lyrics_avg` in a terminal from the `dist/` directory, the user will then be prompted to enter the name of the Artist they want to find the average number of words in the lyrics of.

This program comes with a number of optional arguments that can be listed by running `lyrics_avg --help`, the effects of which are listed as follows:
 - **\-v** or **\--verbose** will enable a more detailed program output, such as listing which tracks are removed, the reasoning behind the removal, and displaying non-successful API responses.
 - **\-p** or **\--performance** will show the time taken for API requests to finish.
 - **\-s** or **\--statistics** will output more detailed statistics based on the program results, such as the min/max values of the data, the standard deviation, and the variance.
 - **\-r NUM** or **\--results NUM** will change the number of search results considered when searching for an Artist name in the MusicBrainz database, e.g. if a user runs `lyrics_avg -r 3` and inputs the name **Elvis**, the program will return the top 3 results of artists with a similar name in the database (_Elvis Presley, Elvis Costello, Elvis Crespo)_ and prompt the user to select the correct one by entering the correct number.
 - **\-g** or **\--graph** will show a scatter graph of the lyrics data plotted as **number of words in a song over time**.
