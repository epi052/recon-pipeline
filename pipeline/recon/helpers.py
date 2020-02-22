import sys
import inspect
import pkgutil
import importlib
from pathlib import Path
from collections import defaultdict


def get_scans():
    """ Iterates over the recon package and its modules to find all of the \*Scan classes.

    **A contract exists here that says any scans need to end with the word scan in order to be found by this function.**

    Example:
        ``defaultdict(<class 'list'>, {'AmassScan': ['recon.amass'], 'MasscanScan': ['recon.masscan'], ... })``

    Returns:
        dict containing mapping of ``classname -> [modulename, ...]`` for all potential recon-pipeline commands
    """
    scans = defaultdict(list)

    file = Path(__file__).resolve()
    web = file.parent / "web"
    recon = file.parents[1] / "recon"

    lib_paths = [str(web), str(recon)]

    # recursively walk packages; import each module in each package
    # walk_packages yields ModuleInfo objects for all modules recursively on path
    # prefix is a string to output on the front of every module name on output.
    for loader, module_name, is_pkg in pkgutil.walk_packages(path=lib_paths, prefix=f"{__package__}."):
        try:
            importlib.import_module(module_name)
        except ModuleNotFoundError:
            # skipping things like recon.aquatone, not entirely sure why they're showing up...
            pass

    # walk all modules, grabbing classes that we've written and add them to the classlist defaultdict
    # getmembers returns all members of an object in a list of tuples (name, value)
    for name, obj in inspect.getmembers(sys.modules[__package__]):
        if inspect.ismodule(obj) and not name.startswith("_"):
            # we're only interested in modules that don't begin with _ i.e. magic methods __len__ etc...

            for subname, subobj in inspect.getmembers(obj):
                if inspect.isclass(subobj) and subname.lower().endswith("scan"):
                    # now we only care about classes that end in [Ss]can
                    scans[subname].append(f"{__package__}.{name}")

    return scans
