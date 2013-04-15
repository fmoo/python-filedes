from filedes.test.base import BaseFDTestCase
from filedes import FD, get_open_fds, LocalFileDescriptor
from subprocess import Popen, PIPE, STDOUT
import os
import filedes
import unittest2


class CloseOnExecuteTests(BaseFDTestCase):
    def testPipeCloseOnExcecute(self):
        r, w = os.pipe()

        # Set close on execute on this guy
        FD(w).set_cloexec()

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

                # Make sure the read fd persisted, but the write fd was not.
                self.assertIn(r, remote_fds)
                self.assertNotIn(w, remote_fds)

                # As an added check, make sure the mode flags on the remote
                # and local process' fds are identical
                self.assertEquals(FD(r, p.pid).mode, FD(r).mode)

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
            FD(r).close()
            FD(w).close()


class PipeTests(BaseFDTestCase):
    def testPipeConstructor(self):
        r, w = filedes.pipe()
        self.assertIsInstance(r, LocalFileDescriptor)
        self.assertIsInstance(w, LocalFileDescriptor)
        r.close()
        w.close()


class DupTests(BaseFDTestCase):
    def dupTestCommon(self, r, w, r2):
        # make sure they're not the same
        self.assertNotEquals(r, r2)
        self.assertNotEquals(int(r), int(r2))

        # make sure we can read from the original fd
        self.assertEquals(w.write("OK"), 2)
        self.assertEquals(r.read(2), "OK")

        # make sure we can read from the dup'd fd
        self.assertEquals(w.write("OK"), 2)
        self.assertEquals(r2.read(2), "OK")

        # now close them
        r.close()
        w.close()
        r2.close()


    def testDup(self):
        r, w = filedes.pipe()
        r2 = r.dup()
        self.dupTestCommon(r, w, r2)

    def testDup2(self):
        r, w = filedes.pipe()
        r2 = r.dup(63)
        self.dupTestCommon(r, w, r2)


if __name__ == '__main__':
    unittest2.main()
