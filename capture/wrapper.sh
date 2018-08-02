#!/bin/sh
sleep 1;
if [ -z $1 ]
then
    echo capture paused, waiting for full initialisation...
    sleep 120
    exit 1
else
    echo starting capture with args $@
    /usr/sbin/tcpdump $@
fi