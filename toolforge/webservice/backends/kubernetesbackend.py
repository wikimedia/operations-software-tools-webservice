from __future__ import print_function

import os
import subprocess
import sys
import time

import pykube

from toolforge.common.tool import PROJECT
from toolforge.common.utils import parse_quantity
from toolforge.webservice.backends import Backend
from toolforge.webservice.services import GenericWebService
from toolforge.webservice.services import JSWebService
from toolforge.webservice.services import LighttpdPlainWebService
from toolforge.webservice.services import LighttpdWebService
from toolforge.webservice.services import PythonWebService


class KubernetesBackend(Backend):
    """
    Backend spawning webservices with a k8s Deployment + Service
    """

    DEFAULT_RESOURCES = {
        "limits": {
            # Pods will be killed if they go over memory limit
            "memory": "2Gi",
            # Pods can still burst to more than cpu limit
            "cpu": "2",
        },
        "requests": {
            # Pods are guaranteed at least this many resources
            "memory": "256Mi",
            "cpu": "0.125",
        },
    }

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
            "resources": {
                "limits": {
                    # Pods will be killed if they go over memory limit
                    # Higher Memory Limit for jdk8, but not higher request
                    # So it can use more memory before being killed, but will
                    # die when there is a memory crunch
                    "memory": "4Gi",
                    # Pods can still burst to more than cpu limit
                    "cpu": "2",
                },
                "requests": {
                    # Pods are guaranteed at least this many resources
                    "memory": "256Mi",
                    "cpu": "0.125",
                },
            },
        },
        "jdk11": {
            "cls": GenericWebService,
            "image": "toolforge-jdk11-sssd-web",
            "resources": {
                "limits": {
                    # Pods will be killed if they go over memory limit
                    # Higher Memory Limit for jdk8, but not higher request
                    # So it can use more memory before being killed, but will
                    # die when there is a memory crunch
                    "memory": "4Gi",
                    # Pods can still burst to more than cpu limit
                    "cpu": "2",
                },
                "requests": {
                    # Pods are guaranteed at least this many resources
                    "memory": "256Mi",
                    "cpu": "0.125",
                },
            },
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
    }

    def __init__(
        self,
        tool,
        wstype,
        canonical=False,
        mem=None,
        cpu=None,
        replicas=1,
        extra_args=None,
    ):
        super(KubernetesBackend, self).__init__(
            tool, wstype, canonical=canonical, extra_args=extra_args
        )
        self.project = PROJECT
        self.webservice = KubernetesBackend.CONFIG[type]["cls"](
            tool, extra_args
        )

        kubeconfig = pykube.KubeConfig.from_file(
            os.path.expanduser("~/.kube/config")
        )

        self.container_image = "{registry}/{image}:latest".format(
            registry="docker-registry.tools.wmflabs.org",
            image=KubernetesBackend.CONFIG[type]["image"],
        )
        # Defaults are used for request so this just affects the burst, up to
        # certain limits (set as max in the limitrange) as well as
        # a proportional request (which affects scheduling).
        # The namespace quotas also have impact on what can be done.
        if mem or cpu:
            self.container_resources = {"limits": {}, "requests": {}}
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
                    self.container_resources["requests"]["cpu"] = str(
                        dec_cpu / 2
                    )
                self.container_resources["limits"]["cpu"] = cpu
        else:
            # Defaults are cpu: 500m and memory: 512Mi
            self.container_resources = None

        self.replicas = replicas
        self.api = pykube.HTTPClient(kubeconfig)
        # Labels for all objects created by this webservice
        self.webservice_labels = {
            "tools.wmflabs.org/webservice": "true",
            "tools.wmflabs.org/webservice-version": "1",
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

        self.shell_labels = {
            "tools.wmflabs.org/webservice-interactive": "true",
            "tools.wmflabs.org/webservice-interactive-version": "1",
            "toolforge": "tool",
            "name": "interactive",
        }
        self.shell_label_selector = ",".join(
            ["{k}={v}".format(k=k, v=v) for k, v in self.shell_labels.items()]
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
        objs = kind.objects(self.api).filter(
            namespace=self._get_ns(), selector=selector
        )
        # Ignore objects that are in the process of being deleted.
        objs = [
            o
            for o in objs
            if o.obj["metadata"].get("deletionTimestamp", None) is None
        ]

        return objs

    def _delete_objs(self, kind, selector):
        """
        Delete objects of kind matching selector if they exist
        """
        o_list = self._find_objs(kind, selector)
        for o in o_list:
            o.delete()

    def _wait_for_pods(self, label_selector, timeout=30):
        """
        Wait for at least 1 pod to become 'ready'
        """
        for _ in range(timeout):
            pods = self._find_objs(pykube.Pod, label_selector)
            if self._any_pod_in_state(pods, "Running"):
                return True
            time.sleep(1)
        return False

    def _get_svc(self):
        """
        Return full spec for the webservice service
        """
        return {
            "kind": "Service",
            "apiVersion": "v1",
            "metadata": {
                "name": self.tool.name,
                "namespace": self._get_ns(),
                "labels": self.webservice_labels,
            },
            "spec": {
                "ports": [
                    {
                        "name": "http",
                        "protocol": "TCP",
                        "port": 8000,
                        "targetPort": 8000,
                    }
                ],
                "selector": {"name": self.tool.name},
            },
        }

    def _get_ingress_legacy(self):
        """
        Returns the full spec of the legacy ingress object for this webservice
        """
        ingress = {
            "apiVersion": "extensions/v1beta1",  # pykube is old
            "kind": "Ingress",
            "metadata": {
                "name": "{}-legacy".format(self.tool.name),
                "namespace": "tool-{}".format(self.tool.name),
                "annotations": {
                    "nginx.ingress.kubernetes.io/configuration-snippet": "rewrite ^(/{})$ $1/ redirect;\n".format(
                        self.tool.name
                    ),
                    "nginx.ingress.kubernetes.io/rewrite-target": "/{}/$2".format(
                        self.tool.name
                    ),
                },
                "labels": self.webservice_labels,
            },
            "spec": {
                "rules": [
                    {
                        "host": "{}.wmflabs.org".format(self.project),
                        "http": {
                            "paths": [
                                {
                                    "path": "/{}(/|$)(.*)".format(
                                        self.tool.name
                                    ),
                                    "backend": {
                                        "serviceName": self.tool.name,
                                        "servicePort": 8000,
                                    },
                                }
                            ]
                        },
                    }
                ]
            },
        }

        if self.canonical:
            ingress["metadata"]["annotations"] = {
                "nginx.ingress.kubernetes.io/permanent-redirect": "https://{}.toolforge.org/$2".format(
                    self.tool.name
                )
            }

        return ingress

    def _get_ingress_subdomain(self):
        """
        Returns the full spec of the domain-based routing ingress object for
        this webservice
        """
        return {
            "apiVersion": "extensions/v1beta1",  # pykube is old
            "kind": "Ingress",
            "metadata": {
                "name": "{}-subdomain".format(self.tool.name),
                "namespace": "tool-{}".format(self.tool.name),
                "labels": self.webservice_labels,
            },
            "spec": {
                "rules": [
                    {
                        "host": "{}.toolforge.org".format(self.tool.name),
                        "http": {
                            "paths": [
                                {
                                    "backend": {
                                        "serviceName": self.tool.name,
                                        "servicePort": 8000,
                                    }
                                }
                            ]
                        },
                    }
                ]
            },
        }

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
            "apiVersion": "extensions/v1beta1",  # Warning, this is deprecated
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

    def _get_shell_pod(self):
        cmd = ["/bin/bash", "-il"]
        return {
            "apiVersion": "v1",
            "kind": "Pod",
            "metadata": {
                "namespace": self._get_ns(),
                "name": "interactive",
                "labels": self.shell_labels,
            },
            "spec": self._get_container_spec(
                "interactive",
                self.container_image,
                cmd,
                resources=None,
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
            if pod.obj["status"]["phase"] == state:
                return True

        return False

    def request_start(self):
        self.webservice.check()
        deployments = self._find_objs(
            pykube.Deployment, self.webservice_label_selector
        )
        if len(deployments) == 0:
            pykube.Deployment(self.api, self._get_deployment()).create()

        svcs = self._find_objs(pykube.Service, self.webservice_label_selector)
        if len(svcs) == 0:
            pykube.Service(self.api, self._get_svc()).create()

        ingresses = self._find_objs(
            pykube.Ingress, self.webservice_label_selector
        )
        if len(ingresses) == 0:
            pykube.Ingress(self.api, self._get_ingress_legacy()).create()
            pykube.Ingress(self.api, self._get_ingress_subdomain()).create()

    def request_stop(self):
        self._delete_objs(pykube.Ingress, self.webservice_label_selector)

        self._delete_objs(pykube.Service, self.webservice_label_selector)
        # No cascading delete support yet. So we delete all of the objects by
        # hand Can be simplified after
        # https://github.com/kubernetes/kubernetes/pull/23656
        # Because we are using old objects in the new cluster (because pykube)
        # deletion policy must be explicitly set in the namespaces by
        # maintain-kubeusers and STILL defaults to "orphan"
        self._delete_objs(pykube.Deployment, self.webservice_label_selector)
        self._delete_objs(
            pykube.ReplicaSet, "name={name}".format(name=self.tool.name)
        )
        self._delete_objs(pykube.Pod, self.webservice_label_selector)

    def request_restart(self):
        # For most intents and purposes, the only thing necessary
        # to restart a Kubernetes application is to delete the pods.
        print("Restarting...")
        self._delete_objs(pykube.Pod, self.webservice_label_selector)
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
        pods = self._find_objs(pykube.Pod, self.webservice_label_selector)
        if self._any_pod_in_state(pods, "Running"):
            return Backend.STATE_RUNNING
        if self._any_pod_in_state(pods, "Pending"):
            return Backend.STATE_PENDING
        svcs = self._find_objs(pykube.Service, self.webservice_label_selector)
        deployments = self._find_objs(
            pykube.Deployment, self.webservice_label_selector
        )
        if len(svcs) != 0 and len(deployments) != 0:
            return Backend.STATE_PENDING
        else:
            return Backend.STATE_STOPPED

    def shell(self):
        podSpec = self._get_shell_pod()
        if len(self._find_objs(pykube.Pod, self.shell_label_selector)) == 0:
            pykube.Pod(self.api, podSpec).create()

        if not self._wait_for_pods(self.shell_label_selector):
            print("Pod is not ready in time", file=sys.stderr)
            self._delete_objs(pykube.Pod, self.shell_label_selector)
            sys.exit(1)
        kubectl = subprocess.Popen(
            ["/usr/bin/kubectl", "attach", "--tty", "--stdin", "interactive"]
        )

        kubectl.wait()
        # kubectl attach prints the following when done: Session ended, resume
        # using 'kubectl attach interactive -c interactive -i -t' command when
        # the pod is running
        # This isn't true, since we actually kill the pod when done
        print("Pod stopped. Session cannot be resumed.", file=sys.stderr)

        self._delete_objs(pykube.Pod, self.shell_label_selector)
