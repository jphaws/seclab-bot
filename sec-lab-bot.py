#!/usr/bin/env python3


import sys
import ssl
import hmac
import time
import curses
import socket
import logging
import hashlib
from pyfiglet import Figlet
from base64 import b64decode as b64dec, b64encode as b64enc


KEY_FILE = './psk.b64'


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


OPEN_REQ_FLAG = 0xFF
CLOSE_REQ_FLAG = 0x00
KEYGEN_REQ_FLAG = 0xAA


ALL_GOOD = 0xFF
KEYGEN_ACK = 0x55


EXIT_SUCCESS = 0
EXIT_FAILURE = 1


DEBUG = True if SOCKET_HOST in ["localhost", "127.0.0.1"] else False


SSL_CIPHER_LIST = "AES256:AESCCM:AESGCM:CHACHA20:SUITEB128:SUITEB192" if not DEBUG else "ALL"

SSL_CA_FILE = './pinned.pem'


def read_key_from_file():
    with open(KEY_FILE, 'rb') as f:
        return b64dec(f.read())


def write_key_to_file(key):
    with open(KEY_FILE, 'wb') as f:
        f.write(b64enc(key))


KEY = read_key_from_file()


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
    """ Takes a request type (open/close/keygen) and makes the request """
    logging.info(log("client sent " + reqtype + " request"))
    try:
        with ssl_wrap_socket(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as conn:
            conn.connect((SOCKET_HOST, SOCKET_PORT))
            conn.sendall(make_request(reqtype))
            if reqtype in ["open", "close"]:
                if int.from_bytes(conn.recv(1), 'little') != ALL_GOOD:
                    raise Exception("client received bad response")
            elif reqtype in ["keygen"]:
                data = conn.recv(1)
                if int.from_bytes(data, 'little') != KEYGEN_ACK:
                    logging.warning(log("client received bad response"))
                    return
                tdata = conn.recv(8)
                if time.time().__trunc__() - int.from_bytes(tdata, 'little') > 10000:
                    logging.warning(log("client received stale response"))
                    return
                write_key_to_file(conn.recv(64))
        return EXIT_SUCCESS
    except Exception as e:
        logging.warning(log(str(e) + " during " + reqtype + " request"))
        return EXIT_FAILURE


def timestamp():
    """ 8-byte timestamp for the request (for freshness) """
    return int.to_bytes(time.time().__trunc__(), 8, 'little', signed=True)


def log(s):
    """ Take a string and preprend a local timestamp for logging """
    return "\t[" + time.asctime() + "]\t" + s


def make_request(reqtype):
    data = b""
    val = None
    if reqtype == "open":
        val = OPEN_REQ_FLAG
    elif reqtype == "close":
        val = CLOSE_REQ_FLAG
    elif reqtype == "keygen":
        val = KEYGEN_REQ_FLAG
    data += int.to_bytes(val, 1, 'little', signed=False)
    data += timestamp()
    mac = hmac.new(KEY, msg=data, digestmod=hashlib.sha256)
    data += mac.digest()
    return data


def ncurses_write(win, s):
    try:
        win.addstr(s, curses.A_BOLD)
    except Exception as e:
        logging.warning(str(e))


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
    success = True
    
    while True:          
        try:                 
            key = win.getch() # block for keypress
            win.clear()
            if state == STATE_CLOSED:
                if ssl_request("open") == EXIT_SUCCESS:
                    ncurses_write(win, OPEN_BANNER)
                    success = True
                else:
                    success = False
                    logging.warning(log("open request failed"))
            elif state == STATE_OPEN:
                if ssl_request("close") == EXIT_SUCCESS:
                    ncurses_write(win, CLOSE_BANNER)
                    success = True
                else:
                    success = False
                    logging.warning(log("close request failed"))
            if success:
                state ^= 1

        except KeyboardInterrupt:
            logging.info(log("client exit"))
            return


if __name__ == '__main__':
    if "--init" in sys.argv:
        ssl_request("keygen")
    curses.wrapper(main)
