Commands
========

``recon-pipeline`` provides three commands ``install``, ``scan``, and ``status``.  All other commands are inherited
from `cmd2 <https://github.com/python-cmd2/cmd2>`_.

.. _install_command:

install
#######

.. argparse::
    :module: recon
    :func: install_parser
    :prog: install

.. _scan_command:

scan
####

.. argparse::
    :module: recon
    :func: scan_parser
    :prog: scan

.. _status_command:

status
######

.. argparse::
    :module: recon
    :func: status_parser
    :prog: status