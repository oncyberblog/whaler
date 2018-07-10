import os, io, sys, time, datetime, shutil, logging, traceback

import docker

from BaseContainer import BaseContainer

logger = logging.getLogger(__name__)

DOCKER_DAEMON_LOCAL_URL='unix://var/run/docker.sock'

LOGGING_CONTAINER_NAME="whaler_logging"
LOGGING_IMAGE_NAME="logzio/logzio-docker"


class LoggingContainer(BaseContainer):
	
	def __init__(self):
		BaseContainer.__init__(self, DOCKER_DAEMON_LOCAL_URL, LOGGING_CONTAINER_NAME)

	def deployContainer(self):
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
			self.container=container
			logger.info("deployed new container %s" % container.name)

		except Exception as e:
			logger.error("failed deploying new container [%s]" %e)


	

