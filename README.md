# TLS Attack Demos


This repository is a WIP framework which implements different SSL/TLS attacks to
show the feasibility in practise.

Currently implemented:

- BREACH
- POODLE

## Requirements

- Python 3
- Docker
- scapy-python3
- Patched scapy-ssl_tls

## How to run

1. Create the networks: ./create_docker_networks.sh
2. Build the docker images: ./build.sh
3. Start the server image: cd victim_server && ./start_docker.sh
4. Run one of the samples:

### BREACH

1. As a setup.py is currently missing: export PYTHONPATH="."
2. ./scripts/ssl-demos.py -u &lt;target url&gt; -p &lt;port to capture&gt; -i &lt;ip address to capture&gt; -b &gt;cookies to sent in the victim request&gt; -I &lt;interface to capture&gt; Breach -t &lt;token to guess&gt; -P &gt;prefix for the attack&gt;

Parameter | Description | Example
--------- | ----------- | -------
target url | A url to a webpage which uses HTTP compression and reflects GET parameters. {DATA} will be replaced by the attack string. | https://127.0.0.1:2001?affiliate={DATA}
port to capture | The port the webserver listens on. Will be used as a pcap filter | 2001
ip address to capture | The ip address of the webserver. Will be used as a pcap filter | 127.0.0.1
cookies to sent in the victim request | The cookies which will be sent by the victim simulator. Required to provide sessions | SESSION=0372e249-7932-41ba-8dbb-6e79e991c8e7
prefix for the attack | A prefix of a place where the to be guessed secret is located. Required to increase the compression probabilty | input type="hidden" name="csrftoken" value="
token to guess | The secret we want to guess. Allows to show better status messages. The guessing algorithm does not use it in any way | 9f0fea5a00946a9a4c606178d85a6464018bc140
interface to capture | The interface we want to capture on | lo

Breach in action:
[![asciicast](https://asciinema.org/a/WxvNaYmETlQ5v2cw2B5qtCPnP.png)](https://asciinema.org/a/WxvNaYmETlQ5v2cw2B5qtCPnP)

### Poodle

1. Export the privkey.pem from the server image (for visualization): docker exec &lt;container&gt; cat privkey.pem > victim_server/privkey.pem
2. As a setup.py is currently missing: export PYTHONPATH="."
3. ./scripts/ssl-demos.py -p &lt;port to capture&gt; -i &lt;ip address of the server&gt; -I &lt;interface 1&gt; Poodle -I2 &lt;interface 2&gt;
4. Start the victim client: cd victim_client && ./poodle.sh

Parameter | Description | Example
--------- | ----------- | -------
port to capture | The port the webserver listens on. Will be used as a pcap filter | 2000
ip address of the server | The ip address of the webserver. Will be used in the MitM | 172.10.2.2
interface 1 | The first interface | docker1
interface 2 | The second interface | docker2
