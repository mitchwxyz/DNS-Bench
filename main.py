"""A simple tool to check response times of various DNS servers."""

import time
from collections import defaultdict
from typing import Any

from dns.resolver import Resolver
from rich.console import Console
from rich.table import Table


def benchmark_dns_servers(
    servers: list[str], domain: str, num_queries: int = 8
) -> dict[str, dict[str, Any]]:
    """Benchmark DNS server response times for a given domain by sending multiple queries.

    Args:
        servers (list[str]): A list of DNS server IP addresses to test.
        domain (str): The domain name to query. Ex. google.com
        num_queries (int): Number of queries to send to each server. Default is 8.

    Returns:
       dict: A dictionary containing the following keys for each server:
           "times" (list[float]): List of response times in milliseconds.
           "stdev" (float): Standard deviation of response times.
           "name" (str): Resolved name for the server.
            "error" (bool): An error was encountered.

    """
    results = defaultdict(dict)

    for server in servers:
        resolver = Resolver()
        resolver.nameservers = [server]
        times = []
        failure_count = 0

        try:
            # Resolve DNS server's hostname for informative output.
            dns_name = str(resolver.resolve_address(server)[0])
            print(f"Testing Response Times from {dns_name}")
        except Exception as e:
            print(f"Error resolving name for server {server}: {e}")
            dns_name = "Unknown"
            failure_count += 1

        for _ in range(num_queries):
            start = time.time()
            try:
                resolver.resolve(domain)
                elapsed = time.time() - start
                times.append(elapsed * 1000)  # Convert seconds to milliseconds
            except Exception as e:
                print(f"Error querying {domain} on {server}: {e}")
                failure_count += 1
            if failure_count > 2:
                print(f"More than 2 Errors attempting to query {server}. Skipping.")
                break

        if times:
            # Calculate mean and standard deviation of response times
            mean = sum(times) / len(times)
            variance = sum((x - mean) ** 2 for x in times) / len(times)
            stdev = variance**0.5

            results[server] = {
                "times": times,
                "mean": mean,
                "stdev": stdev,
                "name": dns_name,
                "error": False,
            }
        else:
            results[server] = {
                "name": dns_name,
                "error": True,
            }

    return results


def red_string(input: str | int | float) -> str:
    """Convert to string and Markup red."""
    return f"[red]{input!s}[/red]"


def display_results(results: dict[str, dict[str, Any]]) -> None:
    """Display the results of DNS server benchmarks in a tabular format using the Rich library.

    Args:
        results (dict): A dictionary containing benchmark results for each DNS server.
            "times" (list[float]): List of response times in milliseconds.
            "stdev" (float): Standard deviation of response times.
            "name" (str): Resolved name for the server.
            "error" (bool): An error was encountered.

    """
    console = Console()
    table = Table(show_header=True, header_style="bold magenta")

    # Define table columns
    table.add_column("DNS Server", justify="left")
    table.add_column("DNS Name", justify="left")
    table.add_column("Response Times (ms)", justify="right")
    table.add_column("Average (ms)", justify="center")
    table.add_column("Std Dev (ms)", justify="center")

    for server, data in results.items():
        name = data.get("name", "Unknown")
        times = data.get("times", [])
        mean = data.get("mean", 0.0)
        stddev = data.get("stdev", 0.0)
        error = data.get("error", False)

        # Handle empty times list gracefully
        if not times or error:
            table.add_row(
                red_string(server),
                red_string(name),
                red_string("Error on query attempt"),
                red_string(mean),
                red_string(stddev),
            )
        else:
            times_str = ",".join(f"{time: >3.0f}" for time in times)
            table.add_row(server, name, times_str, f"{mean:.1f}", f"{stddev:.1f}")

    # Display the table
    console.print(table)


if __name__ == "__main__":
    # Example DNS servers and domain to query
    servers = [
        "8.8.8.8",  # Google Public DNS
        "8.8.4.4",  # Google Public DNS
        "1.1.1.1",  # Cloudflare DNS
        "1.0.0.1",  # Cloudflare DNS
        "208.67.222.222",  # OpenDNS
        "208.67.220.220",  # OpenDNS
        "4.2.2.1",  # Level 3 Communications
        "4.2.2.2",  # Level 3 Communications
        "4.2.2.3",  # Level 3 Communications
        "4.2.2.4",  # Level 3 Communications
        "4.2.2.5",  # Level 3 Communications
        "4.2.2.6",  # Level 3 Communications
        "209.244.0.3",  # CenturyLink DNS
        "209.244.0.4",  # CenturyLink DNS
        "0.0.0.0",  # Sinkhole to test error handling
        "205.171.3.65",  # Windstream DNS
        "192.168.1.190",  # Local DNS
    ]

    results = benchmark_dns_servers(servers, "apple.com")
    display_results(results)
