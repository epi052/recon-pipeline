import sys
import subprocess
from pathlib import Path
from contextlib import redirect_stdout, redirect_stderr

from cmd2.utils import StdSim


def is_kali():
    return any(
        [
            "kali" in x
            for x in subprocess.run(
                "cat /etc/lsb-release".split(), stdout=subprocess.PIPE
            )
            .stdout.decode()
            .split()
        ]
    )


def normalize(block):
    """ Normalize a block of text to perform comparison.
    Strip newlines from the very beginning and very end  Then split into separate lines and strip trailing whitespace
    from each line.
    """
    assert isinstance(block, str)
    block = block.strip("\n")
    return [line.rstrip() for line in block.splitlines()]


def run_cmd(app, cmd):
    """ Clear out and err StdSim buffers, run the command, and return out and err """
    saved_sysout = sys.stdout
    sys.stdout = app.stdout

    # This will be used to capture app.stdout and sys.stdout
    copy_cmd_stdout = StdSim(app.stdout)

    # This will be used to capture sys.stderr
    copy_stderr = StdSim(sys.stderr)

    try:
        app.stdout = copy_cmd_stdout
        with redirect_stdout(copy_cmd_stdout):
            with redirect_stderr(copy_stderr):
                app.onecmd_plus_hooks(cmd)
    finally:
        app.stdout = copy_cmd_stdout.inner_stream
        sys.stdout = saved_sysout

    out = copy_cmd_stdout.getvalue()
    err = copy_stderr.getvalue()
    return normalize(out), normalize(err)


def setup_install_test(tool=None):
    tools = Path.home() / ".cache" / ".tool-dict.pkl"

    try:
        tools.unlink()
    except FileNotFoundError:
        pass

    if tool is not None:
        try:
            tool.unlink()
        except FileNotFoundError:
            pass
