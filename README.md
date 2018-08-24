# Whaler

Whaler is a Docker Daemon honeypot / sandbox. It exposes an insecure Docker Daemon API with the intention of attracting and capturing attempts to run malicious containers.
 
Whaler runs entirely in Docker and at the heart of the solution is a Docker in Docker (DinD) container which serves as the honeypot.

## Notes

Whaler should be run on an isolated server (e.g. Cloud) and assume that a sophisticated hacker will be able to trivially bypass the Docker container to obtain root on the server.

The honeypot can be set up for remote Docker logging, and the compose file allows for easy integration with a free logz.io account. Note, do not connect a paid for account as this can also be easily abused should the attacker comprimise the host machine and bust your logging budget!

## Overview of deployment

Whaler is run as a single docker-compose stack, which consists of the following containers:

### victim
A Docker in Docker container, with an insecure Daemon exposed on port 2375. No containers are deployed. Due to the requirements for DinD, this container must run as privileged, and hence the assumption the host can be easily compromised (should the attacker realise the "host" is actually another container!). 

### agent 
The controller performs the following key functions:
remotely monitors the victim container for Docker events via the Docker API on port 2375
 - it logs full details of the container being started, including startup command and parameters
 - captures all traffic into and out of the victim container, producing a simple summary report
 - stops the container after a configurable delay (30 seconds)
 - performs a 'diff' against the original DinD image to help identify container escape attempts 
 - creates a tar archive of the DinD and malicious containers and images in the host folder
 - resets the system for the next attack

 Events and information are logged to stdout, for collection by the logging container and visualisation in Logz.io 

### capture
Runs a tcpdump to capture a series of rolling pcap files from the victim container interface for future analysis. Currently hard coded to store up to 500MB files on a rotating basis.

### logging
provides a simple docker integration with logz.io so key data from the hosts can be logged to ELK for analysis.

## Installation
This is a PoC and use of this is at your own risk.

Installation has been tested on Ubuntu 16.04 and steps below may need to be modified for other servers.

To collect logs using logz.io, register a free account and obtain your API key from the portal.

First launch a new cloud based Ubuntu image, for example in Azure or AWS. Ensure firewall rules permit inbound traffic on ports 22 (for SSH) and 2375 (for our vulnerable Docker Daemon). Ensure this is in an isolated VPC / subnet and has no IAM roles / access over other cloud based resources you may have.

SSH into your new server and execute the following:

```
curl https://raw.githubusercontent.com/oncyberblog/whaler/master/get-whaler.sh | sudo sh

```

The server will reboot once complete, next log back in and `cd whaler`.

set your logz.io key and environment with

```
export LOGZIO_TOKEN=<API KEY>
export LOGZIO_ENV=whaler
```

reset and re-deploy the solution:

```
./reset-redeploy -d
```

Logs should start shipping within a few minutes. You can test the setup by accessing the Daemon remotely from another machine with docker installed:

```
docker -H=<IP address of your Whaler server> run hello-world
```

You will see corresponding events in logz.io and note the container and image is archived to /tmp on the honeypot server.

