.. _install-ref-label:

Installation Instructions
=========================

There are two primary phases for installation:

* prior to `cmd2 <https://github.com/python-cmd2/cmd2>`_ being installed
* everything else

Manual Steps
############

First, the manual steps to get cmd2 installed in a virtual environment are as follows (and shown below)

.. code-block::

    apt install pipenv
    git clone https://github.com/epi052/recon-pipeline.git
    cd recon-pipeline
    pipenv install cmd2


.. raw:: html

    <script id="asciicast-293306" src="https://asciinema.org/a/293306.js" async></script>

Everything Else
###############

After manual installation of cmd2_ is complete, the recon-pipeline shell provides its own :ref:`install_command` command (seen below).
A simple ``install all`` will handle all installation steps.  Installation has **only** been tested on **Kali 2019.4**.

Individual tools may be installed by running ``install TOOLNAME`` where ``TOOLNAME`` is one of the known tools that make
up the pipeline.

The installer maintains a (naive) list of installed tools at ``~/.cache/.tool-dict.pkl``.  The installer in no way
attempts to be a package manager.  It knows how to execute the steps necessary to install its tools.  Beyond that, it's
like Jon Snow, it knows nothing.

.. raw:: html

    <script id="asciicast-294414" src="https://asciinema.org/a/294414.js" async></script>

Alternative Distros
###################

If you're using a different distribution (i.e. not Kali), meeting the criteria below should be sufficient
for the auto installer to function:

- systemd-based system (luigid is installed as a systemd service)
- derivative of debian (some tools are installed using apt)

The alternatives would be to manually install each tool or to modify the distro-specific portions of the commands
laid out in ``recon.__init__``.  For example, on Fedora, you could change the package manager from ``apt-get`` to
``dnf`` and remove any ``apt-get`` specific options.

Example from ``recon-pipeline/recon/__init__.py``

.. code-block::

    "pipenv": {
        "installed": False,
        "dependencies": None,
        "commands": ["sudo apt-get install -y -q pipenv"],
    },

would become

.. code-block::

    "pipenv": {
        "installed": False,
        "dependencies": None,
        "commands": ["sudo dnf install -y pipenv"],
    },






