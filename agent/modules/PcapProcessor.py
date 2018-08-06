import logging, json, re, sys, datetime

from Configuration import Configuration

from scapy.all import *

from geoip import geolite2

logger = logging.getLogger(__name__)

class PcapProcessor:

    def __init__(self, containerName, pcapFilePath):
        self.containerName = containerName
        self.pcapFilePath=pcapFilePath

    def setAttackerIP(self, packet):
        self.attackerIp=packet[IP].src
    
    def addContactedIps(self, packet):
        if self.scanningDetected or not IP in packet:
            return
        if not packet[IP].dst in self.contactedIps:
            self.contactedIps[packet[IP].dst]= {}
           
            if len(self.contactedIps.keys()) >= 100:
                self.scanningDetected = True
    
    def addDns(self, packet):
        if packet.haslayer(DNSRR):
            for i in range(packet[DNS].ancount):
                dnsrr=packet[DNS].an[i]
                self.dnsRecords[dnsrr.rdata]=dnsrr.rrname[:-1]
                

    def isScanningDetected(self):
        return self.scanningDetected

    def getSummaryReport(self):

        self.attackerIp="UNKNOWN"
        self.dnsRecords={}
        self.contactedIps={}
        report={'reportTimestamp': datetime.now().isoformat(),
                    'containerName': self.containerName,
                    'attackerIp': self.attackerIp,
                    'dnsQueries': self.dnsRecords,
                    'contactedIps': self.contactedIps
        }

        logger.debug("Loading and parsing file %s...." % self.pcapFilePath)
        
        #determine attacker
        sniff(offline=self.pcapFilePath, filter="(dst net 172 and dst port 2375) and not src net 172", prn=lambda x: self.setAttackerIP(x), store=0)
        report['attackerIp'] = self.attackerIp

        #get dns records
        sniff(offline=self.pcapFilePath, filter="port 53", prn=lambda x: self.addDns(x), store=0)
        
        #get contacted IPs (outbound comms)
        self.scanningDetected=False
        sniff(offline=self.pcapFilePath, filter="dst net not 172 and tcp or udp", prn=lambda x: self.addContactedIps(x), stop_filter=lambda x: self.isScanningDetected(), store=0)
        
        for ipAddress in self.contactedIps.keys():
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
            
            #remove noise from docker and dns
            if ipAddress in ['8.8.8.8','8.8.4.4']:
                del(self.contactedIps[ipAddress])
            elif self.contactedIps[ipAddress]['domain'].endswith('docker.com'):
                del(self.contactedIps[ipAddress])
                del(self.dnsRecords[ipAddress])
            elif self.contactedIps[ipAddress]['domain'].endswith('docker.io'):
                del(self.contactedIps[ipAddress])
                del(self.dnsRecords[ipAddress])

        for dnsRecord in self.dnsRecords.keys():
            if self.dnsRecords[dnsRecord].endswith('docker.com') or self.dnsRecords[dnsRecord].endswith('docker.io'):
                del(self.dnsRecords[dnsRecord])

        return report
                
                    
if __name__ == "__main__":
    fileName=sys.argv[1]
    print "loading file %s" % fileName
    report = PcapProcessor('test_container', fileName).getSummaryReport()
    strReport = json.dumps(report, sort_keys=True,indent=4)
    print strReport

