.. _scan-ref-label:

Running Scans
=============

All scans are ran from within ``recon-pipeline``'s shell.  There are a number of individual scans, however to execute
multiple scans at once, ``recon-pipeline`` includes wrappers around multiple commands.  As of version |version|, the
following individual scans are available

- :class:`recon.amass.AmassScan`
- :class:`recon.web.aquatone.AquatoneScan`
- :class:`recon.web.corscanner.CORScannerScan`
- :class:`recon.web.gobuster.GobusterScan`
- :class:`recon.masscan.MasscanScan`
- :class:`recon.nmap.SearchsploitScan`
- :class:`recon.web.subdomain_takeover.SubjackScan`
- :class:`recon.nmap.ThreadedNmapScan`
- :class:`recon.web.subdomain_takeover.TKOSubsScan`
- :class:`recon.web.webanalyze.WebanalyzeScan`

Additionally, two wrapper scans are made available as well.

- :class:`recon.wrappers.FullScan` - runs the entire pipeline
- :class:`recon.wrappers.HTBScan` - nicety for hackthebox players (myself included) that omits the scans in FullScan that don't make sense for HTB

Example Scan
============

.. raw:: html

    <script id="asciicast-293302" src="https://asciinema.org/a/293302.js" async></script>