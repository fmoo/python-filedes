from __future__ import absolute_import

from filedes.test.base import BaseFDTestCase
from filedes.subprocess import Popen
from filedes import get_open_fds
from subprocess import PIPE, STDOUT
import filedes


class SubprocessTests(BaseFDTestCase):
    def testPopenCloseFds(self):
        r, w = filedes.pipe()

        try:
            # Create a subprocess that prints and blocks waiting for input
            p = Popen("echo ok; read foo", shell=True,
                      stdin=PIPE, stdout=PIPE, stderr=STDOUT,
                      close_fds=True)
            try:
                # Wait for the process to let us know it's alive
                ready = p.stdout.read(3)
                self.assertEquals(ready, "ok\n")

                # Get the list of FDs of the remote process
                remote_fds = get_open_fds(p.pid)

                # Make sure the read fd persisted, but the write fd was not.
                self.assertNotIn(r, remote_fds)
                self.assertNotIn(w, remote_fds)

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
            r.close()
            w.close()
