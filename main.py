"""Parse the greppable output of Nmap (from -oG) for a service into lines formatted as `host:port` and print the result.

Example:
    python3 main.py --nmap_out=/tmp/nmap-out.gnmap --service_substr=http

Example with debug logs:
    python3 main.py --nmap_out=/tmp/nmap-out.gnmap --service_substr=http --v=1
"""

import re

from absl import app
from absl import logging
from absl import flags

NMAP_OUT = flags.DEFINE_string("nmap_out", default=None, required="True",
                               help="The path to the file output when running nmap with '-oG'.")
SERVICE_SUBSTR = flags.DEFINE_string("service_substr", default=None, required=True,
                                     help="The substring of the service to filter for. Example: 'http'")

_HOST_PREFIX = "Host:"
_PORTS_PREFIX = "Ports:"
_PORTS_REGEX = re.compile("(?P<port>[0-9]+)/(?P<status>[a-z]*)/(?P<protocol>[a-z]*)//(?P<service>[a-z]*)///,?")


def _get_host(host_line: str) -> str:
    return host_line.split()[1]


def _get_ports_info(ports_line: str) -> list[tuple[int, str, str, str]]:
    ports_info = []
    for part in ports_line.split():
        matches = re.match(_PORTS_REGEX, part)
        if not matches:
            continue
        port = int(matches.groupdict()["port"])
        status = matches.groupdict()["status"]
        protocol = matches.groupdict()["protocol"]
        service = matches.groupdict()["service"]
        ports_info.append((port, status, protocol, service))
    return ports_info


def _build_service_map(ports_info: list[tuple[int, str, str, str]]) -> dict[str, list[int]]:
    service_map = {}
    for port, status, protocol, service in ports_info:
        if service not in service_map:
            service_map[service] = []
        service_map[service].append(port)
    return service_map


def _get_ports_for_service_substr(service_substr: str, service_map: dict[str, list[int]]) -> list[int]:
    service_ports = []
    for service, ports in service_map.items():
        if service_substr in service:
            service_ports.extend(ports)
    return service_ports


def _build_output(host: str, ports: list[int]) -> list[str]:
    output = []
    for port in ports:
        output.append(f"{host}:{port}")
    return output


def _parse_and_print():
    logging.debug(f"Reading input file: {NMAP_OUT.value}")
    host_ports_line = None
    with open(NMAP_OUT.value) as f:
        for line in f.readlines():
            if _PORTS_PREFIX in line:
                host_ports_line = line
                break
    if not host_ports_line:
        logging.fatal(f"No line with '{_PORTS_PREFIX}' found in input file: {NMAP_OUT.value}")
    if _HOST_PREFIX not in host_ports_line:
        logging.fatal(f"Line with '{_PORTS_PREFIX} does not contain '{_HOST_PREFIX}'")

    host = _get_host(host_ports_line)
    logging.debug(f"Host: {host}")
    ports_info = _get_ports_info(host_ports_line)
    logging.debug("All ports info:")
    for info in ports_info:
        logging.debug(info)
    service_map = _build_service_map(ports_info)
    logging.debug("Service map:")
    logging.debug(service_map)
    service_ports = _get_ports_for_service_substr(SERVICE_SUBSTR.value, service_map)
    host_with_ports = _build_output(host, service_ports)
    for line in host_with_ports:
        logging.debug(line)
        # Print to stdout for easy piping.
        print(line)


def main(argv):
    del argv  # Unused.
    _parse_and_print()


if __name__ == '__main__':
    app.run(main)
