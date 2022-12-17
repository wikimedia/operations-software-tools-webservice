from copy import deepcopy
import tempfile

import pytest

from toolsws.backends.kubernetes import (
    _containers_are_same,
    K8sClient,
    KubernetesBackend,
)
from toolsws.tool import Tool

FAKE_K8S_CONFIG_DATA = {
    "clusters": [
        {
            "name": "toolforge",
            "cluster": {
                "server": "https://example.com:6443",
            },
        },
    ],
    "contexts": [
        {
            "name": "toolforge",
            "context": {
                "cluster": "toolforge",
                "namespace": "tool-test",
                "user": "tf-test",
            },
        },
    ],
    "current-context": "toolforge",
    "users": [
        {
            "name": "tf-test",
            "user": {
                "client-certificate": "/tmp/fake.crt",
                "client-key": "/tmp/fake.key",
            },
        }
    ],
}


FAKE_CONTAINER_SPEC = {
    "replicas": 1,
    "selector": {"matchLabels": {"foo": "bar"}},
    "template": {
        "metadata": {"labels": {"foo": "bar"}},
        "spec": {
            "containers": [
                {
                    "name": "example",
                    "image": "docker-registry.tools.wmflabs.org/example:latest",
                    "command": ["./example"],
                    "workingDir": "/data/project/example",
                    "ports": [
                        {
                            "name": "http",
                            "protocol": "TCP",
                            "port": 8000,
                            "targetPort": 8000,
                        }
                    ],
                    "resources": {
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
                }
            ]
        },
    },
}


@pytest.fixture
def patch_k8s_client_from_file(monkeypatch):
    def mock_from_file():
        return K8sClient(FAKE_K8S_CONFIG_DATA)

    monkeypatch.setattr(K8sClient, "from_file", mock_from_file)


@pytest.fixture()
def fake_tool() -> Tool:
    # patch so it doesn't need to access the file system (which fails on CI)
    Tool._PROJECT = "tools"

    with tempfile.TemporaryDirectory() as tmpdir:
        yield Tool("test", "tools.test", 52503, 52503, tmpdir)


@pytest.mark.parametrize(
    "wstype,given,expected",
    [
        ["python3.9", {}, KubernetesBackend.DEFAULT_RESOURCES],
        ["jdk11", {}, KubernetesBackend.DEFAULT_JDK_RESOURCES],
        [
            "python3.9",
            {"cpu": "1"},
            {
                "limits": {
                    "memory": "512Mi",
                    "cpu": "1",
                },
                "requests": {
                    "memory": "256Mi",
                    "cpu": "0.5",
                },
            },
        ],
    ],
)
def test_KubernetesBackend_parse_resources(
    patch_k8s_client_from_file,
    fake_tool: Tool,
    wstype: str,
    given: dict,
    expected: dict,
):
    backend = KubernetesBackend(
        fake_tool,
        wstype,
        mem=given.get("mem", None),
        cpu=given.get("cpu", None),
        webservice_config={},
    )

    assert type(backend.container_resources) is dict
    assert backend.container_resources == expected


def test_containers_are_same_same():
    # equal containers should be the same
    assert _containers_are_same(FAKE_CONTAINER_SPEC, FAKE_CONTAINER_SPEC)

    # take a copy to not modify global state
    container = deepcopy(FAKE_CONTAINER_SPEC)
    container["template"]["spec"]["containers"][0]["resources"] = {
        "limits": {
            "memory": "512Mi",
            "cpu": "500m",  # changed from 0.5
        },
        "requests": {
            "memory": "262144Ki",  # changed from 256Mi
            "cpu": "0.125",
        },
    }

    assert _containers_are_same(FAKE_CONTAINER_SPEC, container)


def test_containers_are_same_different_image():
    # take a copy to not modify global state
    container = deepcopy(FAKE_CONTAINER_SPEC)
    container["template"]["spec"]["containers"][0]["image"] = "test"

    assert not _containers_are_same(FAKE_CONTAINER_SPEC, container)


def test_containers_are_same_different_resources():
    # take a copy to not modify global state
    container = deepcopy(FAKE_CONTAINER_SPEC)
    container["template"]["spec"]["containers"][0]["resources"] = {
        "limits": {
            "memory": "512Mi",
            "cpu": "500mi",  # changed from 0.5 / 500m
        },
        "requests": {
            "memory": "256M",  # changed from 256Mi
            "cpu": "0.125",
        },
    }

    assert not _containers_are_same(FAKE_CONTAINER_SPEC, container)
