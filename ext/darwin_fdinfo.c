#include <python2.7/Python.h>
#include <libproc.h>
#include <stdlib.h>
#include <unistd.h>

static PyObject *
fdinfo_get_open_fds(PyObject *self, PyObject *args)
{
    int pid = -1;

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
    struct proc_fdinfo *procFDInfo = (struct proc_fdinfo *)malloc(bufferSize);
    if (!procFDInfo) {
        PyErr_SetString(PyExc_MemoryError, "Error allocating memory for fdinfo buffer");
        return NULL;
    }

    int bufferUsed = proc_pidinfo(pid, PROC_PIDLISTFDS, 0, procFDInfo, bufferSize);
    int numberOfProcFDs = bufferUsed / PROC_PIDLISTFD_SIZE;

    PyObject *result = Py_BuildValue("[]");
    if (!result) {
        goto cleanup_error;
    }

    int i;
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
fdinfo_stat_pid_fd(PyObject *self, PyObject *args)
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

    /**
     * TODO: Instead of just returning mode, take this tuple and
     * dump it into posix.stat_result
     *
     * st_mode=33188, st_ino=9065647, st_dev=234881028L, st_nlink=1, st_uid=1717611107, st_gid=1876110778, st_size=73728, st_atime=1364460851, st_mtime=1364460851, st_ctime=1364460851
     */
    PyObject *mode = Py_BuildValue("i", vnodeinfo.pvi.vi_stat.vst_mode);

    if (!mode) {
        return NULL;
    }

    return mode;
}


static PyMethodDef FDInfoMethods[] = {
    {"get_open_fds", fdinfo_get_open_fds, METH_VARARGS,
      "Returns the open FDs for the given ppid."
    },
    {"stat_pid_fd", fdinfo_stat_pid_fd, METH_VARARGS,
      "Returns a stat struct for the given PID and FD."
    },
    {NULL, NULL, 0, NULL}        /* Sentinel */
};


PyMODINIT_FUNC
init_fdinfo(void)
{
    PyObject *m;

    m = Py_InitModule("_fdinfo", FDInfoMethods);
    if (m == NULL)
        return;
}
