#!/usr/bin/python
import datetime, time, logging, os, json

import docker

from modules.FingerprintService import FingerprintService
from modules.CaptureContainer import CaptureContainer
from modules.VictimContainer import VictimContainer
from modules.LoggingContainer import LoggingContainer
from modules.Configuration import Configuration

logger = logging.getLogger(__name__)

class Whaler():
	
	def __init__(self):
		logger.info("Initialising Whaler")
		self.victimCli=docker.DockerClient(base_url=Configuration().get("dockerDaemonVictimUrl"))
		self.hostCli=docker.DockerClient(base_url=Configuration().get("dockerDaemonHostUrl"))
		self.fingerprintService=FingerprintService()
		self.reports=self.loadReports()
		

	def run(self):
		logger.info("Starting Whaler")
		
		self.victimContainer=VictimContainer()
		self.captureContainer=CaptureContainer()

		self.victimContainer.redeployContainer()
		self.victimContainer.resetBaselineFileChanges()
		
		self.captureContainer.redeployContainer()

		self.loggingContainer=LoggingContainer()
		self.loggingContainer.redeployContainer()
		
		self.victimContainer.listen(self)


	def onStart(self, container):
		#let the container run for some time, to generate evidence
		logger.info("New container reported [%s] image %s will terminate in [%s] seconds" % (container.name,
										container.image.tags,
										Configuration().get("maliciousContainerRunDurationSeconds")))
		
		outputFolder= "%s/%s/%s/%s/%s" % (	Configuration().get("dataDirectory"), 
											datetime.datetime.now().strftime('%Y%m%d'), 
											datetime.datetime.now().strftime('%H%M'),
											container.image.tags[0],
											container.name)
		if not os.path.exists(outputFolder): os.makedirs(outputFolder)

		time.sleep(Configuration().get("maliciousContainerRunDurationSeconds"))
		self.victimContainer.stopContainer(container)

		#get report
		report=self.getReport(container)
		self.saveReport(report)

		if self.fingerprintService.isKnownContainer(report['fingerprint']):
			logger.info("Found fingerprint match, will not archive container, or pcap")

			self.victimContainer.redeployContainer()
			self.captureContainer.redeployContainer()
		else:
			#New attack -snapshot container(s) and pcap
			
			self.victimContainer.snapshotContainer(container, outputFolder+"/snapshots")
			self.captureContainer.archiveCaptureFile(container, outputFolder)

			#restart capture container and save pcap
			self.victimContainer.snapshotVictimContainer(outputFolder)
			self.victimContainer.redeployContainer()
			self.captureContainer.redeployContainer()
		
		self.victimCli.volumes.prune()
		self.hostCli.volumes.prune()

	def getReport(self, container):

		changedFiles=self.victimContainer.getFileSystemDifferencesFromBaseline()
		logger.debug("identifed changed file set as %s" % changedFiles)

		#check fingerprints - match explicitly, or use fuzzy logic for dynamic scripts / filenames
		fingerprint=self.fingerprintService.getFingerprint(container, changedFiles)
	
		#get Pcap summary
		pcapReport=self.captureContainer.getPcapFileReport(container.name)
		
		#form report
		report={'containerName': container.name,
	   		'timestamp': datetime.datetime.now().isoformat(), 
			'fingerprint': fingerprint,
			'pcapReport': pcapReport}
		
		logger.info("Report: %s" % report)
		return report

	def loadReports(self):
		reportFolder= Configuration().get("reportFolder")
		if not os.path.exists(reportFolder): os.makedirs(reportFolder)
		
		if os.path.exists(reportFolder + '/reports.json'):
			with open(reportFolder + '/reports.json') as json_data_file:
					reports = json.load(json_data_file)
		else:
			reports=[]
		
		return reports

	def saveReport(self, report):
		reportFolder= Configuration().get("reportFolder")
		self.reports.append(report)
		
		with open(reportFolder + '/reports.json', 'w') as outfile:
			json.dump(self.reports, outfile)

if __name__ == '__main__':
		Whaler().run()