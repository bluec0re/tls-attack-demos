#!/bin/bash

#docker run --rm -v "$PWD/scripts:/shared" --network docker1 ssl-demos-client 'curl -v3k https://172.10.1.1:2000/AAAAAAAAAAAAAA --ciphers AES128-SHA -b SESSION=40f37b6e-5a12-46a2-9b16-61fa5ffca10f -d BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB -A POODLE/DEMO'
docker run --rm -v "$PWD/scripts:/shared" --network docker1 ssl-demos-client /usr/bin/python3 /shared/poodle.py
