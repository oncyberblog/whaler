import os, io, sys, time, datetime, subprocess, threading

import docker

#
# ContainerWatcher class - runs as seperate thread.
# looks for newly spawned containers and:
# 	i) stops them
#	ii) archives the image as a tar to /tmp for later analysis
#	ii) removes the cotainer
#
class ContainerWatcher(threading.Thread):
	
	def __init__(self, cli):
		threading.Thread.__init__(self)
		self.stopped = threading.Event()
		self.daemon = True
		self.cli = cli
		if 'CONTAINER_KILL_DELAY' in os.environ:
			self.containerKillDelay = float(os.environ['CONTAINER_KILL_DELAY'])
		else:
			self.containerKillDelay = 30
		print "CONTAINER_KILL_DELAY is %s " % self.containerKillDelay

	def run(self):
		

		while not self.stopped.wait(5):
			self.processNewContainers(self.cli)
			
	def stop(self):
		self.stopped.set()

	def processNewContainers(self, cli):
		for container in self.cli.containers.list(all=True):
			print "{'timestamp':'%s', source':'ContainerWatcher', 'action':'NewContainerFound', 'id':'%s', 'status':'%s'}" % (datetime.datetime.now().isoformat(),container.id,container.status)
			time.sleep(self.containerKillDelay)
			container.stop()
			diffs=container.diff()
			print "{'timestamp':'%s', source':'ContainerWatcher', 'action':'NewContainerStopped', 'id':'%s', 'status':'%s'}" % (datetime.datetime.now().isoformat(),container.id,container.status)
			print "{'timestamp':'%s', source':'ContainerWatcher', 'action':'ContainerDiffs', 'diff':%s}" % (datetime.datetime.now().isoformat(),diffs)
			self.archiveContainerAndImage(container)
			container.remove()
			print "{'timestamp':'%s', source':'ContainerWatcher', 'action':'NewContainerRemoved', 'id':'%s'}" % (datetime.datetime.now().isoformat(),container.id)
		sys.stdout.flush()

	def archiveContainerAndImage(self, container):
		image=container.image
		outputFile='/tmp/whaler/snapshots/image-'+image.id+'.tar'
		f = open(outputFile, 'w')

		for chunk in image.save():
			f.write(chunk)
		f.close()
		print "{'timestamp':'%s', source':'ContainerWatcher', 'action':'SavedContainerImage', 'containerId':'%s', 'imageId':'%s', 'file':'%s'}" % (datetime.datetime.now().isoformat(),container.id,image.tags,outputFile)

		outputFile='/tmp/whaler/snapshots/container-'+image.id+'.tar'
		f = open(outputFile, 'w')

		for chunk in container.export():
			f.write(chunk)
		f.close()
		print "{'timestamp':'%s', source':'ContainerWatcher', 'action':'SavedContainer', 'containerId':'%s', 'imageId':'%s', 'file':'%s'}" % (datetime.datetime.now().isoformat(),container.id,image.tags,outputFile)
		
		
#Local and victim docker daemon configuration - local one not currently used
DOCKER_DAEMON_LOCAL_URL='unix://var/run/docker.sock'
DOCKER_DAEMON_VICTIM_URL='tcp://victim:2375'

#hooks docker start container event and stops the container
def start(cli, event):
	containerId=event['id']
	container=cli.containers.get(containerId)
	print "{'timestamp':'%s', source':'EventWatcher', 'action':'NewContainerStartEvent', 'id':'%s', 'status':'%s', attrs:%s}" % (datetime.datetime.now().isoformat(),container.id,container.status,container.attrs)

def main():
	#setup local and victim docker clients
	thismodule = sys.modules[__name__]

	localClient = docker.DockerClient(base_url=DOCKER_DAEMON_LOCAL_URL)
	victimClient = docker.DockerClient(base_url=DOCKER_DAEMON_VICTIM_URL)

	ContainerWatcher(victimClient).start()
	
	print "started watcher"
	for event in victimClient.events(decode=True):
		print "{'timestamp':'%s', source':'EventWatcher', 'action':'DaemonEvent', 'event':%s}" % (datetime.datetime.now().isoformat(),event)
		if (hasattr( thismodule , event['Action'])):
			getattr( thismodule , event['Action'])( victimClient, event )
		else:
			pass
			#no action handler found for event type
	

if __name__ == '__main__':
		main()

def onExit():
	print "exiting..."

import atexit
atexit.register(onExit)



