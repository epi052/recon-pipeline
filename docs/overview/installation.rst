.. _install-ref-label:

Installation Instructions
=========================

There are two primary phases for installation:

* prior to the python dependencies being installed
* everything else

Manual Steps
############

First, the steps to get python dependencies installed in a virtual environment are as follows (and shown below)

Kali
----

.. code-block:: console

    sudo apt install pipenv


Ubuntu 18.04
------------

.. code-block:: console

    sudo apt install python3-pip
    pip install --user pipenv
    echo "PATH=${PATH}:~/.local/bin" >> ~/.bashrc
    bash

Both OSs After ``pipenv`` Install
---------------------------------

.. code-block:: console

    git clone https://github.com/epi052/recon-pipeline.git
    cd recon-pipeline
    pipenv install
    pipenv shell


.. raw:: html

    <script id="asciicast-318395" src="https://asciinema.org/a/318395.js" async></script>

Everything Else
###############

After installing the python dependencies, the recon-pipeline shell provides its own :ref:`install_command` command (seen below).
A simple ``install all`` will handle all installation steps.  Installation has **only** been tested on **Kali 2019.4 and Ubuntu 18.04**.

    **Ubuntu-18.04 Note (and newer kali versions)**: You may consider running ``sudo -v`` prior to running ``./recon-pipeline.py``. ``sudo -v`` will refresh your creds, and the underlying subprocess calls during installation won't prompt you for your password. It'll work either way though.

Individual tools may be installed by running ``install TOOLNAME`` where ``TOOLNAME`` is one of the known tools that make
up the pipeline.

The installer maintains a (naive) list of installed tools at ``~/.cache/.tool-dict.pkl``.  The installer in no way
attempts to be a package manager.  It knows how to execute the steps necessary to install its tools.  Beyond that, it's
like Jon Snow, **it knows nothing**.

.. raw:: html

    <script id="asciicast-294414" src="https://asciinema.org/a/294414.js" async></script>

Alternative Distros
###################

In v0.8.1, an effort was made to remove OS specific installation steps from the installer.  However, if you're
using an untested distribution (i.e. not Kali/Ubuntu 18.04), meeting the criteria below **should** be sufficient
for the auto installer to function:

- systemd-based system (``luigid`` is installed as a systemd service)
- python3.6+ installed

With the above requirements met, following the installation steps above starting with ``pipenv install`` should be sufficient.

The alternative would be to manually install each tool.