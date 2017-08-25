#!/bin/bash

docker network rm docker1
docker network rm docker2

 docker network create --opt='com.docker.network.bridge.name=docker1' --driver=bridge --subnet=172.10.1.0/24 --ip-range=172.10.1.0/24 --gateway=172.10.1.1 docker1
 docker network create --opt='com.docker.network.bridge.name=docker2' --driver=bridge --subnet=172.10.2.0/24 --ip-range=172.10.2.0/24 --gateway=172.10.2.1 docker2
