#include <Python.h>
#include <libproc.h>
#include <stdlib.h>
#include <unistd.h>
#include <stdbool.h>


extern void init_posix(void);
extern PyObject *fgetsockopt(PyObject *self, PyObject *args);
extern PyObject *fsetsockopt(PyObject *self, PyObject *args);

static PyObject *posix;
static PyObject *stat_result;

static bool
_filedes_get_proc_fdinfo(pid_t pid, struct proc_fdinfo **procFDInfo,
                         long *numfds) {
    // Figure out the size of the buffer needed to hold the list of open FDs
    int bufferSize = proc_pidinfo(pid, PROC_PIDLISTFDS, 0, 0, 0);
    if (bufferSize == -1) {
        PyErr_SetString(PyExc_OSError, "Unable to get open file handles for fd");
        return false;
    }

    // Get the list of open FDs
    *procFDInfo = (struct proc_fdinfo *)malloc(bufferSize);
    if (!procFDInfo) {
        PyErr_SetString(PyExc_MemoryError, "Error allocating memory for fdinfo buffer");
        return false;
    }

    int bufferUsed = proc_pidinfo(pid, PROC_PIDLISTFDS, 0, *procFDInfo, bufferSize);
    *numfds = bufferUsed / PROC_PIDLISTFD_SIZE;
    return true;
}

static PyObject *
filedes_get_open_fds(PyObject *self, PyObject *args)
{
    pid_t pid = -1;

    if (!PyArg_ParseTuple(args, "|i", &pid))
        return NULL;

    if (pid == -1) {
        pid = getpid();
    }

    // Figure out the size of the buffer needed to hold the list of open FDs
    int bufferSize = proc_pidinfo(pid, PROC_PIDLISTFDS, 0, 0, 0);
    if (bufferSize == -1) {
        PyErr_SetString(PyExc_OSError, "Unable to get open file handles for fd");
        return NULL;
    }

    // Get the list of open FDs
    struct proc_fdinfo *procFDInfo;
    long numberOfProcFDs;

    if (!_filedes_get_proc_fdinfo(pid, &procFDInfo, &numberOfProcFDs)) {
        return NULL;
    }

    PyObject *result = Py_BuildValue("[]");
    if (!result) {
        goto cleanup_error;
    }

    long i;
    for(i = 0; i < numberOfProcFDs; i++) {
        //printf("FD #%d: %d\n", procFDInfo[i].proc_fd, procFDInfo[i].proc_fdtype);
        PyObject *ifd = Py_BuildValue("i", procFDInfo[i].proc_fd);
        if (!ifd) {
            goto cleanup_error;
        }
        int append_result = PyList_Append(result, ifd);
        Py_DECREF(ifd);
        if (append_result == -1) {
            goto cleanup_error;
        }
    }

    free(procFDInfo);
    return result;

cleanup_error:
    Py_XDECREF(result);
    free(procFDInfo);
    return NULL;
}


static PyObject *
filedes_stat_pid_fd(PyObject *self, PyObject *args)
{
    int pid, fd;

    if (!PyArg_ParseTuple(args, "ii", &pid, &fd))
        return NULL;

    // Get the list of open FDs
    struct proc_fdinfo *procFDInfo;
    long numberOfProcFDs;
    if (!_filedes_get_proc_fdinfo(pid, &procFDInfo, &numberOfProcFDs)) {
        return NULL;
    }

    // Find the requested FD in the process' fds in order to get the
    // appropriate fdtype.  Default to VNODE.
    uint32_t proc_fdtype = PROX_FDTYPE_VNODE;
    int i;
    for (i = 0; i < numberOfProcFDs; i++) {
        if (procFDInfo[i].proc_fd == fd) {
            proc_fdtype = procFDInfo[i].proc_fdtype;
        }
    }

    struct vinfo_stat stat;
    PyObject *result = NULL,
             *start_args = NULL;
    switch (proc_fdtype) {
    case PROX_FDTYPE_SOCKET:
        {
            struct socket_fdinfo sockinfo;
            int bufferUsed = proc_pidfdinfo(pid, fd, PROC_PIDFDSOCKETINFO,
                  &sockinfo, PROC_PIDFDSOCKETINFO_SIZE);
            if (bufferUsed != PROC_PIDFDSOCKETINFO_SIZE) {
                goto cleanup_filedes_stat_pid_fd;
            }
            stat = sockinfo.psi.soi_stat;
        }
        break;

    case PROX_FDTYPE_PIPE:
        {
            struct pipe_fdinfo pipeinfo;
            int bufferUsed = proc_pidfdinfo(pid, fd, PROC_PIDFDPIPEINFO,
                  &pipeinfo, PROC_PIDFDPIPEINFO_SIZE);
            if (bufferUsed != PROC_PIDFDPIPEINFO_SIZE) {
                goto cleanup_filedes_stat_pid_fd;
            }
            stat = pipeinfo.pipeinfo.pipe_stat;
        }
        break;

    case PROX_FDTYPE_KQUEUE:
        goto cleanup_filedes_stat_pid_fd;

    default:
        // This should be the default, but it doesnt work for
        // procFDInfo[i].proc_fdtype IN
        // (PROX_FDTYPE_PIPE, PROX_FDTYPE_KQUEUE, PROX_FDTYPE_SOCKET)
        {
            struct vnode_fdinfo vnodeinfo;
            int bufferUsed = proc_pidfdinfo(pid, fd, PROC_PIDFDVNODEINFO,
                  &vnodeinfo, PROC_PIDFDVNODEINFO_SIZE);
            if (bufferUsed != PROC_PIDFDVNODEINFO_SIZE) {
                goto cleanup_filedes_stat_pid_fd;
            }
            stat = vnodeinfo.pvi.vi_stat;
        }
    }

    start_args = Py_BuildValue("((iiliiillll))",
        stat.vst_mode,
        stat.vst_ino,
        stat.vst_dev,
        stat.vst_nlink,
        stat.vst_uid,
        stat.vst_gid,
        stat.vst_size,
        stat.vst_atime,
        stat.vst_mtime,
        stat.vst_ctime
    );
    if (!start_args) {
        goto cleanup_filedes_stat_pid_fd;
    }

    result = PyObject_CallObject(stat_result, start_args);
    if (!result) {
        goto cleanup_filedes_stat_pid_fd;
    }

cleanup_filedes_stat_pid_fd:
    Py_XDECREF(start_args);
    free(procFDInfo);
    return result;
}


static PyMethodDef FDInfoMethods[] = {
    {"get_open_fds", filedes_get_open_fds, METH_VARARGS,
      "Returns the open FDs for the given ppid."
    },
    {"stat_pid_fd", filedes_stat_pid_fd, METH_VARARGS,
      "Returns a stat struct for the given PID and FD."
    },
    {"getsockopt", fgetsockopt, METH_VARARGS,
     "getsockopt(fd, level, option[, buffersize]) -> value\n\n"
     "Get a socket option.  See the Unix manual for level and option.\n"
     "If a nonzero buffersize argument is given, the return value is a\n"
     "string of that length; otherwise it is an integer."
    },
    {"setsockopt", fsetsockopt, METH_VARARGS,
     "setsockopt(fd, level, option, value)\n\n"
     "Set a socket option.  See the Unix manual for level and option.\n"
     "The value argument can either be an integer or a string."
    },
    {NULL, NULL, 0, NULL}        /* Sentinel */
};


PyMODINIT_FUNC
init_filedes(void)
{
    PyObject *m;

    m = Py_InitModule("_filedes", FDInfoMethods);
    if (m == NULL)
        return;

    posix = PyImport_ImportModule("posix");
    if (posix == NULL)
        return;

    stat_result = PyObject_GetAttrString(posix, "stat_result");
    if (stat_result == NULL)
        return;

    init_posix();
}
