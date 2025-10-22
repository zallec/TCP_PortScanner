# Async TCP Port Scanner

Small and simple asyncio-based TCP port scanner written in Python. It performs concurrent TCP connect scans against one or more hosts and can optionally attempt to grab small service banners (including a simple HTTP probe for common HTTP ports). I am a student that was trying to learn more about port scanners, so there is not much here, but any comments would be greatly appreciated.

This repository contains:

- `main.py` — the scanner implementation and CLI.

## Features

- Asyncio-based concurrent scanning
- Scan port ranges or comma-separated lists (e.g. `22,80,8000-8100`)
- Scan multiple hosts at once (comma-separated)
- Adjustable per-connection timeout and maximum concurrency
- Optional banner grabbing (small read or HTTP GET probe for HTTP ports)

## Requirements

- Python 3.8+ (asyncio.run is used)

No external dependencies.

## Safety & Legal

Only scan systems you own or have explicit permission to test. Unauthorized scanning may be illegal and/or against acceptable use policies.

## Usage

Basic CLI options (see `--help` for full list):

- `--hosts, -H` — Comma-separated hostnames or IPs (default in `main.py` is `130.0.0.1`).
- `--ports, -p` — Ports to scan. Supports ranges and lists (default is `1-1024`).
- `--timeout, -t` — Per-connection timeout in seconds (default 1.0).
- `--concurrency, -c` — Maximum concurrent connection attempts (default 500).
- `--banner` — Attempt to read a small banner from open ports.

Examples

Run a quick scan of common ports on a host:

```powershell
python main.py --hosts example.com --ports 22,80,443
```

Scan a range of ports with higher concurrency and shorter timeouts:

```powershell
python main.py --hosts 192.168.1.100 --ports 1-1024 --timeout 0.8 --concurrency 200
```

Scan multiple hosts and try to grab banners:

```powershell
python main.py --hosts example.com,192.168.1.50 --ports 80,443,8080 --banner
```

## Output

Open ports are printed to stdout in the format:

- `HOST:PORT OPEN` or
- `HOST:PORT OPEN  (banner: <text>)` when a banner is captured.

## Implementation notes

- The scanner uses TCP connect to determine open ports. It is not stealthy and will complete full TCP handshakes.
- Banner grabbing uses a small read; for common HTTP ports a simple HTTP/1.0 GET probe with a Host header is sent.
- Port parsing validates ranges and port numbers (1-65535).

## Contributing

Contributions are welcome. By submitting an issue or pull request you agree to license your contribution under the terms of this project's MIT License. See `CONTRIBUTING.md` for details on preferred practices and how to format contributions.

## License

This project is licensed under the MIT License — see the `LICENSE` file for details.

SPDX-License-Identifier: MIT