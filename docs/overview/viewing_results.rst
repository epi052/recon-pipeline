.. _view-scan-label:

Viewing Scan Results
====================

As of version 0.9.0, scan results are stored in a database located (by default) at ``~/.local/recon-pipeline/databases``.

Using the :ref:`view_command` command
==========================

Manually interacting with the Database
======================================

If for whatever reason you'd like to query the database manually, from within the recon-pipeline shell, you can use the ``py`` command to drop into a python REPL with your current ReconShell instance available as ``self``.

.. code-block:: console

    ./pipeline/recon-pipeline.py
    recon-pipeline> py
    Python 3.7.5 (default, Nov 20 2019, 09:21:52)
    [GCC 9.2.1 20191008] on linux
    Type "help", "copyright", "credits" or "license" for more information.

    End with `Ctrl-D` (Unix) / `Ctrl-Z` (Windows), `quit()`, `exit()`.
    Non-Python commands can be issued with: app("your command")

    >>> self
    <__main__.ReconShell object at 0x7f69f457f790>

Once in the REPL, the database is available as ``self.db_mgr``.
