#!/usr/bin/python
import datetime, time, logging, json

from FingerprintService import FingerprintService
from CaptureContainer import CaptureContainer
from VictimContainer import VictimContainer
from LoggingContainer import LoggingContainer

logger = logging.getLogger(__name__)

WHALER_DATA_OUTPUT_FOLDER="/tmp/whaler/"
CONTAINER_KILL_DELAY_SECS=10
FUZZY_MATCH_THRESHOLD=85

class IncidentManager():
	
	def __init__(self, hostCli, victimCli):
		
		self.victimCli = victimCli
		self.hostCli = hostCli
		self.fingerprintService=FingerprintService()
		

	def run(self):
		logger.info("Starting IncidentManager")
		
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
		
		
		
