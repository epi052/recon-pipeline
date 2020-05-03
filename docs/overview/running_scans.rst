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
- :class:`pipeline.recon.web.waybackurls.WaybackurlsScan`
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

**New as of v0.9.0**: In the event you're scanning a single ip address or host, simply use ``--target``.  It accepts a single target and works in conjunction with ``--exempt-list`` if specified.

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
    [-] WaybackurlsScan queued
    [-] SubjackScan queued
    [-] AquatoneScan queued
    [-] GobusterScan queued
    [db-1] recon-pipeline>

.. raw:: html

    <script id="asciicast-318397" src="https://asciinema.org/a/318397.js" async></script>

Existing Results Directories and You
####################################

When running additional scans against the same target, you have a few options.  You can either

- use a new directory
- reuse the same directory

If you use a new directory, the scan will start from the beginning.

If you choose to reuse the same directory, ``recon-pipeline`` will resume the scan from its last successful point.  For instance, say your last scan failed while running nmap.  This means that the pipeline executed all upstream tasks (amass and masscan) successfully.  When you use the same results directory for another scan, the amass and masscan scans will be skipped, because they've already run successfully.

**Note**: There is a gotcha that can occur when you scan a target but get no results.  For some scans, the pipeline may still mark the Task as complete (masscan does this).  In masscan's case, it's because it outputs a file to ``results-dir/masscan-results/`` whether it gets results or not.  Luigi interprets the file's presence to mean the scan is complete.

In order to reduce confusion, as of version 0.9.3, the pipeline will prompt you when reusing results directory.

.. code-block:: console

    [db-2] recon-pipeline> scan FullScan --results-dir testing-results --top-ports 1000 --rate 500 --target tesla.com
    [*] Your results-dir (testing-results) already exists. Subfolders/files may tell the pipeline that the associated Task is complete. This means that your scan may start from a point you don't expect. Your options are as follows:
       1. Resume existing scan (use any existing scan data & only attempt to scan what isn't already done)
       2. Remove existing directory (scan starts from the beginning & all existing results are removed)
       3. Save existing directory (your existing folder is renamed and your scan proceeds)
    Your choice?
