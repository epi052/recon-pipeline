import uuid
import yaml
from pathlib import Path

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


yaml.add_constructor("!join", join)
yaml.add_constructor("!join_empty", join_empty)
yaml.add_constructor("!join_path", join_path)
yaml.add_constructor("!get_default", get_default)
yaml.add_constructor("!get_tool_path", get_tool_path)


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
