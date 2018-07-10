import os, io, sys, time, datetime, subprocess, threading, logging


import docker

logger = logging.getLogger(__name__)

VICTIM_CONTAINER_NAME="whaler_victim"

#
# 
class VictimFileSystemWatcher(threading.Thread):
	
	def __init__(self, incidentManager, hostCli):
		logger.info("Initialising VictimFileSystemWatcher")
		threading.Thread.__init__(self)
		self.stopped = threading.Event()
		self.daemon = True
		self.hostCli = hostCli
		self.incidentManager = incidentManager
		self.initialChangedFiles = self.getChangedFilesAndDirectories()
		logger.info("Baselined intial changed files set [%s files]" % len(self.initialChangedFiles))

	def run(self):
		logger.info("Started VictimFileSystemWatcher")
		while not self.stopped.wait(5):
			try:
				diffs = self.getChangedFilesAndDirectories()
				
				newFiles=[]
				for diff in diffs:
					if diff not in self.initialChangedFiles and not diff.startswith("/run/docker/"):
						newFiles.append(diff)
				
				if newFiles:
					logger.info("new files %s" % newFiles)
					self.incidentManager.reportVictimFsChanges(newFiles)
				
			except Exception as e:
					logger.error("Lost connection, retrying in 60s...[%s]" % e)


	def stop(self):
		self.stopped.set()
	
	def getChangedFilesAndDirectories(self):
		result=[]
		victimContainer=self.hostCli.containers.get(VICTIM_CONTAINER_NAME)
		diffs=victimContainer.diff()
		
		for diff in diffs:
			result.append(diff['Path'])
		
		return result

		


		
