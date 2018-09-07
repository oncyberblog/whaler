import logging, logging.handlers, os

from Configuration import Configuration

LOG_FILE=Configuration().get("dataDirectory") + "/whaler.log"

#logging - to file and console
logger=logging.getLogger('')
logger.setLevel(logging.DEBUG)

fileHandler = logging.handlers.RotatingFileHandler(filename=LOG_FILE, backupCount=1000)
fileHandler.setLevel(logging.DEBUG)

consoleHandler=logging.StreamHandler()
consoleHandler.setLevel(logging.INFO)

formatter=logging.Formatter('%(asctime)s - %(levelname)s - %(module)s - %(message)s')
fileHandler.setFormatter(formatter)
consoleHandler.setFormatter(formatter)

logger.addHandler(fileHandler)
logger.addHandler(consoleHandler)

#roll logs

if os.path.isfile(LOG_FILE):
    fileHandler.doRollover()
