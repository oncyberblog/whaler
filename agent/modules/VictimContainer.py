import time, datetime, logging

import docker

from BaseContainer import BaseContainer
from modules.Configuration import Configuration

logger = logging.getLogger(__name__)

class VictimContainer(BaseContainer):
	
	def __init__(self):
		BaseContainer.__init__(self, Configuration().get("dockerDaemonHostUrl"), Configuration().get("victimContainerName"))
		self.victimCli=self.getCli(Configuration().get("dockerDaemonVictimUrl"))

	def redeployContainer(self):
		if Configuration().get("victimContainerDisableRedeploy"):
			logger.info("Skipping redeploy container, disabled in configuration for testing")
		else:
			BaseContainer.redeployContainer(self)

	def deployContainer(self):
		try:
			logger.debug("Deploying new VictimContainer [%s]" % Configuration().get("victimContainerName"))
			container = self.cli.containers.run(	image=Configuration().get("victimContainerImage"),
													name=Configuration().get("victimContainerName"),
													network=Configuration().get("victimNetworkName"),
													privileged=True,  
													restart_policy={"Name": "on-failure"},
													ports={'2375/tcp': 2375},
													detach=True,
													dns=['8.8.8.8', '8.8.4.4']
														
			)
			self.container=container

			logger.debug("waiting 10 seconds for container to stabilise and baseline for file changes...")
			time.sleep(10)
			
			self.resetBaselineFileChanges()
			
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
					time.sleep(10)
	
	def processEvents(self, eventListener):
		events=self.victimCli.events(decode=True)
		logger.info("VictimContainer: Connected and streaming Daemon events")

		for event in events:
			logger.debug(event)
			logger.debug("{'timestamp':'%s', source':'VictimContainer', 'action':'DaemonEvent', 'event':%s}" % (datetime.datetime.now().isoformat(),event))
			if (hasattr( self , "on"+event['Action'].title())):
				getattr( self , "on"+event['Action'].title())( event, eventListener )
			else:
				pass
				#no action handler found for event type

	#event handler for start container - call back to listener
	def onStart(self, event, eventListener):
		containerId=event['id']
		container=self.victimCli.containers.get(containerId)
		logger.debug("{'timestamp':'%s', source':'VictimContainer', 'action':'NewContainerStartEvent', 'id':'%s', 'status':'%s', attrs:%s}" % (datetime.datetime.now().isoformat(),container.id,container.status,container.attrs))
		eventListener.onStart(container)

	def snapshotVictimContainer(self, filePath):
		self.snapshotContainer(self.container, filePath)

