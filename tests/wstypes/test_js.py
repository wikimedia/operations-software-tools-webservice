import os
import tempfile
from typing import Optional

import pytest

from toolsws.tool import Tool
from toolsws.wstypes import JSWebService, WebService


@pytest.fixture
def tool_with_package_json(content: Optional[str]) -> Tool:
    with tempfile.TemporaryDirectory() as tmpdir:
        tool = Tool("test", "tools.test", 52503, 52503, tmpdir)

        os.mkdir(tool.get_homedir_subpath("www"))
        os.mkdir(tool.get_homedir_subpath("www/js"))

        package_path = tool.get_homedir_subpath("www/js/package.json")

        if content is not None:
            with open(package_path, "w") as package_file:
                package_file.write(content)

        yield tool


@pytest.mark.parametrize(
    "content",
    [
        None,
        "{}",
        '{"scripts": {}}',
        '{"scripts": {"dev": "foo"}}',
    ],
)
def test_JSWebService_check_broken(tool_with_package_json: Tool):
    wstype = JSWebService(tool_with_package_json)

    with pytest.raises(WebService.InvalidWebServiceException):
        wstype.check("node12")


@pytest.mark.parametrize("content", ['{"scripts": {"start": "foo"}}'])
def test_JSWebService_check_working(tool_with_package_json: Tool):
    wstype = JSWebService(tool_with_package_json)
    assert wstype.check("node12") is None
