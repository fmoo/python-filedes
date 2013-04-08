import socket
import os


def _unix_socket_helper(path, type, sock_method):
    s = socket.socket(socket.AF_UNIX, type)
    sock_method(s, path)
    return s

def make_unix_socket(path, type):
    if os.path.exists(path):
        os.remove(path)
    return _unix_socket_helper(path, type, socket.socket.bind)

def make_unix_stream_socket(path):
    return make_unix_socket(path, socket.SOCK_STREAM)

def make_unix_dgram_socket(path):
    return make_unix_socket(path, socket.SOCK_DGRAM)

def connect_unix_socket(path, type):
    return _unix_socket_helper(path, type, socket.socket.connect)

def connect_unix_stream_socket(path):
    return connect_unix_socket(path, socket.SOCK_STREAM)

def connect_unix_dgram_socket(path):
    return connect_unix_socket(path, socket.SOCK_DGRAM)
