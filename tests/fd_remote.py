from __future__ import absolute_import

from filedes.test.base import BaseFDTestCase
from filedes.subprocess import Popen
from filedes import get_open_fds, FD
from subprocess import PIPE, STDOUT
import unittest2
import tempfile
import sys
import select


class RemoteFDTests(BaseFDTestCase):
    def testPipe(self):
        import filedes
        self.checkSubprocessFDs(filedes.pipe())

    def testSocket(self):
        import socket
        s = socket.socket()
        self.checkSubprocessFDs([FD(s.fileno())])
        del s

    def testTempFile(self):
        f = tempfile.TemporaryFile()
        fd = FD(f.fileno())
        # tempfile APIs set cloexec = True for added security
        fd.set_cloexec(False)
        self.checkSubprocessFDs([fd], close=False)
        del f

    def testNamedTempFile(self):
        f = tempfile.NamedTemporaryFile()
        fd = FD(f.fileno())
        # tempfile APIs set cloexec = True for added security
        fd.set_cloexec(False)
        self.checkSubprocessFDs([fd], close=False)
        del f

    @unittest2.skipUnless(sys.platform.startswith("linux"), "requires Linux")
    def testEpoll(self):
        e = select.epoll()
        fd = FD(e)
        self.checkSubprocessFDs([fd], close=False)
        del e

    @unittest2.skipUnless(sys.platform.startswith("darwin"), "requires OSX")
    def testKqueue(self):
        k = select.kqueue()
        fd = FD(k)
        try:
            self.checkSubprocessFDs([fd], close=False)
        finally:
            del k

    def checkSubprocessFDs(self, check_fds, close=True):
        try:
            # Create a subprocess that prints and blocks waiting for input
            p = Popen("echo ok; read foo", shell=True,
                      stdin=PIPE, stdout=PIPE, stderr=STDOUT)
            try:
                # Wait for the process to let us know it's alive
                ready = p.stdout.read(3)
                self.assertEquals(ready, "ok\n")

                # Get the list of FDs of the remote process
                remote_fds = get_open_fds(p.pid)

                # Make sure the check_fds persisted and have an identical mode
                for fd in check_fds:
                    self.assertIn(fd, remote_fds)
                    self.assertEquals(FD(int(fd), p.pid).mode, fd.mode)

                # Now send some output to the remote process to unblock it
                p.stdin.write("ok\n")
                p.stdin.flush()

                # Wait for it to shutdown
                self.assertEquals(p.wait(), 0)
            finally:
                # Popen does not close PIPE fds on process shutdown
                # automatically, even if there's no data in it.  Since the
                # exception context is propagated to the test cases' tearDown,
                # the popen's pipes will show up as a leak
                if p.poll() is None:
                    p.kill()
                    self.assertEquals(p.wait(), -9)
                del p
        finally:
            if close:
                for fd in check_fds:
                    fd.close()


if __name__ == '__main__':
    unittest2.main()
