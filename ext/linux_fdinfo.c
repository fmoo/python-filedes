#include <python2.7/Python.h>

#include <sys/types.h>
#include <dirent.h>


static PyObject *
fdinfo_get_open_fds(PyObject *self, PyObject *args)
{
    PyObject *result = NULL;
    int pid = -1;

    if (!PyArg_ParseTuple(args, "|i", &pid))
        return NULL;

    if (pid == -1) {
        pid = getpid();
    }

    char fddir[256];
    if (sprintf(fddir, "/proc/%d/fd", pid) < 0) {
        return NULL;
    }

    DIR *dir = opendir(fddir);
    if (dir == NULL) {
        return NULL;
    }

    int skipfd = dirfd(dir);
    if (skipfd == -1) {
        goto cleanup_error;
    }

    result = Py_BuildValue("[]");
    if (!result) {
        goto cleanup_error;
    }

    struct dirent dirEntry;
    struct dirent *readdir_result;
    int fd;

    int ri = readdir_r(dir, &dirEntry, &readdir_result);
    if (ri != 0) {
        goto cleanup_error;
    }
    while (readdir_result != NULL) {
        // skip . and ..
        if (dirEntry.d_name[0] == '.') {
            goto next_dirent;
        }

        int sscanf_result; 
        sscanf_result = sscanf(dirEntry.d_name, "%d", &fd);
        if (sscanf_result <= 0) {
            goto cleanup_error;
        }

        // skip the fd associated with the opendir()
        if (skipfd == fd) {
            goto next_dirent;
        }

        PyObject *ifd = Py_BuildValue("i", fd);
        if (!ifd) {
            goto cleanup_error;
        }
        int append_result = PyList_Append(result, ifd);
        Py_DECREF(ifd);
        if (append_result == -1) {
            goto cleanup_error;
        }

next_dirent:
        ri = readdir_r(dir, &dirEntry, &readdir_result);
        if (ri != 0) {
            goto cleanup_error;
        }
    }

    closedir(dir);
    return result;

cleanup_error:
    closedir(dir);
    Py_XDECREF(result);
    return NULL;
}


static PyMethodDef FDInfoMethods[] = {
    {"get_open_fds",  fdinfo_get_open_fds, METH_VARARGS,
      "Returns the open FDs for the given ppid."
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
