Creating a New Wrapper Scan
===========================

If for whatever reason you want something other than FullScan, the process for defining a new scan is relatively simple.
The ``HTBScan`` is a good example.

1. Define your new class, inheriting from **luigi.WrapperTask** and use the ``inherits`` decorator to include any scan you want to utilize

.. code-block:: python

    @inherits(SearchsploitScan, AquatoneScan, GobusterScan, WebanalyzeScan)
    class HTBScan(luigi.WrapperTask):
        ...

2. Include all parameters needed by any of the scans passed to ``inherits``

.. code-block:: python

    def requires(self):
        """ HTBScan is a wrapper, as such it requires any Tasks that it wraps. """
        args = {
            "results_dir": self.results_dir,
            "rate": self.rate,
            "target_file": self.target_file,
            "top_ports": self.top_ports,
            "interface": self.interface,
            "ports": self.ports,
            "exempt_list": self.exempt_list,
            "threads": self.threads,
            "proxy": self.proxy,
            "wordlist": self.wordlist,
            "extensions": self.extensions,
            "recursive": self.recursive,
        }
        ...

3. ``yield`` from each scan, keeping in mind that some of the parameters won't be universal (i.e. need to be removed/added)

.. code-block:: python

    def requires(self):
        """ HTBScan is a wrapper, as such it requires any Tasks that it wraps. """
        ...

        yield GobusterScan(**args)

        # remove options that are gobuster specific; if left dictionary unpacking to other scans throws an exception
        for gobuster_opt in ("proxy", "wordlist", "extensions", "recursive"):
            del args[gobuster_opt]

        # add aquatone scan specific option
        args.update({"scan_timeout": self.scan_timeout})

        yield AquatoneScan(**args)

        del args["scan_timeout"]

        yield SearchsploitScan(**args)
        yield WebanalyzeScan(**args)
