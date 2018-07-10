import datetime, time, logging, json, os
from fuzzywuzzy import fuzz
logger = logging.getLogger(__name__)
WHALER_DATA_OUTPUT_FOLDER = '/tmp/whaler/'
FUZZY_MATCH_THRESHOLD = 80

class FingerprintService:

    def __init__(self):
        self.fingerprints = self.loadFingerprints()

    def isKnownContainer(self, container, filesChanged):
        print self.fingerprints
        fingerprint = self.getFingerprint(container, filesChanged)
        if fingerprint in self.fingerprints or self.isFuzzyMatch(fingerprint):
            return True
        self.fingerprints.append(fingerprint)
        return False

    def loadFingerprints(self):
        fingerprints = []
        if os.path.exists(WHALER_DATA_OUTPUT_FOLDER + '/fingerprints.json'):
            with open(WHALER_DATA_OUTPUT_FOLDER + '/fingerprints.json', 'r') as (inputFile):
                fingerprints = json.load(inputFile)
        logger.info('Intialised Fingerprint set [%s] items' % len(fingerprints))
        return fingerprints

    def getFingerprint(self, container, filesChanged):
        fingerprint = {'Tty': False, 'Cmd': u'', 'Entrypoint': u'', 'Image': u'', 'MountsSource': u'', 'hostFileChanges': u''}
        if container.attrs['Config']['Tty']:
            fingerprint['Tty'] = container.attrs['Config']['Tty']
        if container.attrs['Config']['Cmd']:
            fingerprint['Cmd'] = (' ').join(container.attrs['Config']['Cmd'])
        if container.attrs['Config']['Image']:
            fingerprint['Image'] = container.attrs['Config']['Image']
        if container.attrs['Config']['Entrypoint']:
            fingerprint['Entrypoint'] = (' ').join(container.attrs['Config']['Entrypoint'])
        if container.attrs['Mounts']:
            fingerprint['MountsSource'] = (' ').join(sorted([ x['Source'] for x in container.attrs['Mounts'] ]))
        if filesChanged:
            fingerprint['hostFileChanges'] = (' ').join(sorted(filesChanged))
        logger.info('Built fingerprint for container: %s' % fingerprint)
        return fingerprint

    def isFuzzyMatch(self, fingerprint):
        cmdString1 = '%s %s' % (fingerprint['Cmd'], fingerprint['Entrypoint'])
        for oldFingerprint in self.fingerprints:
            logger.info('COMPARE: %s %s' % (fingerprint, oldFingerprint))
            cmdString2 = '%s %s' % (oldFingerprint['Cmd'], oldFingerprint['Entrypoint'])
            logger.info('ratio cmd and entry point is %s ' % fuzz.token_set_ratio(cmdString1, cmdString2))
            logger.info('ratio changed files is %s ' % fuzz.token_set_ratio(fingerprint['hostFileChanges'], oldFingerprint['hostFileChanges']))
            match = fingerprint['MountsSource'] == oldFingerprint['MountsSource'] and fingerprint['Tty'] == oldFingerprint['Tty'] and fingerprint['Image'] == oldFingerprint['Image'] and fuzz.token_set_ratio(cmdString1, cmdString2) > FUZZY_MATCH_THRESHOLD
            if fingerprint['hostFileChanges'] != oldFingerprint['hostFileChanges']:
                match = match and fuzz.token_set_ratio(fingerprint['hostFileChanges'], oldFingerprint['hostFileChanges']) > FUZZY_MATCH_THRESHOLD
            if match:
                logger.info('ratio cmd and entry point is %s ' % fuzz.token_set_ratio(cmdString1, cmdString2))
                logger.info('ratio changed files is %s ' % fuzz.token_set_ratio(fingerprint['hostFileChanges'], oldFingerprint['hostFileChanges']))
                logger.info('Found fuzzy match. Current: %s Cached: %s' % (fingerprint, oldFingerprint))
                return True

    def reportVictimFsChanges(self, filesChanged):
        self.victimFSChangedFiles = sorted(filesChanged)
        logger.info('files changed %s' % self.victimFSChangedFiles)

