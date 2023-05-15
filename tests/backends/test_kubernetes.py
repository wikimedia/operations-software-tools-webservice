from copy import deepcopy
from pathlib import Path
import tempfile

import pytest
from toolforge_weld.kubernetes import K8sClient
from toolforge_weld.kubernetes_config import Kubeconfig

from toolsws.backends.kubernetes import (
    _containers_are_same,
    KubernetesBackend,
    KubernetesRoutingHandler,
)
from toolsws.tool import Tool
from toolsws.wstypes.ws import WebService


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

FAKE_IMAGE_CONFIG_DATA = {
    "kind": "ConfigMap",
    "apiVersion": "v1",
    # spec omitted, since it's not really relevant
    "data": {
        "images-v1.yaml": """
jdk17:
  state: stable
  aliases:
    - tf-jdk17
  variants:
    jobs-framework:
      image: docker-registry.tools.wmflabs.org/toolforge-jdk17-sssd-base
    webservice:
      image: docker-registry.tools.wmflabs.org/toolforge-jdk17-sssd-web
      extra:
        wstype: generic
        resources: jdk
node12:
  aliases:
  - tf-node12
  - tf-node12-DEPRECATED
  state: deprecated
  variants:
    jobs-framework:
      image: docker-registry.tools.wmflabs.org/toolforge-node12-sssd-base
    webservice:
      image: docker-registry.tools.wmflabs.org/toolforge-node12-sssd-web
      extra:
        wstype: lighttpd
node16:
  aliases:
  - tf-node16
  state: stable
  variants:
    jobs-framework:
      image: docker-registry.tools.wmflabs.org/toolforge-node16-sssd-base
    webservice:
      image: docker-registry.tools.wmflabs.org/toolforge-node16-sssd-web
      extra:
        wstype: js
php7.3:
  aliases:
  - tf-php73
  - tf-php73-DEPRECATED
  state: deprecated
  variants:
    jobs-framework:
      image: docker-registry.tools.wmflabs.org/toolforge-php73-sssd-base
    webservice:
      image: docker-registry.tools.wmflabs.org/toolforge-php73-sssd-web
      extra:
        wstype: lighttpd
php7.4:
  aliases:
  - tf-php74
  state: stable
  variants:
    jobs-framework:
      image: docker-registry.tools.wmflabs.org/toolforge-php74-sssd-base
    webservice:
      image: docker-registry.tools.wmflabs.org/toolforge-php74-sssd-web
      extra:
        wstype: lighttpd
""",
    },
}


@pytest.fixture
def fake_k8s_client() -> K8sClient:
    kubeconfig = Kubeconfig(
        path=Path("dummy/path"),
        current_server="https://example.com:6443",
        current_namespace="tool-test",
        client_cert_file=Path("/tmp/fake.crt"),
        client_key_file=Path("/tmp/fake.key"),
    )
    return K8sClient(
        kubeconfig=kubeconfig,
        user_agent="webservice",
    )


@pytest.fixture
def patch_k8s_client_from_file(monkeypatch, fake_k8s_client: K8sClient):
    def mock_from_file(*args, **kwargs):
        real_get_object = fake_k8s_client.get_object

        def mock_get_object(*args, **kwargs):
            # this is a hack
            if args == ("configmaps", "image-config") and kwargs == {
                "namespace": "tf-public"
            }:
                return FAKE_IMAGE_CONFIG_DATA
            return real_get_object(*args, **kwargs)

        monkeypatch.setattr(fake_k8s_client, "get_object", mock_get_object)

        return fake_k8s_client

    monkeypatch.setattr(K8sClient, "from_file", mock_from_file)


@pytest.fixture()
def patch_k8s_backend_get_types_no_lrucache():
    KubernetesBackend.get_types.cache_clear()


@pytest.fixture
def fake_tool() -> Tool:
    # patch so it doesn't need to access the file system (which fails on CI)
    Tool._PROJECT = "tools"
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Tool("test", "tools.test", 52503, 52503, tmpdir)


def test_KubernetesRoutingHandler_public_domain_default(
    fake_k8s_client: K8sClient,
    fake_tool: Tool,
):
    handler = KubernetesRoutingHandler(
        api=fake_k8s_client,
        tool=fake_tool,
        namespace=f"tool-{fake_tool.name}",
        webservice_config={},
    )

    assert (
        handler._get_ingress_subdomain()["spec"]["rules"][0]["host"]
        == "test.toolforge.org"
    )


def test_KubernetesRoutingHandler_public_domain_config(
    fake_k8s_client: K8sClient,
    fake_tool: Tool,
):
    handler = KubernetesRoutingHandler(
        api=fake_k8s_client,
        tool=fake_tool,
        namespace=f"tool-{fake_tool.name}",
        webservice_config={"public_domain": "example.com"},
    )

    assert (
        handler._get_ingress_subdomain()["spec"]["rules"][0]["host"]
        == "test.example.com"
    )


def test_KubernetesBackend_get_types(
    patch_k8s_client_from_file,
    patch_k8s_backend_get_types_no_lrucache,
):
    types = KubernetesBackend.get_types()
    assert type(types) is dict

    for name, data in types.items():
        if name == "buildservice":
            continue

        assert type(name) is str
        assert type(data) is dict

        assert issubclass(data["cls"], WebService)
        assert type(data["image"]) is str
        assert "limits" in data["resources"]


@pytest.mark.parametrize(
    "wstype,given,expected",
    [
        ["php7.4", {}, KubernetesBackend.DEFAULT_RESOURCES["default"]],
        ["jdk17", {}, KubernetesBackend.DEFAULT_RESOURCES["jdk"]],
        [
            "php7.4",
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
    patch_k8s_backend_get_types_no_lrucache,
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
