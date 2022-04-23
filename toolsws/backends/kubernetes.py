from __future__ import print_function

import json
import os
import subprocess
import sys
import time

import requests
import urllib3
import yaml

from toolsws.tool import Tool
from toolsws.utils import parse_quantity
from toolsws.wstypes import GenericWebService
from toolsws.wstypes import JSWebService
from toolsws.wstypes import LighttpdPlainWebService
from toolsws.wstypes import LighttpdWebService
from toolsws.wstypes import PythonWebService

from .backend import Backend


class KubernetesException(Exception):
    """Base class for exceptions related to the Kubernetes backend."""


class KubernetesConfigFileNotFoundException(KubernetesException):
    """Raised when a Kubernetes client is attempted to be created but the configuration file does not exist."""


class KubernetesRoutingHandler:
    """Create and manage service and ingress objects to route HTTP requests."""

    def __init__(self, api, tool, namespace, extra_labels=None):
        self.api = api
        self.tool = tool
        self.namespace = namespace

        # Labels for all objects created by this webservice
        # TODO: unduplicate
        self.webservice_labels = {
            "app.kubernetes.io/component": "web",
            "app.kubernetes.io/managed-by": "webservice",
            "toolforge": "tool",
            "name": self.tool.name,
        }

        self.webservice_label_selector = ",".join(
            [
                "{k}={v}".format(k=k, v=v)
                for k, v in self.webservice_labels.items()
                if k not in ["toolforge", "name"]
            ]
        )

        # this is after label_selector is created, to make sure we don't have conflicting
        # objects from different sources
        if extra_labels is not None:
            self.webservice_labels.update(extra_labels)

    def _find_objs(self, kind, selector):
        """
        Return objects of kind matching selector, or None if they don't exist.

        Objects that are currently being deleted by the Kubernetes service
        (meaning they have a non-empty metadata.deletionTimestamp value) are
        ignored.
        """
        objs = self.api.get_objects(kind, selector=selector)
        # Ignore objects that are in the process of being deleted.
        return [
            o
            for o in objs
            if o["metadata"].get("deletionTimestamp", None) is None
        ]

    def _get_ingress_subdomain(self):
        """
        Returns the full spec of the domain-based routing ingress object for
        this webservice
        """
        return {
            "apiVersion": "networking.k8s.io/v1",
            "kind": "Ingress",
            "metadata": {
                "name": "{}-subdomain".format(self.tool.name),
                "namespace": self.namespace,
                "labels": self.webservice_labels,
            },
            "spec": {
                "rules": [
                    {
                        "host": "{}.toolforge.org".format(self.tool.name),
                        "http": {
                            "paths": [
                                {
                                    "path": "/",
                                    "pathType": "Prefix",
                                    "backend": {
                                        "service": {
                                            "name": self.tool.name,
                                            "port": {
                                                "number": 8000,
                                            },
                                        },
                                    },
                                },
                            ],
                        },
                    },
                ],
            },
        }

    def _get_svc(self, target_port=8000, selector=None):
        """
        Return full spec for the webservice service
        """
        service = {
            "kind": "Service",
            "apiVersion": "v1",
            "metadata": {
                "name": self.tool.name,
                "namespace": self.namespace,
                "labels": self.webservice_labels,
            },
            "spec": {
                "ports": [
                    {
                        "name": "http",
                        "protocol": "TCP",
                        "port": 8000,
                        "targetPort": target_port,
                    }
                ],
            },
        }

        if selector:
            service["spec"]["selector"] = selector

        return service

    def _get_endpoints(self, ip, port):
        """
        Return full spec for an external endpoint object with the specified IP address and port.
        """
        return {
            "kind": "Endpoints",
            "apiVersion": "v1",
            "metadata": {
                "name": self.tool.name,
                "namespace": self.namespace,
                "labels": self.webservice_labels,
            },
            "subsets": [
                {
                    "addresses": [
                        {
                            "ip": ip,
                        },
                    ],
                    "ports": [
                        {
                            "port": port,
                            "name": "http",
                        }
                    ],
                }
            ],
        }

    def _start_common(self, target_port=8000, service_selector=None):
        """Create objects used for routing to a web service on any backend."""
        svcs = self._find_objs("services", self.webservice_label_selector)
        if len(svcs) == 0:
            self.api.create_object(
                "services", self._get_svc(target_port, service_selector)
            )

        ingresses = self._find_objs(
            "ingresses", self.webservice_label_selector
        )
        if len(ingresses) == 0:
            self.api.create_object("ingresses", self._get_ingress_subdomain())

    def start_external(self, ip, port):
        """Create objects required to route traffic to an external service with the specified address and port."""
        self._start_common(target_port=port)

        endpoints = self._find_objs(
            "endpoints", self.webservice_label_selector
        )
        if len(endpoints) == 0:
            self.api.create_object("endpoints", self._get_endpoints(ip, port))

    def start_kubernetes(self):
        """Create objects required to route traffic to a Kubernetes webservice."""
        self._start_common(service_selector={"name": self.tool.name})

    def stop(self):
        """Clean up any created objects."""
        self.api.delete_objects("ingresses", self.webservice_label_selector)
        self.api.delete_objects("services", self.webservice_label_selector)


class KubernetesBackend(Backend):
    """
    Backend spawning webservices with a k8s Deployment + Service
    """

    DEFAULT_RESOURCES = {
        "limits": {
            "memory": "512Mi",
            "cpu": "0.5",
        },
        "requests": {
            # Pods are guaranteed at least this many resources
            "memory": "256Mi",
            "cpu": "0.125",
        },
    }

    DEFAULT_JDK_RESOURCES = (
        {
            "limits": {
                # Higher Memory Limit for JDK based webservices, but not
                # higher request, so it can use more memory before being
                # killed, but will die when there is a memory crunch.
                "memory": "1Gi",
                "cpu": "0.5",
            },
            "requests": {
                # Pods are guaranteed at least this many resources
                "memory": "256Mi",
                "cpu": "0.125",
            },
        },
    )

    CONFIG = {
        "php5.6": {
            "deprecated": True,
            "cls": LighttpdWebService,
            "image": "toolforge-php5-sssd-web",
            "resources": DEFAULT_RESOURCES,
        },
        "php7.2": {
            "cls": LighttpdWebService,
            "image": "toolforge-php72-sssd-web",
            "resources": DEFAULT_RESOURCES,
        },
        "php7.3": {
            "cls": LighttpdWebService,
            "image": "toolforge-php73-sssd-web",
            "resources": DEFAULT_RESOURCES,
        },
        "php7.4": {
            "cls": LighttpdWebService,
            "image": "toolforge-php74-sssd-web",
            "resources": DEFAULT_RESOURCES,
        },
        "tcl": {
            "cls": LighttpdPlainWebService,
            "image": "toolforge-tcl86-sssd-web",
            "resources": DEFAULT_RESOURCES,
        },
        "python": {
            "deprecated": True,
            "cls": PythonWebService,
            "image": "toolforge-python34-sssd-web",
            "resources": DEFAULT_RESOURCES,
        },
        "python3.5": {
            "cls": PythonWebService,
            "image": "toolforge-python35-sssd-web",
            "resources": DEFAULT_RESOURCES,
        },
        "python3.7": {
            "cls": PythonWebService,
            "image": "toolforge-python37-sssd-web",
            "resources": DEFAULT_RESOURCES,
        },
        "python3.9": {
            "cls": PythonWebService,
            "image": "toolforge-python39-sssd-web",
            "resources": DEFAULT_RESOURCES,
        },
        "python2": {
            "deprecated": True,
            "cls": PythonWebService,
            "image": "toolforge-python2-sssd-web",
            "resources": DEFAULT_RESOURCES,
        },
        "ruby2": {
            "deprecated": True,
            "cls": GenericWebService,
            "image": "toolforge-ruby21-sssd-web",
            "resources": DEFAULT_RESOURCES,
        },
        "ruby25": {
            "cls": GenericWebService,
            "image": "toolforge-ruby25-sssd-web",
            "resources": DEFAULT_RESOURCES,
        },
        "ruby27": {
            "cls": GenericWebService,
            "image": "toolforge-ruby27-sssd-web",
            "resources": DEFAULT_RESOURCES,
        },
        "golang": {
            "deprecated": True,
            "cls": GenericWebService,
            "image": "toolforge-golang-sssd-web",
            "resources": DEFAULT_RESOURCES,
        },
        "golang111": {
            "cls": GenericWebService,
            "image": "toolforge-golang111-sssd-web",
            "resources": DEFAULT_RESOURCES,
        },
        "jdk8": {
            "deprecated": True,
            "cls": GenericWebService,
            "image": "toolforge-jdk8-sssd-web",
            "resources": DEFAULT_JDK_RESOURCES,
        },
        "jdk11": {
            "cls": GenericWebService,
            "image": "toolforge-jdk11-sssd-web",
            "resources": DEFAULT_JDK_RESOURCES,
        },
        "jdk17": {
            "cls": GenericWebService,
            "image": "toolforge-jdk17-sssd-web",
            "resources": DEFAULT_JDK_RESOURCES,
        },
        "nodejs": {
            "deprecated": True,
            "cls": JSWebService,
            "image": "toolforge-node6-sssd-web",
            "resources": DEFAULT_RESOURCES,
        },
        "node10": {
            "cls": JSWebService,
            "image": "toolforge-node10-sssd-web",
            "resources": DEFAULT_RESOURCES,
        },
        "node12": {
            "cls": JSWebService,
            "image": "toolforge-node12-sssd-web",
            "resources": DEFAULT_RESOURCES,
        },
        "perl5.32": {
            "cls": LighttpdPlainWebService,
            "image": "toolforge-perl532-sssd-web",
            "resources": DEFAULT_RESOURCES,
        },
    }

    def __init__(
        self,
        tool,
        wstype,
        mem=None,
        cpu=None,
        replicas=1,
        extra_args=None,
    ):
        super(KubernetesBackend, self).__init__(
            tool, wstype, extra_args=extra_args
        )

        config = KubernetesBackend.CONFIG[self.wstype]

        self.project = Tool.get_current_project()
        self.webservice = config["cls"](tool, extra_args)
        self.container_image = "{registry}/{image}:latest".format(
            registry="docker-registry.tools.wmflabs.org",
            image=config["image"],
        )

        self.container_resources = config["resources"]

        if mem:
            dec_mem = parse_quantity(mem)
            if dec_mem < parse_quantity("256Mi"):
                self.container_resources["requests"]["memory"] = mem
            else:
                self.container_resources["requests"]["memory"] = str(
                    dec_mem / 2
                )
            self.container_resources["limits"]["memory"] = mem

        if cpu:
            dec_cpu = parse_quantity(cpu)
            if dec_cpu < parse_quantity("250m"):
                self.container_resources["requests"]["cpu"] = cpu
            else:
                self.container_resources["requests"]["cpu"] = str(dec_cpu / 2)
            self.container_resources["limits"]["cpu"] = cpu

        self.replicas = replicas
        self.api = K8sClient.from_file()
        self.routing_handler = KubernetesRoutingHandler(
            self.api, self.tool, self._get_ns()
        )

        # Labels for all objects created by this webservice
        self.webservice_labels = {
            "app.kubernetes.io/component": "web",
            "app.kubernetes.io/managed-by": "webservice",
            "toolforge": "tool",
            "name": self.tool.name,
        }

        self.webservice_label_selector = ",".join(
            [
                "{k}={v}".format(k=k, v=v)
                for k, v in self.webservice_labels.items()
                if k not in ["toolforge", "name"]
            ]
        )

    def _get_ns(self):
        return "tool-{}".format(self.tool.name)

    def _find_objs(self, kind, selector):
        """
        Return objects of kind matching selector, or None if they don't exist.

        Objects that are currently being deleted by the Kubernetes service
        (meaning they have a non-empty metadata.deletionTimestamp value) are
        ignored.
        """
        objs = self.api.get_objects(kind, selector=selector)
        # Ignore objects that are in the process of being deleted.
        return [
            o
            for o in objs
            if o["metadata"].get("deletionTimestamp", None) is None
        ]

    def _wait_for_pods(self, label_selector, timeout=30):
        """
        Wait for at least 1 pod to become 'ready'
        """
        for _ in range(timeout):
            pods = self._find_objs("pods", label_selector)
            if self._any_pod_in_state(pods, "Running"):
                return True
            time.sleep(1)
        return False

    def _get_deployment(self):
        """
        Return the full spec of the deployment object for this webservice
        """
        cmd = [
            "/usr/bin/webservice-runner",
            "--type",
            self.webservice.name,
            "--port",
            "8000",
        ]
        if self.extra_args:
            cmd.extend(self.extra_args)

        ports = [{"name": "http", "containerPort": 8000, "protocol": "TCP"}]

        return {
            "kind": "Deployment",
            "apiVersion": "apps/v1",
            "metadata": {
                "name": self.tool.name,
                "namespace": self._get_ns(),
                "labels": self.webservice_labels,
            },
            "spec": {
                "replicas": self.replicas,
                "selector": {"matchLabels": self.webservice_labels},
                "template": {
                    "metadata": {"labels": self.webservice_labels},
                    "spec": self._get_container_spec(
                        "webservice",
                        self.container_image,
                        cmd,
                        self.container_resources,
                        ports,
                    ),
                },
            },
        }

    def _get_shell_pod(self, name):
        """Get the specification for an interactive pod."""
        cmd = ["/bin/bash", "-il"]
        if self.extra_args:
            cmd = self.extra_args
        return {
            "apiVersion": "v1",
            "kind": "Pod",
            "metadata": {
                "namespace": self._get_ns(),
                "name": name,
                "labels": {
                    "name": name,
                    "app.kubernetes.io/component": "webservice-interactive",
                    "app.kubernetes.io/managed-by": "webservice",
                    "app.kubernetes.io/version": "2",
                    # Needed to trigger mounting of volumes
                    "toolforge": "tool",
                },
            },
            "spec": self._get_container_spec(
                name,
                self.container_image,
                cmd,
                resources=self.container_resources,
                ports=None,
                stdin=True,
                tty=True,
            ),
        }

    def _get_container_spec(
        self,
        name,
        container_image,
        cmd,
        resources,
        ports=None,
        stdin=False,
        tty=False,
    ):
        """Get the specification for a container."""
        homedir = "/data/project/{toolname}/".format(toolname=self.tool.name)
        return {
            "containers": [
                {
                    "name": name,
                    "image": container_image,
                    "command": cmd,
                    "workingDir": homedir,
                    "ports": ports,
                    "resources": resources,
                    "tty": tty,
                    "stdin": stdin,
                }
            ]
        }

    def _any_pod_in_state(self, podlist, state):
        """
        Returns true if any pod in the input list of pods are in a given state
        """
        for pod in podlist:
            if pod["status"]["phase"] == state:
                return True

        return False

    def request_start(self):
        self.webservice.check(self.wstype)

        deployments = self._find_objs(
            "deployments", self.webservice_label_selector
        )
        if len(deployments) == 0:
            self.api.create_object("deployments", self._get_deployment())

        self.routing_handler.start_kubernetes()

    def request_stop(self):
        self.routing_handler.stop()

        selector = self.webservice_label_selector
        self.api.delete_objects("deployments", selector)
        self.api.delete_objects(
            "replicasets", "name={name}".format(name=self.tool.name)
        )
        self.api.delete_objects("pods", selector)

    def request_restart(self):
        # For most intents and purposes, the only thing necessary
        # to restart a Kubernetes application is to delete the pods.
        print("Restarting...")
        self.api.delete_objects("pods", self.webservice_label_selector)
        # TODO: It would be cool and not terribly hard here to detect a pod
        # with an error or crash state and dump the logs of that pod for the
        # user to examine.
        if not self._wait_for_pods(self.webservice_label_selector, timeout=30):
            print(
                "Your webservice is taking quite while to restart. If it isn't"
                " up shortly, run a 'webservice stop' and the start command "
                "used to run this webservice to begin with.",
                file=sys.stderr,
            )
            sys.exit(1)

    def get_state(self):
        # TODO: add some state concept around ingresses
        pods = self._find_objs("pods", self.webservice_label_selector)
        if self._any_pod_in_state(pods, "Running"):
            return Backend.STATE_RUNNING
        if self._any_pod_in_state(pods, "Pending"):
            return Backend.STATE_PENDING
        svcs = self._find_objs("services", self.webservice_label_selector)
        deployments = self._find_objs(
            "deployments", self.webservice_label_selector
        )
        if len(svcs) != 0 and len(deployments) != 0:
            return Backend.STATE_PENDING
        else:
            return Backend.STATE_STOPPED

    def shell(self):
        """Run an interactive container on the k8s cluster."""
        name = "shell-{}".format(int(time.time()))

        shell_env = os.environ.copy()
        shell_env["GOMAXPROCS"] = "1"

        # --overrides is used because there does not seem to be any other way
        # to tell `kubectl run` what workingDir to use for the container. This
        # is annoying, but mostly reasonable as a typical Docker image would
        # set a consistent workingDir in its definition rather than the
        # backwards compatible with grid engine system that Toolforge uses of
        # mounting in an external $HOME.
        cmd = [
            "/usr/bin/kubectl",
            "run",
            name,
            "--attach=true",
            "--stdin=true",
            "--tty=true",
            "--restart=Never",
            "--rm=true",
            "--wait=true",
            "--quiet=true",
            "--pod-running-timeout=1m",
            "--image={}".format(self.container_image),
            "--overrides={}".format(json.dumps(self._get_shell_pod(name))),
            "--command=true",
            "--",
        ]
        if self.extra_args:
            cmd.extend(self.extra_args)
        else:
            cmd.extend(["/bin/bash", "-il"])

        try:
            kubectl = subprocess.Popen(cmd, env=shell_env)
            kubectl.wait()
            return kubectl.returncode
        finally:
            # Belt & suspenders cleanup just in case kubectl leaks the pod
            self.api.delete_objects("pods", "name={}".format(name))


# T253412: Disable warnings about unverifed TLS certs when talking to the
# Kubernetes API endpoint
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class K8sClient(object):
    """Kubernetes API client."""

    VERSIONS = {
        "deployments": "apps/v1",
        "endpoints": "v1",
        "ingresses": "networking.k8s.io/v1",
        "pods": "v1",
        "replicasets": "apps/v1",
        "services": "v1",
    }

    @classmethod
    def from_file(cls, filename=None):
        """Create a client from a kubeconfig file."""
        if not filename:
            filename = os.getenv("KUBECONFIG", "~/.kube/config")
        filename = os.path.expanduser(filename)

        if not os.path.exists(filename):
            raise KubernetesConfigFileNotFoundException(filename)

        with open(filename) as f:
            data = yaml.safe_load(f.read())
        return cls(data)

    def __init__(self, config, timeout=10):
        """Constructor."""
        self.config = config
        self.timeout = timeout
        self.context = self._find_cfg_obj(
            "contexts", config["current-context"]
        )
        self.cluster = self._find_cfg_obj("clusters", self.context["cluster"])
        self.server = self.cluster["server"]
        self.namespace = self.context["namespace"]

        user = self._find_cfg_obj("users", self.context["user"])
        self.session = requests.Session()
        self.session.cert = (user["client-certificate"], user["client-key"])
        # T253412: We are deliberately not validating the api endpoint's TLS
        # certificate. The only way to do this with a self-signed cert is to
        # pass the path to a CA bundle. We actually *can* do that, but with
        # python2 we have seen the associated clean up code fail and leave
        # /tmp full of orphan files.
        self.session.verify = False

    def _find_cfg_obj(self, kind, name):
        """Lookup a named object in our config."""
        for obj in self.config[kind]:
            if obj["name"] == name:
                return obj[kind[:-1]]
        raise KeyError(
            "Key {} not found in {} section of config".format(name, kind)
        )

    def _make_kwargs(self, url, **kwargs):
        """Setup kwargs for a Requests request."""
        version = kwargs.pop("version", "v1")
        if version == "v1":
            root = "api"
        else:
            root = "apis"
        kwargs["url"] = "{}/{}/{}/namespaces/{}/{}".format(
            self.server, root, version, self.namespace, url
        )
        name = kwargs.pop("name", None)
        if name is not None:
            kwargs["url"] = "{}/{}".format(kwargs["url"], name)
        if "timeout" not in kwargs:
            kwargs["timeout"] = self.timeout
        return kwargs

    def _get(self, url, **kwargs):
        """GET request."""
        r = self.session.get(**self._make_kwargs(url, **kwargs))
        r.raise_for_status()
        return r.json()

    def _post(self, url, **kwargs):
        """POST request."""
        r = self.session.post(**self._make_kwargs(url, **kwargs))
        r.raise_for_status()
        return r.status_code

    def _delete(self, url, **kwargs):
        """DELETE request."""
        r = self.session.delete(**self._make_kwargs(url, **kwargs))
        r.raise_for_status()
        return r.status_code

    def get_objects(self, kind, selector=None):
        """Get list of objects of the given kind in the namespace."""
        return self._get(
            kind,
            params={"labelSelector": selector},
            version=K8sClient.VERSIONS[kind],
        )["items"]

    def delete_objects(self, kind, selector=None):
        """Delete objects of the given kind in the namespace."""
        if kind == "services":
            # Annoyingly Service does not have a Delete Collection option
            for svc in self.get_objects(kind, selector):
                self._delete(
                    kind,
                    name=svc["metadata"]["name"],
                    version=K8sClient.VERSIONS[kind],
                )
        else:
            self._delete(
                kind,
                params={"labelSelector": selector},
                version=K8sClient.VERSIONS[kind],
            )

    def create_object(self, kind, spec):
        """Create an object of the given kind in the namespace."""
        return self._post(
            kind,
            json=spec,
            version=K8sClient.VERSIONS[kind],
        )
