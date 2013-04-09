from filedes.test.base import BaseFDTestCase
from filedes import FD
import tempfile


class TestFDCmp(BaseFDTestCase):
    def testEquals(self):
        tf = tempfile.TemporaryFile()
        fds = self.getNewFDs()
        self.assertEquals(len(fds), 1)
        fd = fds[0]

        self.assertEquals(fd, FD(tf.fileno()))
        self.assertEquals(fd, tf.fileno())
        self.assertNotEquals(fd, object())
