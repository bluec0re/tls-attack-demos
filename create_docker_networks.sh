#!/bin/bash

docker network create --driver=bridge --subnet=172.10.1.0/24 --ip-range=172.10.1.0/24 --gateway=172.10.1.1 docker1
docker network create --driver=bridge --subnet=172.10.2.0/24 --ip-range=172.10.2.0/24 --gateway=172.10.2.1 docker2
