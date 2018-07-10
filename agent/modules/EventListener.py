import os, io, sys, time, datetime, subprocess, threading, logging, traceback

import docker

logger = logging.getLogger(__name__)

class EventListener():
	
	def __init__(self, incidentManager, victimCli):
		self.incidentManager=incidentManager
		self.victimCli=victimCli

	def listen(self):
		logger.info("Started EventListener")
		while True:
				try:
					self.processEvents()
				except Exception as e:
					logger.warn("EventListener: Lost connection, retrying in 10s...[%s]" % e)
					traceback.print_exc(file=sys.stdout)
					time.sleep(10)

		
	
	def processEvents(self):
		events=self.victimCli.events(decode=True)
		logger.info("EventListener: Connected and streaming Daemon events")

		for event in events:
			logger.info("{'timestamp':'%s', source':'EventListener', 'action':'DaemonEvent', 'event':%s}" % (datetime.datetime.now().isoformat(),event))
			if (hasattr( self , "on"+event['Action'].title())):
				getattr( self , "on"+event['Action'].title())( event )
			else:
				pass
				#no action handler found for event type

	#START Daemon event hooks
	def onStart(self, event):
		containerId=event['id']
		container=self.victimCli.containers.get(containerId)
		logger.info("{'timestamp':'%s', source':'EventListener', 'action':'NewContainerStartEvent', 'id':'%s', 'status':'%s', attrs:%s}" % (datetime.datetime.now().isoformat(),container.id,container.status,container.attrs))

		self.incidentManager.reportNewContainer(container)	
	
	#END Daemon event hooks
	