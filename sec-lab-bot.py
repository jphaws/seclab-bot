#!/usr/bin/env python3

import sys
import hmac
import curses
from pyfiglet import Figlet

FIGLET_FONT = 'doh'
FIGLET_WIDTH = 256

CLOSED = 0
OPEN = 1

class NetworkException(Exception):
    pass

def send_open_request():
    try:
        pass # TODO
    #except something assertion-related:
        # raise NetworkException("Error response to open request")
    except:
        raise NetworkException("Failed to send open request")
    finally:
        pass # if connection: close()

def send_close_request():
    try:
        pass # TODO
    #except something assertion-related:
        # raise NetworkException("Error response to close request")
    except:
        raise NetworkException("Failed to send close request")
    finally:
        pass # if connection: close()

"""
        TODO
    ************
    * bold     *
    * color    *
    * requests *
    ************
"""

def main(win):
    fig = Figlet(font=FIGLET_FONT, width=FIGLET_WIDTH)
    state = CLOSED
    while True:          
        try:                 
            key = win.getch()         
            if key != -1:
                win.clear()
                if state == CLOSED:
                    try:
                        send_open_request()
                        banner = fig.renderText('The Lab is\nOPEN :)')
                    except NetworkException as e:
                        print(e, file=sys.stderr)
                elif state == OPEN:
                    try:
                        send_close_request()
                        banner = fig.renderText('The Lab is\nCLOSED :(')
                    except NetworkException as e:
                        print(e, file=sys.stderr)
                win.addstr(banner)
                state ^= 1
        except KeyboardInterrupt:
            return

if __name__ == '__main__':
    curses.wrapper(main)
