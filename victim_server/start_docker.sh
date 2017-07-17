#!/bin/bash

docker run --rm -p2000:2000 -v "$PWD/scripts:/shared" ssl-demos-server
