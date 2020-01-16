from __future__ import print_function

import os
import subprocess
import sys
import time

import pykube

from toollabs.common.utils import parse_quantity
from toollabs.webservice.backends import Backend
from toollabs.webservice.services import GenericWebService
from toollabs.webservice.services import JSWebService
from toollabs.webservice.services import LighttpdPlainWebService
from toollabs.webservice.services import LighttpdWebService
from toollabs.webservice.services import PythonWebService


class KubernetesBackend(Backend):
    """
    Backend spawning webservices with a k8s Deployment + Service
    """

    CONFIG = {
        "php5.6": {
            "cls": LighttpdWebService,
            "image": "toollabs-php-web",
            "tf-image": "toolforge-php5-sssd-web",
            "resources": {
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
            },
        },
        "php7.2": {
            "cls": LighttpdWebService,
            "image": "toollabs-php72-web",
            "tf-image": "toolforge-php72-sssd-web",
            "resources": {
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
            },
        },
        "php7.3": {
            "cls": LighttpdWebService,
            "image": "toolforge-php73-web",
            "tf-image": "toolforge-php73-sssd-web",
            "resources": {
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
            },
        },
        "tcl": {
            "cls": LighttpdPlainWebService,
            "image": "toollabs-tcl-web",
            "tf-image": "toolforge-tcl86-sssd-web",
            "resources": {
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
            },
        },
        "python": {
            "cls": PythonWebService,
            "image": "toollabs-python-web",
            "tf-image": "toolforge-python34-sssd-web",
            "resources": {
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
            },
        },
        "python3.5": {
            "cls": PythonWebService,
            "image": "toollabs-python35-web",
            "tf-image": "toolforge-python35-sssd-web",
            "resources": {
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
            },
        },
        "python3.7": {
            "cls": PythonWebService,
            "image": "toolforge-python37-web",
            "tf-image": "toolforge-python37-sssd-web",
            "resources": {
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
            },
        },
        "python2": {
            "cls": PythonWebService,
            "image": "toollabs-python2-web",
            "tf-image": "toolforge-python2-sssd-web",
            "resources": {
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
            },
        },
        "ruby2": {
            "cls": GenericWebService,
            "image": "toollabs-ruby-web",
            "tf-image": "toolforge-ruby21-sssd-web",
            "resources": {
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
            },
        },
        "ruby25": {
            "cls": GenericWebService,
            "image": "toolforge-ruby25-web",
            "tf-image": "toolforge-ruby25-sssd-web",
            "resources": {
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
            },
        },
        "golang": {
            "cls": GenericWebService,
            "image": "toollabs-golang-web",
            "tf-image": "toolforge-golang-sssd-web",
            "resources": {
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
            },
        },
        "golang111": {
            "cls": GenericWebService,
            "image": "toolforge-golang111-web",
            "tf-image": "toolforge-golang111-sssd-web",
            "resources": {
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
            },
        },
        "jdk8": {
            "cls": GenericWebService,
            "image": "toollabs-jdk8-web",
            "tf-image": "toolforge-jdk8-sssd-web",
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
            "image": "toolforge-jdk11-web",
            "tf-image": "toolforge-jdk11-sssd-web",
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
            "cls": JSWebService,
            "image": "toollabs-nodejs-web",
            "tf-image": "toolforge-node6-sssd-web",
            "resources": {
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
            },
        },
        "node10": {
            "cls": JSWebService,
            "image": "toollabs-node10-web",
            "tf-image": "toolforge-node10-sssd-web",
            "resources": {
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
            },
        },
    }

    def __init__(
        self, tool, project, type, mem=None, cpu=None, extra_args=None
    ):
        super(KubernetesBackend, self).__init__(tool, type, extra_args)
        self.project = project
        self.webservice = KubernetesBackend.CONFIG[type]["cls"](
            tool, extra_args
        )

        kubeconfig = pykube.KubeConfig.from_file(
            os.path.expanduser("~/.kube/config")
        )

        self.current_context = kubeconfig.current_context
        if self.current_context == "toolforge":
            # Use the sssd image
            self.container_image = "{registry}/{image}:latest".format(
                registry="docker-registry.tools.wmflabs.org",
                image=KubernetesBackend.CONFIG[type]["tf-image"],
            )
            # In this cluster, defaults are used for request so this just
            # affects the burst, up to certain limits (set as max in the
            # limitrange)
            # The namespace quotas also have impact on what can be done.
            if mem or cpu:
                self.container_resources = {"limits": {}, "requests": {}}
                if mem:
                    if parse_quantity(mem) < parse_quantity("256Mi"):
                        self.container_resources["requests"]["memory"] = mem
                    else:
                        self.container_resources["requests"][
                            "memory"
                        ] = "256Mi"
                    self.container_resources["limits"]["memory"] = mem
                if cpu:
                    if parse_quantity(cpu) < parse_quantity("250m"):
                        self.container_resources["requests"]["cpu"] = cpu
                    else:
                        self.container_resources["requests"]["cpu"] = "250m"
                    self.container_resources["limits"]["cpu"] = cpu
            else:
                # Defaults are cpu: 500m and memory: 512Mi
                self.container_resources = None
        else:
            self.container_resources = KubernetesBackend.CONFIG[type][
                "resources"
            ]
            self.container_image = "{registry}/{image}:latest".format(
                registry="docker-registry.tools.wmflabs.org",
                image=KubernetesBackend.CONFIG[type]["image"],
            )

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
        return (
            "tool-{}".format(self.tool.name)
            if (self.current_context == "toolforge")
            else self.tool.name
        )

    def _find_obj(self, kind, selector):
        """
        Returns object of kind matching selector, or None if it doesn't exist.

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
        if not objs:
            return None
        elif len(objs) == 1:
            return objs[0]
        else:
            raise ValueError(
                (
                    "Found {} objects of type {} matching selector {}: {}. "
                    "See https://phabricator.wikimedia.org/T156626"
                ).format(
                    len(objs),
                    kind.__name__,
                    selector,
                    ", ".join(repr(o) for o in objs),
                )
            )

    def _delete_obj(self, kind, selector):
        """
        Delete object of kind matching selector if it exists
        """
        o = self._find_obj(kind, selector)
        if o is not None:
            o.delete()

    def _wait_for_pod(self, label_selector, timeout=30):
        """
        Wait for a pod to become 'ready'
        """
        for _ in range(timeout):
            pod = self._find_obj(pykube.Pod, label_selector)
            if pod is not None:
                if pod.obj["status"]["phase"] == "Running":
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

    def _get_ingress(self):
        """
        Return the full spec of an ingress object for this webservice.
        """
        return {
            "apiVersion": "extensions/v1beta1",  # pykube is old
            "kind": "Ingress",
            "metadata": {
                "name": self.tool.name,
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
            cmd.append("--extra_args")
            cmd.append(self.extra_args)

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
                "replicas": 1,
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
        # All the paths we want to mount from host nodes onto container
        hostMounts = {
            "dumps": "/public/dumps/",
            "home": "/data/project/",
            "nfs": "/mnt/nfs/",  # Not sure this should be mounted
            "scratch": "/data/scratch/",
            "wmcs-project": "/etc/wmcs-project",
        }

        homedir = "/data/project/{toolname}/".format(toolname=self.tool.name)

        if self.current_context == "toolforge":
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
        else:
            return {
                "volumes": [
                    {"name": key, "hostPath": {"path": value}}
                    for key, value in hostMounts.items()
                ],
                "containers": [
                    {
                        "name": name,
                        "image": container_image,
                        "command": cmd,
                        "workingDir": homedir,
                        "env": [
                            # FIXME: This should be set by NSS maybe?!
                            {"name": "HOME", "value": homedir}
                        ],
                        "ports": ports,
                        "volumeMounts": [
                            {"name": key, "mountPath": value}
                            for key, value in hostMounts.items()
                        ],
                        "resources": resources,
                        "tty": tty,
                        "stdin": stdin,
                    }
                ],
            }

    def request_start(self):
        self.webservice.check()
        deployment = self._find_obj(
            pykube.Deployment, self.webservice_label_selector
        )
        if deployment is None:
            pykube.Deployment(self.api, self._get_deployment()).create()

        svc = self._find_obj(pykube.Service, self.webservice_label_selector)
        if svc is None:
            pykube.Service(self.api, self._get_svc()).create()

        if self.current_context == "toolforge":
            ingress = self._find_obj(
                pykube.Ingress, self.webservice_label_selector
            )
            if ingress is None:
                pykube.Ingress(self.api, self._get_ingress()).create()

    def request_stop(self):
        if self.current_context == "toolforge":
            self._delete_obj(pykube.Ingress, self.webservice_label_selector)

        self._delete_obj(pykube.Service, self.webservice_label_selector)
        # No cascading delete support yet. So we delete all of the objects by
        # hand Can be simplified after
        # https://github.com/kubernetes/kubernetes/pull/23656
        # Because we are using old objects in the new cluster (because pykube)
        # deletion policy must be explicitly set in the namespaces by
        # maintain-kubeusers and STILL defaults to "orphan"
        self._delete_obj(pykube.Deployment, self.webservice_label_selector)
        self._delete_obj(
            pykube.ReplicaSet, "name={name}".format(name=self.tool.name)
        )
        self._delete_obj(pykube.Pod, self.webservice_label_selector)

    def request_restart(self):
        # For most intents and purposes, the only thing necessary
        # to restart a Kubernetes application is to delete the pods.
        print("Restarting...")
        self._delete_obj(pykube.Pod, self.webservice_label_selector)
        # TODO: It would be cool and not terribly hard here to detect a pod
        # with an error or crash state and dump the logs of that pod for the
        # user to examine.
        if not self._wait_for_pod(self.webservice_label_selector, timeout=30):
            print(
                "Your webservice is taking quite while to restart. If it isn't"
                " up shortly, run a 'webservice stop' and the start command "
                "used to run this webservice to begin with."
            )
            sys.exit(1)

    def get_state(self):
        # TODO: add some state concept around ingresses
        pod = self._find_obj(pykube.Pod, self.webservice_label_selector)
        if pod is not None:
            if pod.obj["status"]["phase"] == "Running":
                return Backend.STATE_RUNNING
            elif pod.obj["status"]["phase"] == "Pending":
                return Backend.STATE_PENDING
        svc = self._find_obj(pykube.Service, self.webservice_label_selector)
        deployment = self._find_obj(
            pykube.Deployment, self.webservice_label_selector
        )
        if svc is not None and deployment is not None:
            return Backend.STATE_PENDING
        else:
            return Backend.STATE_STOPPED

    def shell(self):
        podSpec = self._get_shell_pod()
        if self._find_obj(pykube.Pod, self.shell_label_selector) is None:
            pykube.Pod(self.api, podSpec).create()

        if not self._wait_for_pod(self.shell_label_selector):
            print("Pod is not ready in time")
            self._delete_obj(pykube.Pod, self.shell_label_selector)
            sys.exit(1)
        kubectl = subprocess.Popen(
            ["/usr/bin/kubectl", "attach", "--tty", "--stdin", "interactive"]
        )

        kubectl.wait()
        # kubectl attach prints the following when done: Session ended, resume
        # using 'kubectl attach interactive -c interactive -i -t' command when
        # the pod is running
        # This isn't true, since we actually kill the pod when done
        print("Pod stopped. Session cannot be resumed.")

        self._delete_obj(pykube.Pod, self.shell_label_selector)
