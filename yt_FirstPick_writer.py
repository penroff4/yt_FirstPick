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
import csv
from time import gmtime, strftime


first_picks_csv = 'FirstPicks.csv'


def csv_writer(path, data):
    # Method to record data to csv

    with open(path, 'w', newline='') as csv_file:
        writer = csv.writer(csv_file, delimiter=',')

        for line in data:
            writer.writerow(line)

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

    # Set record ID for search transaction based on Date and Time of initiation
    record_id = int(strftime("%Y%m%d%H%M%S"))

    # Here we go!
    try:
        print("\n{} || Searching".format(strftime("%H:%M:%S")))

        # Set up 'Initial Search' record
        initial_search_action = {"id": record_id,
                                 "date": strftime("%Y:%m:%d"),
                                 "time": strftime("%H:%M:%S"),
                                 "action": "Initial Search",
                                 "result_url": "",
                                 "search_term": yt_search_string,
                                 "result_number": yt_result_number,
                                 "video_name": ""}

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
        returned_result = 'https://www.youtube.com' + \
                          linkElems[yt_result_number].get('href')

        webbrowser.open(returned_result)

        # Set up 'Initial Search' record
        try_this_action = {"id": record_id,
                           "date": strftime("%Y:%m:%d"),
                           "time": strftime("%H:%M:%S"),
                           "action": "Try This",
                           "result_url": returned_result,
                           "search_term": yt_search_string,
                           "result_number": yt_result_number,
                           "video_name": ""}

        # Go through the video page HTML to find the song name
        res = requests.get('https://www.youtube.com' +
                        linkElems[yt_result_number].get('href'))
        soup = bs4.BeautifulSoup(res.text, "html.parser")
        song_name = soup.select('.watch-title')[0].text.replace('\n', '').strip()

        # Let me know what I'm listening to!
        print("{} || Now playing \'{}\'".format(strftime("%H:%M:%S"), song_name))

        now_playing_action = {"id": record_id,
                              "date": strftime("%Y%m%d"),
                              "time": strftime("%H:%M:%S"),
                              "action": "Now Playing",
                              "result_url": returned_result,
                              "search_term": yt_search_string,
                              "result_number": yt_result_number,
                              "video_name": song_name}

        # Write all actions to csv
        initial_search_action_data = [initial_search_action["id"],
                                      initial_search_action["date"],
                                      initial_search_action["time"],
                                      initial_search_action["action"],
                                      initial_search_action["result_url"],
                                      initial_search_action["search_term"],
                                      initial_search_action["result_number"],
                                      initial_search_action["video_name"]]

        try_this_action_data = [try_this_action["id"],
                                try_this_action["date"],
                                try_this_action["time"],
                                try_this_action["action"],
                                try_this_action["result_url"],
                                try_this_action["search_term"],
                                try_this_action["result_number"],
                                try_this_action["video_name"]]

    # If YouTube isn't responding, quit and tell user
    except urllib.error.HTTPError as e:
        print("An HTTP error %d occurred:\n%s" % (e.resp.status, e.content))
