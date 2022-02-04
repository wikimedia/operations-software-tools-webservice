import socket

from toolsws.backends.kubernetes import (
    K8sClient,
    KubernetesConfigFileNotFoundException,
    KubernetesRoutingHandler,
)
from toolsws.tool import Tool


class ProxyException(Exception):
    pass


def get_active_dynamicproxy():
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


def register_dynamicproxy(port):
    """Register with the dynamicproxy."""
    proxy = get_active_dynamicproxy()
    if len(proxy.strip()) == 0:
        # Kill switch for dynamicproxy: we don't want to create and deploy new
        # tools-webservice versions to enable/disable dynamicproxy registrations
        # Instead, treat empty /etc/active-proxy (controlled via Puppet) as
        # "do not use dynamicproxy"
        return

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    current_ip = socket.gethostbyname(socket.getfqdn())
    cmd = "registerCanonical"

    try:
        sock.connect((proxy, 8282))
        sock.sendall(
            ("%s\n.*\nhttp://%s:%u\n" % (cmd, current_ip, port)).encode(
                "utf-8"
            )
        )
        res = sock.recv(1024).decode("utf-8")
        if res != "ok":
            raise ProxyException("Port registration failed!")
    finally:
        sock.close()


def unregister_dynamicproxy():
    """Unregister with the dynamicproxy."""
    proxy = get_active_dynamicproxy()
    if len(proxy.strip()) == 0:
        return

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((proxy, 8282))
        sock.sendall("unregister\n.*\n".encode("utf-8"))
        res = sock.recv(1024).decode("utf-8")
        if res != "ok":
            raise ProxyException("Port unregistration failed!")
    finally:
        sock.close()


def get_kubernetes_routing_handler():
    tool = Tool.from_currentuser()

    try:
        k8s_client = K8sClient.from_file()
    except KubernetesConfigFileNotFoundException:
        return None

    return KubernetesRoutingHandler(
        k8s_client,
        tool,
        "tool-{}".format(tool.name),
        {"webservice.toolforge.org/gridengine": "true"},
    )


def register_kubernetes(port):
    """Register with the Kubernetes ingress."""
    routing_handler = get_kubernetes_routing_handler()
    if routing_handler:
        routing_handler.start_external(
            socket.gethostbyname(socket.getfqdn()), port
        )


def unregister_kubernetes():
    """Unregister with the Kubernetes ingress."""
    routing_handler = get_kubernetes_routing_handler()
    if routing_handler:
        routing_handler.stop()


def register(port):
    """Register with all used proxies."""
    register_dynamicproxy(port)
    register_kubernetes(port)


def unregister():
    """Unregister with all used proxies."""
    unregister_dynamicproxy()
    unregister_kubernetes()
