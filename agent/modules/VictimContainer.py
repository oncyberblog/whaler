import os, io, sys, time, datetime, shutil, logging, traceback

import docker

from BaseContainer import BaseContainer

logger = logging.getLogger(__name__)

DOCKER_DAEMON_LOCAL_URL='unix://var/run/docker.sock'
DOCKER_DAEMON_VICTIM_URL='tcp://victim:2375'

VICTIM_CONTAINER_NAME="whaler_victim"
VICTIM_ALIAS="victim"

VICTIM_IMAGE_NAME="docker:stable-dind"

WHALER_NETWORK_NAME="whaler_default"

class VictimContainer(BaseContainer):
	
	def __init__(self):
		BaseContainer.__init__(self, DOCKER_DAEMON_LOCAL_URL, VICTIM_CONTAINER_NAME)
		self.victimCli=self.getCli(DOCKER_DAEMON_VICTIM_URL)

	def deployContainer(self):
		try:
			logger.info("Deploying new VictimContainer [%s]" % VICTIM_CONTAINER_NAME)
			container = self.cli.containers.run(	image=VICTIM_IMAGE_NAME,
													name=VICTIM_CONTAINER_NAME,
													privileged=True,  
													restart_policy={"Name": "on-failure"},
													ports={'2375/tcp': 2375},
													detach=True,
														
			)
			self.container=container
			logger.info("waiting 10 seconds for container to stabilise and baseline for file changes...")
			time.sleep(10)
			self.resetBaselineFileChanges()
			network = self.cli.networks.get(WHALER_NETWORK_NAME)
			logger.info("got network [%s]" % network.name)
			network.connect(container, aliases=[VICTIM_ALIAS])
			logger.info("attached victim container to network [%s] with alias [%s]" % (network.name, VICTIM_ALIAS))
			logger.info("deployed new container [%s]" % container.name)
			

		except Exception as e:
			logger.error("failed deploying new container [%s]" % e)

	def listen(self, eventListener):
		logger.info("Daemon Event Listener Started")
		while True:
				try:
					self.processEvents(eventListener)
				except Exception as e:
					logger.warn("VictimContainer: Lost connection, retrying in 10s...[%s]" % e)
					#traceback.print_exc(file=sys.stdout)
					time.sleep(10)
	
	def processEvents(self, eventListener):
		events=self.victimCli.events(decode=True)
		logger.info("VictimContainer: Connected and streaming Daemon events")

		for event in events:
			logger.info(event)
			logger.info("{'timestamp':'%s', source':'VictimContainer', 'action':'DaemonEvent', 'event':%s}" % (datetime.datetime.now().isoformat(),event))
			if (hasattr( self , "on"+event['Action'].title())):
				getattr( self , "on"+event['Action'].title())( event, eventListener )
			else:
				pass
				#no action handler found for event type

	#event handler for start container - call back to listener
	def onStart(self, event, eventListener):
		containerId=event['id']
		container=self.victimCli.containers.get(containerId)
		logger.info("{'timestamp':'%s', source':'VictimContainer', 'action':'NewContainerStartEvent', 'id':'%s', 'status':'%s', attrs:%s}" % (datetime.datetime.now().isoformat(),container.id,container.status,container.attrs))
		eventListener.onStart(container)

	def snapshotVictimContainer(self, filePath):
		self.snapshotContainer(self.container, filePath)

	def captureEvidence(self):
		pass

