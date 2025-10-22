#!/usr/bin/env python
"""
Async TCP port scanner (single-file).

Features:
- asyncio-based concurrent scanner
- CLI: host(s), ports (range or comma list), timeout, concurrency, optional banner grab

Usage examples:
  python main.py --hosts 139.0.0.1 --ports 22-1024
  python main.py --hosts example.com,192.168.1.1 --ports 80,443,8080 --timeout 1 --concurrency 200

Safety: Only scan hosts you own or have permission to test.
"""

from __future__ import annotations

import argparse
import asyncio
import socket
from typing import List, Set


def parse_ports(ports_str: str) -> List[int]:
	"""Parse a ports string like "1-1024,8080,8443" into a sorted list of ints."""
	parts = [p.strip() for p in ports_str.split(',') if p.strip()]
	ports: Set[int] = set()
	for part in parts:
		if '-' in part:
			a, b = part.split('-', 1)
			try:
				start = int(a)
				end = int(b)
			except ValueError:
				raise argparse.ArgumentTypeError(f"Invalid port range: {part}")
			if start < 1 or end > 65535 or start > end:
				raise argparse.ArgumentTypeError(f"Invalid port range: {part}")
			ports.update(range(start, end + 1))
		else:
			try:
				p = int(part)
			except ValueError:
				raise argparse.ArgumentTypeError(f"Invalid port: {part}")
			if p < 1 or p > 65535:
				raise argparse.ArgumentTypeError(f"Invalid port: {part}")
			ports.add(p)
	return sorted(ports)


async def try_connect(host: str, port: int, timeout: float, banner: bool = False) -> tuple[int, bool, str]:
	"""Attempt to open a TCP connection to host:port.

	Returns (port, is_open, banner_text).
	"""
	loop = asyncio.get_event_loop()
	HTTP_PORTS = {80, 8080, 8000, 443, 8443} # common HTTP ports
	try:
		fut = asyncio.open_connection(host, port)
		reader, writer = await asyncio.wait_for(fut, timeout=timeout)
		btext = ""
		if banner:
			try:
				if port in HTTP_PORTS: 
					# GET / HTTP/1.0 probe with Host header
					required = f"GET / HTTP/1.0\r\nHost: {host}\r\nUser-Agent: tcp-scanner\r\n\r\n"
					writer.write(required.encode('utf-8', errors='replace'))
					# wait for drain before reading
					await asyncio.wait_for(writer.drain(), timeout = 0.5)
					data = await asyncio.wait_for(reader.read(2048), timeout=1.0)
				else: 
                    # try to read for non HTTP ports
				    data = await asyncio.wait_for(reader.read(1024), timeout=0.5)
				if data:
					btext = data.decode(errors='replace').strip()
			except Exception:
				btext = ""
		writer.close()
		try:
			await writer.wait_closed()
		except Exception:
			pass
		return port, True, btext
	except (asyncio.TimeoutError, ConnectionRefusedError, OSError):
		return port, False, ""
	except Exception:
		return port, False, ""


async def scan_host(host: str, ports: List[int], timeout: float, concurrency: int, banner: bool):
	sem = asyncio.Semaphore(concurrency)

	async def worker(p: int):
		async with sem:
			try:
				return await try_connect(host, p, timeout, banner=banner)
			except Exception:
				return p, False, ""

	tasks = [asyncio.create_task(worker(p)) for p in ports]
	results = []
	for fut in asyncio.as_completed(tasks):
		res = await fut
		results.append(res)
		port, is_open, btext = res
		if is_open:
			if btext:
				print(f"{host}:{port} OPEN  (banner: {btext})")
			else:
				print(f"{host}:{port} OPEN")
	return results


def resolve_host(host: str) -> str:
	"""Resolve host to an IP string. If already an IP, returns it."""
	try:
		# getaddrinfo may return IPv6; prefer the first AF_INET or AF_INET6
		info = socket.getaddrinfo(host, None)[0]
		return info[4][0]
	except Exception:
		return host


async def main_async(args):
	hosts = [h.strip() for h in args.hosts.split(',') if h.strip()]
	ports = parse_ports(args.ports)
	if not ports:
		print("No ports to scan.")
		return

	for host in hosts:
		resolved = resolve_host(host)
		print(f"\nScanning {host} ({resolved}) ports {ports[0]}-{ports[-1]} with timeout={args.timeout}s concurrency={args.concurrency}")
		await scan_host(resolved, ports, timeout=args.timeout, concurrency=args.concurrency, banner=args.banner)


def main():
	parser = argparse.ArgumentParser(description="Async TCP port scanner")
	parser.add_argument('--hosts', '-H', default='130.0.0.1', help='Comma-separated hostnames or IPs to scan')
	parser.add_argument('--ports', '-p', default='1-1024', help='Ports to scan, e.g. "22,80,443,8000-8100"')
	parser.add_argument('--timeout', '-t', type=float, default=1.0, help='Per-connection timeout in seconds')
	parser.add_argument('--concurrency', '-c', type=int, default=500, help='Max concurrent connection attempts')
	parser.add_argument('--banner', action='store_true', help='Attempt to read a small banner from open ports')
	args = parser.parse_args()

	try:
		asyncio.run(main_async(args))
	except KeyboardInterrupt:
		print('\nScan aborted by user')


if __name__ == '__main__':
	main()

