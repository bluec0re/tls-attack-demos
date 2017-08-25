#!/bin/bash

docker run --rm -p2001:2001 --network docker2 -v "$PWD/scripts:/shared" ssl-demos-server
#docker run --rm --network docker2 -v "$PWD/scripts:/shared" ssl-demos-server
