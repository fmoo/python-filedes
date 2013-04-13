#include <Python.h>

#include <sys/types.h>
#include <sys/socket.h>

static PyObject *socket_error;
static PyObject *set_error(void);

PyObject *
fsetsockopt(PyObject *self, PyObject *args)
{
    int fd;
    int level;
    int optname;
    int res;
    char *buf;
    int buflen;
    int flag;

    if (PyArg_ParseTuple(args, "iiii:setsockopt",
                         &fd, &level, &optname, &flag)) {
        buf = (char *) &flag;
        buflen = sizeof flag;
    }
    else {
        PyErr_Clear();
        if (!PyArg_ParseTuple(args, "iiis#:setsockopt",
                              &fd, &level, &optname, &buf, &buflen))
            return NULL;
    }
    res = setsockopt(fd, level, optname, (void *)buf, buflen);
    if (res < 0)
        return set_error();
    Py_INCREF(Py_None);
    return Py_None;
}

PyObject *
fgetsockopt(PyObject *self, PyObject *args)
{
    int fd;
    int level;
    int optname;
    int res;
    PyObject *buf;
    socklen_t buflen = 0;

    if (!PyArg_ParseTuple(args, "iii|i:getsockopt",
                          &fd, &level, &optname, &buflen))
        return NULL;

    if (buflen == 0) {
        int flag = 0;
        socklen_t flagsize = sizeof flag;
        res = getsockopt(fd, level, optname,
                         (void *)&flag, &flagsize);
        if (res < 0)
            return set_error();
        return PyInt_FromLong(flag);
    }
#ifdef __VMS
    /* socklen_t is unsigned so no negative test is needed,
       test buflen == 0 is previously done */
    if (buflen > 1024) {
#else
    if (buflen <= 0 || buflen > 1024) {
#endif
        PyErr_SetString(socket_error,
                        "getsockopt buflen out of range");
        return NULL;
    }
    buf = PyString_FromStringAndSize((char *)NULL, buflen);
    if (buf == NULL)
        return NULL;
    res = getsockopt(fd, level, optname,
                     (void *)PyString_AS_STRING(buf), &buflen);
    if (res < 0) {
        Py_DECREF(buf);
        return set_error();
    }
    _PyString_Resize(&buf, buflen);
    return buf;
}


void
init_posix(void)
{
    PyObject *_socket = PyImport_ImportModule("_socket");
    if (_socket == NULL)
        // TODO: Set exception?
        return;

    socket_error = PyObject_GetAttrString(_socket, "error");
    if (socket_error == NULL)
        // TODO: Set exception?
        return;
}

static PyObject *
set_error(void)
{
#ifdef MS_WINDOWS
    int err_no = WSAGetLastError();
    /* PyErr_SetExcFromWindowsErr() invokes FormatMessage() which
       recognizes the error codes used by both GetLastError() and
       WSAGetLastError */
    if (err_no)
        return PyErr_SetExcFromWindowsErr(socket_error, err_no);
#endif

    return PyErr_SetFromErrno(socket_error);
}


