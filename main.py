"""Parse the greppable output of Nmap (from -oG) for a service into lines formatted as `host:port` and print the result.

Example:
    python main.py --nmap_out=/tmp/nmap-out.gnmap --service_substr=http

Example with debug logs:
    python main.py --nmap_out=/tmp/nmap-out.gnmap --service_substr=http --v=1
"""

import re

from absl import app
from absl import logging
from absl import flags

NMAP_OUT = flags.DEFINE_string("nmap_out", default=None, required="True",
                               help="The path to the file output when running nmap with '-oG'. Required.")
SERVICE_SUBSTR = flags.DEFINE_string("service_substr", default=None, required=True,
                                     help="The substring of the service to filter for. Example: 'http'. Required.")

_HOST_PREFIX = "Host: "
_PORTS_PREFIX = "Ports: "
_FIELD_SEPARATOR = "\t"
_PORT_INFO_SEPARATOR = ", "
_PORT_INFO_REGEX = re.compile(
    "(?P<port>[0-9]+)/(?P<state>[^/]*)/(?P<protocol>[^/]*)/(?P<owner>[^/]*)/(?P<service>[^/]*)/(?P<sun_rpc_info>[^/]*)/(?P<version_info>[^/]*)/[^/]*,?")


def _get_host(host_line: str) -> str:
    return host_line.split()[1]


def _get_ports_info(ports_line: str) -> list[tuple[int, str, str, str]]:
    ports_info = []
    for part in ports_line.split(_FIELD_SEPARATOR):
        if not part.startswith(_PORTS_PREFIX):
            continue
        for port_info in part.strip(_PORTS_PREFIX).split(_PORT_INFO_SEPARATOR):
            matches = re.match(_PORT_INFO_REGEX, port_info)
            if not matches:
                continue
            port = int(matches.groupdict()["port"])
            state = matches.groupdict()["state"]
            protocol = matches.groupdict()["protocol"]
            service = matches.groupdict()["service"]
            ports_info.append((port, state, protocol, service))
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


def _get_hosts_with_ports(host_ports_lines: list[str]) -> list[str]:
    host_with_ports = []
    for host_ports_line in host_ports_lines:
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
        host_with_ports.extend(_build_output(host, service_ports))
    return host_with_ports


def _parse_and_print():
    logging.debug(f"Reading input file '{NMAP_OUT.value}'")
    host_ports_lines = []
    with open(NMAP_OUT.value) as f:
        for line in f.readlines():
            if _HOST_PREFIX in line and _PORTS_PREFIX in line:
                host_ports_lines.append(line)
    if not host_ports_lines:
        logging.fatal(f"No line with '{_PORTS_PREFIX}' found in input file '{NMAP_OUT.value}'")

    logging.debug(f"Found {len(host_ports_lines)} Host/Port lines")
    host_with_ports = _get_hosts_with_ports(host_ports_lines)

    if not host_with_ports:
        logging.warning(
            f"No ports found for service substring '{SERVICE_SUBSTR.value}' and input file '{NMAP_OUT.value}'")
    else:
        logging.debug(f"Parsed {len(host_with_ports)} Host/Port")
    for line in host_with_ports:
        logging.debug(line)
        # Print to stdout for easy piping.
        print(line)


def main(argv):
    del argv  # Unused.
    _parse_and_print()


if __name__ == '__main__':
    app.run(main)
