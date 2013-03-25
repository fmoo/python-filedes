import stat
import os

import _fdinfo
get_open_fds = _fdinfo.get_open_fds

def stat_pid_fd(pid, fd):
    # TODO: Implement for darwin
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
    def __init__(self, fd, stat_result, pid):
        self.fd = fd
        self.pid = pid
        self._stat_result = stat_result

    @property
    def mode(self):
        return self._stat_result.st_mode
    
    @property
    def typestr(self):
        return _TYPE_LOOKUP.get(stat.S_IFMT(self.mode),
                                "unknown (0%o)" % stat.S_IFMT(self.mode))

    def __int__(self):
        return self.fd

    def __repr__(self):
        return "<%s %s file #%d>" % (self.LOCAL, self.typestr, self.fd)


class LocalFileDescriptor(_FileDescriptor):
    """A file descriptor belonging to the current process"""
    LOCAL = "local"


class RemoteFileDescriptor(_FileDescriptor):
    """A file descriptor belonging to another process"""
    LOCAL = "remote"


def FD(fd, stat_result=None, pid=None):
    if pid is None:
        pid = os.getpid()
        local = True
    elif pid == os.getpid():
        local = True
    else:
        local = False

    if stat_result is None:
        if local:
            stat_result = os.fstat(fd)
        else:
            stat_result = stat_pid_fd(pid, fd)

    if local:
        return LocalFileDescriptor(fd, stat_result, pid)
    else:
        return RemoteFileDescriptor(fd, stat_result, pid)


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
