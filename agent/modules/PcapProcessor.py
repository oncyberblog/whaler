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

    def processPacket(self, packet):
        print packet.summary()

    def setAttackerIP(self, packet):
        self.attackerIp=packet[IP].src
    
    def addContactedIps(self, packet):
        if self.scanningDetected or not IP in packet:
            return
        if not packet[IP].dst in self.contactedIps:
            self.contactedIps[packet[IP].dst]= {}
           
            if len(self.contactedIps.keys()) >= 100:
                self.scanningDetected = True
                print "set scanning detected %s" % self.scanningDetected
                print self.isScanningDetected()
    
    def addDns(self, packet):
        if packet.haslayer(DNSRR):
                if packet[DNSRR].type ==1: #A record reply
                    self.dnsRecords[packet[DNSRR].rdata]=packet[DNSRR].rrname[:-1]

    def isScanningDetected(self):
        return self.scanningDetected

    def getSummaryReport(self, pcapFilePath):

        self.attackerIp="UNKNOWN"
        self.dnsRecords={}
        self.contactedIps={}
        report={'attackerIp': self.attackerIp,
                    'dnsQueries': self.dnsRecords,
                    'contactedIps': self.contactedIps
        }

        print "Loading and parsing file %s...." % pcapFilePath
        
        #determine attacker
        sniff(offline=pcapFilePath, filter="(dst net 172 and dst port 2375) and not src net 172", prn=lambda x: self.setAttackerIP(x), store=0)
        
        #get dns records
        sniff(offline=pcapFilePath, filter="port 53", prn=lambda x: self.addDns(x), store=0)
        
        #get contacted IPs (outbound comms)
        self.scanningDetected=False
        sniff(offline=pcapFilePath, filter="dst net not 172 and tcp or udp", prn=lambda x: self.addContactedIps(x), stop_filter=lambda x: self.isScanningDetected(), store=0)
        print "contactedIps IP is %s" % self.contactedIps
        
        for ipAddress in self.contactedIps:
            #add geo-location data
            match = geolite2.lookup(ipAddress)
            if match:
                self.contactedIps[ipAddress]['country']=match.country
                self.contactedIps[ipAddress]['continent']=match.continent
                self.contactedIps[ipAddress]['timezone']=match.timezone
                self.contactedIps[ipAddress]['location']=match.location

            if ipAddress in self.dnsRecords:
                self.contactedIps[ipAddress]['domain']=self.dnsRecords[ipAddress]
            else:
                self.contactedIps[ipAddress]['domain']='unknown'

        return report
                
                    
if __name__ == "__main__":
    fileName=sys.argv[1]
    print "loading file %s" % fileName
    report = PcapProcessor().getSummaryReport(fileName)
    strReport = json.dumps(report, sort_keys=True,indent=4)
    print strReport

