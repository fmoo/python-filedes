from __future__ import absolute_import
from subprocess import Popen as _Popen
from .fd import get_open_fds
import os

class Popen(_Popen):
    def _close_fds(self, but):
        for fd in get_open_fds():
            if fd < 3 or fd == but:
                continue
            try:
                os.close(fd)
            except:
                pass
