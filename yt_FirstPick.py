#! python3
# yt_FirstPick.py - Opens up first search result from YouTube based on search
#                   string

"""
Usage example:
python3 youtube_search.py
    -s or --search_string = '<string>'
"""

from time import sleep
from selenium import webdriver
import requests
import bs4
import urllib.error
import argparse
import csv
import os
from time import strftime
from threading import Thread
import configparser
from prompt_toolkit import prompt
from prompt_toolkit.styles import style_from_dict
from prompt_toolkit.token import Token

config = configparser.ConfigParser()
config.read('yt_FirstPick_Settings.ini')


first_picks_csv = config['app settings']['first_picks_history_csv']

chrome_bin_path = config['app settings']['chromedriver_path']

number_of_repeats = int(config['app settings']['number_of_songs'])

opts = webdriver.ChromeOptions()
opts.binary_location = chrome_bin_path
browser = webdriver.Chrome(chrome_options=opts)

style = style_from_dict({
    Token.Toolbar: '#ffffff bg:#333333'
})

#######################################


def get_bottom_toolbar_tokens(cli):
    return [(Token.Toolbar, ' q - Quit  r - Previous Song  n - Next Song')]


#######################################


# Write records to CSV
def csv_writer(path, data):
    # Method to record data to csv

    if os.path.isfile(path):
        with open(path, 'a', newline='') as csv_file:
            writer = csv.writer(csv_file, delimiter=',')

            for line in data:
                writer.writerow(line)

    else:
        with open(path, 'w', newline='') as csv_file:
            writer = csv.writer(csv_file, delimiter=',')

            for line in data:
                writer.writerow(line)


#######################################


# Initialize the search, find YouTube result, and write the records
def new_first_pick(search_string, yt_result_number):

    # Set session ID for session based on initial search record id
    current_session_id = int(strftime("%y%m%d%H%M%S"))

    # Make search string url friendly, replace spaces with + symbol
    yt_search_string = str.replace(search_string, ' ', '+')

    print("\n{} || Searching".format(strftime("%H:%M:%S")))

    # Set up 'Initial Search' record
    initial_search_action = {"id": 1,
                             "session_id": current_session_id,
                             "date": strftime("%y:%m:%d"),
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
    link_elems = soup.select('.yt-lockup-title a')

    print("{} || Try this one...".format(strftime("%H:%M:%S")))

    # Open Chrome to the first search result
    returned_result = 'https://www.youtube.com' + \
                      link_elems[yt_result_number].get('href')

    browser.get(returned_result)

    # Set up 'Initial Search' record
    try_this_action = {"id": 2,
                       "session_id": current_session_id,
                       "date": strftime("%y:%m:%d"),
                       "time": strftime("%H:%M:%S"),
                       "action": "Try This",
                       "result_url": returned_result,
                       "search_term": yt_search_string,
                       "result_number": yt_result_number,
                       "video_name": ""}

    # Go through the video page HTML to find the song name
    res = requests.get('https://www.youtube.com' +
                       link_elems[yt_result_number].get('href'))
    soup = bs4.BeautifulSoup(res.text, "html.parser")
    song_name = soup.select(
        '.watch-title')[0].text.replace('\n', '').strip()

    # Let me know what I'm listening to!
    print("{} || Now playing \'{}\'"
          .format(strftime("%H:%M:%S"), song_name))

    now_playing_action = {"id": 3,
                          "session_id": current_session_id,
                          "date": strftime("%y:%m:%d"),
                          "time": strftime("%H:%M:%S"),
                          "action": "Now Playing",
                          "result_url": returned_result,
                          "search_term": yt_search_string,
                          "result_number": yt_result_number,
                          "video_name": song_name}

    # Write all actions to csv
    initial_search_action_data = [initial_search_action["id"],
                                  initial_search_action["session_id"],
                                  initial_search_action["date"],
                                  initial_search_action["time"],
                                  initial_search_action["action"],
                                  initial_search_action["result_url"],
                                  initial_search_action["search_term"],
                                  initial_search_action["result_number"],
                                  initial_search_action["video_name"]]

    try_this_action_data = [try_this_action["id"],
                            try_this_action["session_id"],
                            try_this_action["date"],
                            try_this_action["time"],
                            try_this_action["action"],
                            try_this_action["result_url"],
                            try_this_action["search_term"],
                            try_this_action["result_number"],
                            try_this_action["video_name"]]

    now_playing_action_data = [now_playing_action["id"],
                               now_playing_action["session_id"],
                               now_playing_action["date"],
                               now_playing_action["time"],
                               now_playing_action["action"],
                               now_playing_action["result_url"],
                               now_playing_action["search_term"],
                               now_playing_action["result_number"],
                               now_playing_action["video_name"]]

    transaction_data = [initial_search_action_data, try_this_action_data,
                        now_playing_action_data]

    csv_writer(first_picks_csv, transaction_data)

    return current_session_id


#######################################

def current_song():

    # Set video url
    video_url = browser.current_url

    # Instantiate YouTube video page request object
    res = requests.get(video_url)

    # Go through the video page HTML to find the song name
    soup = bs4.BeautifulSoup(res.text, "html.parser")
    video_name = soup.select(
        '.watch-title')[0].text.replace('\n', '').strip()

    # Let me know what I'm listening to!
    print("{} || Now playing \'{}\'"
          .format(strftime("%H:%M:%S"), video_name))


#######################################


# Record YouTube's auto play result
def next_song_writer(current_session_id, search_term, result_number,
                     record_id):

    # Set video url
    video_url = browser.current_url

    # Instantiate YouTube video page request object
    res = requests.get(video_url)

    # Go through the video page HTML to find the song name
    soup = bs4.BeautifulSoup(res.text, "html.parser")
    video_name = soup.select(
        '.watch-title')[0].text.replace('\n', '').strip()

    # Let me know what I'm listening to!
    print("{} || Now playing \'{}\'"
          .format(strftime("%H:%M:%S"), video_name))

    # Set up 'Next Video' record
    next_video_action = {"id": record_id+3,
                         "session_id": current_session_id,
                         "date": strftime("%y:%m:%d"),
                         "time": strftime("%H:%M:%S"),
                         "action": "Next Video",
                         "result_url": video_url,
                         "search_term": search_term,
                         "result_number": result_number,
                         "video_name": video_name}

    # Write all actions to csv
    initial_search_action_data = [next_video_action["id"],
                                  next_video_action["session_id"],
                                  next_video_action["date"],
                                  next_video_action["time"],
                                  next_video_action["action"],
                                  next_video_action["result_url"],
                                  next_video_action["search_term"],
                                  next_video_action["result_number"],
                                  next_video_action["video_name"]]

    transaction_data = [initial_search_action_data]

    csv_writer(first_picks_csv, transaction_data)


#######################################


# Check to see if YouTube's auto play has kicked in
def next_song_checker(old_url, search_term, result_number, current_session_id,
                      record_id, number_of_repeats):

    for i in range(1, number_of_repeats):
        # Grab URL from current page
        current_url = browser.current_url

        # If the URL hasn't changed, wait and check again later
        while current_url == old_url:
            # Pause...take a deep breath
            sleep(10)
            # Reset URL to current page
            current_url = browser.current_url

    # Once the URL has changed, write down the record
    next_song_writer(current_session_id, search_term, result_number, record_id)

#######################################


def cmd_input():
    while True:

        user_input = prompt('> ',
                            get_bottom_toolbar_tokens=get_bottom_toolbar_tokens
                            , style=style)

        if user_input == 'r':

            print('Let\'s go back one song...')

            # browser.execute_script("window.history.go(-1)")
            browser.back()

            current_song()

        elif user_input == 'n':

            print('Let\'s hear the next song...')

            next_song = \
                browser.find_element_by_xpath(
                    '//*[@id="watch7-sidebar-modules"]/div[1]/div/div[2]/ul/li'
                    '/div[1]/a/span[1]')

            next_song.click()

            current_song()

        elif user_input == 'q':

            browser.close()
            exit("Quiting...")


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

    # Set chosen search result from cmd line or to 1 by default
    if not args.number:
        args.number = 0
    else:
        args.number = int(args.number.strip()) - 1

    # Here we go!
    try:

        # Run the search URL, pull up the video, and write the records
        session_id = new_first_pick(args.search_string, args.number)

        # Check for a new song, and write records when it shows up
        t1 = Thread(target=next_song_checker, args=(browser.current_url,
                    args.search_string, args.number, session_id, 1,
                    number_of_repeats))
        t2 = Thread(target=cmd_input)

        # t1.start()
        t2.start()

    # If YouTube isn't responding, quit and tell user
    except urllib.error.HTTPError as e:
        print("An HTTP error %d occurred:\n%s" % (e.resp.status, e.content))
