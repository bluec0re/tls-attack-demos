#!/bin/bash

curl -v3k 'https://172.10.1.1:2000/?AAAAAAAAAAAAA' --ciphers AES256-SHA -b 'SESSION=4b975fad-8512-42f6-9a6c-c92c1e85bba5' -d 'BBBB'
