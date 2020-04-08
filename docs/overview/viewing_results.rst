.. toctree::
    :hidden:
    :maxdepth: 1

.. _view-scan-label:

Viewing Scan Results
====================

As of version 0.9.0, scan results are stored in a database located (by default) at ``~/.local/recon-pipeline/databases``.  Databases themselves are managed through the :ref:`database_command` while viewing their contents is done via :ref:`view_command`.

Using the :ref:`view_command` command
=====================================

The view command allows one to inspect different pieces of scan information via the following sub-commands

    - endpoints (gobuster results)
    - nmap-scans
    - ports
    - searchsploit-results
    - targets
    - web-technologies (webanalyze results)

Each of the sub-commands has a list of tab-completable options and values that can help drilling down to the data you care about.

All of the subcommands offer a ``--paged`` option for dealing with large amounts of output.  ``--paged`` will show you one page of output at a time (using ``less`` under the hood).

Chaining Results w/ Commands
############################

All of the results can be **piped out to other commands**.  Let's say you want to feed some results from ``recon-pipeline`` into another tool that isn't part of the pipeline.  Simply using a normal unix pipe ``|`` followed by the next command will get that done for you.  Below is an example of piping targets into `gau <https://github.com/lc/gau>`_

.. code-block:: console

    [db-2] recon-pipeline> view targets --paged
    3.tesla.cn
    3.tesla.com
    api-internal.sn.tesla.services
    api-toolbox.tesla.com
    api.mp.tesla.services
    api.sn.tesla.services
    api.tesla.cn
    api.toolbox.tb.tesla.services
    ...

    [db-2] recon-pipeline> view targets | gau
    https://3.tesla.com/pt_PT/model3/design
    https://3.tesla.com/pt_PT/model3/design?redirect=no
    https://3.tesla.com/robots.txt
    https://3.tesla.com/sites/all/themes/custom/tesla_theme/assets/img/icons/favicon-160x160.png?2
    https://3.tesla.com/sites/all/themes/custom/tesla_theme/assets/img/icons/favicon-16x16.png?2
    https://3.tesla.com/sites/all/themes/custom/tesla_theme/assets/img/icons/favicon-196x196.png?2
    https://3.tesla.com/sites/all/themes/custom/tesla_theme/assets/img/icons/favicon-32x32.png?2
    https://3.tesla.com/sites/all/themes/custom/tesla_theme/assets/img/icons/favicon-96x96.png?2
    https://3.tesla.com/sv_SE/model3/design
    ...


view endpoints
##############

An endpoint consists of a status code and the scanned URL.  Endpoints are populated via gobuster.  Simply running ``view endpoints`` will show all endpoints stored in the current database.

.. code-block:: console

    [200] http://westream.teslamotors.com/y
    [301] https://mobileapps.teslamotors.com/aspnet_client
    [403] https://209.133.79.49/analog.html
    [302] https://209.133.79.49/api
    [403] https://209.133.79.49/cgi-bin/
    [200] https://209.133.79.49/client

Each option can be used to filter results

.. code-block:: console

    [db-2] recon-pipeline> view endpoints  --host shop.uk.teslamotors.com
    [402] http://shop.uk.teslamotors.com/
    [403] https://shop.uk.teslamotors.com:8443/
    [301] http://shop.uk.teslamotors.com/assets
    [302] http://shop.uk.teslamotors.com/admin.cgi
    [200] http://shop.uk.teslamotors.com/.well-known/apple-developer-merchantid-domain-association
    [302] http://shop.uk.teslamotors.com/admin
    [403] http://shop.uk.teslamotors.com:8080/
    [302] http://shop.uk.teslamotors.com/admin.php
    [302] http://shop.uk.teslamotors.com/admin.pl
    [200] http://shop.uk.teslamotors.com/crossdomain.xml
    [403] https://shop.uk.teslamotors.com/

If you'd like to include any headers found during scanning, ``--headers`` will do that for you.

.. code-block:: console

    [302] http://shop.uk.teslamotors.com/admin.php
    [302] http://shop.uk.teslamotors.com/admin.cgi
    [302] http://shop.uk.teslamotors.com/admin
    [200] http://shop.uk.teslamotors.com/crossdomain.xml
    [403] https://shop.uk.teslamotors.com/
      Server: cloudflare
      Date: Mon, 06 Apr 2020 13:56:12 GMT
      Content-Type: text/html
      Content-Length: 553
      Retry-Count: 0
      Cf-Ray: 57fc02c788f7e03f-DFW
    [403] https://shop.uk.teslamotors.com:8443/
      Content-Type: text/html
      Content-Length: 553
      Retry-Count: 0
      Cf-Ray: 57fc06e5fcbfd266-DFW
      Server: cloudflare
      Date: Mon, 06 Apr 2020 13:59:00 GMT
    [302] http://shop.uk.teslamotors.com/admin.pl
    [200] http://shop.uk.teslamotors.com/.well-known/apple-developer-merchantid-domain-association
    [403] http://shop.uk.teslamotors.com:8080/
      Server: cloudflare
      Date: Mon, 06 Apr 2020 13:58:50 GMT
      Content-Type: text/html; charset=UTF-8
      Set-Cookie: __cfduid=dfbf45a8565fda1325b8c1482961518511586181530; expires=Wed, 06-May-20 13:58:50 GMT; path=/; domain=.shop.uk.teslamotors.com; HttpOnly; SameSite=Lax
      Cache-Control: max-age=15
      X-Frame-Options: SAMEORIGIN
      Alt-Svc: h3-27=":443"; ma=86400, h3-25=":443"; ma=86400, h3-24=":443"; ma=86400, h3-23=":443"; ma=86400
      Expires: Mon, 06 Apr 2020 13:59:05 GMT
      Cf-Ray: 57fc06a53887d286-DFW
      Retry-Count: 0
    [402] http://shop.uk.teslamotors.com/
      Cf-Cache-Status: DYNAMIC
      X-Dc: gcp-us-central1,gcp-us-central1
      Date: Mon, 06 Apr 2020 13:54:49 GMT
      Cf-Ray: 57fc00c39c0b581d-DFW
      X-Request-Id: 79146367-4c68-4e1b-9784-31f76d51b60b
      Set-Cookie: __cfduid=d94fad82fbdc0c110cb03cbcf58d097e21586181289; expires=Wed, 06-May-20 13:54:49 GMT; path=/; domain=.shop.uk.teslamotors.com; HttpOnly; SameSite=Lax _shopify_y=e3f19482-99e9-46cd-af8d-89fb8557fd28; path=/; expires=Thu, 07 Apr 2022 01:33:13 GMT
      X-Shopid: 4232821
      Content-Language: en
      Alt-Svc: h3-27=":443"; ma=86400, h3-25=":443"; ma=86400, h3-24=":443"; ma=86400, h3-23=":443"; ma=86400
      X-Content-Type-Options: nosniff
      X-Permitted-Cross-Domain-Policies: none
      X-Xss-Protection: 1; mode=block; report=/xss-report?source%5Baction%5D=index&source%5Bapp%5D=Shopify&source%5Bcontroller%5D=storefront_section%2Fshop&source%5Bsection%5D=storefront&source%5Buuid%5D=79146367-4c68-4e1b-9784-31f76d51b60b
      Server: cloudflare
      Content-Type: text/html; charset=utf-8
      X-Sorting-Hat-Shopid: 4232821
      X-Shardid: 78
      Content-Security-Policy: frame-ancestors *; report-uri /csp-report?source%5Baction%5D=index&source%5Bapp%5D=Shopify&source%5Bcontroller%5D=storefront_section%2Fshop&source%5Bsection%5D=storefront&source%5Buuid%5D=79146367-4c68-4e1b-9784-31f76d51b60b
      Retry-Count: 0
      X-Sorting-Hat-Podid: 78
      X-Shopify-Stage: production
      X-Download-Options: noopen
    [301] http://shop.uk.teslamotors.com/assets


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

Once in the REPL, the currently connected database is available as ``self.db_mgr``.  The database is an instance of :ref:`db_manager_label` and has a ``session`` attribute which can be used to issue manual SQLAlchemy style queries.

.. code-block:: console

    >>> from pipeline.models.port_model import Port
    >>> self.db_mgr.session.query(Port).filter_by(port_number=443)
    <sqlalchemy.orm.query.Query object at 0x7f8cef804250>
    >>>


