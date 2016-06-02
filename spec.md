Seclab Bot Protocol
===================

1. Establish TLS connection
2. Send OPEN/CLOSE message


**Message Spec**

The client will use python ssl to establish a TLS1.2 session with the server. It will use a custom SSL context which pins thewhitehat.club SSL certificate.

The client will receieve a 256-bit key K from the server.

The client will send the following message:

```
  IV                          (32 bytes)
  Encrypted:
    open (0xFF) | close (0x00)  (1 byte) (sanity check, because "change state" is really the only required message)
    timestamp                   (4 bytes)
  HMAC                        (32 bytes)
```

Encrypt-then-MAC will be used with a strongly unforgeable hash function for maximal privacy and integrity.

python pycrypto will be used to encrypt the message with AES-256-CFB after generating a 256-bit random IV.

python hmac and hashlib will be used to HMAC the message with SHA256.
