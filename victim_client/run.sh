#!/bin/bash

docker run --rm -v "$PWD/scripts:/shared" --network docker1 -t -i ssl-demos-client
