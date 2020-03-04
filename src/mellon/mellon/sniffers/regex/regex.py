from zope import component
from zope import interface
import mellon
import re

from sparc.logging import logging
logger = logging.getLogger(__name__)

@interface.implementer(mellon.ISecretSniffer)
@component.adapter(mellon.ISnippet)
class RegExSecretSniffer(object):
    @classmethod
    def get_patterns(cls):
        sm = component.getSiteManager()
        config = sm.getUtility(mellon.IMellonApplication).get_config()
        conf_regex = config.mapping().get_value('MellonRegexSniffer')
        
        patterns = {'all': [], 'byte': [], 'unicode':[], 'text':[] } #list of dicts
        for type_ in patterns.keys():
            if type_ in conf_regex['pattern_files']:
                logger.debug(u"found pattern file {}, looking for regex patterns to load ...".format(conf_regex['pattern_files'][type_]))
                with open(conf_regex['pattern_files'][type_]) as f:
                    for pattern in [p.strip() for p in f]:
                        types = [type_] if type_ in ('byte', 'unicode', 'text', ) else ['byte', 'unicode', 'text']
                        for t in types:
                            logger.debug(u"loading pattern '{}' into {} Regex secret sniffer".format(pattern, t))
                            patterns[t].append({'pattern': pattern,
                                                'prog':re.compile(pattern if t in ['unicode','text'] else bytes(pattern,'utf-8'))})
        return patterns
    patterns = None   
       
    def create_secret(self, pattern, matched_data):
        return  component.createObject(u"mellon.secret", 
                            name=u"Matched regex pattern {} on {}".\
                                    format(pattern,matched_data), 
                                parent=self.context)            
    
    def __init__(self, context):
        self.context = context
        if not RegExSecretSniffer.patterns:
            logger.debug(u"Regex pattern files not yet loaded, initializing...")
            RegExSecretSniffer.patterns = RegExSecretSniffer.get_patterns()
            logger.debug(u"Regex pattern file initialization complete.")

    def __iter__(self):
        for entry in self.patterns['all']:
            match = entry['prog'].search(self.context.data)
            if match:
                yield self.create_secret(entry['pattern'],match.group(0))

@component.adapter(mellon.IBytesSnippet)
class ByteRegExSecretSniffer(RegExSecretSniffer):
    def __iter__(self):
        for entry in self.patterns['byte']:
            match = entry['prog'].search(self.context.data)
            if match:
                yield self.create_secret(entry['pattern'],match.group(0))

@component.adapter(mellon.IUnicodeSnippet)
class UnicodeRegExSecretSniffer(RegExSecretSniffer):
    def __iter__(self):
        for entry in self.patterns['unicode']:
            match = entry['prog'].search(self.context.data)
            if match:
                yield self.create_secret(entry['pattern'],match.group(0))

@component.adapter(mellon.ITextSnippet)
class TextRegExSecretSniffer(RegExSecretSniffer):
    def __iter__(self):
        #logger.debug(u"examining text contents for pattern matches: \n{}\n".format(self.context.data))
        for entry in self.patterns['text']:
            logger.debug(u"searching for matches on pattern {}".format(entry))
            match = entry['prog'].search(self.context.data)
            if match:
                yield self.create_secret(entry['pattern'],match.group(0))