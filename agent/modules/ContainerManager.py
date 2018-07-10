import os, io, sys, time, datetime, subprocess, threading, sched, shutil, logging

import docker

logger = logging.getLogger(__name__)

CAPTURE_CONTAINER_NAME="whaler_capture"
CAPTURE_IMAGE_NAME="marsmensch/tcpdump"

LOGGING_CONTAINER_NAME="whaler_logging"
LOGGING_IMAGE_NAME="logzio/logzio-docker"

WHALER_NETWORK_NAME="whaler_default"

WHALER_DATA_OUTPUT_FOLDER="/tmp/whaler/"

#
# 
class ContainerManager():
	
	def __init__(self, incidentManager, hostCli, victimCli):
		logger.info("Initialising ContainerManager")
		self.victimCli = victimCli
		self.hostCli = hostCli
		self.containers={}
		self.incidentManager = incidentManager

	def stopContainer(self, container):
		logger.info("Stopping container %s" % container.name)
		container.stop()
	
	def XXXarchiveCaptureFiles(self, pCapFileStoragePath):
		try:
			shutil.copyfile(WHALER_DATA_OUTPUT_FOLDER + "/capture/capfile", pCapFileStoragePath + "/capture.pcap")
			logger.info("Saved Pcap file(s) to %s/capture.pcap" % pCapFileStoragePath)
		except Exception as e:
			logger.error("Error archiving capture file [%s]" % e)

	def XXXdeployNewCaptureContainer(self):
		self.removeContainer(self.hostCli, CAPTURE_CONTAINER_NAME)
		self.addCaptureContainer()

	def deployNewLoggingContainer(self):
		self.removeContainer(self.hostCli, LOGGING_CONTAINER_NAME)
		self.addLoggingContainer()	

	def XXXaddCaptureContainer(self):
		try:
			logger.info("Deploying new Capture container [%s]" % CAPTURE_CONTAINER_NAME)
			container = self.hostCli.containers.run(	image='marsmensch/tcpdump',
														name=CAPTURE_CONTAINER_NAME, 
														restart_policy={"Name": "on-failure"},
														volumes={WHALER_DATA_OUTPUT_FOLDER+'/capture': {'bind': WHALER_DATA_OUTPUT_FOLDER + '/capture', 'mode': 'rw'}},
														network_mode="container:whaler_victim",
														detach=True,
														command='-W 5 -G 30 -w /tmp/whaler/capture/capfile -i eth0',
														
			)
			
			logger.info("deployed new container %s" % container.name)

		except Exception as e:
			logger.error("failed deploying new container [%s]" %e)

	def XXXaddLoggingContainer(self):
		if  not os.environ.get('LOGZIO_TOKEN'):
			logger.info("No Logzio API key found, cannot setup logging module")
			return
		
		try:
			logger.info("Deploying new Logging container [%s]" % LOGGING_CONTAINER_NAME)
			container = self.hostCli.containers.run(	image=LOGGING_IMAGE_NAME,
														name=LOGGING_CONTAINER_NAME, 
														restart_policy={"Name": "on-failure"},
														volumes={'/var/run/docker.sock': {'bind': '/var/run/docker.sock', 'mode': 'rw'}},
														detach=True,
														environment=["LOGZIO_TOKEN=%s" % os.environ['LOGZIO_TOKEN']],
														command=['-z',os.environ.get('LOGZIO_ENV'),'-a',os.environ.get('LOGZIO_ENV'), '--statsinterval', '3600'],
														
			)
			
			logger.info("deployed new container %s" % container.name)

		except Exception as e:
			logger.error("failed deploying new container [%s]" %e)

	#generic remove container function
	def removeContainer(self, cli, containerName):
		try:
			logger.info("Removing container [%s]" % containerName)
			container = cli.containers.get(containerName)
			container.remove(force=True)
			logger.info("removed cotaniner [%s]" % containerName)
		except docker.errors.NotFound:
			logger.warn("container [%s] not found to remove" % containerName)
		except Exception as e:
			logger.error("Unable to kill / remove victim container [%s]" % e)

	def snapshotContainer(self, container, filePath):
		logger.info("Snapshotting image and container for [%s] to [%s]" % (container.name, filePath))

		if not os.path.exists(filePath): os.makedirs(filePath)
		
		image=container.image
		outputFile=filePath + '/IMG_' + container.name + '-' + container.id + '.tar'
		f = open(outputFile, 'w')

		for chunk in image.save():
			f.write(chunk)
		f.close()
		logger.info("{'timestamp':'%s', source':'ContainerManager', 'action':'SavedContainerImage', 'containerId':'%s', 'imageId':'%s', 'file':'%s'}" % (datetime.datetime.now().isoformat(),container.id,image.tags,outputFile))

		outputFile=filePath + '/CNT_' + container.name + '-' + container.id + '.tar'
		f = open(outputFile, 'w')

		for chunk in container.export():
			f.write(chunk)
		f.close()
		logger.info("{'timestamp':'%s', source':'ContainerManager', 'action':'SavedContainer', 'containerId':'%s', 'imageId':'%s', 'file':'%s'}" % (datetime.datetime.now().isoformat(),container.id,image.tags,outputFile))
		
		
