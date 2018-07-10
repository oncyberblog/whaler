import os, io, sys, time, datetime, shutil, logging, traceback

import docker

from BaseContainer import BaseContainer

logger = logging.getLogger(__name__)

DOCKER_DAEMON_LOCAL_URL='unix://var/run/docker.sock'

CAPTURE_CONTAINER_NAME="whaler_capture"
CAPTURE_IMAGE_NAME="marsmensch/tcpdump"

WHALER_NETWORK_NAME="whaler_default"

WHALER_DATA_OUTPUT_FOLDER="/tmp/whaler/"

class CaptureContainer(BaseContainer):
	
	def __init__(self):
		BaseContainer.__init__(self, DOCKER_DAEMON_LOCAL_URL, CAPTURE_CONTAINER_NAME)

	def deployContainer(self):
		try:
			logger.info("Deploying new Capture container [%s]" % CAPTURE_CONTAINER_NAME)
			container = self.cli.containers.run(	image='marsmensch/tcpdump',
														name=CAPTURE_CONTAINER_NAME, 
														restart_policy={"Name": "on-failure"},
														volumes={WHALER_DATA_OUTPUT_FOLDER+'/capture': {'bind': WHALER_DATA_OUTPUT_FOLDER + '/capture', 'mode': 'rw'}},
														network_mode="container:whaler_victim",
														detach=True,
														command='-W 5 -G 30 -w /tmp/whaler/capture/capfile -i eth0',
														
			)
			self.container=container
			logger.info("deployed new container %s" % container.name)

		except Exception as e:
			logger.error("failed deploying new container [%s]" %e)

	def archiveCaptureFile(self, pCapFileStoragePath):
		try:
			shutil.copyfile(WHALER_DATA_OUTPUT_FOLDER + "/capture/capfile", pCapFileStoragePath + "/capture.pcap")
			logger.info("Saved Pcap file(s) to %s/capture.pcap" % pCapFileStoragePath)
		except Exception as e:
			logger.error("Error archiving capture file [%s]" % e)


