import json
import logging
import subprocess
from pathlib import Path
from urllib.parse import urlparse

import luigi
from luigi.util import inherits
from luigi.contrib.sqla import SQLAlchemyTarget

from .targets import GatherWebTargets
from ..config import defaults
from ...tools import tools

import pipeline.models.db_manager
from ..helpers import get_tool_state
from ...models.port_model import Port
from ...models.header_model import Header
from ...models.endpoint_model import Endpoint
from ...models.screenshot_model import Screenshot


@inherits(GatherWebTargets)
class AquatoneScan(luigi.Task):
    """ Screenshot all web targets and generate HTML report.

    Install:
        .. code-block:: console

            mkdir /tmp/aquatone
            wget -q https://github.com/michenriksen/aquatone/releases/download/v1.7.0/aquatone_linux_amd64_1.7.0.zip -O /tmp/aquatone/aquatone.zip
            unzip /tmp/aquatone/aquatone.zip -d /tmp/aquatone
            sudo mv /tmp/aquatone/aquatone /usr/local/bin/aquatone
            rm -rf /tmp/aquatone

    Basic Example:
        ``aquatone`` commands are structured like the example below.

        ``cat webtargets.tesla.txt | /opt/aquatone -scan-timeout 900 -threads 20``

    Luigi Example:
        .. code-block:: python

            PYTHONPATH=$(pwd) luigi --local-scheduler --module recon.web.aquatone AquatoneScan --target-file tesla --top-ports 1000

    Args:
        threads: number of threads for parallel aquatone command execution
        scan_timeout: timeout in miliseconds for aquatone port scans
        db_location: specifies the path to the database used for storing results *Required by upstream Task*
        exempt_list: Path to a file providing blacklisted subdomains, one per line. *Optional by upstream Task*
        top_ports: Scan top N most popular ports *Required by upstream Task*
        ports: specifies the port(s) to be scanned *Required by upstream Task*
        interface: use the named raw network interface, such as "eth0" *Required by upstream Task*
        rate: desired rate for transmitting packets (packets per second) *Required by upstream Task*
        target_file: specifies the file on disk containing a list of ips or domains *Required by upstream Task*
        results_dir: specifes the directory on disk to which all Task results are written *Required by upstream Task*
    """

    threads = luigi.Parameter(default=defaults.get("threads", ""))
    scan_timeout = luigi.Parameter(default=defaults.get("aquatone-scan-timeout", ""))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db_mgr = pipeline.models.db_manager.DBManager(db_location=self.db_location)
        self.results_subfolder = Path(self.results_dir) / "aquatone-results"

    @staticmethod
    def meets_requirements():
        """ Reports whether or not this scan's needed tool(s) are installed or not """
        needs = ["aquatone"]
        tools = get_tool_state()

        if tools:
            return all([tools.get(x).get("installed") is True for x in needs])

    def requires(self):
        """ AquatoneScan depends on GatherWebTargets to run.

        GatherWebTargets accepts exempt_list and expects rate, target_file, interface,
                         and either ports or top_ports as parameters

        Returns:
            luigi.Task - GatherWebTargets
        """
        args = {
            "results_dir": self.results_dir,
            "rate": self.rate,
            "target_file": self.target_file,
            "top_ports": self.top_ports,
            "interface": self.interface,
            "ports": self.ports,
            "exempt_list": self.exempt_list,
            "db_location": self.db_location,
        }
        return GatherWebTargets(**args)

    def output(self):
        """ Returns the target output for this task.

        Returns:
            luigi.contrib.sqla.SQLAlchemyTarget
        """
        return SQLAlchemyTarget(
            connection_string=self.db_mgr.connection_string, target_table="screenshot", update_id=self.task_id
        )

    def _get_similar_pages(self, url, results):
        # populate similar pages if any exist
        similar_pages = None

        for cluster_id, cluster in results.get("pageSimilarityClusters").items():
            if url not in cluster:
                continue

            similar_pages = list()

            for similar_url in cluster:
                if similar_url == url:
                    continue

                similar_pages.append(self.db_mgr.get_or_create(Screenshot, url=similar_url))

        return similar_pages

    def parse_results(self):
        """ Read in aquatone's .json file and update the associated Target record """

        """ Example data

            "https://email.assetinventory.bugcrowd.com:8443/": {
              "uuid": "679b0dc7-02ea-483f-9e0a-3a5e6cdea4b6",
              "url": "https://email.assetinventory.bugcrowd.com:8443/",
              "hostname": "email.assetinventory.bugcrowd.com",
              "addrs": [
                "104.20.60.51",
                "104.20.61.51",
                "2606:4700:10::6814:3d33",
                "2606:4700:10::6814:3c33"
              ],
              "status": "403 Forbidden",
              "pageTitle": "403 Forbidden",
              "headersPath": "headers/https__email_assetinventory_bugcrowd_com__8443__42099b4af021e53f.txt",
              "bodyPath": "html/https__email_assetinventory_bugcrowd_com__8443__42099b4af021e53f.html",
              "screenshotPath": "screenshots/https__email_assetinventory_bugcrowd_com__8443__42099b4af021e53f.png",
              "hasScreenshot": true,
              "headers": [
                {
                  "name": "Cf-Ray",
                  "value": "55d396727981d25a-DFW",
                  "decreasesSecurity": false,
                  "increasesSecurity": false
                },
                ...
              ],
              "tags": [
                {
                  "text": "CloudFlare",
                  "type": "info",
                  "link": "http://www.cloudflare.com",
                  "hash": "9ea92fc7dce5e740ccc8e64d8f9e3336a96efc2a"
                }
              ],
              "notes": null
            },
            ...

              "pageSimilarityClusters": {
                "11905c72-fd18-43de-9133-99ba2a480e2b": [
                  "http://52.53.92.161/",
                  "https://staging.bitdiscovery.com/",
                  "https://52.53.92.161/",
                  ...
                ],
                "139fc2c4-0faa-4ae3-a6e4-0a1abe2418fa": [
                  "https://104.20.60.51:8443/",
                  "https://email.assetinventory.bugcrowd.com:8443/",
                  ...
                ],
        """
        try:
            with open(self.results_subfolder / "aquatone_session.json") as f:
                # results.keys -> dict_keys(['version', 'stats', 'pages', 'pageSimilarityClusters'])
                results = json.load(f)
        except FileNotFoundError as e:
            logging.error(e)
            return

        for page, page_dict in results.get("pages").items():
            headers = list()

            url = page_dict.get("url")  # one url to one screenshot, unique key

            # build out the endpoint's data to include headers, this has value whether or not there's a screenshot
            endpoint = self.db_mgr.get_or_create(Endpoint, url=url)
            if not endpoint.status_code:
                status = page_dict.get("status").split(maxsplit=1)
                if len(status) > 1:
                    endpoint.status_code, _ = status
                else:
                    endpoint.status_code = status[0]

            for header_dict in page_dict.get("headers"):
                header = self.db_mgr.get_or_create(Header, name=header_dict.get("name"), value=header_dict.get("value"))

                if endpoint not in header.endpoints:
                    header.endpoints.append(endpoint)

                headers.append(header)

            endpoint.headers = headers

            parsed_url = urlparse(url)

            ip_or_hostname = parsed_url.hostname
            tgt = self.db_mgr.get_or_create_target_by_ip_or_hostname(ip_or_hostname)

            endpoint.target = tgt

            if not page_dict.get("hasScreenshot"):
                # if there isn't a screenshot, save the endpoint data and move along
                self.db_mgr.add(endpoint)
                # This causes an integrity error on insertion due to the task_id being the same for two
                # different target tables.  Could subclass SQLAlchemyTarget and set the unique-ness to be the
                # combination of update_id + target_table.  The question is, does it matter?
                # TODO: assess above and act
                # SQLAlchemyTarget(
                #     connection_string=self.db_mgr.connection_string, target_table="endpoint", update_id=self.task_id
                # ).touch()
                continue

            # build out screenshot data
            port = parsed_url.port if parsed_url.port else 80
            port = self.db_mgr.get_or_create(Port, protocol="tcp", port_number=port)

            image = (self.results_subfolder / page_dict.get("screenshotPath")).read_bytes()

            screenshot = self.db_mgr.get_or_create(Screenshot, url=url)
            screenshot.port = port
            screenshot.endpoint = endpoint
            screenshot.target = screenshot.endpoint.target
            screenshot.image = image

            similar_pages = self._get_similar_pages(url, results)

            if similar_pages is not None:
                screenshot.similar_pages = similar_pages

            self.db_mgr.add(screenshot)
            self.output().touch()

        self.db_mgr.close()

    def run(self):
        """ Defines the options/arguments sent to aquatone after processing.

        cat webtargets.tesla.txt | /opt/aquatone -scan-timeout 900 -threads 20

        Returns:
            list: list of options/arguments, beginning with the name of the executable to run
        """
        self.results_subfolder.mkdir(parents=True, exist_ok=True)

        command = [
            tools.get("aquatone").get("path"),
            "-scan-timeout",
            self.scan_timeout,
            "-threads",
            self.threads,
            "-silent",
            "-out",
            self.results_subfolder,
        ]

        aquatone_input_file = self.results_subfolder / "input-from-webtargets"

        with open(aquatone_input_file, "w") as f:
            for target in self.db_mgr.get_all_web_targets():
                f.write(f"{target}\n")

        with open(aquatone_input_file) as target_list:
            subprocess.run(command, stdin=target_list)

        aquatone_input_file.unlink()

        self.parse_results()
