.. toctree::
    :maxdepth: 1
    :hidden:

.. _commands-ref-label:

Commands
========

``recon-pipeline`` provides a handful of commands:

- ``install``
- ``scan``
- ``status``
- ``database``
- ``view``

All other available commands are inherited from `cmd2 <https://github.com/python-cmd2/cmd2>`_.

.. _install_command:

install
#######

.. argparse::
    :module: pipeline.recon
    :func: install_parser
    :prog: install


.. _database_command:

database
########

.. argparse::
    :module: pipeline.recon
    :func: database_parser
    :prog: database

.. _scan_command:

scan
####

.. argparse::
    :module: pipeline.recon
    :func: scan_parser
    :prog: scan

.. _status_command:

status
######

.. argparse::
    :module: pipeline.recon
    :func: status_parser
    :prog: status

.. _view_command:

view
#######

.. argparse::
    :module: pipeline.recon
    :func: view_parser
    :prog: view
