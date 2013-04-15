from filedes.test.base import BaseFDTestCase
import os
import unittest2


class TestFDTypes(BaseFDTestCase):
    def testPipe(self):
        r, w = os.pipe()

        fds = self.getNewFDs()
        self.assertEquals(len(fds), 2)
        self.assertItemsEqual(fds, [r, w])

        for f in fds:
            self.assertEquals(f.typestr, 'fifo')

        os.close(r)
        os.close(w)


if __name__ == '__main__':
    unittest2.main()
