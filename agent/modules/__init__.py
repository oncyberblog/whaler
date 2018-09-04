import logging, logging.handlers, os

from Configuration import Configuration

LOG_FILE=Configuration().get("dataDirectory") + "/whaler.log"

#logging - to file and console
should_roll_over = os.path.isfile(LOG_FILE)
handler = logging.handlers.RotatingFileHandler(LOG_FILE, mode='w', backupCount=1000)
if should_roll_over:  # log already exists, roll over!
    handler.doRollover()

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(module)s - %(message)s', filename=LOG_FILE,level=logging.DEBUG, filemode='w')
console = logging.StreamHandler()
console.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(module)s - %(message)s'))
console.setLevel(logging.INFO)
logging.getLogger('').addHandler(console)
