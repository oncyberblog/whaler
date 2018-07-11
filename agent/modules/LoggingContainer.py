import os, logging

import docker

from BaseContainer import BaseContainer
from Configuration import Configuration

logger = logging.getLogger(__name__)

class LoggingContainer(BaseContainer):
	
	def __init__(self):
		BaseContainer.__init__(self, Configuration().get("dockerDaemonHostUrl"), Configuration().get("loggingContainerName"))

	def deployContainer(self):
		if  not os.environ.get('LOGZIO_TOKEN'):
			logger.info("No Logzio API key found, cannot setup logging module")
			return
		
		try:
			logger.debug("Deploying new Logging container [%s]" % Configuration().get("loggingContainerName"))
			container = self.cli.containers.run(	image=Configuration().get("loggingContaineeImage"),
														name=Configuration().get("loggingContainerName"), 
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


	

