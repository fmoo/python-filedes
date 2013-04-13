fdinfo
======
fdinfo is a python library for using file descriptors in a more intuitive way.

Key features
============
* Get detailed info about fds in both the local as well as external processes
* Perform fcntl (TBD: read/write) operations directly on descriptor objects
* Unittest helper class for making sure your tests don't leak fds or threads.
* TBD: Set various socket and fd flags in a more native way, such as `fd.set_cloexec()` or `fd.set_nonblocking()`
* Socket helpers let you set socket options in a more native way, such as `fd.socket.set_reuseaddr()`
