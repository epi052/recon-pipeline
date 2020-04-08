==============
recon-pipeline
==============

``recon-pipeline`` was designed to chain together multiple security tools as part of a Flow-Based Programming paradigm.
Each component is part of a network of "black box" processes.  These components exchange data between each other and
can be reconnected in different ways to form different applications without any internal changes.

Getting Started
===============

.. include:: overview/summary.rst

.. toctree::
    :maxdepth: 2
    :hidden:

    overview/index

Changing the Code
=================

.. toctree::
    :maxdepth: 1

    Creating a New Wrapper Scan <modifications/index>

API Reference
=============

.. toctree::
    :maxdepth: 2

    api/commands
    api/manager
    api/models
    api/parsers
    api/scanners

Indices and tables
==================

* :ref:`genindex`
* :ref:`search`
