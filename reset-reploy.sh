#!/bin/bash
sudo rm -rf /var/tmp/whaler
docker stop $(docker ps -aq); docker rm $(docker ps -aq); docker network prune -f; docker-compose build && docker-compose up $1
sleep 10
tail -f /var/tmp/whaler/whaler.log | grep INFO
