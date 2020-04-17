.. _scope-ref-label:

Defining Target Scope
=====================

**New in v0.9.0**: In the event you're scanning a single ip address or host, simply use ``--target``.  It accepts a single target and works in conjunction with ``--exempt-list`` if specified.

.. code-block:: console

    [db-1] recon-pipeline> scan HTBScan --target 10.10.10.183 --top-ports 1000
    ...

In order to scan more than one host at a time, the pipeline needs a file that describes the target's scope to be provided as an argument to the `--target-file` option.  The target file can consist of domains, ip addresses, and ip ranges, one per line.


In order to scan more than one host at a time, the pipeline expects a file that describes the target's scope to be provided as an argument to the ``--target-file`` option. The target file can consist of domains, ip addresses, and ip ranges, one per line.  Domains, ip addresses and ip ranges can be mixed/matched within the scope file.

.. code-block:: console

    tesla.com
    tesla.cn
    teslamotors.com
    ...

Some bug bounty scopes have expressly verboten subdomains and/or top-level domains, for that there is the
``--exempt-list`` option. The exempt list follows the same rules as the target file.

.. code-block:: console

    shop.eu.teslamotors.com
    energysupport.tesla.com
    feedback.tesla.com
    ...


