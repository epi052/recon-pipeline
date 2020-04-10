.. _scope-ref-label:

Defining Target Scope
=====================

The pipeline expects a file that describes the target's scope to be provided as an argument to the
``--target-file`` option. The target file can consist of domains, ip addresses, and ip ranges, one per line.  Domains, ip
addresses and ip ranges can be mixed/matched within the scope file.

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


