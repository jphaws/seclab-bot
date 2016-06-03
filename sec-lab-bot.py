#!/usr/bin/env python3


import sys
import ssl
import hmac
import time
import curses
import socket
import logging
from pyfiglet import Figlet


LOG_FILE = './client.log'

logging.basicConfig(filename=LOG_FILE, level=logging.DEBUG)


FIGLET_FONT = 'doh'
FIGLET_WIDTH = 256

fig = Figlet(font=FIGLET_FONT, width=FIGLET_WIDTH)


OPEN_BANNER = fig.renderText('The Lab is\nOPEN :)'.strip())
CLOSE_BANNER = fig.renderText('The Lab is\nCLOSED :('.strip())


SOCKET_HOST = "127.0.0.1"
SOCKET_PORT = 8080


STATE_CLOSED = 0
STATE_OPEN = 1


DEBUG = True if SOCKET_HOST in ["localhost", "127.0.0.1"] else False


SSL_CIPHER_LIST = "AES256:AESCCM:AESGCM:CHACHA20:SUITEB128:SUITEB192" if not DEBUG else "ALL"

SSL_CA_FILE = './pinned.pem'


def ssl_wrap_socket(sock):
    """ Takes a socket, spits out an SSL-enabled socket, using horrible security if connecting to localhost (testing) """
    context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    if DEBUG:
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
    else:
        context.verify_mode = ssl.CERT_REQUIRED
        context.check_hostname = True
        context.verify_flags = ssl.VERIFY_CRL_CHECK_CHAIN | ssl.VERIFY_CRL_CHECK_LEAF | ssl.VERIFY_X509_STRICT
        context.load_verify_locations(capath=SSL_CA_FILE)
    context.set_ciphers(SSL_CIPHER_LIST)
    return context.wrap_socket(sock, server_hostname=SOCKET_HOST)


def ssl_request(reqtype):
    """ Takes a request type (open/close) and returns a decorator """
    def decorator(fn):
        """ Takes a function and calls it, wrapped in try/catch, given an SSL connection """
        def inner():
            try:
                with ssl_wrap_socket(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as conn:
                    conn.connect((SOCKET_HOST, SOCKET_PORT))
                    fn(conn)
            except Exception as e:
                logging.warning(log(str(e)))
        return inner
    return decorator


def timestamp():
    """ 8-byte timestamp for the request (for freshness) """
    return int.to_bytes(time().__trunc__(), 8, 'little', signed=True)


def log(s):
    """ Take a string and preprend a local timestamp for logging """
    return "[" + time.asctime() + "] " + s


@ssl_request("open")
def send_open_request(conn=None):
    """ Send an 'OPEN' request to the server """
    logging.info(log("client sent open request"))
    conn.sendall(log("Hello, World! I'm open!\n").encode())


@ssl_request("close")
def send_close_request(conn=None):
    """ Send a 'CLOSE' request to the server """
    logging.info(log("client sent close request"))
    conn.sendall(log("Hello, World! I'm closed.\n").encode())


def main(win):
    """ ncurses loop, banner generation """
    logging.info(log("client init"))

    state = STATE_CLOSED

    # ncurses init
    win.clear()
    curses.curs_set(0)
    win.nodelay(0)
    win.addstr("Any key to toggle, Control-c to quit")
    win.refresh()
    
    while True:          
        try:                 
            key = win.getch() # block for keypress
            win.clear()
            if state == STATE_CLOSED:
                send_open_request()
                try:
                    win.addstr(OPEN_BANNER, curses.A_BOLD)
                except Exception as e:
                    logging.warning(str(e))
            elif state == STATE_OPEN:
                send_close_request()
                try:
                    win.addstr(CLOSE_BANNER, curses.A_BOLD)
                except Exception as e:
                    logging.warning(str(e))

            state ^= 1

        except KeyboardInterrupt:
            logging.info(log("client exit"))
            return


if __name__ == '__main__':
    curses.wrapper(main)
