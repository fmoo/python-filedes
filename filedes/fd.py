from __future__ import absolute_import

import stat
import os
import fcntl
import socket

import _filedes
get_open_fds = _filedes.get_open_fds

if hasattr(_filedes, "stat_pid_fd"):
    stat_pid_fd = _filedes.stat_pid_fd
else:
    def stat_pid_fd(pid, fd):
        return os.stat("/proc/%d/fd/%d" % (pid, fd))


def get_fileno(fd_or_obj):
    """Returns the file descriptor number for the given `fd_or_obj`"""
    try:
        return int(fd_or_obj)
    except:
        if hasattr(fd_or_obj, 'fileno') and callable(fd_or_obj.fileno):
            return fd_or_obj.fileno()
    raise TypeError("Unable to get fd from %s" % fd_or_obj)


_TYPE_LOOKUP = {
    000: "anon_inode",
    stat.S_IFBLK: "block",
    stat.S_IFCHR: "character",
    stat.S_IFDIR: "directory",
    stat.S_IFIFO: "fifo",
    stat.S_IFLNK: "symlink",
    stat.S_IFREG: "regular",
    stat.S_IFSOCK: "socket",
    0160000: "whiteout",
}


class _FileDescriptor(object):
    """Base class for local and remote file descriptors"""
    def __init__(self, fd, pid=None):
        self._fd = fd
        self._pid = pid
        self._stat_result = None

    @property
    def fd(self):
        return self._fd

    @property
    def stat(self):
        # TODO: Maybe we shouldn't cache this?
        if self._stat_result is None:
            self._stat_result = self._get_stat()
        return self._stat_result

    @property
    def pid(self):
        if self._pid is None:
            self._pid = self._get_pid()
        return self._pid

    @property
    def mode(self):
        """Returns the mode bits from the stat results for this FD"""
        return self.stat.st_mode

    @property
    def typecode(self):
        """Returns the type code bits from the mode for this FD"""
        return stat.S_IFMT(self.mode)

    @property
    def typestr(self):
        """Returns a string corresponding to the type of this FD"""
        return _TYPE_LOOKUP.get(self.typecode,
            "unknown (0%o)" % stat.S_IFMT(self.mode))

    def __int__(self):
        return self.fd

    def __cmp__(self, b):
        try:
            return cmp(self.fd, get_fileno(b))
        except:
            if self is b:
                return 0
            else:
                return cmp(hash(self), hash(b))

    def __repr__(self):
        return "<%s %s file #%d>" % (self.LOCAL, self.typestr, self.fd)

    def _get_stat(self):
        raise NotImplementedError()

    def _get_pid(self):
        raise NotImplementedError()


class LocalFileDescriptor(_FileDescriptor):
    """A file descriptor belonging to the current process"""
    LOCAL = "local"
    _socket = None

    def read(self, n):
        """Read `n` bytes from the underlying fd"""
        return os.read(self.fd, n)

    def write(self, str):
        """Read `str` to the underlying fd"""
        return os.write(self.fd, str)

    def close(self):
        """Close underlying fd"""
        return os.close(self.fd)

    def ioctl(self, *args):
        """Call an ioctl on this fd"""
        return fcntl.ioctl(self.fd, *args)

    def fcntl(self, *args):
        """Call a fcntl on this fd"""
        return fcntl.fcntl(self.fd, *args)

    @property
    def socket(self):
        """Return a socket helper for the underlying fd"""
        if self._socket is None:
            if self.typecode != stat.S_IFSOCK:
                raise TypeError("%s is not a socket" % self.typestr)
            self._socket = SocketHelper(self)
        return self._socket

    def is_cloexec(self):
        """Returns whether the close-on-execute bit is set on this FD"""
        return self.get_fd_flag(fcntl.FD_CLOEXEC)

    def set_cloexec(self, cloexec=True):
        """Sets the close-on-execute bit on this FD"""
        return self.set_fd_flag(fcntl.FD_CLOEXEC, cloexec)

    cloexec = property(is_cloexec, set_cloexec)

    def is_nonblocking(self):
        """Returns whether the stream for this FD is in nonblocking mode"""
        return self.get_status_flag(os.O_NONBLOCK)

    def set_nonblocking(self, nonblocking=True):
        """Sets whether the stream for this FD is in nonblocking mode"""
        return self.set_status_flag(os.O_NONBLOCK, nonblocking)

    nonblocking = property(is_nonblocking, set_nonblocking)

    def get_fd_flag(self, flag):
        """Returns the value of the fd `flag` for this FD"""
        return self._get_flag(flag, c_get=fcntl.F_GETFD)

    def set_fd_flag(self, flag, value):
        """Sets an fd `flag` to the given `value`"""
        return self._set_flag(flag, value, c_get=fcntl.F_GETFD, c_set=fcntl.F_SETFD)

    def get_status_flag(self, flag):
        """Returns the value of the status `flag` for this FD"""
        return self._get_flag(flag, c_get=fcntl.F_GETFL)

    def set_status_flag(self, flag, value):
        """Sets a status `flag` to the given `value`"""
        return self._set_flag(flag, value, c_get=fcntl.F_GETFL,
                             c_set=fcntl.F_SETFL)

    def _get_flag(self, flag, c_get):
        flags = self.fcntl(fd, c_get)
        return bool(flags & flag == flag)

    def _set_flag(self, flag, value, c_get, c_set):
        flags = self.fcntl(c_get)
        if value:
            flags |= flag
        else:
            flags &= ~flag
        return self.fcntl(c_set, flags)

    def _get_stat(self):
        return os.fstat(self.fd)

    def _get_pid(self):
        return os.getpid()


class SocketHelper(object):
    def __init__(self, fd):
        self.fd = int(fd)

    def setopt(self, level, optname, value):
        """Set the `optname` sockopt at `level` to `value`"""
        return _filedes.setsockopt(self.fd, level, optname, value)

    def getopt(self, level, optname, buflen=0):
        """Returns the `name` sockopt at `level` from this socket"""
        return _filedes.getsockopt(self.fd, level, optname, buflen)

    def set_reuse(self, value=True):
        """Enable SO_REUSE on this socket"""
        return self.setopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, value)

    def get_reuse(self):
        """Get whether SO_REUSE is set on this socket"""
        return bool(self.getopt(socket.SOL_SOCKET, socket.SO_REUSEADDR))


class RemoteFileDescriptor(_FileDescriptor):
    """A file descriptor belonging to another process"""
    LOCAL = "remote"

    def _get_pid(self):
        assert self._pid is not None
        return self._pid

    def _get_stat(self):
        return stat_pid_fd(self.pid, self.fd)


def FD(fd, pid=None):
    """Returns the FileDescriptor object for the given integer `fd`

    `pid` may also be provided if you want to get extended information about
    fds belonging to other processes.
    """
    fd = get_fileno(fd)
    if pid is None or pid == os.getpid():
        return LocalFileDescriptor(fd, pid=pid)
    else:
        return RemoteFileDescriptor(fd, pid)


if __name__ == '__main__':
    import errno
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("pids", nargs="*", default=[None], type=int, metavar="PID")
    ns = ap.parse_args()
    for pid in ns.pids:
        if pid is None:
            open_fds = get_open_fds()
        else:
            open_fds = get_open_fds(pid)
        for fd in open_fds:
            try:
                print FD(fd, pid=pid)
            except OSError as e:
                if e.errno == errno.EBADF:
                    print "%d: EBADF" % fd
                else:
                    raise
