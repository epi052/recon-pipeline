.. _scan-ref-label:

Running Scans
=============

All scans are ran from within ``recon-pipeline``'s shell.  There are a number of individual scans, however to execute
multiple scans at once, ``recon-pipeline`` includes wrappers around multiple commands.  As of version |version|, the
following individual scans are available

- :class:`pipeline.recon.amass.AmassScan`
- :class:`pipeline.recon.web.aquatone.AquatoneScan`
- :class:`pipeline.recon.web.corscanner.CORScannerScan`
- :class:`pipeline.recon.web.gobuster.GobusterScan`
- :class:`pipeline.recon.masscan.MasscanScan`
- :class:`pipeline.recon.nmap.SearchsploitScan`
- :class:`pipeline.recon.web.subdomain_takeover.SubjackScan`
- :class:`pipeline.recon.nmap.ThreadedNmapScan`
- :class:`pipeline.recon.web.subdomain_takeover.TKOSubsScan`
- :class:`pipeline.recon.web.webanalyze.WebanalyzeScan`

Additionally, two wrapper scans are made available as well.

- :class:`pipeline.recon.wrappers.FullScan` - runs the entire pipeline
- :class:`pipeline.recon.wrappers.HTBScan` - nicety for hackthebox players (myself included) that omits the scans in FullScan that don't make sense for HTB

Example Scan
============

.. raw:: html

    <script id="asciicast-293302" src="https://asciinema.org/a/293302.js" async></script>