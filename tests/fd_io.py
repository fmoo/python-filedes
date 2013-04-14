from filedes.test.base import BaseFDTestCase
from filedes import FD
import os


class TestFDIO(BaseFDTestCase):
    def testReadWrite(self):
        r, w = os.pipe()
        self.assertEquals(FD(w).write("OK"), 2)
        self.assertEquals(FD(r).read(2), "OK")
        FD(r).close()
        FD(w).close()

    def testWriteAfterClose(self):
        r, w = os.pipe()
        fw = FD(w)
        fw.close()
        with self.assertRaises(OSError):
            fw.write("oops")
        FD(r).close()
