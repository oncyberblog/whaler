#!/usr/bin/python
import datetime, time, logging, json

import docker

from modules.FingerprintService import FingerprintService
from modules.CaptureContainer import CaptureContainer
from modules.VictimContainer import VictimContainer
from modules.LoggingContainer import LoggingContainer

logger = logging.getLogger(__name__)

DOCKER_DAEMON_LOCAL_URL='unix://var/run/docker.sock'
DOCKER_DAEMON_VICTIM_URL='tcp://victim:2375'

WHALER_DATA_OUTPUT_FOLDER="/tmp/whaler/"
CONTAINER_KILL_DELAY_SECS=10
FUZZY_MATCH_THRESHOLD=85

class Whaler():
	
	def __init__(self):
		logger.info("Initialising Whaler")
		self.victimCli=docker.DockerClient(base_url=DOCKER_DAEMON_VICTIM_URL)
		self.hostCli=docker.DockerClient(base_url=DOCKER_DAEMON_LOCAL_URL)
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

		

	def shutdown(self):
		pass


	def getOutputFolder(self, container):
		return WHALER_DATA_OUTPUT_FOLDER + "%s/%s/%s/%s" % (datetime.datetime.now().strftime('%Y%m%d'), datetime.datetime.now().strftime('%H%M'),container.image.tags[0], container.name)

	def onStart(self, container):
		#let the container run for some time, to generate evidence
		logger.info("New container reported [%s] will terminate in [%s] seconds" % (container.name, CONTAINER_KILL_DELAY_SECS))
		
		outputFolder=self.getOutputFolder(container)

		time.sleep(CONTAINER_KILL_DELAY_SECS)
		self.victimContainer.stopContainer(container)

		

		logger.info("output folder is %s" % outputFolder)

		changedFiles=self.victimContainer.getFileSystemDifferencesFromBaseline()

		logger.info("identifed changed file set as %s" % changedFiles)

		#check fingerprints - match explicitly, or use fuzzy logic for dynamic scripts / filenames
		if self.fingerprintService.isKnownContainer(container, changedFiles):

			logger.info("Found fingerprint match, will not archive container, or pcap")
			self.victimContainer.snapshotVictimContainer(outputFolder)
			self.victimContainer.redeployContainer()
			self.captureContainer.redeployContainer()
		else:
			#New attack -snapshot container(s) and pcap
			self.victimContainer.snapshotContainer(container, outputFolder+"/snapshots")
			self.captureContainer.archiveCaptureFile(outputFolder)

			#restart capture container and save pcap
			self.victimContainer.snapshotVictimContainer(outputFolder)
			self.victimContainer.redeployContainer()
			self.captureContainer.redeployContainer()	
		
if __name__ == '__main__':
		Whaler().run()