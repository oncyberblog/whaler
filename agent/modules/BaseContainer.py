import os, datetime, logging, hashlib

import docker

logger = logging.getLogger(__name__)

class BaseContainer:
	
	def __init__(self, cliUrl, containerName):
		self.firstRun=True
		self.cli = self.getCli(cliUrl)
		self.containerName=containerName
		self.container=self.getContainer()
		self.baselineChangedFiles = []
	
	def deployContainer(self):
		self.container=self.getContainer()

	def getCli(self, url):
		return docker.DockerClient(base_url=url)

	def getContainer(self, containerName=None):
		if not containerName: 
			containerName = self.containerName
		try:
			logger.debug("Getting container [%s] " % containerName)
			return self.cli.containers.get(containerName)

		except Exception as e:
			if not self.firstRun:
				logger.warn("unable to get container [%s] error[%s]" % (containerName, e))	
			return None

	def stopContainer(self, targetContainer=None):
		if targetContainer: 
			container=targetContainer
		else:
			container=self.container

		if container:
			try:
				container.stop()
				container.wait()
				logger.info("Stopped container [%s]" % container.name)
			except Exception as e:
				logger.info("Unable to stop container - likely removed /completed already")
		else:
			if not self.firstRun:
				logger.warn("Could not stop container, has it been initialised?")

	def removeContainer(self):
		if not self.container:
			if not self.firstRun:
				logger.warn("Could not remove container, has it been initialised?")
			self.firstRun=False
			return

		try:
			logger.debug("Removing container [%s]" % self.containerName)
			self.container.stop()
			self.container.remove(force=True)
			self.container=None
			logger.info("removed cotaniner [%s]" % self.containerName)
			self.cli.volumes.prune()
		
		except docker.errors.NotFound:
			if not self.firstRun:
				logger.warn("container [%s] not found to remove" % self.containerName)
		
		except Exception as e:
			logger.error("Unable to kill / remove container [%s]" % e)
		
		self.firstRun=False
	

	def redeployContainer(self):
		self.removeContainer()
		self.deployContainer()

	def snapshotContainer(self, container, filePath):
		logger.info("Snapshotting image and container for [%s] to [%s]" % (container.name, filePath))

		if not os.path.exists(filePath): os.makedirs(filePath)
		
		try:
			image=container.image
			outputFile=filePath + '/IMG_' + container.name + '-' + container.id + '.tar'
			f = open(outputFile, 'w')

			for chunk in image.save():
				f.write(chunk)
			f.close()

			logger.debug("{'timestamp':'%s', source':'BaseContainer', 'action':'SavedContainerImage', 'containerId':'%s', 'imageId':'%s', 'file':'%s'}" % (datetime.datetime.now().isoformat(),container.id,image.tags,outputFile))
		except Exception as e:
			logger.info("Failed to save image for container [%s]" % container.name)
		
		try:
			outputFile=filePath + '/CNT_' + container.name + '-' + container.id + '.tar'
			f = open(outputFile, 'w')

			for chunk in container.export():
				f.write(chunk)
			f.close()
			logger.debug("{'timestamp':'%s', source':'BaseContainer', 'action':'SavedContainer', 'containerId':'%s', 'imageId':'%s', 'file':'%s'}" % (datetime.datetime.now().isoformat(),container.id,image.tags,outputFile))
		except Exception as e:
			logger.info("Failed to save container for [%s]" % container.name)

	def resetBaselineFileChanges(self):
		self.baselineChangedFiles = self.getAllFileSystemChanges()
		
	def getAllFileSystemChanges(self):
		if not self.container:
			logger.warn("Could not baseline changed files for container [%s], has container been initialised?" % self.containerName)
			return
	
		result=[]
		for diff in self.container.diff():
			result.append(diff['Path'])
		return result
	
	def getFileSystemDifferencesFromBaseline(self):
		diffs = self.getAllFileSystemChanges()
			
		newFiles=[]
		for diff in diffs:
			if diff not in self.baselineChangedFiles and not diff.startswith("/run/docker/"):
				newFiles.append(diff)
		
		return newFiles