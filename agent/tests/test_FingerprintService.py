import unittest

from modules.FingerprintService import FingerprintService

class FakeContainer():
    attrs={'Config':
                {
                    'Tty': False, 
                    'Cmd':  ['/bin/echo'],
                    'Image': 'provider/image',
                    'Entrypoint': ['testing', '>', '/etc/somefile.txt']
                },
            'Mounts': [{'Source':'/etc/source1'}, {'Source':'/etc/source2'}]

    }

class TestStringMethods(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

       
    def test_simplematching(self):
        fingerPrintService = FingerprintService()
        #reset fingerprints
        fingerPrintService.fingerprints=[]

        fakeContainer = FakeContainer()
        filesChanged = ['']

        #no changes
        self.assertFalse(fingerPrintService.isKnownContainer(fakeContainer, filesChanged), "Failed to detect new container")
        self.assertTrue(fingerPrintService.isKnownContainer(fakeContainer, filesChanged), "Failed to identify a simple matched fingerprint")

        #change Tty
        fakeContainer.attrs['Config']['Tty'] = True
        self.assertFalse(fingerPrintService.isKnownContainer(fakeContainer, filesChanged), "Failed to identify change to Tty")
        self.assertTrue(fingerPrintService.isKnownContainer(fakeContainer, filesChanged), "Failed to identify a simple matched fingerprint")

        #change Cmd
        fakeContainer.attrs['Config']['Cmd'] = ['some', 'new', 'cmd', 'param', 'set']
        self.assertFalse(fingerPrintService.isKnownContainer(fakeContainer, filesChanged), "Failed to identify change to Cmd")
        self.assertTrue(fingerPrintService.isKnownContainer(fakeContainer, filesChanged), "Failed to identify a simple matched fingerprint")

        #change Image
        fakeContainer.attrs['Config']['Image'] = 'some/otherimage'
        self.assertFalse(fingerPrintService.isKnownContainer(fakeContainer, filesChanged), "Failed to identify change to Image")
        self.assertTrue(fingerPrintService.isKnownContainer(fakeContainer, filesChanged), "Failed to identify a simple matched fingerprint")

        #change Entrypoint
        fakeContainer.attrs['Config']['Entrypoint'] = ['other', 'entrypoints', 'here']
        self.assertFalse(fingerPrintService.isKnownContainer(fakeContainer, filesChanged), "Failed to identify change to Entrypoint")
        self.assertTrue(fingerPrintService.isKnownContainer(fakeContainer, filesChanged), "Failed to identify a simple matched fingerprint")

        #change Mounts
        fakeContainer.attrs['Mounts'].append({'Source':'/new/mount'})
        self.assertFalse(fingerPrintService.isKnownContainer(fakeContainer, filesChanged), "Failed to identify change to Mount")
        self.assertTrue(fingerPrintService.isKnownContainer(fakeContainer, filesChanged), "Failed to identify a simple matched fingerprint")

        #test FilesChanged
        filesChanged = ['/etc/somefile.txt']
        self.assertFalse(fingerPrintService.isKnownContainer(fakeContainer, filesChanged), "Failed to identify change to Changed files")
        self.assertTrue(fingerPrintService.isKnownContainer(fakeContainer, filesChanged), "Failed to identify a simple matched fingerprint")

    def test_fuzzy_matching(self):
        fingerPrintService = FingerprintService()
        #reset fingerprints
        fingerPrintService.fingerprints=[]

        fakeContainer = FakeContainer()
        filesChanged = ['']

        fakeContainer.attrs['Config']['Cmd'] = ['/bin/do/something', '1234567890']
        fakeContainer.attrs['Config']['Entrypoint'] = ['-o', 'somefile', '1234567890']

        #baseline
        self.assertFalse(fingerPrintService.isKnownContainer(fakeContainer, filesChanged), "Failed to detect new container")
        self.assertTrue(fingerPrintService.isKnownContainer(fakeContainer, filesChanged), "Failed to identify a simple matched fingerprint")

        fakeContainer.attrs['Config']['Cmd'] = ['/bin/do/something', 'ABCDEFGHIJ']
        fakeContainer.attrs['Config']['Entrypoint'] = ['-o', 'somefile', 'ABCDEFGHIJ']

        self.assertTrue(fingerPrintService.isKnownContainer(fakeContainer, filesChanged), "Failed to detect new container by fuzzy match")

