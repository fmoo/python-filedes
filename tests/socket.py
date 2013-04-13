from __future__ import absolute_import

from filedes.test.base import BaseFDTestCase
from filedes import FD
import unittest2
import socket
import os


class SocketTests(BaseFDTestCase):
    def testNotASocket(self):
        r, w = os.pipe()
        try:
            with self.assertRaises(TypeError):
                FD(r).socket
        finally:
            os.close(r)
            os.close(w)

    def testReuse(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('127.0.0.1', 0))
        host, port = s.getsockname()

        s2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        with self.assertRaises(socket.error):
            s2.bind(('127.0.0.1', port))

        FD(s).socket.set_reuse()

        with self.assertRaises(socket.error):
            s2.bind(('127.0.0.1', port))

        FD(s2).socket.set_reuse()
        s2.bind(('127.0.0.1', port))


if __name__ == '__main__':
    unittest2.main()
