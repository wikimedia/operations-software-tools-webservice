import socket


class ProxyException(Exception):
    pass


def get_active_proxy():
    """Return the active master proxy to register with"""
    with open("/etc/active-proxy", "r") as f:
        return f.read().strip()


def get_open_port():
    """Tries to get a random open port to listen on

    It does this by starting to listen on a socket, letting the kernel
    determine the open port. It then immediately closes it and returns the
    port.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def register(port):
    """Register with the master proxy."""
    proxy = get_active_proxy()
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    current_ip = socket.gethostbyname(socket.getfqdn())
    cmd = "registerCanonical"

    try:
        sock.connect((proxy, 8282))
        sock.sendall("%s\n.*\nhttp://%s:%u\n" % (cmd, current_ip, port))
        res = sock.recv(1024)
        if res != "ok":
            raise ProxyException("Port registration failed!")
    finally:
        sock.close()


def unregister():
    """Unregister with the master proxy."""
    proxy = get_active_proxy()
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((proxy, 8282))
        sock.sendall("unregister\n.*\n")
        res = sock.recv(1024)
        if res != "ok":
            raise ProxyException("Port unregistration failed!")
    finally:
        sock.close()
