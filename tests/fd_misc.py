from filedes.test.base import BaseFDTestCase
from filedes import FD, get_open_fds, LocalFileDescriptor
from subprocess import Popen, PIPE, STDOUT
import os
import filedes


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
