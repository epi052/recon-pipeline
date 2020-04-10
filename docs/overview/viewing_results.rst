.. toctree::
    :hidden:
    :maxdepth: 1

.. _view-scan-label:

Viewing Scan Results
====================

As of version 0.9.0, scan results are stored in a database located (by default) at ``~/.local/recon-pipeline/databases``.  Databases themselves are managed through the :ref:`database_command` command while viewing their contents is done via :ref:`view_command`.

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

An endpoint consists of a status code and the scanned URL.  Endpoints are populated via gobuster.

Show All Endpoints
------------------

.. code-block:: console

    [db-2] recon-pipeline> view endpoints --paged
    [200] http://westream.teslamotors.com/y
    [301] https://mobileapps.teslamotors.com/aspnet_client
    [403] https://209.133.79.49/analog.html
    [302] https://209.133.79.49/api
    [403] https://209.133.79.49/cgi-bin/
    [200] https://209.133.79.49/client
    ...

Filter by Host
--------------

.. code-block:: console

    [db-2] recon-pipeline> view endpoints --host shop.uk.teslamotors.com
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
    [db-2] recon-pipeline>

Filter by Host and Status Code
------------------------------

.. code-block:: console

    [db-2] recon-pipeline> view endpoints --host shop.uk.teslamotors.com --status-code 200
    [200] http://shop.uk.teslamotors.com/crossdomain.xml
    [200] http://shop.uk.teslamotors.com/.well-known/apple-developer-merchantid-domain-association
    [db-2] recon-pipeline>

Remove Status Code from Output
------------------------------

Using ``--plain`` will remove the status-code prefix, allowing for easy piping of results into other commands.

.. code-block:: console

    [db-2] recon-pipeline> view endpoints --host shop.uk.teslamotors.com --plain
    http://shop.uk.teslamotors.com/admin.pl
    http://shop.uk.teslamotors.com/admin
    http://shop.uk.teslamotors.com/
    http://shop.uk.teslamotors.com/admin.cgi
    http://shop.uk.teslamotors.com/.well-known/apple-developer-merchantid-domain-association
    http://shop.uk.teslamotors.com:8080/
    http://shop.uk.teslamotors.com/crossdomain.xml
    https://shop.uk.teslamotors.com:8443/
    https://shop.uk.teslamotors.com/
    http://shop.uk.teslamotors.com/admin.php
    http://shop.uk.teslamotors.com/assets
    [db-2] recon-pipeline>

Include Headers
---------------

If you'd like to include any headers found during scanning, ``--headers`` will do that for you.

.. code-block:: console

    [db-2] recon-pipeline> view endpoints --host shop.uk.teslamotors.com --headers
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
    [db-2] recon-pipeline>

view nmap-scans
###############

Nmap results can be filtered by host, NSE script type, scanned port, and product.

Show All Results
----------------

.. code-block:: console

    [db-2] recon-pipeline> view nmap-scans --paged
    2600:9000:21d4:7800:c:d401:5a80:93a1 - http
    ===========================================

    tcp port: 80 - open - syn-ack
    product: Amazon CloudFront httpd :: None
    nse script(s) output:
      http-server-header
        CloudFront
      http-title
        ERROR: The request could not be satisfied

    ...

Filter by product
-----------------

.. code-block:: console

    [db-2] recon-pipeline> view nmap-scans --product "Splunkd httpd"
    209.133.79.101 - http
    =====================

    tcp port: 443 - open - syn-ack
    product: Splunkd httpd :: None
    nse script(s) output:
      http-robots.txt
        1 disallowed entry
        /
      http-server-header
        Splunkd
      http-title
        404 Not Found
      ssl-cert
        Subject: commonName=*.teslamotors.com/organizationName=Tesla Motors, Inc./stateOrProvinceName=California/countryName=US
        Subject Alternative Name: DNS:*.teslamotors.com, DNS:teslamotors.com
        Not valid before: 2019-01-17T00:00:00
        Not valid after:  2021-02-03T12:00:00
      ssl-date
        TLS randomness does not represent time

Filter by NSE Script
--------------------

.. code-block:: console

    [db-2] recon-pipeline> view nmap-scans --nse-script ssl-cert --paged
    199.66.9.47 - http-proxy
    ========================

    tcp port: 443 - open - syn-ack
    product: Varnish http accelerator :: None
    nse script(s) output:
      ssl-cert
        Subject: commonName=*.tesla.com/organizationName=Tesla, Inc./stateOrProvinceName=California/countryName=US
        Subject Alternative Name: DNS:*.tesla.com, DNS:tesla.com
        Not valid before: 2020-02-07T00:00:00
        Not valid after:  2022-04-08T12:00:00

    ...

Filter by NSE Script and Port Number
------------------------------------

.. code-block:: console

    [db-2] recon-pipeline> view nmap-scans --nse-script ssl-cert --port 8443
    104.22.11.42 - https-alt
    ========================

    tcp port: 8443 - open - syn-ack
    product: cloudflare :: None
    nse script(s) output:
      ssl-cert
        Subject: commonName=sni.cloudflaressl.com/organizationName=Cloudflare, Inc./stateOrProvinceName=CA/countryName=US
        Subject Alternative Name: DNS:*.tesla.services, DNS:tesla.services, DNS:sni.cloudflaressl.com
        Not valid before: 2020-02-13T00:00:00
        Not valid after:  2020-10-09T12:00:00
    [db-2] recon-pipeline>

Filter by Host (ipv4/6 or domain name)
--------------------------------------

.. code-block:: console

    [db-2] recon-pipeline> view nmap-scans --host 2600:9000:21d4:3000:c:d401:5a80:93a1
    2600:9000:21d4:3000:c:d401:5a80:93a1 - http
    ===========================================

    tcp port: 80 - open - syn-ack
    product: Amazon CloudFront httpd :: None
    nse script(s) output:
      http-server-header
        CloudFront
      http-title
        ERROR: The request could not be satisfied

    [db-2] recon-pipeline>

Include Command Used to Scan
----------------------------

The ``--commandline`` option will append the command used to scan the target to the results.

.. code-block:: console

    [db-2] recon-pipeline> view nmap-scans --host 2600:9000:21d4:3000:c:d401:5a80:93a1 --commandline
    2600:9000:21d4:3000:c:d401:5a80:93a1 - http
    ===========================================

    tcp port: 80 - open - syn-ack
    product: Amazon CloudFront httpd :: None
    nse script(s) output:
      http-server-header
        CloudFront
      http-title
        ERROR: The request could not be satisfied
    command used:
      nmap --open -sT -n -sC -T 4 -sV -Pn -p 80 -6 -oA /home/epi/PycharmProjects/recon-pipeline/tests/data/tesla-results/nmap-results/nmap.2600:9000:21d4:3000:c:d401:5a80:93a1-tcp 2600:9000:21d4:3000:c:d401:5a80:93a1

    [db-2] recon-pipeline>

view ports
##########

Port results are populated via masscan.  Ports can be filtered by host and port number.

Show All Results
----------------

.. code-block:: console

    [db-2] recon-pipeline> view ports --paged
    apmv3.go.tesla.services: 80
    autodiscover.teslamotors.com: 80
    csp.teslamotors.com: 443
    image.emails.tesla.com: 443
    marketing.teslamotors.com: 443
    partnerleadsharing.tesla.com: 443
    service.tesla.cn: 80
    shop.uk.teslamotors.com: 8080
    sip.tesla.cn: 5061
    ...

Filter by Host
--------------

.. code-block:: console

    [db-2] recon-pipeline> view ports --host tesla.services
    tesla.services: 8443,8080
    [db-2] recon-pipeline>


Filter by Port Number
---------------------

.. code-block:: console

    [db-2] recon-pipeline> view ports --port-number 8443
    tesla.services: 8443,8080
    104.22.10.42: 8443,8080
    104.22.11.42: 8443,8080
    2606:4700:10::6816:a2a: 8443,8080
    2606:4700:10::6816:b2a: 8443,8080
    [db-2] recon-pipeline>

view searchsploit-results
#########################

Searchsploit results can be filtered by host and type, the full path to any relevant exploit code can be shown as well.

Show All Results
----------------

.. code-block:: console

    [db-2] recon-pipeline> view searchsploit-results --paged
    52.209.48.104, 34.252.120.214, 52.48.121.107, telemetry-eng.vn.tesla.services
    =============================================================================
      local    | 40768.sh |  Nginx (Debian Based Distros + Gentoo) - 'logrotate' Local Privilege
                          |    Escalation
      remote   | 12804.txt|  Nginx 0.6.36 - Directory Traversal
      local    | 14830.py |  Nginx 0.6.38 - Heap Corruption
      webapps  | 24967.txt|  Nginx 0.6.x - Arbitrary Code Execution NullByte Injection
      dos      | 9901.txt |  Nginx 0.7.0 < 0.7.61 / 0.6.0 < 0.6.38 / 0.5.0 < 0.5.37 / 0.4.0 <
                          |    0.4.14 - Denial of Service (PoC)
      remote   | 9829.txt |  Nginx 0.7.61 - WebDAV Directory Traversal
      remote   | 33490.txt|  Nginx 0.7.64 - Terminal Escape Sequence in Logs Command Injection
      remote   | 13822.txt|  Nginx 0.7.65/0.8.39 (dev) - Source Disclosure / Download
      remote   | 13818.txt|  Nginx 0.8.36 - Source Disclosure / Denial of Service
      remote   | 38846.txt|  Nginx 1.1.17 - URI Processing SecURIty Bypass
      remote   | 25775.rb |  Nginx 1.3.9 < 1.4.0 - Chuncked Encoding Stack Buffer Overflow
                          |    (Metasploit)
      dos      | 25499.py |  Nginx 1.3.9 < 1.4.0 - Denial of Service (PoC)
      remote   | 26737.pl |  Nginx 1.3.9/1.4.0 (x86) - Brute Force
      remote   | 32277.txt|  Nginx 1.4.0 (Generic Linux x64) - Remote Overflow
      webapps  | 47553.md |  PHP-FPM + Nginx - Remote Code Execution
    ...

Filter by Host
--------------

.. code-block:: console

    [db-2] recon-pipeline> view searchsploit-results --paged --host telemetry-eng.vn.tesla.services
    52.209.48.104, 34.252.120.214, 52.48.121.107, telemetry-eng.vn.tesla.services
    =============================================================================
      local    | 40768.sh |  Nginx (Debian Based Distros + Gentoo) - 'logrotate' Local Privilege
                          |    Escalation
      remote   | 12804.txt|  Nginx 0.6.36 - Directory Traversal
      local    | 14830.py |  Nginx 0.6.38 - Heap Corruption
      webapps  | 24967.txt|  Nginx 0.6.x - Arbitrary Code Execution NullByte Injection
      dos      | 9901.txt |  Nginx 0.7.0 < 0.7.61 / 0.6.0 < 0.6.38 / 0.5.0 < 0.5.37 / 0.4.0 <
                          |    0.4.14 - Denial of Service (PoC)
      remote   | 9829.txt |  Nginx 0.7.61 - WebDAV Directory Traversal
      remote   | 33490.txt|  Nginx 0.7.64 - Terminal Escape Sequence in Logs Command Injection
      remote   | 13822.txt|  Nginx 0.7.65/0.8.39 (dev) - Source Disclosure / Download
      remote   | 13818.txt|  Nginx 0.8.36 - Source Disclosure / Denial of Service
      remote   | 38846.txt|  Nginx 1.1.17 - URI Processing SecURIty Bypass
      remote   | 25775.rb |  Nginx 1.3.9 < 1.4.0 - Chuncked Encoding Stack Buffer Overflow
                          |    (Metasploit)
      dos      | 25499.py |  Nginx 1.3.9 < 1.4.0 - Denial of Service (PoC)
      remote   | 26737.pl |  Nginx 1.3.9/1.4.0 (x86) - Brute Force
      remote   | 32277.txt|  Nginx 1.4.0 (Generic Linux x64) - Remote Overflow
      webapps  | 47553.md |  PHP-FPM + Nginx - Remote Code Execution
    [db-2] recon-pipeline>

Filter by Type
--------------

.. code-block:: console

    [db-2] recon-pipeline> view searchsploit-results --paged  --type webapps
    52.209.48.104, 34.252.120.214, 52.48.121.107, telemetry-eng.vn.tesla.services
    =============================================================================
      webapps  | 24967.txt|  Nginx 0.6.x - Arbitrary Code Execution NullByte Injection
      webapps  | 47553.md |  PHP-FPM + Nginx - Remote Code Execution
    ...

Include Full Path to Exploit Code
---------------------------------

.. code-block:: console

    52.209.48.104, 34.252.120.214, 52.48.121.107, telemetry-eng.vn.tesla.services
    =============================================================================
      webapps |  Nginx 0.6.x - Arbitrary Code Execution NullByte Injection
              |  /home/epi/.recon-tools/exploitdb/exploits/multiple/webapps/24967.txt
      webapps |  PHP-FPM + Nginx - Remote Code Execution
              |  /home/epi/.recon-tools/exploitdb/exploits/php/webapps/47553.md
    ...

view targets
############

Target results can be filtered by type and whether or not they've been reported as vulnerable to subdomain takeover.

Show All Results
----------------

.. code-block:: console

    [db-2] recon-pipeline> view targets --paged

    3.tesla.com
    api-internal.sn.tesla.services
    api-toolbox.tesla.com
    api.mp.tesla.services
    api.sn.tesla.services
    api.tesla.cn
    ...

Filter by Target Type
---------------------

.. code-block:: console

    [db-2] recon-pipeline> view targets --type ipv6 --paged
    2600:1404:23:183::358f
    2600:1404:23:188::3fe7
    2600:1404:23:18f::700
    2600:1404:23:190::700
    2600:1404:23:194::16cf
    ...

Filter by Possibility of Subdomain Takeover
-------------------------------------------

.. code-block:: console

    [db-2] recon-pipeline> view targets --paged --vuln-to-subdomain-takeover
    [vulnerable] api-internal.sn.tesla.services
    ...

view web-technologies
#####################

Web technology results are produced by webanalyze.  Web technology results can be filtered by host, type, and product.

Show All Results
----------------

.. code-block:: console

    [db-2] recon-pipeline> view web-technologies --paged
    Varnish (Caching)
    =================

       - inventory-assets.tesla.com
       - www.tesla.com
       - errlog.tesla.com
       - static-assets.tesla.com
       - partnerleadsharing.tesla.com
       - 199.66.9.47
       - onboarding-pre-delivery-prod.teslamotors.com
       - 2600:1404:23:194::16cf
       - 2600:1404:23:196::16cf
    ...

Filter by Technology Type
-------------------------

.. code-block:: console

    [db-2] recon-pipeline> view web-technologies --type "Programming languages"
    PHP (Programming languages)
    ===========================

       - www.tesla.com
       - dummy.teslamotors.com
       - 209.10.208.20
       - 211.147.80.206
       - trt.tesla.com
       - trt.teslamotors.com
       - cn-origin.teslamotors.com
       - www.tesla.cn
       - events.tesla.cn
       - 23.67.209.106
       - service.teslamotors.com

    Python (Programming languages)
    ==============================

       - api-toolbox.tesla.com
       - 52.26.53.228
       - 34.214.187.20
       - 35.166.29.132
       - api.toolbox.tb.tesla.services
       - toolbox.teslamotors.com
       - 209.133.79.93

    Ruby (Programming languages)
    ============================

       - storagesim.teslamotors.com
       - 209.10.208.39
    ...

Filter by Product
-----------------

.. code-block:: console

    [db-2] recon-pipeline> view web-technologies --product OpenResty-1.15.8.2
    OpenResty-1.15.8.2 (Web servers)
    ================================

       - links.tesla.com

    [db-2] recon-pipeline>

Filter by Host
--------------

.. code-block:: console

    [db-2] recon-pipeline> view web-technologies --host api-toolbox.tesla.com
    api-toolbox.tesla.com
    =====================
       - gunicorn-19.4.5 (Web servers)
       - Python (Programming languages)
    [db-2] recon-pipeline>

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


