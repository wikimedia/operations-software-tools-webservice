import tempfile

import pytest

from toolsws.backends.kubernetes import K8sClient, KubernetesBackend
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
