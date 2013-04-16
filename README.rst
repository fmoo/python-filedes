fdinfo
======
fdinfo is a python library for using file descriptors in a more intuitive way.

Examples
========

Creating a socket with SO_REUSEADR (or SO_REUSEPORT on BSD):

.. code:: python

  from filedes import FD
  s = socket.socket()
  FD(s).socket.set_reuse()

Enabling non-blocking mode on a PIPE

.. code:: python

  import os
  from filedes import FD
  r, w = os.pipe()
  FD(r).set_nonblocking()

Disabling the close on execute bit for a temporary file

.. code:: python

  import tempfile
  from filedes import FD
  tf = tempfile.NamedTemporaryFile()
  FD(tf).set_cloexec(False)

Listing the open FDs and their types of the current PID:

.. code:: python

  from filedes import FD, get_open_fds
  for fd in get_open_fds():
      print fd, FD(fd).typestr

Sending fds to another process over a unix socket

.. code:: python

  from filedes import FD

  # Send a single FD
  FD(sock).socket.send_fd(an_fd)

  # Or for multiple FDs
  FD(sock).socket.send_fds(multiple_fds)

  # To receive one fd (in a different pid)
  an_fd = FD(sock).socket.recv_fd()

  # To receive multiple fds (in a different pid)
  two_fds = FD(sock).socket.recv_fds(2)


Additional Features
-------------------
* Get detailed info about fds of external processes (parent, etc)
* Perform fcntl and ioctl operations directly on descriptor objects
* Unittest helper class for making sure your tests don't leak fds or threads.
* A Popen() subclass with a more intelligent `close_fds` for systems with a high fs.file-max set

Platforms
=========
fdinfo is primarily developed on Linux, but it doesn't work just there.
It has been tested on the following platforms:

- Linux
- OSX

Developing for Darwin is tricky since there is no procfs, so some
operations on filedescriptors in different pids may not work as desired.

This library has been tested with python2.7

Technical Ramblings
===================
Accessing explicit fd metadata is surprisingly nontrivial, so this library
ships with a CPython extension that varies by the platform it's built on.

Even on Linux, where you have the insanely versatile procfs, doing a naive
os.listdir() on the /proc/{os.getpid()}/fd will include the fd of the diropen()
call.  And since there's no low-level diropen API in python itself, an
extension is required to remove the FD without relying on stat()ing each file
in order to see which one returns an EBADF.

Darwin/OSX is trickier, since there's no procfs.  If you look into the lsof
source code, you will eventually make your way to BSD's native `libproc` API.
While this library  is incredibly powerful, there's definitely no API for this
native functionality in Python
