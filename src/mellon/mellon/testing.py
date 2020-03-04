"""
We provide some sane starting points for Mellon test layers.  We have 3
starting layers:
 - A basic layer that loads the Mellon file based ZCML components
 - A Runtime layer that registers the Mellon application and configures it
 - An executed layer that runs the mellon application.
"""

from .mellon import create_and_register_app
from .reporters.memory.memory import reset_report
from .sniffers.test.test import reset_test_sniffer
import mellon
from .interfaces import IPath, IBinaryChecker
from sparc.testing.testlayer import SparcZCMLFileLayer
from zope import component
import zope.component.hooks
from zope.component.globalregistry import BaseGlobalComponents
from zope.component.testlayer import ZCMLLayerBase
from zope import interface

# A basic layer with Mellon ZCML components registered (does not include the
# mellon.IMellonApplication runtime component)
MELLON_INTEGRATION_LAYER = SparcZCMLFileLayer(mellon)
    
# A layer with a registered and configured, but unexecuted, Mellon application
class MellonApplicationRuntimeLayer(ZCMLLayerBase):
    """
    Provides a configured and registered IMellonApplication layer (but 
    not executed).
    
    Most use-cases will want to extend this class, in doing so, have the 
    ability to update the runtime config.  Extenders can simply define their
    own class-level config property.
    
    A sample extension layer might look like this:
    import your.package
    class YourRuntimeLayer(MellonApplicationRuntimeLayer):
        
        def setUp(self):
            self.config = \
                {
                'ZCMLConfiguration': [{'package': 'your.plugin.package'},
                                      {'package': 'mellon.reporters.memory'},
                                      {'package': 'mellon', 'file': 'ftesting-bin_check-override.zcml'}
                                     ],
                'YourYamlEntry': 'some plugin yaml value'
                }
            super(YourRuntimeLayer, self).setUp() #should be called after config is defined
            
    YOUR_LAYER = YourRuntimeLayer(your.package)
    
    The above layer would make your plugin available along side a memory
    reporter (nice for easy testing purposes).  In addition, a file binary
    checker that only looks at file extensions is loaded (again, makes testing
    a little more sane).
    """
    verbose = False
    debug = False
    config = {
            'ZopeComponentConfiguration': {
                    'zcml': [
                            {'package': 'mellon', 'file': 'ftesting.zcml'}
                        ]
                }
            
        }
    
    def setUp(self):
        #install a empty global registry
        zope.component.hooks.siteinfo.sm = BaseGlobalComponents('MellonTesting')
        super(MellonApplicationRuntimeLayer, self).setUp()
        if self.verbose or self.debug:
            self.insure_logger_components()
        self.init_mellon_app()

    def insure_logger_components(self):
        add = True
        for zcml in self.config['ZopeComponentConfiguration']['zcml']:
            if zcml.get('package', None) == 'mellon.reporters.logger':
                add = False
        if add:
            self.config['ZopeComponentConfiguration']['zcml'].append({'package': 'mellon.reporters.logger'})
    
    def tearDown(self):
        reset_report() #added for convenience only...extender's would still need to register the memory reporter zcml
        reset_test_sniffer() #same
        """
        I don't think we need this because ZCMLLayerBase is our parent...it should
        be able to reset the component registry appropriately
        sm = component.getGlobalSiteManager()
        app = sm.getUtility(IMellonApplication)
        sm.unregisterUtility(component=app, provided=IMellonApplication)
        """
        super(MellonApplicationRuntimeLayer, self).tearDown()
        zope.component.hooks.setSite() #reset global registry to global found in zope.component.globalregistry
    
    def _load_zcml(self, context):
        """Since the Mellon app does this for us, we need to pass
        """
        pass
    
    def init_mellon_app(self):
        self.app = create_and_register_app(self.config, self.verbose, self.debug)
        
MELLON_RUNTIME_LAYER = MellonApplicationRuntimeLayer(mellon)
    
# A layer with an executed Mellon application.  This isn't of much use, except
# to show an example on how to create a layer with an executed Mellon app.
class MellonApplicationExecutedLayer(MellonApplicationRuntimeLayer):
    """
    Provides environment for post-executed Mellon application.
    """
    def setUp(self):
        super(MellonApplicationExecutedLayer, self).setUp()
        #self.app._pdb = True #uncomment to help debug mellon execution 
        self.app.go()
        
MELLON_EXECUTED_LAYER = MellonApplicationExecutedLayer(mellon)
        
@interface.implementer(IBinaryChecker)
@component.adapter(IPath)
class RegexTesterBinaryChecker(object):
    def __init__(self, context):
        self.context = context
    
    def check(self):
        return True if self.context[-3:] == 'bin' else False