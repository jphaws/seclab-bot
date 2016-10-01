Seclab Bot
==========

Making the White Hat Security Club Lab great again

[![Lab Status](https://thewhitehat.club/status.svg)](https://thewhitehat.club/)

Requirements (outside of python3-pip)
-------------------------------------

* libssl-dev (to build cryptography with pip3 install cryptography)

Getting this running
--------------------

1. Install `python3`
2. `pip3 install -r requirements.txt # optionally in a virtualenv`
3. Copy the pre-shared key from the server, placing it in `files/psk.b64`
4. `python3 sec-lab-bot.py`
5. Enjoy
