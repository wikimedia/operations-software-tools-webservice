from datetime import datetime
from functools import lru_cache
import json
import os
import subprocess
import sys
import time
from typing import Any, ClassVar, Dict, Optional

from toolforge_weld.kubernetes import K8sClient, parse_quantity
import yaml

from toolsws.backends.backend import Backend
from toolsws.tool import Tool
from toolsws.wstypes import GenericWebService
from toolsws.wstypes import JSWebService
from toolsws.wstypes import LighttpdPlainWebService
from toolsws.wstypes import LighttpdWebService
from toolsws.wstypes import PythonWebService


DEFAULT_HTTP_PORT = 8000
STARTED_AT_ANNOTATION = "toolforge.org/started-at"


class KubernetesRoutingHandler:
    """Create and manage service and ingress objects to route HTTP requests."""

    DEFAULT_PUBLIC_DOMAIN: ClassVar[str] = "toolforge.org"

    def __init__(
        self,
        *,
        api: K8sClient,
        tool: Tool,
        namespace: str,
        webservice_config: Dict[str, Any],
        extra_labels: Optional[Dict[str, str]] = None,
    ):
        self.api = api
        self.tool = tool
        self.namespace = namespace

        self.domain = webservice_config.get(
            "public_domain", self.DEFAULT_PUBLIC_DOMAIN
        )

        # Labels for all objects created by this webservice
        # TODO: unduplicate
        self.webservice_labels = {
            "app.kubernetes.io/component": "web",
            "app.kubernetes.io/managed-by": "webservice",
            "toolforge": "tool",
            "name": self.tool.name,
        }

        self.webservice_label_selector = {
            k: v
            for k, v in self.webservice_labels.items()
            if k not in ["toolforge", "name"]
        }

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
        objs = self.api.get_objects(kind, label_selector=selector)
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
                        "host": f"{self.tool.name}.{self.domain}",
                        "http": {
                            "paths": [
                                {
                                    "path": "/",
                                    "pathType": "Prefix",
                                    "backend": {
                                        "service": {
                                            "name": self.tool.name,
                                            "port": {
                                                "number": DEFAULT_HTTP_PORT,
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

    def _get_svc(self, target_port=DEFAULT_HTTP_PORT, selector=None):
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
                        "port": DEFAULT_HTTP_PORT,
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

    def _start_common(
        self, target_port=DEFAULT_HTTP_PORT, service_selector=None
    ):
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
        self.api.delete_objects(
            "ingresses", label_selector=self.webservice_label_selector
        )
        self.api.delete_objects(
            "services", label_selector=self.webservice_label_selector
        )


class KubernetesBackend(Backend):
    """
    Backend spawning webservices with a k8s Deployment + Service
    """

    DEFAULT_RESOURCES = {
        "default": {
            "limits": {
                "memory": "512Mi",
                "cpu": "0.5",
            },
            "requests": {
                # Pods are guaranteed at least this many resources
                "memory": "256Mi",
                "cpu": "0.125",
            },
        },
        "jdk": {
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
    }

    CONFIG_VARIANT_KEY = "webservice"
    # TODO: make configurable
    CONFIG_IMAGE_TAG = "latest"
    CONFIG_SUPPORTED_WS_TYPES = {
        "generic": GenericWebService,
        "js": JSWebService,
        "lighttpd": LighttpdWebService,
        "lighttpd-plain": LighttpdPlainWebService,
        "python": PythonWebService,
    }

    DEFAULT_BUILD_SERVICE_REGISTRY = "tools-harbor.wmcloud.org"

    @staticmethod
    @lru_cache()
    def get_types():
        client = K8sClient.from_file(
            K8sClient.locate_config_file(), user_agent="webservice"
        )
        configmap = client.get_object(
            "configmaps", "image-config", namespace="tf-public"
        )
        yaml_data = yaml.safe_load(configmap["data"]["images-v1.yaml"])

        types = {
            "buildservice": {
                "cls": GenericWebService,
                "resources": KubernetesBackend.DEFAULT_RESOURCES["default"],
                "use_webservice_runner": False,
                "state": "stable",
            }
        }

        for name, data in yaml_data.items():
            if KubernetesBackend.CONFIG_VARIANT_KEY not in data["variants"]:
                continue

            variant = data["variants"][KubernetesBackend.CONFIG_VARIANT_KEY]
            resources = variant["extra"].get("resources", "default")

            # TODO: this dict might benefit from being a separate class
            # or an instance of WebService directly
            types[name] = {
                "cls": KubernetesBackend.CONFIG_SUPPORTED_WS_TYPES[
                    variant["extra"]["wstype"]
                ],
                "image": "{image}:{tag}".format(
                    image=variant["image"],
                    tag=KubernetesBackend.CONFIG_IMAGE_TAG,
                ),
                "resources": KubernetesBackend.DEFAULT_RESOURCES[resources],
                "state": data["state"],
            }

        return types

    def __init__(
        self,
        tool,
        wstype,
        webservice_config,
        buildservice_image=None,
        mem=None,
        cpu=None,
        replicas=1,
        extra_args=None,
    ):
        super(KubernetesBackend, self).__init__(
            tool, wstype, extra_args=extra_args
        )

        config = KubernetesBackend.get_types()[self.wstype]

        self.project = Tool.get_current_project()
        self.webservice = config["cls"](tool, extra_args)

        if self.wstype == "buildservice":
            self.container_image = "{registry}/{image}".format(
                registry=webservice_config.get(
                    "buildservice_repository",
                    self.DEFAULT_BUILD_SERVICE_REGISTRY,
                ),
                image=buildservice_image,
            )
        else:
            self.container_image = config["image"]

        self.container_resources = config["resources"]
        self.use_webservice_runner = config.get("use_webservice_runner", True)

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
        self.api = K8sClient.from_file(
            K8sClient.locate_config_file(), user_agent="webservice"
        )
        self.routing_handler = KubernetesRoutingHandler(
            api=self.api,
            tool=self.tool,
            namespace=self._get_ns(),
            webservice_config=webservice_config,
        )

        # Labels for all objects created by this webservice
        self.webservice_labels = {
            "app.kubernetes.io/component": "web",
            "app.kubernetes.io/managed-by": "webservice",
            "toolforge": "tool",
            "name": self.tool.name,
        }

        self.webservice_label_selector = {
            k: v
            for k, v in self.webservice_labels.items()
            if k not in ["toolforge", "name"]
        }

    def _get_ns(self):
        return "tool-{}".format(self.tool.name)

    def _find_objs(self, kind, selector):
        """
        Return objects of kind matching selector, or None if they don't exist.

        Objects that are currently being deleted by the Kubernetes service
        (meaning they have a non-empty metadata.deletionTimestamp value) are
        ignored.
        """
        objs = self.api.get_objects(kind, label_selector=selector)
        # Ignore objects that are in the process of being deleted.
        return [
            o
            for o in objs
            if o["metadata"].get("deletionTimestamp", None) is None
        ]

    def _wait_for_pods(self, label_selector, started_at, timeout=30):
        """
        Wait for at least 1 pod with the given startedAt annotation to become 'ready'
        """
        for _ in range(timeout):
            pods = self._find_objs("pods", label_selector)
            pods = [
                pod
                for pod in pods
                if pod["metadata"]["annotations"].get(STARTED_AT_ANNOTATION)
                == started_at
            ]
            if self._any_pod_in_state(pods, "Running"):
                return True
            time.sleep(1)
        return False

    def _get_deployment(self, started_at):
        """
        Return the full spec of the deployment object for this webservice,
        started at the given timestamp.
        """
        if self.use_webservice_runner:
            cmd = [
                "/usr/bin/webservice-runner",
                "--type",
                self.webservice.name,
                "--port",
                str(DEFAULT_HTTP_PORT),
            ]
        else:
            cmd = []

        if self.extra_args:
            cmd.extend(self.extra_args)

        ports = [
            {
                "name": "http",
                "containerPort": DEFAULT_HTTP_PORT,
                "protocol": "TCP",
            }
        ]

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
                    "metadata": {
                        "labels": self.webservice_labels,
                        "annotations": {
                            # this annotation, which changes each time the deployment is updated,
                            # will cause Kubernetes to cleanly restart the deployment
                            # (start new pod, wait for it to be ready, stop old pod)
                            STARTED_AT_ANNOTATION: started_at,
                        },
                    },
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
        spec = {
            "containers": [
                {
                    "name": name,
                    "image": container_image,
                    "ports": ports,
                    "resources": resources,
                    "tty": tty,
                    "stdin": stdin,
                }
            ]
        }
        if cmd:
            spec["containers"][0]["command"] = cmd

        if self.wstype == "buildservice":
            spec["containers"][0]["env"] = [
                # For regular images, webservice-runner would take care of configuring the HTTP
                # server to listen on port 8000, but for buildservice ones we need to set the
                # PORT env var as it's what most buildpacks will use by default.
                {
                    "name": "PORT",
                    "value": str(DEFAULT_HTTP_PORT),
                },
                {
                    "name": "NO_HOME",
                    "value": "a buildservice pod does not need a home env",
                },
            ]
        else:
            spec["containers"][0][
                "workingDir"
            ] = "/data/project/{toolname}/".format(toolname=self.tool.name)

        return spec

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
            started_at = datetime.utcnow().isoformat()
            self.api.create_object(
                "deployments", self._get_deployment(started_at)
            )

        self.routing_handler.start_kubernetes()

    def request_stop(self):
        self.routing_handler.stop()

        self.api.delete_objects(
            "deployments", label_selector=self.webservice_label_selector
        )
        self.api.delete_objects(
            "replicasets",
            label_selector="name={name}".format(name=self.tool.name),
        )
        self.api.delete_objects(
            "pods", label_selector=self.webservice_label_selector
        )

    def request_restart(self):
        print("Restarting...")

        # To restart the Kubernetes application, we replace the Deployment object.
        # At least the startedAt timestamp is always different,
        # so Kubernetes will always create a new pod and stop the old one,
        # even if the rest of the Deployment did not change.
        # (But it is also possible that the replace command also specified
        # updated container resources, such as CPU or memory, which changed.)

        started_at = datetime.utcnow().isoformat()
        self.api.replace_object(
            "deployments", self._get_deployment(started_at)
        )

        # TODO: It would be cool and not terribly hard here to detect a pod
        # with an error or crash state and dump the logs of that pod for the
        # user to examine.
        if not self._wait_for_pods(
            self.webservice_label_selector, started_at, timeout=30
        ):
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
        deployment = self._get_live_deployment()
        if len(svcs) != 0 and deployment:
            return Backend.STATE_PENDING
        else:
            return Backend.STATE_STOPPED

    def _get_live_deployment(self):
        deployments = self._find_objs(
            "deployments", self.webservice_label_selector
        )
        if len(deployments) == 1:
            return deployments[0]
        return None

    def shell(self) -> int:
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
            self.api.delete_objects(
                "pods", label_selector="name={}".format(name)
            )
