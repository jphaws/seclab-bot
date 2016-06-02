#!/usr/bin/env python3

import sys
import hmac
import curses
from pyfiglet import Figlet

FIGLET_FONT = 'doh'
FIGLET_WIDTH = 256

CLOSED = 0
OPEN = 1

def main(win):
    fig = Figlet(font=FIGLET_FONT, width=FIGLET_WIDTH)
    win.nodelay(1)
    state = CLOSED
    while True:          
        try:                 
            key = win.getkey()         
            win.clear()
            if state == CLOSED:
                banner = fig.renderText('OPEN')
            elif state == OPEN:
                banner = fig.renderText('CLOSED')
            win.addstr(banner)
            state ^= 1
        except KeyboardInterrupt:
            return
        except Exception as e:
            # No input   
            pass

if __name__ == '__main__':
    curses.wrapper(main)
