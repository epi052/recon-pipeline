import re
import uuid
from http import client
from pathlib import Path

import yaml

from ..recon.config import defaults

definitions = Path(__file__).parent
tools = {}


def join(loader, node):
    """ yaml tag handler to join a sequence of items into a space-separated string at load time """
    seq = loader.construct_sequence(node)
    return " ".join([str(val) for val in seq])


def join_empty(loader, node):
    """ yaml tag handler to join a sequence of items into a single string with no separations """
    seq = loader.construct_sequence(node)
    return "".join([str(val) for val in seq])


def join_path(loader, node):
    """ yaml tag handler to join a sequence of items into a filesystem path at load time """
    seq = loader.construct_sequence(node)
    return "/".join([str(i) for i in seq])


def get_default(loader, node):
    """ yaml tag handler to access defaults dict at load time """
    py_str = loader.construct_python_str(node)
    return py_str.format(**defaults)


def get_tool_path(loader, node):
    """ yaml tag handler to access tools dict at load time """
    py_str = loader.construct_python_str(node)
    return py_str.format(**tools)


def get_go_version(loader=None, node=None):
    """ download latest version of golang """
    arch = defaults.get("arch")
    err_msg = "Could not find latest go version download url"

    conn = client.HTTPSConnection("go.dev")
    conn.request("GET", "/dl/")
    response = conn.getresponse().read().decode()

    for line in response.splitlines():
        if "linux-amd64.tar.gz" in line:
            match = re.search(rf"href=./dl/(go.*\.linux-{arch}\.tar\.gz).>", line)
            if not match:
                return err_msg.replace("find", "parse")
            return match.group(1)  # go1.16.3.linux-
    return err_msg


yaml.add_constructor("!join", join)
yaml.add_constructor("!join_empty", join_empty)
yaml.add_constructor("!join_path", join_path)
yaml.add_constructor("!get_default", get_default)
yaml.add_constructor("!get_tool_path", get_tool_path)
yaml.add_constructor("!get_go_version,", get_go_version)


def load_yaml(file):
    try:
        config = yaml.full_load(file.read_text())
        tool_name = str(file.name.replace(".yaml", ""))
        tools[tool_name] = config
    except KeyError as error:  # load dependencies first
        dependency = error.args[0]
        dependency_file = definitions / (dependency + ".yaml")
        load_yaml(dependency_file)
        load_yaml(file)


for file in definitions.iterdir():
    if file.name.endswith(".yaml") and file.name.replace(".yaml", "") not in tools:
        load_yaml(file)

for tool_name, tool_definition in tools.items():
    tool_definition["installed"] = Path(tool_definition.get("path", f"/{uuid.uuid4()}")).exists()
