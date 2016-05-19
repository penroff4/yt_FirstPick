#! python3
# yt_FirstPick.py - Opens up first search result from YouTube based on search
#                   string

"""
Usage example:

python3 youtube_search.py
    -s or --search_string = '<string>'

"""

import webbrowser
import requests
import bs4
import urllib.error
import argparse
from time import gmtime, strftime

# ================================__main__=====================================

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Find first result on '
                                                 'YouTube')
    # The string to be searched for on YouTube
    parser.add_argument('-s', '--search_string', help='string to use for '
                                                      'YouTube search')
    # The specific youtube search result to return
    parser.add_argument('-n', '--number', help='search result number you want '
                                               'to play')

    args = parser.parse_args()

    # Check that parameters were entered and are valid.  Quit if not.
    if not args.search_string:
        exit("Please specify a search string!")

    # Make search string url friendly, replace spaces with + symbol
    yt_search_string = str.replace(args.search_string, ' ', '+')

    # Set chosen search result from cmd line or to 1 by default
    if not args.number:
        yt_result_number = 0
    else:
        yt_result_number = int(args.number.strip()) - 1

    # Here we go!
    try:
        print("{} || Searching".format(strftime("%H:%M:%S")))

        # Grab HTML from YouTube search results page
        res = requests.get(
            'https://www.youtube.com/results?search_query={}'.format(
                yt_search_string))
        # Make sure our request was successful
        res.raise_for_status()

        # Use BeautifulSoup to find URL of first search result in HTML
        soup = bs4.BeautifulSoup(res.text, "html.parser")
        linkElems = soup.select('.yt-lockup-title a')

        print("{} || Try this one...".format(strftime("%H:%M:%S")))

        # Open Chrome to the first search result
        webbrowser.open('https://www.youtube.com' +
                        linkElems[yt_result_number].get('href'))

        # Go through the video page HTML to find the song name
        res = requests.get('https://www.youtube.com' +
                        linkElems[yt_result_number].get('href'))
        soup = bs4.BeautifulSoup(res.text, "html.parser")
        song_name = soup.select('.watch-title')[0].text.replace('\n', '').strip()

        # Let me know what I'm listening to!
        print("{} || Now playing \'{}\'".format(strftime("%H:%M:%S"), song_name))

    # If YouTube isn't responding, quit and tell user
    except urllib.error.HTTPError as e:
        print("An HTTP error %d occurred:\n%s" % (e.resp.status, e.content))
