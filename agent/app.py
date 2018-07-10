import threading,sys,time,logging


from modules.IncidentManager import IncidentManager


incidentManager = None
logger = logging.getLogger(__name__)

import docker

#Local and victim docker daemon configuration - local one not currently used
DOCKER_DAEMON_LOCAL_URL='unix://var/run/docker.sock'
DOCKER_DAEMON_VICTIM_URL='tcp://victim:2375'

def main():
	logger.info("Starting Whaler...")
	class FlushStdOut(threading.Thread):
		def run(self):
			while True:
				sys.stdout.flush()
				time.sleep(5)
	
	FlushStdOut().start()
	

	victimCli=docker.DockerClient(base_url=DOCKER_DAEMON_VICTIM_URL)
	hostCli=docker.DockerClient(base_url=DOCKER_DAEMON_LOCAL_URL)
	incidentManager = IncidentManager(hostCli,victimCli)
	incidentManager.run()

if __name__ == '__main__':
		main()

def onExit():
	incidentManager.shutdown()
	logger.info("Exiting Whaler...")

import atexit
atexit.register(onExit)



