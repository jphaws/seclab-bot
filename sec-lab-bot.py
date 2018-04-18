#!/usr/bin/env python3
""" SecLab Bot client """

import sys
import ssl
import hmac
import time
import curses
import socket
import logging
import hashlib
from base64 import b64decode as b64d, b64encode as b64e
from pyfiglet import Figlet

KEY_FILE = 'files/psk.b64'

LOG_FILE = 'files/client.log'
MAX_LOG_ENTRIES = 1024

FIGLET_FONT = 'doh'
#FIGLET_WIDTH = 256
FIGLET_WIDTH = 154
FIGLET = Figlet(font=FIGLET_FONT, width=FIGLET_WIDTH)
BANNER_OPEN = FIGLET.renderText('Lab is OPEN :)'.strip())
BANNER_CLOSE = FIGLET.renderText('Lab is CLOSED :('.strip())

with open('coffee.txt', 'r') as f:
    coffee = f.read()

BANNER_COFFEE = FIGLET.renderText(('Out for\n').strip()) + coffee

SOCKET_HOST = "thewhitehat.club"
#SOCKET_HOST = "localhost"
SOCKET_PORT = 3737

BYTE_ORDER = 'big'  # endianness

MAX_AGE = 10  # seconds


class SecLabBotException(Exception):
    """ Generic Exception
        for SecLabBot-specific problems
    """
    pass


# Some magic numbers with pre-agreed meanings
# for the server and client, AKA a protocol
FLAG_OPEN_REQ = 0xFF
FLAG_CLOSE_REQ = 0x00
FLAG_KEYGEN_REQ = 0xAA
FLAG_ALL_GOOD = 0xFF
FLAG_KEYGEN_ACK = 0x55
FLAG_COFFEE_REQ = 0xCC

STATE_CLOSED = 0
STATE_OPEN = 1

EXIT_SUCCESS = True
EXIT_FAILURE = False

DEBUG = SOCKET_HOST in ["localhost", "127.0.0.1"]

# Pin TLS and only use good ciphers
SSL_CA_FILE = 'files/pinned.pem'
SSL_CIPHER_LIST =\
 "AESGCM:AESCCM:AES256:SUITEB192:SUITEB128:CHACHA20" if not DEBUG else "ALL"


def read_key_from_file():
    """ Read saved HMACing key """
    try:
        with open(KEY_FILE, 'rb') as key_file:
            return b64d(key_file.read())
    except:
        logging.warning("error reading from key file")


def write_key_to_file(key):
    """ Write new HMACing key """
    try:
        with open(KEY_FILE, 'wb') as key_file:
            key_file.write(b64e(key))
    except:
        logging.warning("error writing to key file")


KEY = read_key_from_file()


def ssl_wrap_socket(sock):
    """ Takes a socket, spits out an SSL-enabled socket
        using horrible security if connecting to localhost (testing)
    """
    context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    if DEBUG:
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
    else:
        context.verify_mode = ssl.CERT_NONE
    context.set_ciphers(SSL_CIPHER_LIST)
    return context.wrap_socket(sock, server_hostname=SOCKET_HOST)


def wire_decode_int(data, sgn=False):
    """ decode bytes to int from the wire """
    return int.from_bytes(data, byteorder=BYTE_ORDER, signed=sgn)


def wire_encode_int(i, size, sgn=False):
    """ encode int to bytes for the wire """
    return i.to_bytes(size, byteorder=BYTE_ORDER, signed=sgn)


def timestamp():
    """ timestamp (to be encoded or compared) """
    return time.time().__trunc__()


def timestamp_bytes():
    """ 8-byte timestamp for the request (for freshness)
         keep at 8 bytes to avoid the 2038 problem
    """
    return wire_encode_int(timestamp(), 8, sgn=True)


def timestamp_verify(tdata):
    """ Validate timestamp freshness """
    return (timestamp() - wire_decode_int(tdata, sgn=True)) <= MAX_AGE


def ssl_request(reqtype):
    """ Takes a request type (open/close/keygen) and makes the request """
    logging.info("client sent " + reqtype + " request")
    try:
        with ssl_wrap_socket(
            socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ) as conn:
            conn.connect((SOCKET_HOST, SOCKET_PORT))
            conn.sendall(make_request(reqtype))
            if reqtype in ["open", "close", "coffee"]:
                if wire_decode_int(conn.recv(1)) != FLAG_ALL_GOOD:
                    raise SecLabBotException("client received bad response")
            elif reqtype in ["keygen"]:
                if wire_decode_int(conn.recv(1)) != FLAG_KEYGEN_ACK:
                    raise SecLabBotException("client received bad response")
                if not timestamp_verify(conn.recv(8)):
                    raise SecLabBotException("client received stale response")
                write_key_to_file(conn.recv(32))
            else:
                raise SecLabBotException("Unknown request type in ssl_request")
        return EXIT_SUCCESS
    except Exception as exc:
        logging.warning(str(exc) + " during " + reqtype + " request")
        return EXIT_FAILURE


def make_request(reqtype):
    """ Creates an HMAC'd request message bytestring """
    data = b""
    val = None
    if reqtype == "open":
        val = FLAG_OPEN_REQ
    elif reqtype == "close":
        val = FLAG_CLOSE_REQ
    elif reqtype == "coffee":
        val = FLAG_COFFEE_REQ
    elif reqtype == "keygen":
        val = FLAG_KEYGEN_REQ
    else:
        logging.error("Unknown request type in make_request")
        raise ValueError
    data += wire_encode_int(val, 1, sgn=False)
    data += timestamp_bytes()
    mac = hmac.new(KEY, msg=data, digestmod=hashlib.sha256)
    data += mac.digest()
    return data


def ncurses_write(win, msg):
    """ Takes an ncurses screen and a string and writes to the screen """
    try:
        win.clear()
        win.addstr(msg, curses.A_BOLD)
    except Exception as exc:
        logging.warning("NCurses exception: " + str(exc))


def main(win):
    """ ncurses loop """
    logging.info("client init")

    state = STATE_CLOSED

    # ncurses init
    win.clear()
    curses.curs_set(0)
    win.nodelay(0)
    win.addstr("Use any key to toggle, or control-c to quit")
    win.refresh()
    success = True

    gotchar = 0

    while True:
        try:
            if not truncate_log():
                return
            ch = win.getch()  # block for keypress
            if time.time() - gotchar < 0.1:
                continue
            if ch == ord('c') and state == STATE_OPEN: # coffee mode
                reqtype = "coffee"
                success = ssl_request(reqtype)
                if success:
                    ncurses_write(win, BANNER_COFFEE)
            elif state == STATE_CLOSED:
                reqtype = "open"
                success = ssl_request(reqtype)
                if success:
                    ncurses_write(win, BANNER_OPEN)
            elif state == STATE_OPEN:
                reqtype = "close"
                success = ssl_request(reqtype)
                if success:
                    ncurses_write(win, BANNER_CLOSE)
            if success:
                logging.info(reqtype + " request success")
                state ^= 1
            else:
                curses.flash()
                curses.beep()
                logging.warning(reqtype + " request failed")
            gotchar = time.time()
        except KeyboardInterrupt:
            logging.info("client exit")
            return


def show_help():
    """ Print help information """
    print("SecLab Bot usage: python3 sec-lab-bot.py [--keygen]")
    print()
    print("The following files are required for operation:")
    print("\tLOG_FILE\t[files/client.log]")
    print("\tKEY_FILE\t[files/psk.b64]")
    print("\tSSL_CERT_FILE\t[files/pinned.pem]")
    print()
    print("The --keygen option will request a new PSK from the server")
    print()
    print("Use any key to toggle open/close, or control-c to quit")


def truncate_log():
    """ Dump the log file if it's gotten too long """
    try:
        with open(LOG_FILE, 'w+') as log_file:
            if len(log_file.readlines()) > MAX_LOG_ENTRIES:
                log_file.write("")
        return True
    except:
        print("Error truncating log file")
        return False


if __name__ == '__main__':
    if "-h" in sys.argv or "--help" in sys.argv:
        show_help()
        sys.exit(0)

    logging.basicConfig(filename=LOG_FILE,
                        format='[%(asctime)s] %(message)s',
                        datefmt='%m/%d/%Y %I:%M:%S %p',
                        level=logging.DEBUG)

    if "--keygen" in sys.argv:
        if ssl_request("keygen"):
            logging.info("Key rotated")
            sys.exit(0)
        else:
            logging.critical("Key rotate failed!")
            sys.exit(1)

    curses.wrapper(main)
    logging.shutdown()
    sys.exit(0)
