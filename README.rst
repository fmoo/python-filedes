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

Sending a PIPE to another process over a unix socket

.. code:: python

  from filedes import FD

  # For a single FD
  FD(sock).socket.send_fd(an_fd)

  # Or for multiple FDs
  FD(sock).socket.send_fds(multiple_fds)


Key features
============
* Get detailed info about fds in both the local as well as external processes
* Perform fcntl and io operations directly on descriptor objects
* Unittest helper class for making sure your tests don't leak fds or threads.
* Set various fd flags in a more native way, such as `fd.set_cloexec()` or `fd.set_nonblocking()`
* Socket helpers let you set socket options in a more native way, such as `fd.socket.set_reuse()`
* A Popen() subclass with a more intelligent `close_fds` for systems with a high fs.file-max set

Platforms
=========
fdinfo is primarily developed on linux, but it doesn't work just there.
It has been tested on the following platforms:

- linux
- OSX
