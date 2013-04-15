from filedes.test.base import BaseFDTestCase
from filedes.socket.unix import make_unix_stream_socket, connect_unix_stream_socket
from filedes import FD
import unittest2
import _ancillary
import os
import warnings
import time
import threading
import multiprocessing


class TestAncillary(BaseFDTestCase):
    def tempnam(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            return os.tempnam(None, 'uxs')

    def fdTestCommon(self, send_f, recv_f):
        SN = self.tempnam()

        def worker():
            pid = os.getpid()
            while True:
                try:
                    f1 = connect_unix_stream_socket(SN)
                    break
                except:
                    time.sleep(0.05)
            r, w = recv_f(f1, 2)
            os.write(w, "OK:%d" % pid)
            os.close(r)
            os.close(w)

        def acceptor(r, w):
            f0 = make_unix_stream_socket(SN)
            f0.listen(1024)

            # Accept a single connection, then we're done
            conn, address = f0.accept()
            send_f(conn, [r, w])

        p1 = multiprocessing.Process(target=worker)
        p1.start()

        r, w = os.pipe()
        t = threading.Thread(target=acceptor, args=(r, w))
        t.setDaemon(True)
        t.start()

        msg = os.read(r, 1024)
        msg, pid = msg.split(":")
        self.assertEquals(msg, "OK")
        self.assertEquals(int(pid), p1.pid)
        self.assertNotEquals(int(pid), os.getpid())

        os.close(r)
        os.close(w)

        p1.join()
        self.assertEquals(p1.exitcode, 0)

        t.join()

    def testAncillarySendRecvFDs(self):
        def send(sock, fds):
            _ancillary.send_fds(sock.fileno(), fds)
        def recv(sock, n_fds):
            return _ancillary.recv_fds(sock.fileno(), n_fds)
        self.fdTestCommon(send, recv)

    def testAncillarySendRecvFD(self):
        def send(sock, fds):
            for fd in fds:
                _ancillary.send_fd(sock.fileno(), fd)
        def recv(sock, n_fds):
            result = []
            for i in xrange(n_fds):
                result.append(_ancillary.recv_fd(sock.fileno()))
            return result
        self.fdTestCommon(send, recv)

    def testFiledesSocketSendRecvFDs(self):
        def send(sock, fds):
            FD(sock).socket.send_fds(fds)
        def recv(sock, n_fds):
            return FD(sock).socket.recv_fds(n_fds)
        self.fdTestCommon(send, recv)

    def testFiledesSocketSendRecvFD(self):
        def send(sock, fds):
            for fd in fds:
                FD(sock).socket.send_fd(fd)
        def recv(sock, n_fds):
            result = []
            for i in xrange(n_fds):
                result.append(FD(sock).socket.recv_fd())
            return result
        self.fdTestCommon(send, recv)


if __name__ == '__main__':
    unittest2.main()
