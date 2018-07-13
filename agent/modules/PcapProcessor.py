import logging

from Configuration import Configuration
from scapy.all import *
from scapy.layers import http

#pip install python-geoip-geolite2
#pip install netaddr

from geoip import geolite2
from netaddr import IPNetwork, IPAddress

import socket

logger = logging.getLogger(__name__)

class PcapProcessor:

    def __init__(self):
        if Configuration.instance:
            pass

    def getHosts(self, pcapFilePath):
        packets = rdpcap(pcapFilePath)
        # Let's iterate through every packet
        externalIps=set([])
        attackerIp=None
        for pkt in packets:
            if IP in pkt:
                ip_src=pkt[IP].src
                ip_dst=pkt[IP].dst
                port_src=pkt[TCP].sport
                port_dst=pkt[TCP].dport

                if (not IPAddress(ip_src) in IPNetwork("172.16.0.0/12")):
                    externalIps.add("%s:%s (%s)" % (ip_src,port_src, self.getHostName(ip_src)))
                if (not IPAddress(ip_dst) in IPNetwork("172.16.0.0/12")):
                    externalIps.add("%s:%s (%s)" % (ip_dst,port_dst, self.getHostName(ip_dst)))

                
                txt= pkt.show(dump=True)
                if port_dst==2375 and 'images/create' in txt:
                    attacherIp=ip_src
                    print pkt.show()
                    #print pkt[Raw].load

            
        print externalIps
        return
        match = geolite2.lookup('52.17.140.163')
        if match:
            print match.country
            print match.continent
            print match.timezone
        print match

    def getHostName(self, ipString):
        #print "lookign up %s" % ipString
        try:
            return socket.gethostbyaddr(ipString)[0]
        except Exception as e:
            return "unknown-host"



pcapProcessor=PcapProcessor()
pcapProcessor.getHosts("/var/tmp/whaler/20180713/1603/hello-world:latest/loving_almeida/capture.pcap")