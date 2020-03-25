import sqlite3
import ipaddress
from pathlib import Path
from urllib.parse import urlparse

from cmd2 import ansi
from sqlalchemy.orm import sessionmaker
from sqlalchemy import exc, or_, create_engine
from sqlalchemy.sql.expression import func, ClauseElement

from .base_model import Base
from .port_model import Port
from .nse_model import NSEResult
from .target_model import Target
from .nmap_model import NmapResult
from .endpoint_model import Endpoint
from .ip_address_model import IPAddress
from .searchsploit_model import SearchsploitResult


class DBManager:
    def __init__(self, db_location):
        self.location = Path(db_location).resolve()
        self.connection_string = f"sqlite:///{self.location}"
        engine = create_engine(self.connection_string)
        Base.metadata.create_all(engine)  # noqa: F405
        session_factory = sessionmaker(bind=engine)
        self.session = session_factory()

    def get_or_create(self, model, defaults=None, **kwargs):
        """ Simple helper to either get an existing record if it exists otherwise create and return a new instance """
        instance = self.session.query(model).filter_by(**kwargs).first()
        if instance:
            return instance
        else:
            params = dict((k, v) for k, v in kwargs.items() if not isinstance(v, ClauseElement))
            if defaults:
                params.update(defaults)
            instance = model(**params)
            return instance

    def add(self, item):
        """ Simple helper to add a record to the database """
        try:
            self.session.add(item)
            self.session.commit()
        except (sqlite3.IntegrityError, exc.IntegrityError):
            print(ansi.style(f"[-] unique key constraint handled, moving on...", fg="bright_white"))
            self.session.rollback()

    def get_target_by_ip_or_hostname(self, ip_or_host):
        """ Simple helper to query a Target record by either hostname or ip address, whichever works """
        instance = (
            self.session.query(Target)
            .filter(
                or_(
                    Target.ip_addresses.any(
                        or_(IPAddress.ipv4_address.in_([ip_or_host]), IPAddress.ipv6_address.in_([ip_or_host]))
                    ),
                    Target.hostname == ip_or_host,
                )
            )
            .first()
        )
        if instance:
            return instance
        else:
            try:
                ipaddress.ip_interface(ip_or_host)
                is_ip_address = True
            except ValueError:
                is_ip_address = False

            if is_ip_address:
                tgt = self.get_or_create(Target)
                if isinstance(ipaddress.ip_address(ip_or_host), ipaddress.IPv4Address):  # ipv4 addr
                    ipaddr = IPAddress(ipv4_address=ip_or_host)
                elif isinstance(ipaddress.ip_address(ip_or_host), ipaddress.IPv6Address):  # ipv6
                    ipaddr = IPAddress(ipv6_address=ip_or_host)

                tgt.ip_addresses.append(ipaddr)
                return tgt

    def get_all_hostnames(self) -> list:
        """ Simple helper to return all hostnames from Target records """
        return [x[0] for x in self.session.query(Target.hostname).filter(Target.hostname != None)]  # noqa: E711

    def get_all_ipv4_addresses(self) -> list:
        """ Simple helper to return all ipv4 addresses from Target records """
        return [
            x[0] for x in self.session.query(IPAddress.ipv4_address).filter(IPAddress.ipv4_address != None)
        ]  # noqa: E711

    def get_all_ipv6_addresses(self) -> list:
        """ Simple helper to return all ipv6 addresses from Target records """
        return [
            x[0] for x in self.session.query(IPAddress.ipv6_address).filter(IPAddress.ipv6_address != None)
        ]  # noqa: E711

    def get_highest_id(self, table):
        """ Simple helper to get the highest id number of the given table """
        highest = self.session.query(func.max(table.id)).first()[0]
        return highest if highest is not None else 1

    def close(self):
        """ Simple helper to close the database session """
        self.session.close()

    def get_all_targets(self):
        """ Simple helper to return all ipv4/6 and hostnames produced by running amass """
        return self.get_all_hostnames() + self.get_all_ipv4_addresses() + self.get_all_ipv6_addresses()

    def get_all_endpoints(self):
        """ Simple helper that returns all Endpoints from the database """
        return self.session.query(Endpoint).all()

    def get_all_port_numbers(self):
        """ Simple helper that returns all Port.port_numbers from the database """
        return set(str(x[0]) for x in self.session.query(Port.port_number).all())

    def get_endpoint_by_status_code(self, code):
        """ Simple helper that returns all Endpoints filtered by status code """
        return self.session.query(Endpoint).filter(Endpoint.status_code == code).all()

    def get_endpoints_by_ip_or_hostname(self, ip_or_host):
        """ Simple helper that returns all Endpoints filtered by ip or hostname """
        endpoints = list()

        tmp_endpoints = self.session.query(Endpoint).filter(Endpoint.url.contains(ip_or_host)).all()

        for ep in tmp_endpoints:
            parsed_url = urlparse(ep.url)
            if parsed_url.hostname == ip_or_host:
                endpoints.append(ep)

        return endpoints

    def get_nmap_scans_by_ip_or_hostname(self, ip_or_host):
        """ Simple helper that returns all Endpoints filtered by ip or hostname """
        scans = list()

        for result in self.session.query(NmapResult).filter(NmapResult.commandline.contains(ip_or_host)).all():
            if result.commandline.split()[-1] == ip_or_host:
                scans.append(result)

        return scans

    def get_status_codes(self):
        """ Simple helper that returns all status codes found during scanning """
        return set(str(x[0]) for x in self.session.query(Endpoint.status_code).all())

    def get_and_filter(self, model, defaults=None, **kwargs):
        """ Simple helper to either get an existing record if it exists otherwise create and return a new instance """
        return self.session.query(model).filter_by(**kwargs).all()

    def get_all_nse_script_types(self):
        """ Simple helper that returns all NSE Script types from the database """
        return set(str(x[0]) for x in self.session.query(NSEResult.script_id).all())

    def get_nse_results_by_script_id(self, nse_script_id):
        """ Simple helper that returns all NSE Scripts filtered by its script id """
        return self.session.query(NSEResult).filter_by(script_id=nse_script_id).all()

    def get_all_nmap_reported_products(self):
        """ Simple helper that returns all products reported by nmap """
        return set(str(x[0]) for x in self.session.query(NmapResult.product).all())

    def get_all_exploit_types(self):
        """ Simple helper that returns all exploit types reported by searchsploit """
        return set(str(x[0]) for x in self.session.query(SearchsploitResult.type).all())

    def add_ipv4_or_v6_address_to_target(self, tgt, ipaddr):
        """ Simple helper that adds an appropriate IPAddress to the given target """

        if isinstance(ipaddress.ip_address(ipaddr), ipaddress.IPv4Address):  # ipv4 addr
            ip_address = self.get_or_create(IPAddress, ipv4_address=ipaddr)
            tgt.ip_addresses.append(ip_address)

        elif isinstance(ipaddress.ip_address(ipaddr), ipaddress.IPv6Address):  # ipv6
            ip_address = self.get_or_create(IPAddress, ipv6_address=ipaddr)
            tgt.ip_addresses.append(ip_address)

        return tgt
