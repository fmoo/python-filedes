#include <Python.h>
#include <stdlib.h>
#include <unistd.h>
#include "libancillary/ancillary.h"

static
PyObject *ancillary_send_fd(PyObject *self, PyObject *args) {
    int sockfd, fd;
    if (!PyArg_ParseTuple(args, "ii", &sockfd, &fd)) {
        // TODO: Set Exception
        return NULL;
    }

    if (ancil_send_fd(sockfd, fd) != 0) {
        PyErr_SetFromErrno(PyExc_OSError);
        return NULL;
    }

    Py_INCREF(Py_None);
    return Py_None;
}

static
PyObject *ancillary_recv_fd(PyObject *self, PyObject *args) {
    int sockfd, fd;
    if (!PyArg_ParseTuple(args, "i", &sockfd)) {
        // TODO: Set Exception
        return NULL;
    }

    if (ancil_recv_fd(sockfd, &fd) != 0) {
        PyErr_SetFromErrno(PyExc_OSError);
        return NULL;
    }

    return Py_BuildValue("i", fd);
}

static
PyObject *ancillary_send_fds(PyObject *self, PyObject *args) {
    // TODO: Make sure n_fds < ANCIL_MAX_N_FDS
    int sockfd;
    PyObject *py_fds;

    if (!PyArg_ParseTuple(args, "iO!", &sockfd, &PyList_Type, &py_fds)) {
        // TODO: Set Exception
        return NULL;
    }

    int length = PyObject_Size(py_fds);
    int i;
    int *fds = malloc(sizeof(int) * length);

    for (i = 0; i < length; i++) {
        PyObject *py_fd = PySequence_GetItem(py_fds, i);
        if (!PyInt_Check(py_fd)) {
            Py_DECREF(py_fd);
            // TODO: Set Exception
            goto send_fds_cleanup;
        }
        fds[i] = (int)PyInt_AsLong(py_fd);
        Py_DECREF(py_fd);
    }

    if (ancil_send_fds(sockfd, fds, length) != 0) {
        PyErr_SetFromErrno(PyExc_OSError);
        goto send_fds_cleanup;
    }

    free(fds);
    Py_INCREF(Py_None);
    return Py_None;

send_fds_cleanup:
    free(fds);
    return NULL;
}

static
PyObject *ancillary_recv_fds(PyObject *self, PyObject *args) {
    int sockfd, num_fds;
    int *fds;
    if (!PyArg_ParseTuple(args, "ii", &sockfd, &num_fds)) {
        // TODO: Set Exception
        return NULL;
    }

    fds = malloc(sizeof(int) * num_fds);

    if (ancil_recv_fds(sockfd, fds, num_fds) != 0) {
        PyErr_SetFromErrno(PyExc_OSError);
        free(fds);
        return NULL;
    }

    PyObject *result = PyList_New(num_fds);
    int i;

    for (i = 0; i < num_fds; i++) {
        PyList_SetItem(result, i, PyInt_FromLong(fds[i]));
    }

    free(fds);
    return result;
}


static PyMethodDef AncillaryMethods[] = {
    {"send_fd", ancillary_send_fd, METH_VARARGS,
      "send_fd(sockfd, fd)\n\n"
      "Send `fd` over `sockfd` (to potentially other processes)"
    },
    {"recv_fd", ancillary_recv_fd, METH_VARARGS,
      "recv_fd(sockfd) -> integer\n\n"
      "Receive an fd from a `sockfd` (potentially from another process)"
    },
    {"send_fds", ancillary_send_fd, METH_VARARGS,
      "send_fds(sockfd, fds)\n\n"
      "Send multiple `fds` over `sockfd` (to potentially other processes)"
    },
    {"recv_fds", ancillary_recv_fd, METH_VARARGS,
      "recv_fds(sockfd, n_fds) -> list(integer)\n\n"
      "Receive multiple fds from a `sockfd` (potentially from another process)"
    },
    {NULL, NULL, 0, NULL}        /* Sentinel */
};


PyMODINIT_FUNC
init_ancillary(void)
{
    PyObject *m;

    // TODO: Export ANCIL_MAX_N_FDS as an attribute

    m = Py_InitModule("_ancillary", AncillaryMethods);
    if (m == NULL)
        return;
}
