#! python3
# yt_FirstPick.py - Opens up first search result from YouTube based on search
#                   string

"""
Usage example:
python3 youtube_search.py
    -s or --search_string = '<string>'
"""

"""
TO DO LIST:
    - Add "History" title to top of scrolling history window
    - Clean up top right corner
    - Add cmd features to bottom of screen
"""

import curses
from time import sleep, strftime
from selenium import webdriver
import sys
import requests
import bs4
import os
import urllib.error
import argparse
import configparser

#######################################

config = configparser.ConfigParser()
config.read('yt_FirstPick_Settings.ini')

chrome_bin_path = config['app settings']['chromedriver_path']

opts = webdriver.ChromeOptions()
opts.binary_location = chrome_bin_path
browser = webdriver.Chrome(chrome_options=opts)
browser.set_window_size(1,1)
browser.set_window_position(-3000,-3000)

screen = curses.initscr()
#######################################


# Initialize the search, find YouTube result, and write the records
def new_first_pick(search_string, yt_result_number, window):

    # Set cursor to invisible
    curses.curs_set(0)

    # Make search string url friendly, replace spaces with + symbol
    yt_search_string = str.replace(search_string, ' ', '+')

    window.addstr(1, 2,"{} || Searching".format(strftime("%H:%M:%S")))
    window.refresh()

    # Grab HTML from YouTube search results page
    res = requests.get(
        'https://www.youtube.com/results?search_query={}'.format(
            yt_search_string))
    # Make sure our request was successful
    res.raise_for_status()

    # Use BeautifulSoup to find URL of first search result in HTML
    soup = bs4.BeautifulSoup(res.text, "html.parser")
    link_elems = soup.select('.yt-lockup-title a')

    window.addstr(2, 2, "{} || Try this one...".format(strftime("%H:%M:%S")))
    window.refresh()

    # Open Chrome to the first search result
    returned_result = 'https://www.youtube.com' + \
                      link_elems[yt_result_number].get('href')

    browser.get(returned_result)

    # Go through the video page HTML to find the song name
    res = requests.get('https://www.youtube.com' +
                       link_elems[yt_result_number].get('href'))
    soup = bs4.BeautifulSoup(res.text, "html.parser")
    song_name = soup.select(
        '.watch-title')[0].text.replace('\n', '').strip()

    # Let me know what I'm listening to!
    window.addstr(3, 2, "{0} || Now playing \'{1}\'".format(strftime("%H:%M:%S"), song_name))
    window.refresh()


#######################################


def get_current_video(window, counter):

    # Set video url
    video_url = browser.current_url

    # Instantiate YouTube video page request object
    res = requests.get(video_url)

    # Go through the video page HTML to find the song name
    soup = bs4.BeautifulSoup(res.text, "html.parser")
    video_name = soup.select(
        '.watch-title')[0].text.replace('\n', '').strip()

    # Let me know what I'm listening to!
    if counter < 1:
        window.addstr("{} || Now Playing \'{}\'".format(strftime("%H:%M:%S"),
            video_name))
    else:
        window.addstr("\n{} || Now playing \'{}\'".format(strftime("%H:%M:%S"), video_name))
    window.refresh()


#######################################

def get_raw_input(stdscr, r, c, prompt_string):
    curses.echo()
    stdscr.addstr(r, c, prompt_string)
    stdscr.refresh()
    input = stdscr.getstr(r + 2, c, 255)
    return input


#######################################


# Check to see if YouTube's auto play has kicked in
def check_for_new_video(old_url, window, counter):

    """
    while True:
        # Grab URL from current page
        current_url = browser.current_url

        # If the URL hasn't changed, wait and check again later
        while current_url == old_url:
            # Pause...take a deep breath
            sleep(1)
            # Reset URL to current page
            current_url = browser.current_url

    """
    # Once the URL has changed, write down the record
    get_current_video(window, counter)


#######################################
"""
cmds:
    r = Go back one song (back page)
    n = Play next song (in auto play list)
    q = Quit program
    m = Switch to Mix of current song
    s = Instigate new seach
    l = Login
    a = add to playlist

        if user_input == 'r':

            print('Let\'s go back one song...')

            # browser.execute_script("window.history.go(-1)")
            browser.back()

            get_current_video()

        elif user_input == 'n':

            print('Let\'s hear the next song...')

            next_song = \
                browser.find_element_by_xpath(
                    '//*[@id="watch7-sidebar-modules"]/div[1]/div/div[2]/ul/li'
                    '/div[1]/a/span[1]')

            next_song.click()

            get_current_video()

        elif user_input == 'q':

            browser.close()
            exit("Quiting...")

        # elif user_input == 'm'

            # jump to YouTube Mix optoin

        # elif user_input == 's'

            # instigate new search with search
"""

#######################################


def main(screen):

    try:
        os.system('clear')
        
        # Add initial formatting
        screen.addstr(" HEADLESS RADIO", curses.A_REVERSE)
        screen.chgat(-1, curses.A_REVERSE)

        parser = argparse.ArgumentParser(
            description='Find first result on YouTube')
        # The string to be searched for on YouTube
        parser.add_argument('-s',
                            '--search_string',
                            help='string to use for YouTube search')
        # The specific youtube search result to return
        parser.add_argument('-n',
                            '--number',
                            help='search result number you want to play')

        args = parser.parse_args()

        # Check that parameters were entered and are valid.  
        # If no search string arg, get from user
        if not args.search_string:
            args.search_string = str(get_raw_input(
            screen, 2, 3, "Where would you like to start? (Enter a search "
                          "string!)"))

        # Set chosen search result from cmd line or to 1 by default
        if not args.number:
            args.number = 0
        else:
            args.number = int(args.number.strip()) - 1

        # Clear screen from "Get Search Param" page
        screen.clear()

        # Add title to main ui page
        screen.addstr(" HEADLESS RADIO", curses.A_REVERSE)
        screen.chgat(-1, curses.A_REVERSE)

        # Add "Initial Search" window
        window_main = curses.newwin(5, curses.COLS - 0, 1, 0)
        window_main.border()
        screen.refresh()

        # Run the search URL, pull up the video, and write the records
        new_first_pick(args.search_string, args.number, window_main)

        # Add title to "Now Playing" window
        screen.move(6,0)
        screen.addstr(" HISTORY", curses.A_REVERSE)
        screen.chgat(-1, curses.A_REVERSE)
        screen.refresh()

        # Set up border window for "Now Playing" output
        window_history_border = curses.newwin(curses.LINES - 8, curses.COLS - 0,
               7, 0 )
        window_history_border.border()
        window_history_border.refresh()

        # Set up actual output window for "Now Playing"
        window_history = curses.newwin(curses.LINES - 10, curses.COLS - 4, 8, 1)

        # Make sure "Now Playing" window scrolls correctly
        window_history.idlok(1)
        window_history.scrollok(True)
        window_history.refresh()

        screen.move(curses.LINES-1, 0)
        screen.addstr(" CMD BAR", curses.A_REVERSE)
        screen.chgat(-1, curses.A_REVERSE)
        screen.refresh()

        while True:
            for i in range(100):
                check_for_new_video(browser.current_url, window_history, i)

        # If YouTube isn't responding, quit and tell user
    except urllib.error.HTTPError as e:
        # sys.exit("An HTTP error %d occurred:\n%s" % (e.resp.status, e.content))
        curses.nocbreak()
        screen.keypad(False)
        curses.echo()
        browser.close()
        sys.exit("An HTTP error {0} occured:\n{1}".format(e.resp.status,
            e.contet))

    except KeyboardInterrupt:
        curses.nocbreak()
        screen.keypad(False)
        curses.echo()
        browser.close()
        sys.exit("You have exited the program via ctrl+c")


# ================================__main__=====================================

if __name__ == "__main__":

    curses.wrapper(main)

