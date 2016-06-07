import os
import pykube
from toollabs.webservice.backends import Backend
from toollabs.webservice.services import LighttpdWebService


class KubernetesBackend(Backend):
    """
    Backend spawning webservices with a k8s Deployment + Service
    """

    CONFIG = {
        'php5.6':  {'cls': LighttpdWebService, 'image': 'toollabs-php-web'}
    }

    def __init__(self, tool, type, extra_args=None):
        super(KubernetesBackend, self).__init__(tool, type, extra_args=None)

        self.container_image = 'docker-registry.tools.wmflabs.org/{image}:latest'.format(
            image=KubernetesBackend.CONFIG[type]['image']
        )
        self.webservice = KubernetesBackend.CONFIG[type]['cls'](tool, extra_args)

        self.api = pykube.HTTPClient(
            pykube.KubeConfig.from_file(
                os.path.expanduser('~/.kube/config')
            )
        )
        # Labels for all objects created by this webservice
        self.labels = {
            "tools.wmflabs.org/webservice": "true",
            "tools.wmflabs.org/webservice-version": "1",
            "name": self.tool.name
        }
        # FIXME: Protect against injection?
        self.label_selector = ','.join(
            ['{k}={v}'.format(k=k, v=v) for k, v in self.labels.items()]
        )

    def _find_obj(self, kind, selector):
        """
        Returns object of kind matching selector, or None if it doesn't exist
        """
        try:
            return kind.objects(self.api).filter(
                namespace=self.tool.name,
                selector=selector
            ).get()
        except pykube.exceptions.ObjectDoesNotExist:
            return None

    def _get_svc(self):
        """
        Return full spec for the webservice service
        """
        return {
            "kind": "Service",
            "apiVersion": "v1",
            "metadata": {
                "name": self.tool.name,
                "namespace": self.tool.name,
                "labels": self.labels
            },
            "spec": {
                "ports": [
                    {
                        "name": "http",
                        "protocol": "TCP",
                        "port": 8000,
                        "targetPort": 8000
                    }
                ],
                "selector": {
                    "name": self.tool.name
                },
            }
        }

    def _get_deployment(self):
        """
        Return the full spec of the deployment object for this webservice
        """
        # All the paths we want to mount from host nodes onto container
        hostMounts = {
            'home': '/data/project/{toolname}/'.format(toolname=self.tool.name),
            'scratch': '/data/scratch/',
            'dumps': '/public/dumps/'
        }

        cmd = [
            "/usr/bin/webservice-runner",
            "--type",
            self.webservice.name,
            "--port",
            "8000"
        ]

        if self.extra_args:
            cmd += " --extra-args '%s'" % self.extra_args

        return {
            "kind": "Deployment",
            "apiVersion": "extensions/v1beta1",
            "metadata": {
                "name": self.tool.name,
                "namespace": self.tool.name,
                "labels": self.labels
            },
            "spec": {
                "replicas": 1,
                "selector": {
                    "matchLabels": self.labels
                },
                "template": {
                    "metadata": {
                        "labels": self.labels
                    },
                    "spec": {
                        "volumes": [
                            {"name": key, "hostPath": {"path": value}}
                            for key, value in hostMounts.items()
                        ],
                        "containers": [
                            {
                                "name": "webservice",
                                "image": self.container_image,
                                "command": cmd,
                                "ports": [
                                    {
                                        "name": "http",
                                        "containerPort": 8000,
                                        "protocol": "TCP"
                                    }
                                ],
                                "volumeMounts": [
                                    {"name": key, "mountPath": value}
                                    for key, value in hostMounts.items()
                                ],
                            }
                        ],
                    }
                }
            }
        }

    def request_start(self):
        self.webservice.check()
        if self._find_obj(pykube.Deployment, self.label_selector) is None:
            pykube.Deployment(self.api, self._get_deployment()).create()
        if self._find_obj(pykube.Service, self.label_selector) is None:
            pykube.Service(self.api, self._get_svc()).create()

    def request_stop(self):
        svc = self._find_obj(pykube.Service, self.label_selector)
        if svc is not None:
            pykube.Service(self.api, svc.obj).delete()

        # No cascading delete support yet. So we delete all of the objects by hand
        # Can be simplified after https://github.com/kubernetes/kubernetes/pull/23656
        dep = self._find_obj(pykube.Deployment, self.label_selector)
        if dep is not None:
            pykube.Deployment(self.api, dep.obj).delete()

        rs = self._find_obj(
            pykube.ReplicaSet, 'name={name}'.format(name=self.tool.name)
        )
        if rs is not None:
            pykube.ReplicaSet(self.api, rs.obj).delete()

        pod = self._find_obj(pykube.Pod, self.label_selector)
        if pod is not None:
            pykube.Pod(self.api, pod.obj).delete()

    def get_state(self):
        if self._find_obj(pykube.Service, self.label_selector) is not None\
                or self._find_obj(pykube.Deployment, self.label_selector) is not None:
            # FIXME: Check if pod is running as well
            return Backend.STATE_RUNNING
        return Backend.STATE_STOPPED
