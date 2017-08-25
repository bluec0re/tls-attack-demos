#!/bin/bash

docker build . --tag ssl-demos

cd victim_server
docker build . --tag ssl-demos-server

cd ../victim_client
docker build . --tag ssl-demos-client
