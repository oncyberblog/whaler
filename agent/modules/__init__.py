import logging

from Configuration import Configuration

LOG_FILE=Configuration().get("dataDirectory") + "/whaler.log"

#logging - to file and console
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(module)s - %(message)s', filename=LOG_FILE,level=logging.DEBUG, filemode='w')
console = logging.StreamHandler()
console.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(module)s - %(message)s'))
logging.getLogger('').addHandler(console)
