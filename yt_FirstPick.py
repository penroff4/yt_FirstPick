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
    - Add cmd features functionality (i.e. method(s) )
    - Bring in threading functionality
    - Implement three Thread classes
        * CmdInput
            - Add "put to queue" call to run method
        * CurrentVideo
            - Add "put to queue" call to run method
        * HistoryPrinter
        * CmdInput and CurrentVideo will feed prompts into a queue, and
          HistoryPrinter will pull those prompts from that queue and into the
          window_history object.
"""

"""
proposed cmd_input cmds:
    r = Go back one song (back page)
    n = Play next song (in auto play list)
    q = Quit program
    m = Switch to Mix of current song
    s = Instigate new seach
    l = Login
    a = add to playlist
"""

import curses
from time import sleep, strftime
from selenium import webdriver
import sys
from threading import Thread
from queue import Queue
import requests
import bs4
import os
import urllib.error
import argparse
import configparser

# ================================__vars__=====================================

# setup config settings
config = configparser.ConfigParser()
config.read('yt_FirstPick_Settings.ini')

# setup chromedriver path
chrome_bin_path = config['app settings']['chromedriver_path']

# setup chrome driver
opts = webdriver.ChromeOptions()
opts.binary_location = chrome_bin_path
browser = webdriver.Chrome(chrome_options=opts)

# set chrome's physical location to be the top left (i.e. out of the way)
browser.set_window_size(1,1)
browser.set_window_position(-3000, -3000)

# Initial screen for curses
screen = curses.initscr()

# Queue for handling prompt input
prompt_queue = Queue()


# ==============================__Classes__====================================

# Object for handling threading of user cmds
class CmdInput(Thread):

    def __init__(self, queue, screen):
        Thread.__init__(self)
        self.queue = queue
        self.screen = screen

    def run(self):

        while True:
            # Get user input of single key stroke
            user_input = screen.getkey()

            # Play previous song
            if user_input == 'r':

                self.queue.put("\nMoving to previous song...\n")

                # browser.execute_script("window.history.go(-1)")
                browser.back()

            # Play next song
            elif user_input == 'n':

                self.queue.put("\nSkipping to next song...\n")
                next_song = browser.find_element_by_xpath('//*[@id="watch7-sidebar-modules"]/div[1]/div/div[2]/ul/li/div[2]/a/span/img')
                next_song.click()

            # Quit application
            elif user_input == 'q':

                self.queue.put("\nQuitting...\n")
                browser.close()
                sys.exit()

            # Switch to YouTube Mix option
            elif user_input == 'm':

                self.queue.put("\nSwitching to YouTube Mix List...\n")

                mix_list_option = browser.find_element_by_xpath(
                '//*[@id="watch-related"]/li[1]/a')

                mix_list_option.click()

            # elif user_input == 's'

                # instigate new search with search


#######################################

# Object for handling 'new video' prompts
class GetCurrentVideo(Thread):

    def __init__(self, queue):
        Thread.__init__(self)
        self.queue = queue

    def run(self):

        previous_url = browser.current_url
        is_first_print = True

        while True:

            current_url = browser.current_url

            while current_url == previous_url:

                sleep(1)

                current_url = browser.current_url

            res = requests.get(current_url)

            soup = bs4.BeautifulSoup(res.text, "html.parser")
            video_name = soup.select(
                ".watch-title")[0].text.replace("\n", "").strip()

            if is_first_print is True:
                update_string = "{} || Now Playing \'{}\'"\
                    .format(strftime("%H:%M:%S"), video_name)
            else:
                update_string = "\n{} || Now Playing \'{}\'"\
                    .format(strftime("%H:%M:%S"), video_name)

            is_first_print = False
            previous_url = current_url

            self.queue.put(update_string)


#######################################

# Object for handling printing threaded prompts into curses window
class WindowQueuePrinter(Thread):

    def __init__(self, queue, window):
        Thread.__init__(self)
        self.queue = queue
        self.window = window

    def run(self):
        while True:
            try:

                if not self.queue.empty():
                    message = self.queue.get(block=True,timeout=1)
                    self.window.addstr(message)
                    self.window.refresh()

                else:
                    sleep(1)

            except self.queue.Empty:
                    sleep(1)
                    pass


# ==============================__Methods__====================================


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

# function for handling raw input in curses
def get_raw_input(stdscr, r, c, prompt_string):
    curses.echo()
    stdscr.addstr(r, c, prompt_string)
    stdscr.refresh()
    input = stdscr.getstr(r + 2, c, 255)
    curses.noecho()
    return input


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
        # screen.addstr(" CMD BAR", curses.A_REVERSE)
        # screen.chgat(-1, curses.A_REVERSE)
        screen.addstr(' N - Next Song', curses.A_REVERSE)
        screen.addstr('  R - Previous Song', curses.A_REVERSE)
        screen.addstr('  Q - Quit', curses.A_REVERSE)
        screen.addstr('  M - Play Mix List', curses.A_REVERSE)
        screen.addstr('  S - Initiate New Search', curses.A_REVERSE)
        screen.chgat(-1, curses.A_REVERSE)
        screen.refresh()

        cmdIn = CmdInput(prompt_queue, screen)
        getCurrentVid = GetCurrentVideo(prompt_queue)
        prompt_printer = WindowQueuePrinter(prompt_queue, window_history)

        cmdIn.Name = 'CmdIn'
        getCurrentVid.Name = 'getCurrentVid'
        prompt_printer.Name = 'prompt_printer'

        prompt_printer.start()
        getCurrentVid.start()
        cmdIn.start()

        # Allow the program to "run forever"
        while True:
            sleep(1)

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
