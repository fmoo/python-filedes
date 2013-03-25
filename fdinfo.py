import stat
import os

try:
    import _fdinfo
    get_open_fds = _fdinfo.get_open_fds
except ImportError:
    import warnings
    warnings.warn("Error importing extension module.  "
                  "Some functionality may be broken")

    def get_open_fds(pid=None):
        if pid is None:
            pid = os.getpid()

        return [int(fd) for fd in os.listdir("/proc/%d/fd" % (pid))]

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


class FD(object):
    def __init__(self, fd, stat_result=None, pid=None):
        self.fd = fd
        if stat_result is None:
            if pid is None or pid == os.getpid():
                stat_result = os.fstat(fd)
            else:
                stat_result = stat_pid_fd(pid, fd)

        self._stat_result = stat_result

    @property
    def mode(self):
        return self._stat_result.st_mode
    
    @property
    def typestr(self):
        return _TYPE_LOOKUP.get(stat.S_IFMT(self.mode), "unknown")

    def __int__(self):
        return self.fd

    def __repr__(self):
        return "<%s file (%d)>" % (self.typestr, self.fd)



if __name__ == '__main__':
    for fd in get_open_fds():
        print FD(fd)
