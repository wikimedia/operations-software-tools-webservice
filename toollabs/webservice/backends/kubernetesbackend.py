import os
import subprocess
import pykube
import time
import sys
from toollabs.webservice.backends import Backend
from toollabs.webservice.services import LighttpdWebService, PythonWebService


class KubernetesBackend(Backend):
    """
    Backend spawning webservices with a k8s Deployment + Service
    """

    CONFIG = {
        'php5.6':  {
            'cls': LighttpdWebService,
            'image': 'toollabs-php-web',
            'shell-image': 'toollabs-php-base',
            'resources': {
                'limits': {
                    # Pods can't use more than these resource limits
                    'memory': '2Gi',  # Pods will be killed if they go over this
                    'cpu': '2'  # Pods can still burst to more than this
                },
                'requests': {
                    # Pods are guaranteed at least this many resources
                    'memory': '256Mi',
                    'cpu': '0.125'
                }
            }
        },
        'python2': {
            'cls': PythonWebService,
            'image': 'toollabs-python2-web',
            'shell-image': 'toollabs-python2-base',
            'resources': {
                 'limits': {
                    # Pods can't use more than these resource limits
                    'memory': '2Gi',  # Pods will be killed if they go over this
                    'cpu': '2'  # Pods can still burst to more than this
                 },
                 'requests': {
                    # Pods are guaranteed at least this many resources
                    'memory': '256Mi',
                    'cpu': '0.125'
                 }
            }
        }
    }

    def __init__(self, tool, type, extra_args=None):
        super(KubernetesBackend, self).__init__(tool, type, extra_args=None)

        self.container_image = 'docker-registry.tools.wmflabs.org/{image}:latest'.format(
            image=KubernetesBackend.CONFIG[type]['image']
        )
        self.shell_image = 'docker-registry.tools.wmflabs.org/{image}:latest'.format(
            image=KubernetesBackend.CONFIG[type]['shell-image']
        )
        self.container_resources = KubernetesBackend.CONFIG[type]['resources']
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

    def _delete_obj(self, kind, selector):
        """
        Delete object of kind matching selector if it exists
        """
        try:
            kind.objects(self.api).filter(
                namespace=self.tool.name,
                selector=selector
            ).get().delete()
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
        cmd = [
            "/usr/bin/webservice-runner",
            "--type",
            self.webservice.name,
            "--port",
            "8000"
        ]

        if self.extra_args:
            cmd += " --extra-args '%s'" % self.extra_args

        ports = [{
            "name": "http",
            "containerPort": 8000,
            "protocol": "TCP"
        }]

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
                    "spec": self._get_container_spec(
                        "webservice",
                        self.container_image,
                        cmd,
                        self.container_resources,
                        ports
                    )
                }
            }
        }

    def _get_container_spec(self, name, container_image, cmd, resources, ports=None, stdin=False, tty=False):
        # All the paths we want to mount from host nodes onto container
        hostMounts = {
            'home': '/data/project/',
            'scratch': '/data/scratch/',
            'dumps': '/public/dumps/'
        }

        homedir = '/data/project/{toolname}/'.format(toolname=self.tool.name)

        return {
            "volumes": [
                {"name": key, "hostPath": {"path": value}}
                for key, value in hostMounts.items()
            ],
            "containers": [{
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
                "stdin": stdin
            }],
        }

    def request_start(self):
        self.webservice.check()
        if self._find_obj(pykube.Deployment, self.label_selector) is None:
            pykube.Deployment(self.api, self._get_deployment()).create()
        if self._find_obj(pykube.Service, self.label_selector) is None:
            pykube.Service(self.api, self._get_svc()).create()

    def request_stop(self):
        self._delete_obj(pykube.Service, self.label_selector)
        # No cascading delete support yet. So we delete all of the objects by hand
        # Can be simplified after https://github.com/kubernetes/kubernetes/pull/23656
        self._delete_obj(pykube.Deployment, self.label_selector)
        self._delete_obj(pykube.ReplicaSet, 'name={name}'.format(name=self.tool.name))
        self._delete_obj(pykube.Pod, self.label_selector)

    def get_state(self):
        svc = self._find_obj(pykube.Service, self.label_selector)
        deployment = self._find_obj(pykube.Deployment, self.label_selector)
        if svc is not None and deployment is not None:
            pod = self._find_obj(pykube.Pod, self.label_selector)
            if pod is not None:
                if pod.obj['status']['phase'] == 'Running':
                    return Backend.STATE_RUNNING
            return Backend.STATE_PENDING
        return Backend.STATE_STOPPED

    def _wait_for_pod(self, label_selector, timeout=30):
        """
        Wait for a pod to become 'ready'
        """
        for i in range(timeout):
            pod = self._find_obj(pykube.Pod, label_selector)
            if pod is not None:
                if pod.obj['status']['phase'] == 'Running':
                    return True
            time.sleep(1)
        return False

    def shell(self):
        labels = {
            'tools.wmflabs.org/webservice-interactive': 'true',
            'tools.wmflabs.org/webservice-interactive-version': '1',
            'name': 'interactive'
        }
        label_selector = ','.join(
            ['{k}={v}'.format(k=k, v=v) for k, v in labels.items()]
        )

        podSpec = {
            'apiVersion': 'v1',
            'kind': 'Pod',
            'metadata': {
                'namespace': self.tool.name,
                'name': 'interactive',
                'labels': labels,
            },
            'spec': self._get_container_spec(
                'interactive',
                self.shell_image,
                ['/bin/bash', '-i', '-l'],
                resources=None,
                ports=None,
                stdin=True,
                tty=True
            )
        }
        if self._find_obj(pykube.Pod, label_selector) is None:
            pykube.Pod(self.api, podSpec).create()

        if not self._wait_for_pod(label_selector):
            print("Pod is not ready in time")
            self._delete_obj(pykube.Pod, label_selector)
            sys.exit(1)
        kubectl = subprocess.Popen([
            '/usr/local/bin/kubectl',
            'attach',
            '--tty',
            '--stdin',
            'interactive'
        ])

        kubectl.wait()
        # kubectl attach prints the following when done:
        # Session ended, resume using 'kubectl attach interactive -c interactive -i -t' command when the pod is running
        # This isn't true, since we actually kill the pod when done
        print("Pod stopped. Session cannot be resumed.")

        self._delete_obj(pykube.Pod, label_selector)
