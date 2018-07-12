#!/usr/bin/python
import datetime, time, logging

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
		

	def run(self):
		logger.info("Starting Whaler")
		
		self.victimContainer=VictimContainer()
		self.victimContainer.redeployContainer()
		self.victimContainer.resetBaselineFileChanges()

		self.captureContainer=CaptureContainer()
		self.captureContainer.redeployContainer()

		self.loggingContainer=LoggingContainer()
		self.loggingContainer.redeployContainer()

		self.victimContainer.listen(self)


	def onStart(self, container):
		#let the container run for some time, to generate evidence
		logger.info("New container reported [%s] will terminate in [%s] seconds" % (container.name, 
										Configuration().get("maliciousContainerRunDurationSeconds")))
		
		outputFolder= "%s/%s/%s/%s/%s" % (	Configuration().get("dataDirectory"), 
											datetime.datetime.now().strftime('%Y%m%d'), 
											datetime.datetime.now().strftime('%H%M'),
											container.image.tags[0],
											container.name)


		time.sleep(Configuration().get("maliciousContainerRunDurationSeconds"))
		self.victimContainer.stopContainer(container)

		changedFiles=self.victimContainer.getFileSystemDifferencesFromBaseline()

		logger.debug("identifed changed file set as %s" % changedFiles)

		#check fingerprints - match explicitly, or use fuzzy logic for dynamic scripts / filenames
		if self.fingerprintService.isKnownContainer(container, changedFiles):
			logger.info("%s" % {	'timestamp': datetime.datetime.now().isoformat(), 
									'source': 'Whaler', 
									'action': 'AttackDetected', 
									'fingerPrintStatus':'Matched',
									'fingerprint': self.fingerprintService.getFingerprint(container, changedFiles)
								}
			)
			logger.info("Found fingerprint match, will not archive container, or pcap")
			self.victimContainer.redeployContainer()
			self.captureContainer.redeployContainer()
		else:
			logger.info("%s" % {	'timestamp': datetime.datetime.now().isoformat(), 
									'source': 'Whaler', 
									'action': 'AttackDetected', 
									'fingerPrintStatus':'UnMatched',
									'fingerprint': self.fingerprintService.getFingerprint(container, changedFiles)
								}
			)
			#New attack -snapshot container(s) and pcap
			self.victimContainer.snapshotContainer(container, outputFolder+"/snapshots")
			self.captureContainer.archiveCaptureFile(outputFolder)

			#restart capture container and save pcap
			self.victimContainer.snapshotVictimContainer(outputFolder)
			self.victimContainer.redeployContainer()
			self.captureContainer.redeployContainer()	
		
if __name__ == '__main__':
		Whaler().run()