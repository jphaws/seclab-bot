#!/usr/bin/env python3

import sys
import hmac
import curses
from pyfiglet import Figlet

FIGLET_FONT = 'doh'
FIGLET_WIDTH = 256

CLOSED = 0
OPEN = 1

def send_open_request():
    pass # TODO

def send_close_request():
    pass # TODO

"""
        TODO
    ************
    * bold     *
    * color    *
    * requests *
    * async    *
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
                    banner = fig.renderText('The Lab is\nOPEN :)')
                    send_open_request()
                elif state == OPEN:
                    banner = fig.renderText('The Lab is\nCLOSED :(')
                    send_close_request()
                win.addstr(banner)
                state ^= 1
        except KeyboardInterrupt:
            return

if __name__ == '__main__':
    curses.wrapper(main)
