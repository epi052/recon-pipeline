.. _scan-ref-label:

Running Scans
=============

All scans are run from within ``recon-pipeline``'s shell.  There are a number of individual scans, however to execute
multiple scans at once, ``recon-pipeline`` includes wrappers around multiple commands.  As of version |version|, the
following individual scans are available

- :class:`pipeline.recon.amass.AmassScan`
- :class:`pipeline.recon.web.aquatone.AquatoneScan`
- :class:`pipeline.recon.web.gobuster.GobusterScan`
- :class:`pipeline.recon.masscan.MasscanScan`
- :class:`pipeline.recon.nmap.SearchsploitScan`
- :class:`pipeline.recon.web.subdomain_takeover.SubjackScan`
- :class:`pipeline.recon.nmap.ThreadedNmapScan`
- :class:`pipeline.recon.web.subdomain_takeover.TKOSubsScan`
- :class:`pipeline.recon.web.webanalyze.WebanalyzeScan`

Additionally, two wrapper scans are made available.  These execute multiple scans in a pipeline.

- :class:`pipeline.recon.wrappers.FullScan` - runs the entire pipeline
- :class:`pipeline.recon.wrappers.HTBScan` - nicety for hackthebox players (myself included) that omits the scans in FullScan that don't make sense for HTB

Example Scan
############

Here are the steps the video below takes to scan tesla[.]com.

Create a targetfile

.. code-block:: console

    # use virtual environment
    pipenv shell

    # create targetfile; a targetfile is required for all scans
    mkdir /root/bugcrowd/tesla
    cd /root/bugcrowd/tesla
    echo tesla.com > tesla-targetfile

    # create a blacklist (if necessary based on target's scope)
    echo energysupport.tesla.com > tesla-blacklist
    echo feedback.tesla.com >> tesla-blacklist
    echo employeefeedback.tesla.com >> tesla-blacklist
    echo ir.tesla.com >> tesla-blacklist

    # drop into the interactive shell
    /root/PycharmProjects/recon-pipeline/pipeline/recon-pipeline.py
    recon-pipeline>


Create a new database to store scan results

.. code-block:: console

    recon-pipeline> database attach
       1. create new database
    Your choice? 1
    new database name? (recommend something unique for this target)
    -> tesla-scan
    [*] created database @ /home/epi/.local/recon-pipeline/databases/tesla-scan
    [+] attached to sqlite database @ /home/epi/.local/recon-pipeline/databases/tesla-scan
    [db-1] recon-pipeline>


Scan the target

.. code-block:: console

    [db-1] recon-pipeline> scan FullScan --exempt-list tesla-blacklist --target-file tesla-targetfile --interface eno1 --top-ports 2000 --rate 1200
    [-] FullScan queued
    [-] TKOSubsScan queued
    [-] GatherWebTargets queued
    [-] ParseAmassOutput queued
    [-] AmassScan queued
    [-] ParseMasscanOutput queued
    [-] MasscanScan queued
    [-] WebanalyzeScan queued
    [-] SearchsploitScan queued
    [-] ThreadedNmapScan queued
    [-] SubjackScan queued
    [-] AquatoneScan queued
    [-] GobusterScan queued
    [db-1] recon-pipeline>

.. raw:: html

    <script id="asciicast-318397" src="https://asciinema.org/a/318397.js" async></script>

