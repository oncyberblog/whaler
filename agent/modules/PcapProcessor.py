import logging, json, re, sys

from Configuration import Configuration
from scapy.all import *


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

    def getDns(self, packets):
        dnsRecords={}
        for pkt in packets:
            if pkt.haslayer(DNSRR):
                if pkt[DNSRR].type ==1: #A record reply
                    dnsRecords[pkt[DNSRR].rdata]=pkt[DNSRR].rrname[:-1]
                    #print "%s = %s" % (pkt[DNSRR].rdata, dnsRecords[pkt[DNSRR].rdata])
        return dnsRecords
    
    def isLocalIp(self, ipString):
        if (IPAddress(ipString) in IPNetwork("172.16.0.0/12")):
            return True
    
    def isDnsIp(self, ipString):
        if (IPAddress(ipString) in IPNetwork("8.8.0.0/16")):
            return True

    def isFiltered(self, srcIp, dstIp, dnsRecords):
        if self.isDnsIp(srcIp) or self.isDnsIp(dstIp):
            #DNS
            return True
        if self.isLocalIp(srcIp) and self.isLocalIp(dstIp):
            #LOCAL <> LOCAL traffic
            return True
        if srcIp in dnsRecords:
            if ".docker.io" in dnsRecords[srcIp] or ".docker.com" in dnsRecords[srcIp]:
                return True
        if dstIp in dnsRecords:
            if ".docker.io" in dnsRecords[dstIp] or ".docker.com" in dnsRecords[dstIp]:
                return True
        return False

    def filterPackets(self, packets, dnsRecords):
        filteredPackets=[]
        for pkt in packets:
            if IP in pkt:
                #print "%s" % pkt.show()
                srcIp=pkt[IP].src
                dstIp=pkt[IP].dst
                if not self.isFiltered(srcIp, dstIp, dnsRecords):
                    filteredPackets.append(pkt)

        return filteredPackets  


    def getAttackerIp(self, packets, dnsRecords):
        attackerIp="UNKNOWN_IP"
        for pkt in packets:
            if TCP in pkt and pkt[TCP].dport==2375 and not self.isFiltered(pkt[IP].src, pkt[IP].dst, dnsRecords):
                attackerIp=pkt[IP].src
        return attackerIp

    def getSummaryReport(self, pcapFilePath):
        
        packets = rdpcap(pcapFilePath)

        dnsRecords=self.getDns(packets)
        packets = self.filterPackets(packets, dnsRecords)

        # get the Attacker IP address
        attackerIp = self.getAttackerIp(packets, dnsRecords)
        print "attacker ip is %s " % attackerIp
        
        contactedIps={}
        report={'attackerIp': attackerIp,
                    'dnsQueries': dnsRecords,
                    'contactedIps': contactedIps
        }

        for pkt in packets:
            if IP in pkt:
                srcIp=pkt[IP].src
                dstIp=pkt[IP].dst
                
                if srcIp not in contactedIps and not self.isLocalIp(srcIp):
                    contactedIps[srcIp]= {}
                if dstIp not in contactedIps and not self.isLocalIp(dstIp):
                    contactedIps[dstIp]= {}

        for ipAddress in contactedIps:
            #add geo-location data
            match = geolite2.lookup(ipAddress)
            if match:
                contactedIps[ipAddress]['country']=match.country
                contactedIps[ipAddress]['continent']=match.continent
                contactedIps[ipAddress]['timezone']=match.timezone
                contactedIps[ipAddress]['location']=match.location

            if ipAddress in dnsRecords:
                contactedIps[ipAddress]['domain']=dnsRecords[ipAddress]
            else:
                contactedIps[ipAddress]['domain']='unknown'

        return report
                
                    
if __name__ == "__main__":
    fileName=sys.argv[1]
    print "loading file %s" % fileName
    report = PcapProcessor().getSummaryReport(fileName)
    strReport = json.dumps(report, sort_keys=True,indent=4)
    print strReport

