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

    struct vnode_fdinfo vnodeinfo;
    int bufferUsed = proc_pidfdinfo(pid, fd, PROC_PIDFDVNODEINFO,
                                    &vnodeinfo, PROC_PIDFDVNODEINFO_SIZE);
    if (bufferUsed != PROC_PIDFDVNODEINFO_SIZE) {
      return NULL;
    }

    PyObject *start_args = Py_BuildValue("((iiiiiillll))",
        vnodeinfo.pvi.vi_stat.vst_mode,
        vnodeinfo.pvi.vi_stat.vst_ino,
        vnodeinfo.pvi.vi_stat.vst_dev,
        vnodeinfo.pvi.vi_stat.vst_nlink,
        vnodeinfo.pvi.vi_stat.vst_uid,
        vnodeinfo.pvi.vi_stat.vst_gid,
        vnodeinfo.pvi.vi_stat.vst_size,
        vnodeinfo.pvi.vi_stat.vst_atime,
        vnodeinfo.pvi.vi_stat.vst_mtime,
        vnodeinfo.pvi.vi_stat.vst_ctime
    );
    if (!start_args) {
      return NULL;
    }

    PyObject *result = PyObject_CallObject(stat_result, start_args);
    if (!result) {
      Py_XDECREF(start_args);
      return NULL;
    }

    Py_XDECREF(start_args);
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
