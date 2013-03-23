import stat
import os

_TYPE_LOOKUP = {
    stat.S_IFBLK: "block",
    stat.S_IFCHR: "character",
    stat.S_IFDIR: "directory",
    stat.S_IFIFO: "fifo",
    stat.S_IFLNK: "symlink",
    stat.S_IFREG: "regular",
    stat.S_IFSOCK: "socket",
    0160000: "whiteout",
}



class FD(object):
    def __init__(self, fd, stat_result=None):
        self.fd = fd
        if stat_result is None:
            stat_result = os.fstat(fd)
        self._stat_result = stat_result
        self.mode & stat.S_IFMT

    @property
    def mode(self):
        return self._stat_result.st_mode
    
    @property
    def typestr(self):
        return _TYPE_LOOKUP.get(self.mode & stat.S_IFMT, "unknown")

    def __int__(self):
        return self.fd

    def __repr__(self):
        return "<%s file (%d)>" % (self.typestr, self.fd)


def get_open_fds(pid=None):
    if pid is None:
        pid = os.getpid()

    return [int(fd) for fd in os.listdir("/proc/%d/fd" % (pid))]


if __name__ == '__main__':
    for fd in get_open_fds():
        print FD(fd)
