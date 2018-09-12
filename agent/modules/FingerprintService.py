import logging, json, os, re

from Configuration import Configuration

from fuzzywuzzy import fuzz

logger = logging.getLogger(__name__)

class FingerprintService:

    def __init__(self):
        self.fingerprints = self.loadFingerprints()

    def isKnownContainer(self, container, filesChanged):
        fingerprint = self.getFingerprint(container, filesChanged)
        if self.isExactMatch(fingerprint, container.name):
            return True

        if self.isFuzzyMatch(fingerprint, container.name):
            return True
        
        logger.info('No match found for [%s], adding new fingerprint %s' % (container.name, fingerprint))
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

    def isExactMatch(self, fingerprint, containerName):
        if fingerprint in self.fingerprints:
            logger.info('Found exact match for [%s]: %s' % (containerName,fingerprint))
            return True
        else:
            return False

    def isFuzzyMatch(self, fingerprint, containerName):
        cmdString1 = '%s %s' % (fingerprint['Cmd'], fingerprint['Entrypoint'])
        #replace randomised hex 6+chars
        cmdString1 = re.sub("[a-f0-9]{6,}", "XXXXXXXXXX", cmdString1)
        
        for oldFingerprint in self.fingerprints:
            cmdString2 = '%s %s' % (oldFingerprint['Cmd'], oldFingerprint['Entrypoint'])
            #replace randomised hex 6+chars
            cmdString2 = re.sub("[a-f0-9]{6,}", "XXXXXXXXXX", cmdString2)

            cmdFuzzRatio = fuzz.token_set_ratio(cmdString1, cmdString2)
            logger.debug('Cmd fuzz ratio is %s' % cmdFuzzRatio) 
            
            match =  (fingerprint['MountsSource'] == oldFingerprint['MountsSource'] and 
                                                    fingerprint['Tty'] == oldFingerprint['Tty'] and 
                                                    fingerprint['Image'] == oldFingerprint['Image'] and 
                                                    cmdFuzzRatio > Configuration().get("fingerprintFuzzyMatchThresholdScore")
            )
            #host file changes are different - check for fuzzy match
            if fingerprint['hostFileChanges'] != oldFingerprint['hostFileChanges']:
                hostFileFuzzRatio = fuzz.token_set_ratio(fingerprint['hostFileChanges'], oldFingerprint['hostFileChanges'])
                logger.debug('Host file fuzz ratio is %s' % hostFileFuzzRatio) 
                match = (match and 
                        hostFileFuzzRatio > Configuration().get("fingerprintFuzzyMatchThresholdScore")
                )
            if match:
                logger.info('Found fuzzy match for [%s]. Current: %s Cached: %s' % (containerName, fingerprint, oldFingerprint))
                return True


