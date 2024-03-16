# Nmap Parser

Small utility to parse greppable output of Nmap (from `-oG`) for a specified service into lines formatted as `host:port`
that can be easily piped into a downstream utility.

Minimal example:

```
python main.py --nmap_out=/tmp/nmap-out.gnmap --service_substr=http`
```

Example with debug logs:

```
python main.py --nmap_out=/tmp/nmap-out.gnmap --service_substr=http --v=1
```

Print help:

```
python main.py --help
```

Dependencies:

- `absl-py`