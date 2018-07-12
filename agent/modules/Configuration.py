import json, logging, os

logger = logging.getLogger(__name__)

class Configuration:

    instance=None

    def __init__(self):
        if Configuration.instance:
            return

        #can be overridden by passing env variable
        WHALER_DATA_DIR="/var/tmp/whaler"

        if "WHALER_DATA_DIR" in os.environ:
            #user specified data directory (override)
            WHALER_DATA_DIR=os.getenv("WHALER_DATA_DIR")

        if not os.path.exists(WHALER_DATA_DIR): os.makedirs(WHALER_DATA_DIR)

        if os.path.exists(WHALER_DATA_DIR + '/config.json'):
            #load from config file (overide)
            logger.info("Loading configuration file %s" % WHALER_DATA_DIR + '/config.json')
            with open(WHALER_DATA_DIR + '/config.json') as json_data_file:
                self.config = json.load(json_data_file)
        else:
            #default configuration
            logger.info("No custom configuration file found at %s/config.json loading default configuration" % WHALER_DATA_DIR)
            self.config={'dataDirectory':WHALER_DATA_DIR,
                            'dockerDaemonHostUrl':'unix://var/run/docker.sock',
                            'dockerDaemonVictimUrl':'tcp://whaler_victim:2375',
                            'maliciousContainerRunDurationSeconds': 10,
                            'fingerprintFuzzyMatchThresholdScore': 85,
                            'captureContainerName': 'whaler_capture',
                            'captureContainerImage': 'marsmensch/tcpdump',
                            'victimContainerName': 'whaler_victim',
                            'victimContainerAlias': 'whaler_victim',
                            'victimContainerImage': 'docker:stable-dind',
                            'victimNetworkName': 'whaler_default',
                            'loggingContainerName': 'whaler_logging',
                            'loggingContainerImage': 'logzio/logzio-docker'}
        
        logger.info("using configuration set %s" % json.dumps(self.config))
        Configuration.instance=self

    def get(self, key):
        return Configuration.instance.config[key]

