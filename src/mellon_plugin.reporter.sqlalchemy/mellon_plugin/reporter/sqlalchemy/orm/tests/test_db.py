import os.path
import unittest
import zope.testrunner
from sparc.testing.fixture import test_suite_mixin

from zope import component
from mellon.reporters.memory.memory import report as memory_report
from ..testing import MELLON_SA_ORM_REPORTER_EXECUTED_LAYER
from .. import models
from .. import interfaces as i


class MellonOrmReporterTestCase(unittest.TestCase):
    layer = MELLON_SA_ORM_REPORTER_EXECUTED_LAYER
    
    def tearDown(self):
        self.layer.session.rollback()
    
    def test_reporter(self):
        # now check orm
        self.assertEquals(len(self.layer.session.query(models.Secret).all()), 2)
    
    def test_unique_entries(self):
        #verify current DN contents
        self.assertEquals(len(self.layer.session.query(models.MellonFile).all()), 2)
        mfile = memory_report[0].__parent__.__parent__
        # create new non-unique model and then merge/check
        mfile_model_new = component.createObject(u"mellon_plugin.reporter.sqlalchemy.orm.model", mfile)
        self.layer.session.merge(mfile_model_new)
        self.assertEquals(len(self.layer.session.query(models.MellonFile).all()), 2)
        # create new unique model and then merge/check
        mfile_model_unique = models.MellonFile(name="new unique file")
        self.layer.session.merge(mfile_model_unique)
        self.assertEquals(len(self.layer.session.query(models.MellonFile).all()), 3)

class test_suite(test_suite_mixin):
    layer = MELLON_SA_ORM_REPORTER_EXECUTED_LAYER
    package = 'mellon_plugin.reporter.sqlalchemy.orm'
    module = 'db'
    
    def __new__(cls):
        suite = super(test_suite, cls).__new__(cls)
        suite.addTest(unittest.makeSuite(MellonOrmReporterTestCase))
        return suite

if __name__ == '__main__':
    zope.testrunner.run([
                         '--path', os.path.dirname(__file__),
                         '--tests-pattern', os.path.splitext(
                                                os.path.basename(__file__))[0]
                         ])