#!/usr/bin/env python3

import sys
import hmac
import curses
import socket
import logging
from time import time
from pyfiglet import Figlet

logging.basicConfig(filename='client.log', level=logging.DEBUG)

FIGLET_FONT = 'doh'
FIGLET_WIDTH = 256

SOCKET_HOST = "127.0.0.1"
SOCKET_PORT = 8080

STATE_CLOSED = 0
STATE_OPEN = 1

class NetworkException(Exception):
    pass

def network_trycatch(reqtype):
    def decorator(fn):
        def inner():
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as conn:
                    conn.connect((SOCKET_HOST, SOCKET_PORT))
                    fn(conn)
            except OSError as e:
                logging.warning(str(e))
            except Exception as e:
                logging.warning(str(e))
        return inner
    return decorator

def timestamp():
    return int.to_bytes(time().__trunc__(), 8, 'little')

@network_trycatch("open")
def send_open_request(conn=None):
    logging.info("client sent open request")
    conn.sendall(b"Hello, World! I'm open!\n")


@network_trycatch("close")
def send_close_request(conn=None):
    logging.info("client sent close request")
    conn.sendall(b"Hello, World! I'm closed.\n")


"""
        TODO
    ************
    * bold     *
    * color    *
    * requests *
    ************
"""

def main(win):
    logging.info("client init")
    fig = Figlet(font=FIGLET_FONT, width=FIGLET_WIDTH)
    state = STATE_CLOSED
    win.clear()
    win.nodelay(0)
    win.addstr("Any key to toggle, Control-c to quit")
    win.refresh()
    while True:          
        try:                 
            key = win.getch()         
            win.clear()
            if state == STATE_CLOSED:
                send_open_request()
                banner = fig.renderText('The Lab is\nOPEN :)'.strip())
            elif state == STATE_OPEN:
                send_close_request()
                banner = fig.renderText('The Lab is\nCLOSED :('.strip())
            try:
                win.addstr(banner)
            except Exception as e:
                logging.warning(str(e))
            state ^= 1
        except KeyboardInterrupt:
            logging.info("client exit")
            return

if __name__ == '__main__':
    curses.wrapper(main)
