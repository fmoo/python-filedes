import unittest2
import unittest
import logging
import sys
from ..fd import FD, get_open_fds


class BaseFDTestCase(unittest2.TestCase):
    def assertNotNone(self, o, msg=''):
        self.assertTrue(o is not None, msg)

    def assertNotEmpty(self, o, msg=''):
        self.assertTrue(len(o) > 0, msg)

    @classmethod
    def setUpClass(cls):
        cls.logger = logging.getLogger('filedes.tests.%s' % cls.__name__)
        super(BaseFDTestCase, cls).setUpClass()

    def setUp(self):
        # Implement setUpClass for old pythons
        if not hasattr(unittest.TestCase, 'setUpClass'):
            cls = self.__class__
            if not hasattr(cls, '_unittest2_setup'):
                cls.setUpClass()
                cls._unittest2_setup = 0
            cls._unittest2_setup += 1
        self._start_fds = [FD(fd) for fd in get_open_fds()]
        self._start_threads = sys._current_frames().keys()

    def tearDown(self):
        end_fds = [FD(fd) for fd in get_open_fds()]
        self.assertItemsEqual(self._start_fds, end_fds, "FDs leaked")

        end_threads = sys._current_frames().keys()
        self.assertItemsEqual(self._start_threads, end_threads, "Threads leaked")

        # Implement tearDownClass for old pythons
        if not hasattr(unittest.TestCase, 'tearDownClass'):
            cls = self.__class__
            if not hasattr(cls, '_unittest2_setup'):
                cls._unittest2_setup = 0
            else:
                cls._unittest2_setup -= 1
            if cls._unittest2_setup == 0:
                cls.tearDownClass()

    def assertContains(self, item, arr, msg=''):
        return self.assertIn(item, arr, msg)
