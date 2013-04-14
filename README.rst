fdinfo
======
fdinfo is a python library for using file descriptors in a more intuitive way.

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
