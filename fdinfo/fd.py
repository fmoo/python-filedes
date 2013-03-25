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
        return _TYPE_LOOKUP.get(stat.S_IFMT(self.mode),
                                "unknown (0%o)" % stat.S_IFMT(self.mode))

    def __int__(self):
        return self.fd

    def __repr__(self):
        return "<%s file (%d)>" % (self.typestr, self.fd)



if __name__ == '__main__':
    import errno
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("pids", nargs="*", default=[None], type=int, metavar="PID")
    ns = ap.parse_args()
    for pid in ns.pids:
        for fd in get_open_fds(pid):
            try:
                print FD(fd, pid=pid)
            except OSError as e:
                if e.errno == errno.EBADF:
                    print "%d: EBADF" % fd
