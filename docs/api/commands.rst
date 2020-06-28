.. toctree::
    :maxdepth: 1
    :hidden:

.. _commands-ref-label:

Commands
========

``recon-pipeline`` provides a handful of commands:

- :ref:`tools_command`
- :ref:`scan_command`
- :ref:`status_command`
- :ref:`database_command`
- :ref:`view_command`

All other available commands are inherited from `cmd2 <https://github.com/python-cmd2/cmd2>`_.

.. _tools_command:

tools
#####

.. argparse::
    :module: pipeline.recon
    :func: tools_parser
    :prog: tools


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
