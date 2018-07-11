import logging, json, os

from Configuration import Configuration

from fuzzywuzzy import fuzz

logger = logging.getLogger(__name__)

class FingerprintService:

    def __init__(self):
        self.fingerprints = self.loadFingerprints()

    def isKnownContainer(self, container, filesChanged):
        fingerprint = self.getFingerprint(container, filesChanged)
        if self.isExactMatch(fingerprint):
            return True

        if self.isFuzzyMatch(fingerprint):
            return True
        
        logger.info('No match found, adding new fingerprint %s' % fingerprint)
        self.fingerprints.append(fingerprint)
        return False

    def loadFingerprints(self):
        fingerprints = []
        if os.path.exists(Configuration().get("dataDirectory") + '/fingerprints.json'):
            with open(Configuration().get("dataDirectory") + '/fingerprints.json', 'r') as (inputFile):
                fingerprints = json.load(inputFile)
        
        logger.info('Intialised known Fingerprint set [%s] items' % len(fingerprints))
        return fingerprints

    def storeFingerprints(self):
        with open(Configuration().get("dataDirectory") + '/fingerprints.json', 'w') as outfile:
            json.dump(self.fingerprints, outfile)

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
        
        logger.info('Built fingerprint for container [%s] %s' % (container.name, fingerprint))

        self.storeFingerprints()

        return fingerprint

    def isExactMatch(self, fingerprint):
        if fingerprint in self.fingerprints:
            logger.info('Found exact match for %s' % fingerprint)
            return True
        else:
            return False

    def isFuzzyMatch(self, fingerprint):
        cmdString1 = '%s %s' % (fingerprint['Cmd'], fingerprint['Entrypoint'])
        
        for oldFingerprint in self.fingerprints:
            cmdString2 = '%s %s' % (oldFingerprint['Cmd'], oldFingerprint['Entrypoint'])
            
            match =  (fingerprint['MountsSource'] == oldFingerprint['MountsSource'] and 
                                                    fingerprint['Tty'] == oldFingerprint['Tty'] and 
                                                    fingerprint['Image'] == oldFingerprint['Image'] and 
                                                    fuzz.token_set_ratio(cmdString1, cmdString2) > Configuration().get("fingerprintFuzzyMatchThresholdScore")
            )
            #host file changes are different - check for fuzzy match
            if fingerprint['hostFileChanges'] != oldFingerprint['hostFileChanges']:
                match = (match and 
                        fuzz.token_set_ratio(fingerprint['hostFileChanges'], oldFingerprint['hostFileChanges']) > Configuration().get("fingerprintFuzzyMatchThresholdScore")
                )
            if match:
                logger.info('Found fuzzy match. Current: %s Cached: %s' % (fingerprint, oldFingerprint))
                return True


