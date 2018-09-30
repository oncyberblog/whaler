import logging, json, os, re

from Configuration import Configuration

from fuzzywuzzy import fuzz

logger = logging.getLogger(__name__)

class FingerprintService:

    def __init__(self):
        self.fingerprints = self.loadFingerprints()

    def isKnownContainer(self, fingerprint):
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

    def storeFingerprint(self, fingerprint, outputFolder):
        with open(outputFolder + '/fingerprint.json', 'w') as outfile:
            json.dump(fingerprint, outfile)



    def storeFingerprints(self):
        with open(Configuration().get("dataDirectory") + '/fingerprints.json', 'w') as outfile:
            json.dump(self.fingerprints, outfile)

    def getFingerprint(self, container, image, filesChanged):
        fingerprint = {'Tty': False, 'Cmd': u'', 'Entrypoint': u'', 'Image': u'', 'MountsSource': u'', 'hostFileChanges': u'', 'Env':u''}
        
        if container.attrs['Config']['Tty']:
            fingerprint['Tty'] = container.attrs['Config']['Tty']
        
        if container.attrs['Config']['Cmd']:
            fingerprint['Cmd'] = (' ').join(container.attrs['Config']['Cmd'])
        
        fingerprint['Image'] = ''.join(image.tags)
        
        if container.attrs['Config']['Entrypoint']:
            fingerprint['Entrypoint'] = (' ').join(container.attrs['Config']['Entrypoint'])
        
        if container.attrs['Mounts']:
            fingerprint['MountsSource'] = (' ').join(sorted([ x['Source'] for x in container.attrs['Mounts'] ]))
        
        if filesChanged:
            fingerprint['hostFileChanges'] = (' ').join(sorted(filesChanged))
        
        if container.attrs['Config']['Env']:
            fingerprint['Env'] = (' ').join(container.attrs['Config']['Env'])
        
        logger.info('Built fingerprint for container [%s] %s' % (container.name, fingerprint))

        self.storeFingerprints()

        return fingerprint

    def isExactMatch(self, fingerprint):
        if fingerprint in self.fingerprints:
            logger.info('Found exact match: %s' % fingerprint)
            return True
        else:
            return False

    def isFuzzyMatch(self, fingerprint):
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
                                                    fingerprint['Env'] == oldFingerprint['Env'] and 
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
                logger.info('Found fuzzy match for [%s]. Current: %s Cached: %s' % (fingerprint, oldFingerprint))
                return True


