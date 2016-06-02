Seclab Bot Protocol
===================

1. Establish TLS connection
2. Send OPEN/CLOSE message


**Message Spec**

The client will use python ssl to establish a TLS1.2 session with the server. It will use a custom SSL context which pins thewhitehat.club SSL certificate.
(TODO: Modify thewhitehat.club Let's Encrypt certificate rotation script to also update the pinned cert, somehow)

The client will receieve a 256-bit key K from the server.

The client will send the following message:

```
  open (0xFF) | close (0x00)  (1 byte) (sanity check, because "change state" is really the only required message)
  timestamp                   (4 bytes)
```

The message will be encrypted using python cryptography.fernet which uses AES-128-CBC, PKCS#7 padding, and HMAC-SHA256.
