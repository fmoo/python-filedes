from filedes.test.base import BaseFDTestCase
from filedes import FD
import os
import errno
import unittest2


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
        try:
            with self.assertRaises(OSError) as ar:
                fw.write("oops")
            self.assertEquals(ar.exception.errno, errno.EBADF)
        finally:
            FD(r).close()

    def testNonblocking(self):
        r, w = os.pipe()
        fr = FD(r)
        try:
            fr.set_nonblocking()
            with self.assertRaises(OSError) as ar:
                fr.read(1)
            self.assertEquals(ar.exception.errno, errno.EAGAIN)
        finally:
            fr.close()
            FD(w).close()

if __name__ == '__main__':
    unittest2.main()
