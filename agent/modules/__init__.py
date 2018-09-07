import logging, logging.handlers, os

from Configuration import Configuration

LOG_FILE=Configuration().get("dataDirectory") + "/whaler.log"

#logging - to file and console


logging.basicConfig(format='%(asctime)s - %(levelname)s - %(module)s - %(message)s', filename=LOG_FILE,level=logging.DEBUG, filemode='w')

#add console
console = logging.StreamHandler()
console.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(module)s - %(message)s'))
console.setLevel(logging.INFO)
logging.getLogger('').addHandler(console)

#roll logs
handler = logging.handlers.RotatingFileHandler(filename=LOG_FILE, backupCount=1000)
logging.getLogger('').addHandler(handler)
if os.path.isfile(LOG_FILE):
    handler.doRollover()
