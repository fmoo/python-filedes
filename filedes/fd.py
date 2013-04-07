import stat
import os
import fcntl

import _filedes
get_open_fds = _filedes.get_open_fds

if hasattr(_filedes, "stat_pid_fd"):
    stat_pid_fd = _filedes.stat_pid_fd
else:
    def stat_pid_fd(pid, fd):
        return os.stat("/proc/%d/fd/%d" % (pid, fd))


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
        self.fd = fd
        self._pid = pid
        self._stat_result = None

    @property
    def stat(self):
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
        return self.stat.st_mode
    
    @property
    def typestr(self):
        return _TYPE_LOOKUP.get(
            stat.S_IFMT(self.mode),
            "unknown (0%o)" % stat.S_IFMT(self.mode))

    def __int__(self):
        return self.fd

    def __repr__(self):
        return "<%s %s file #%d>" % (self.LOCAL, self.typestr, self.fd)

    def _get_stat(self):
        raise NotImplementedError()

    def _get_pid(self):
        raise NotImplementedError()


class LocalFileDescriptor(_FileDescriptor):
    """A file descriptor belonging to the current process"""
    LOCAL = "local"

    def ioctl(self, *args):
        return fcntl.ioctl(self.fd, *args)

    def fcntl(self, *args):
        return fcntl.fcntl(self.fd, *args)

    def _get_stat(self):
        return os.fstat(self.fd)

    def _get_pid(self):
        return os.getpid()


class RemoteFileDescriptor(_FileDescriptor):
    """A file descriptor belonging to another process"""
    LOCAL = "remote"

    def _get_pid(self):
        assert self._pid is not None
        return self._pid

    def _get_stat(self):
        return stat_pid_fd(self.pid, self.fd)


def FD(fd, pid=None):
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
